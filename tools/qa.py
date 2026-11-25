#!/usr/bin/env python3
"""Capture readable section screenshots for visual QA (development only)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "qa"
OUT.mkdir(exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def force_reveal(page):
    page.evaluate("document.querySelectorAll('.reveal').forEach(el => el.classList.add('is-visible'))")
    page.wait_for_timeout(250)


def shoot(page, url, prefix, selectors):
    page.goto(url, wait_until="networkidle")
    force_reveal(page)
    for name, selector in selectors:
        locator = page.locator(selector).first
        try:
            locator.scroll_into_view_if_needed()
            page.wait_for_timeout(120)
            locator.screenshot(path=str(OUT / f"{prefix}-{name}.png"))
        except Exception as error:  # noqa: BLE001
            print("skip", prefix, name, error)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True)
    desktop = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    page = desktop.new_page()

    shoot(
        page,
        (ROOT / "index.html").as_uri(),
        "home",
        [
            ("hero", ".hero"),
            ("manifesto", ".manifesto"),
            ("pillars", ".pillars"),
            ("mosaic", ".mosaic"),
            ("feature", ".feature"),
            ("press", ".press"),
            ("donate", ".donate-band"),
            ("strip", ".strip"),
            ("visit", ".visit"),
            ("footer", ".footer"),
        ],
    )

    shoot(
        page,
        (ROOT / "about.html").as_uri(),
        "about",
        [("hero", ".page-hero"), ("story", ".about-story"), ("guide", ".about-story + .section"), ("values", ".values")],
    )

    shoot(
        page,
        (ROOT / "seva.html").as_uri(),
        "seva",
        [("intro", ".section--tight"), ("block", ".seva-block"), ("aside", ".section--raised"), ("cta", ".cta-band")],
    )

    shoot(page, (ROOT / "gallery.html").as_uri(), "gallery", [("grid", ".section"), ("hero", ".page-hero")])
    shoot(page, (ROOT / "press.html").as_uri(), "press", [("feature", ".press-feature"), ("grid", ".press-grid"), ("kit", ".media-kit")])
    shoot(page, (ROOT / "donate.html").as_uri(), "donate", [("layout", ".donate-layout"), ("after", ".section--raised"), ("faq", ".faq")])
    shoot(page, (ROOT / "contact.html").as_uri(), "contact", [("grid", ".contact-grid"), ("forms", ".accordion-forms")])

    mobile = browser.new_context(
        viewport={"width": 390, "height": 844}, device_scale_factor=1, is_mobile=True, has_touch=True
    )
    mpage = mobile.new_page()
    shoot(
        mpage,
        (ROOT / "hi" / "index.html").as_uri(),
        "mobile-home",
        [("hero", ".hero"), ("pillars", ".pillars"), ("donate", ".donate-band"), ("footer", ".footer")],
    )
    shoot(mpage, (ROOT / "hi" / "donate.html").as_uri(), "mobile-donate", [("layout", ".donate-layout")])

    browser.close()
print("done")
