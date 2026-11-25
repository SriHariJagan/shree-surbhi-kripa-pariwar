#!/usr/bin/env python3
"""Functional smoke test: copy buttons, UPI links, menu, event links, gallery."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        permissions=["clipboard-read", "clipboard-write"],
    )
    page = context.new_page()

    # Copy buttons on the donate page
    page.goto((ROOT / "donate.html").as_uri(), wait_until="load")
    buttons = page.locator(".copy-btn")
    print("copy buttons:", buttons.count())
    expected = page.locator(".copy-btn").first.get_attribute("data-copy")
    buttons.first.click()
    value = page.evaluate("navigator.clipboard.readText()")
    print("first copy:", value, "OK" if value == expected else "MISMATCH")
    label = buttons.first.text_content()
    print("copied label:", label)

    # Every copy button matches its visible target
    values = page.evaluate(
        "Array.from(document.querySelectorAll('.copy-btn')).map(b => b.dataset.copy)"
    )
    print("copy values unique:", len(set(values)), "of", len(values))

    # UPI deep links
    hrefs = page.evaluate(
        "Array.from(document.querySelectorAll('a[href^=\"upi:\"]')).map(a => a.getAttribute('href'))"
    )
    print("upi links:", hrefs)

    # Event section
    page.goto((ROOT / "index.html").as_uri(), wait_until="load")
    print("event anchor:", page.locator("#katha").count())
    print("event tel links:", page.evaluate(
        "Array.from(document.querySelectorAll('.event__contact a')).map(a => a.getAttribute('href'))"
    ))
    print("announcement target:", page.locator(".announcement__link").get_attribute("href"))

    # Mobile menu
    mobile = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    mpage = mobile.new_page()
    mpage.goto((ROOT / "index.html").as_uri(), wait_until="load")
    toggle = mpage.locator(".menu-toggle").first
    toggle.click()
    mpage.wait_for_timeout(350)
    print("menu open:", mpage.locator("body").get_attribute("data-menu") or mpage.locator(".menu.is-open").count())
    print("menu visible:", mpage.locator(".menu").first.is_visible())
    mpage.keyboard.press("Escape")
    mpage.wait_for_timeout(700)
    print("menu after esc:", mpage.locator(".menu").first.is_visible())

    # Gallery filter
    mpage.goto((ROOT / "gallery.html").as_uri(), wait_until="load")
    total = mpage.locator(".gallery-item").count()
    filter_buttons = mpage.locator("[data-filter]")
    print("gallery items:", total, "filters:", filter_buttons.count())
    if filter_buttons.count() > 1:
        data_filter = filter_buttons.nth(1).get_attribute("data-filter")
        filter_buttons.nth(1).click()
        mpage.wait_for_timeout(300)
        visible = mpage.evaluate(
            "Array.from(document.querySelectorAll('.gallery-item')).filter(el => !el.hidden && el.offsetParent !== null).length"
        )
        print("filter", data_filter, "visible:", visible)

    browser.close()
print("done")
