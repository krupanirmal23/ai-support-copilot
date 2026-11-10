"""Convert Supabase Auth .mdx docs -> clean Markdown -> ~500-token chunks -> FAISS index.

Usage:
    python -m copilot.ingest                # uses config.yaml
    python -m copilot.ingest --chunk-tokens 300 --index-dir data/index_300
"""
import argparse
import json
import re
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from copilot.config import load_config, p

DOCS_BASE_URL = "https://supabase.com/docs/guides/"


# ---------------------------------------------------------------- MDX -> Markdown
def _resolve_partials(text: str, partials_dir: Path) -> str:
    def repl(m):
        f = partials_dir / m.group(1)
        return f.read_text() if f.exists() else ""
    for _ in range(3):  # partials can include partials
        text = re.sub(r'<\$Partial\s+path="([^"]+)"[^>]*/>', repl, text)
    return text


def _resolve_shared_data(text: str, shared: dict) -> str:
    """<SharedData data="config">auth.rate_limits.sms.requests_per_hour</SharedData> -> "30"
    (values come from packages/shared-data/config.ts in the same repo/commit)."""
    def repl(m):
        node = shared
        for key in m.group(1).strip().split("."):
            if not isinstance(node, dict) or key not in node:
                return m.group(1)
            node = node[key]
        if isinstance(node, dict) and "value" in node:
            return f"{node['value']} {node.get('unit', '')}".strip()
        return str(node)
    return re.sub(r'<SharedData data="config">([^<]+)</SharedData>', repl, text)


def mdx_to_markdown(text: str, partials_dir: Path, shared: dict | None = None) -> tuple[str, str]:
    """Return (title, markdown). Keeps prose and code; drops JSX wrappers.
    Inside <Tabs>, prose from every tab is kept but code only from the first tab
    (tabs are mostly the same snippet in 5 languages, which bloats chunks)."""
    title = ""
    fm = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if fm:
        t = re.search(r"^title:\s*['\"]?(.*?)['\"]?\s*$", fm.group(1), flags=re.M)
        title = t.group(1) if t else ""
        sub = re.search(r"^subtitle:\s*['\"]?(.*?)['\"]?\s*$", fm.group(1), flags=re.M)
        text = text[fm.end():]
        if sub:
            text = sub.group(1) + "\n\n" + text
    text = _resolve_partials(text, partials_dir)
    if shared:
        text = _resolve_shared_data(text, shared)
    # collapse JSX tags that span several lines (outside code fences) onto one line
    parts = re.split(r"(```.*?```)", text, flags=re.S)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"</?\$?[A-Z][\w.]*[^<>]*?>",
                          lambda m: re.sub(r"\s*\n\s*", " ", m.group(0)), parts[i])
    text = "".join(parts)

    out, in_code, tab_index, keep_code = [], False, 0, True
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            if keep_code:
                out.append(line)
            in_code = not in_code
            continue
        if in_code:
            if keep_code:
                out.append(line)
            continue
        if re.match(r"<Tabs\b", s):
            tab_index = 0
        m = re.match(r'<TabPanel\b.*?label="([^"]+)"', s)
        if m:
            tab_index += 1
            keep_code = tab_index == 1
            out.append(f"\n**{m.group(1)}:**\n")
            continue
        if re.match(r"</Tabs>", s):
            keep_code = True
        m = re.match(r'<Admonition\b.*?type="(\w+)"', s)
        if m:
            out.append(f"\n> **{m.group(1).capitalize()}:** ")
            continue
        if re.match(r"^(import|export)\s", s):
            continue
        line = re.sub(r'<Price\s+price="([^"]+)"\s*/>', r"$\1", line)   # pricing partials
        # drop remaining JSX tags (opening/closing/self-closing) but keep inner text
        line = re.sub(r"</?\$?[A-Z][\w.]*(\s[^<>]*?)?/?>", "", line)
        line = re.sub(r"\{/\*.*?\*/\}", "", line)            # MDX comments
        out.append(line)
    md = "\n".join(out)
    md = re.sub(r"\]\(/docs/", "](https://supabase.com/docs/", md)
    md = re.sub(r"\]\(/dashboard/", "](https://supabase.com/dashboard/", md)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return title, f"# {title}\n\n{md}\n"


