"""Streamlit UI: chat with cited sources + confidence, 'Escalate to human', and a review-queue page.

    streamlit run app.py
"""
import streamlit as st

from copilot.config import load_config
from copilot.pipeline import Copilot
from copilot import review_queue as rq

st.set_page_config(page_title="AI Support Copilot", page_icon="💬", layout="wide")
cfg = load_config()


@st.cache_resource(show_spinner="Loading retrieval index and model…")
def get_copilot():
    return Copilot(cfg)


@st.cache_resource
def get_db():
    return rq.connect(cfg)


con = get_db()
page = st.sidebar.radio("Page", ["Ask", "Review queue"])
st.sidebar.markdown("---")
st.sidebar.caption(f"Corpus: Supabase Auth docs (Apache-2.0)  \n"
                   f"Gate: retrieval score ≥ {cfg['gate']['min_retrieval_score']}, "
                   f"needs a citation, no 'I don't know'  \n"
                   f"top-k = {cfg['retrieval']['top_k']} · prompt {cfg['generation']['prompt_version']}")

if page == "Ask":
    st.title("AI Support Copilot")
    st.caption("Answers come only from the Supabase Auth docs, with citations. "
               "Low-confidence answers go to a human instead of the customer.")
    st.info("This hosted demo runs **Qwen2.5-3B-Instruct Q4_K_M** on free CPU. "
            "Answers usually take about 10–20 seconds. "
            "The review queue is a local SQLite file and resets when the Space restarts.")
    if "history" not in st.session_state:
        st.session_state.history = []

    q = st.chat_input("Ask a question about Supabase Auth…")
    if q:
        with st.spinner("Retrieving and drafting…"):
            res = get_copilot().ask(q)
        if not res["shown_to_user"]:
            res["ticket_id"] = rq.enqueue(con, q, res["answer"], res["confidence"], res["gate_reasons"],
                                          [c["chunk_id"] for c in res["retrieved"]], source="gate")
        st.session_state.history.append(res)

    for i, res in enumerate(st.session_state.history):
        with st.chat_message("user"):
            st.write(res["question"])
        with st.chat_message("assistant"):
            conf = res["confidence"]
            if res["shown_to_user"]:
                st.markdown(res["answer"])
            else:
                st.warning(f"Not confident enough to answer. Sent to the human-review queue "
                           f"(ticket #{res.get('ticket_id')}). Reasons: {', '.join(res['gate_reasons'])}")
            cols = st.columns([1, 1, 2])
            cols[0].metric("Confidence (retrieval score)", f"{conf:.2f}",
                           help=f"Gate threshold: {cfg['gate']['min_retrieval_score']}")
            cols[1].metric("Latency", f"{res['latency_s']:.1f}s")
            if res["shown_to_user"] and not res.get("escalated"):
                if cols[2].button("Escalate to human", key=f"esc{i}"):
                    res["ticket_id"] = rq.enqueue(con, res["question"], res["answer"], conf,
                                                  ["user_escalated"],
                                                  [c["chunk_id"] for c in res["retrieved"]], source="user")
                    res["escalated"] = True
                    st.rerun()
            elif res.get("escalated"):
                cols[2].success(f"Escalated (ticket #{res['ticket_id']})")
            with st.expander("Sources", expanded=res["shown_to_user"]):
                cited = set(res["valid_citations"])
                for n, c in enumerate(res["retrieved"], 1):
                    mark = "✅ cited" if c["chunk_id"] in cited else "retrieved"
                    st.markdown(f"**[S{n}]** [{c['title']} › {c['section'] or 'intro'}]({c['url']}) "
                                f"· score {c['score']:.2f} · {mark}")
            st.caption(f"Model: {res['model']}")

else:
    st.title("Human-review queue")
    st.caption("This queue is stored in a local SQLite file and resets when the Space restarts.")
    status = st.radio("Status", ["open", "resolved"], horizontal=True)
    items = rq.list_items(con, status)
    st.caption(f"{len(items)} {status} item(s)")
    for it in items:
        with st.container(border=True):
            st.markdown(f"**#{it['id']} · {it['question']}**")
            st.caption(f"{it['created_at']} · source: {it['source']} · confidence {it['confidence']:.2f} · "
                       f"reasons: {it['reasons']}")
            st.text_area("Draft answer (not shown to customer)", it["draft_answer"] or "",
                         key=f"d{it['id']}", disabled=True, height=90)
            if status == "open":
                ans = st.text_area("Reviewer answer", key=f"a{it['id']}", height=90)
                if st.button("Resolve", key=f"r{it['id']}") and ans.strip():
                    rq.resolve(con, it["id"], ans.strip())
                    st.rerun()
            else:
                st.markdown(f"**Reviewer answer:** {it['reviewer_answer']}")
