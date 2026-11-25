#!/usr/bin/env python3
"""Capture viewport-sized section shots with lazy images loaded (dev only)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "qa"
OUT.mkdir(exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

SECTIONS = [
    ("hero", ".hero"),
    ("event", "#katha"),
    ("manifesto", ".manifesto"),
    ("pillars", ".pillars"),
    ("mosaic", ".mosaic"),
    ("feature", ".feature"),
    ("press", ".press"),
    ("donate", ".donate-band"),
    ("strip", ".strip"),
    ("visit", ".visit"),
]


def load_all(page):
    page.evaluate(
        """async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 600) {
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 60));
        }
        window.scrollTo(0, 0);
    }"""
    )
    page.evaluate("document.querySelectorAll('.reveal').forEach(el => el.classList.add('is-visible'))")
    page.wait_for_timeout(600)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True)
    for width, height, suffix in [(1440, 900, "1440"), (390, 844, "390")]:
        context = browser.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        page.goto((ROOT / "index.html").as_uri(), wait_until="load")
        load_all(page)
        for name, selector in SECTIONS:
            locator = page.locator(selector).first
            top = locator.evaluate("el => el.getBoundingClientRect().top + window.scrollY")
            page.evaluate(f"window.scrollTo(0, {max(0, top - 70)})")
            page.wait_for_timeout(350)
            page.screenshot(path=str(OUT / f"view-{suffix}-{name}.png"))
        context.close()
    browser.close()
print("done")