# ---------------------------------------------------------------- chunking
def split_sections(md: str):
    """Split on ## / ### headings; yield (heading_path, text)."""
    sections, current, head = [], [], ""
    in_code = False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        m = None if in_code else re.match(r"^(#{2,3})\s+(.*)", line)
        if m:
            if current:
                sections.append((head, "\n".join(current).strip()))
            head, current = m.group(2).strip(), [line]
        else:
            current.append(line)
    if current:
        sections.append((head, "\n".join(current).strip()))
    return [s for s in sections if s[1]]


def chunk_page(md: str, tokenizer, chunk_tokens: int, overlap_tokens: int):
    """Greedy pack of paragraphs within a section up to chunk_tokens; consecutive
    chunks of the same section share ~overlap_tokens of trailing text."""
    chunks = []
    for head, text in split_sections(md):
        paras = [x for x in re.split(r"\n\s*\n", text) if x.strip()]
        buf, buf_tok = [], 0
        for para in paras:
            n = len(tokenizer.encode(para, add_special_tokens=False))
            if n > chunk_tokens:  # very long paragraph/code block: hard split by tokens
                ids = tokenizer.encode(para, add_special_tokens=False)
                pieces = [tokenizer.decode(ids[i:i + chunk_tokens])
                          for i in range(0, len(ids), chunk_tokens - overlap_tokens)]
            else:
                pieces = [para]
            for piece in pieces:
                pn = len(tokenizer.encode(piece, add_special_tokens=False))
                if buf and buf_tok + pn > chunk_tokens:
                    chunks.append((head, "\n\n".join(buf)))
                    # overlap: carry trailing paragraphs up to overlap_tokens
                    carry, ct = [], 0
                    for prev in reversed(buf):
                        t = len(tokenizer.encode(prev, add_special_tokens=False))
                        if ct + t > overlap_tokens:
                            break
                        carry.insert(0, prev)
                        ct += t
                    buf, buf_tok = carry, ct
                buf.append(piece)
                buf_tok += pn
        if buf:
            chunks.append((head, "\n\n".join(buf)))
    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk-tokens", type=int)
    ap.add_argument("--overlap-tokens", type=int)
    ap.add_argument("--index-dir")
    ap.add_argument("--skip-convert", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    ct = args.chunk_tokens or cfg["chunking"]["chunk_tokens"]
    ot = args.overlap_tokens or cfg["chunking"]["overlap_tokens"]
    raw_dir, docs_dir = p(cfg["corpus"]["raw_dir"]), p(cfg["corpus"]["docs_dir"])
    index_dir = p(args.index_dir or cfg["corpus"]["index_dir"])
    index_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.load(open(raw_dir / "manifest.json"))
    if not args.skip_convert:
        docs_dir.mkdir(parents=True, exist_ok=True)
        shared = json.load(open(raw_dir / "_shared_data_config.json"))
        for page in manifest["pages"]:
            title, md = mdx_to_markdown((raw_dir / page["file"]).read_text(), raw_dir / "_partials", shared)
            page["title"] = title
            (docs_dir / page["file"].replace("/", "__").replace(".mdx", ".md")).write_text(md)
        json.dump(manifest, open(raw_dir / "manifest.json", "w"), indent=2)

    model = SentenceTransformer(cfg["embedding"]["model"])
    tok = model.tokenizer
    records = []
    for page in manifest["pages"]:
        md = (docs_dir / page["file"].replace("/", "__").replace(".mdx", ".md")).read_text()
        for i, (head, text) in enumerate(chunk_page(md, tok, ct, ot)):
            slug = page["file"].replace(".mdx", "")
            records.append({
                "chunk_id": f"{slug}#{i}",
                "page": slug,
                "title": page["title"],
                "section": head,
                "url": DOCS_BASE_URL + slug,
                "text": text,
                "n_tokens": len(tok.encode(text, add_special_tokens=False)),
            })
    embed_inputs = [f"{r['title']} > {r['section']}\n{r['text']}" for r in records]
    emb = model.encode(embed_inputs, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(np.asarray(emb, dtype="float32"))
    faiss.write_index(index, str(index_dir / "faiss.index"))
    with open(index_dir / "chunks.jsonl", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    stats = {"pages": len(manifest["pages"]), "chunks": len(records),
             "chunk_tokens": ct, "overlap_tokens": ot,
             "mean_chunk_tokens": round(float(np.mean([r["n_tokens"] for r in records])), 1),
             "embedding_model": cfg["embedding"]["model"]}
    json.dump(stats, open(index_dir / "stats.json", "w"), indent=2)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
