#!/usr/bin/env python3
"""Headless layout inspection helper (development only)."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = ROOT.joinpath("index.html").as_uri()


def measure(page):
    return page.evaluate("""() => {
      const box = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
                display: s.display, grid: s.gridTemplateColumns, aspect: s.aspectRatio,
                objectFit: s.objectFit, height: s.height};
      };
      const img = document.querySelector('.arch--hero img');
      return {
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        mq760: matchMedia('(max-width: 760px)').matches,
        mq1024: matchMedia('(max-width: 1024px)').matches,
        heroInner: box('.hero__inner'),
        heroCopy: box('.hero__copy'),
        heroFigure: box('.hero__figure'),
        arch: box('.arch--hero'),
        archImg: box('.arch--hero img'),
        archSrc: img ? img.currentSrc.split('/').pop() : null,
        archNatural: img ? [img.naturalWidth, img.naturalHeight] : null,
        overlap: box('.hero__overlap'),
        overlapImg: box('.hero__overlap img'),
        headerToggle: box('.menu-toggle'),
        bodyOverflow: getComputedStyle(document.body).overflowX,
      };
    }""")


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True)
    for label, width, height, mobile in [("desktop", 1440, 1000, False), ("mobile", 390, 844, True)]:
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
            is_mobile=mobile,
            has_touch=mobile,
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(600)
        print(label, json.dumps(measure(page), indent=2, ensure_ascii=False))
        page.screenshot(path=str(ROOT / "tools" / f"_shot-{label}.png"), full_page=(label == "desktop"))
        context.close()
    browser.close()
