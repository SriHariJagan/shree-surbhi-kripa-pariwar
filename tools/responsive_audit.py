#!/usr/bin/env python3
"""Responsive audit: horizontal overflow + off-canvas content at every target width."""
from pathlib import Path
import json
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
WIDTHS = [1440, 1280, 1024, 900, 834, 768, 600, 480, 430, 390, 360, 320]
PAGES = [
    "index.html", "about.html", "seva.html", "gallery.html",
    "press.html", "donate.html", "contact.html",
]
HI_PAGES = ["hi/" + name for name in PAGES]

# Decorative or intentionally clipped elements are ignored.
IGNORE = (
    "marquee__track", "event::before", "announcement__dot",
    "lightbox", "menu", "drawer", "skip-link",
)

JS = """
() => {
  const vw = document.documentElement.clientWidth;
  const offenders = [];
  const ignored = %s;
  document.querySelectorAll('body *').forEach(el => {
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return;
    if (el.closest('[aria-hidden="true"]')) return;
    const cls = typeof el.className === 'string' ? el.className : '';
    if (ignored.some(token => cls.includes(token))) return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    if (r.right > vw + 1.5 || r.left < -1.5) {
      offenders.push({
        tag: el.tagName.toLowerCase(),
        cls: cls.slice(0, 90),
        left: Math.round(r.left),
        right: Math.round(r.right),
        text: (el.textContent || '').trim().slice(0, 50),
      });
    }
  });
  // De-duplicate nested offenders, keep the outermost few.
  return {
    vw,
    scrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    offenders: offenders.slice(0, 25),
  };
}
""" % json.dumps(IGNORE)


def run():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        for relative in PAGES + HI_PAGES:
            target = (ROOT / relative).as_uri()
            for width in WIDTHS:
                page.set_viewport_size({"width": width, "height": 900})
                page.goto(target, wait_until="load")
                page.wait_for_timeout(120)
                data = page.evaluate(JS)
                if data["scrollWidth"] > data["vw"] + 1 or data["offenders"]:
                    problems.append(
                        {
                            "page": relative,
                            "width": width,
                            "scrollWidth": data["scrollWidth"],
                            "vw": data["vw"],
                            "offenders": data["offenders"],
                        }
                    )
        browser.close()

    if not problems:
        print("PASS: no horizontal overflow at any width.")
        return

    print(f"FAIL: {len(problems)} page/width combinations with overflow.\n")
    for item in problems:
        print(
            f"{item['page']} @ {item['width']}px "
            f"(scrollWidth {item['scrollWidth']} vs {item['vw']})"
        )
        for offender in item["offenders"]:
            print(
                f"   <{offender['tag']} class=\"{offender['cls']}\"> "
                f"[{offender['left']}..{offender['right']}] {offender['text']!r}"
            )
        print()


if __name__ == "__main__":
    run()
