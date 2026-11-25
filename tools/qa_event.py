#!/usr/bin/env python3
"""Screenshots for the event and payment sections (development only)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "qa"
OUT.mkdir(exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def shoot(page, target, prefix, selectors):
    page.goto(target, wait_until="load")
    page.evaluate("document.querySelectorAll('.reveal').forEach(el => el.classList.add('is-visible'))")
    page.wait_for_timeout(300)
    for name, selector in selectors:
        locator = page.locator(selector).first
        try:
            locator.scroll_into_view_if_needed()
            page.wait_for_timeout(120)
            locator.screenshot(path=str(OUT / f"{prefix}-{name}.png"))
        except Exception as error:  # noqa: BLE001
            print("skip", prefix, name, type(error).__name__)


TARGETS = [
    (1440, "index.html", "ev-1440", [("announce", ".announcement"), ("event", ".event"), ("donate", ".donate-band")]),
    (1024, "index.html", "ev-1024", [("event", ".event"), ("donate", ".donate-band")]),
    (768, "index.html", "ev-768", [("announce", ".announcement"), ("event", ".event")]),
    (480, "index.html", "ev-480", [("announce", ".announcement"), ("event", ".event"), ("donate", ".donate-band")]),
    (390, "index.html", "ev-390", [("announce", ".announcement"), ("event", ".event")]),
    (320, "index.html", "ev-320", [("announce", ".announcement"), ("event", ".event")]),
    (1440, "donate.html", "pay-1440", [("card", ".payment-card")]),
    (768, "donate.html", "pay-768", [("card", ".payment-card")]),
    (390, "donate.html", "pay-390", [("card", ".payment-card")]),
    (320, "donate.html", "pay-320", [("card", ".payment-card")]),
    (1440, "hi/index.html", "hi-1440", [("announce", ".announcement"), ("event", ".event")]),
    (390, "hi/index.html", "hi-390", [("announce", ".announcement"), ("event", ".event"), ("donate", ".donate-band")]),
    (320, "hi/index.html", "hi-320", [("event", ".event")]),
    (390, "hi/donate.html", "hi-pay-390", [("card", ".payment-card")]),
]

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    for width, relative, prefix, selectors in TARGETS:
        page.set_viewport_size({"width": width, "height": 900})
        shoot(page, (ROOT / relative).as_uri(), prefix, selectors)
    browser.close()
print("done")
