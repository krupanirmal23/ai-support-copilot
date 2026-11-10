"""Headless-Chromium screenshots of the running Streamlit app.

    streamlit run app.py --server.headless true --server.port 8501 &
    python scripts/screenshot.py --question "How long is a TOTP MFA code valid?" \
        --question "How do I create a storage bucket and upload a file?"
"""
import argparse

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://localhost:8501")
ap.add_argument("--question", action="append", default=[])
ap.add_argument("--out-dir", default="docs")
ap.add_argument("--escalate-first", action="store_true", help="click Escalate to human on the first answer")
ap.add_argument("--chrome", default="/usr/bin/google-chrome")
args = ap.parse_args()

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=args.chrome, headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 1350})
    page.goto(args.url)
    page.wait_for_selector("text=AI Support Copilot", timeout=120_000)
    for i, q in enumerate(args.question, 1):
        box = page.get_by_placeholder("Ask a question about Supabase Auth…")
        box.fill(q)
        box.press("Enter")
        # each finished answer renders one "Model: ..." caption
        for _ in range(600):
            if page.get_by_text("Model:").count() >= i and page.get_by_text("Retrieving and drafting").count() == 0:
                break
            page.wait_for_timeout(500)
        page.wait_for_timeout(1500)
    if args.escalate_first:
        page.get_by_role("button", name="Escalate to human").first.click()
        page.wait_for_selector("text=Escalated (ticket", timeout=60_000)
        page.wait_for_timeout(1000)
    page.screenshot(path=f"{args.out_dir}/screenshot_chat.png", full_page=True)
    page.get_by_text("Review queue").first.click()
    page.wait_for_selector("text=Human-review queue", timeout=60_000)
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{args.out_dir}/screenshot_review_queue.png", full_page=True)
    browser.close()
print("saved")
