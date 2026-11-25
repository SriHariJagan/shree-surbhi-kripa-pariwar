#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static site builder for Shree Surbhi Kripa Pariwar.

Usage
-----
    python build.py

Writes the English site to the project root and the Hindi site to /hi/.
All content lives in content_en.py and content_hi.py. All visual tokens live
in assets/css/theme.css. Edit those, then run this file again.
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from pathlib import Path

import content_en
import content_hi

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))

PAGE_FILES = [
    ("home", "index.html"),
    ("about", "about.html"),
    ("seva", "seva.html"),
    ("gallery", "gallery.html"),
    ("press", "press.html"),
    ("donate", "donate.html"),
    ("contact", "contact.html"),
]
PAGE_BY_KEY = dict(PAGE_FILES)

LANGS = {
    "en": {
        "code": "en",
        "html_lang": "en",
        "dir": ROOT,
        "prefix": "",
        "content": content_en,
        "other": "hi",
        "locale": "en_IN",
    },
    "hi": {
        "code": "hi",
        "html_lang": "hi",
        "dir": ROOT / "hi",
        "prefix": "../",
        "content": content_hi,
        "other": "en",
        "locale": "hi_IN",
    },
}

NAV_KEYS = ["about", "seva", "gallery", "press", "contact"]

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def e(text: str) -> str:
    """Escape a value for use in an HTML attribute."""
    return html.escape(text, quote=True)


def href(lang: str, key: str) -> str:
    """Return a same-language URL. `key` may include an #anchor."""
    page, _, anchor = key.partition("#")
    filename = PAGE_BY_KEY.get(page, "index.html")
    url = filename + (f"#{anchor}" if anchor else "")
    return url


def asset(lang: str, path: str) -> str:
    return LANGS[lang]["prefix"] + path


def switch_url(lang: str, page_key: str) -> str:
    """Link to the same page in the other language."""
    other = LANGS[lang]["other"]
    prefix = "" if other == "en" else "hi/"
    base = prefix + PAGE_BY_KEY.get(page_key, "index.html")
    return base


def img(
    name: str,
    alt: str,
    lang: str,
    sizes: str = "100vw",
    cls: str = "",
    loading: str = "lazy",
    priority: bool = False,
    style: str = "",
) -> str:
    data = MANIFEST.get(name)
    if not data:
        raise KeyError(f"Unknown image: {name}")
    base = asset(lang, f"assets/images/{data['default']}")
    srcset = ", ".join(
        f"{asset(lang, 'assets/images/' + v['file'])} {v['width']}w" for v in data["variants"]
    )
    attrs = [
        f'src="{base}"',
        f'srcset="{srcset}"',
        f'sizes="{sizes}"',
        f'width="{data["width"]}"',
        f'height="{data["height"]}"',
        f'alt="{e(alt)}"',
        f'loading="{"eager" if priority else loading}"',
        'decoding="async"',
    ]
    if priority:
        attrs.append('fetchpriority="high"')
    if cls:
        attrs.append(f'class="{cls}"')
    if style:
        attrs.append(f'style="{style}"')
    return "<img " + " ".join(attrs) + ">"


def brand_mark(cls: str = "brand__mark") -> str:
    return f'<span class="{cls}" aria-hidden="true"></span>'


def signature() -> str:
    return """<svg viewBox="0 0 120 40" fill="none" aria-hidden="true">
<path d="M4 29c9-1 12-14 20-14 7 0 5 13 12 13 8 0 9-17 18-17 8 0 5 16 13 16 7 0 10-9 17-9 6 0 9 5 15 5 5 0 10-3 17-8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
<path d="M9 34h70" stroke="currentColor" stroke-width=".8" opacity=".45" stroke-linecap="round"/>
</svg>"""


def pin_icon() -> str:
    return """<svg class="map-card__pin" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 21s7-6.1 7-12A7 7 0 1 0 5 9c0 5.9 7 12 7 12Z" stroke="currentColor" stroke-width="1.4"/><circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.4"/></svg>"""


SOCIAL_PATHS = {
    "instagram": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" stroke-width="1.5"/><circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.5"/><circle cx="17.2" cy="6.8" r="1.1" fill="currentColor"/></svg>',
    "facebook": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M14.5 8.5H17V5h-2.5C12 5 10.5 6.7 10.5 9v2H8v3.5h2.5V22H14v-7.5h2.7L17 11h-3V9.3c0-.5.2-.8.5-.8Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>',
    "youtube": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="2.5" y="5.5" width="19" height="13" rx="4" stroke="currentColor" stroke-width="1.5"/><path d="m10 9.5 5 2.5-5 2.5v-5Z" fill="currentColor"/></svg>',
}


def social_row(g: dict, lang: str, cls: str = "social") -> str:
    links = [
        ("instagram", "Instagram", g["instagram"]),
        ("facebook", "Facebook", g["facebook"]),
        ("youtube", "YouTube", g["youtube"]),
    ]
    items = "".join(
        f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer" aria-label="{label}">{SOCIAL_PATHS[key]}</a>'
        for key, label, url in links
    )
    return f'<div class="{cls}">{items}</div>'


def copy_button(value: str, label: str, copied: str, cls: str = "copy-btn") -> str:
    return (
        f'<button class="{cls}" type="button" data-copy="{e(value)}" '
        f'data-copy-label="{e(label)}" data-copied-label="{e(copied)}">{e(label)}</button>'
    )


def tel_href(number: str) -> str:
    digits = re.sub(r"\D", "", number)
    if len(digits) == 10:
        digits = "91" + digits
    return "tel:+" + digits


# ---------------------------------------------------------------------------
# Shell
# ---------------------------------------------------------------------------


def head(lang: str, page_key: str, title: str, description: str, g: dict) -> str:
    prefix = LANGS[lang]["prefix"]
    return f"""<!DOCTYPE html>
<html lang="{LANGS[lang]['html_lang']}" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#210606">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(g['name'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:locale" content="{LANGS[lang]['locale']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefix}assets/brand/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="{prefix}assets/brand/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="{prefix}assets/brand/favicon-192.png">
<link rel="apple-touch-icon" href="{prefix}assets/brand/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Mukta:wght@300;400;500;600;700&family=Tiro+Devanagari+Hindi&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/css/theme.css">
<link rel="stylesheet" href="{prefix}assets/css/main.css">
<script type="application/ld+json">{json.dumps({
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": g["name"],
    "description": g["footer_about"],
    "email": g["contact_email"],
    "address": {"@type": "PostalAddress", "addressLocality": "Gurugram", "addressRegion": "Haryana", "addressCountry": "IN"},
    "sameAs": [g["instagram"], g["facebook"], g["youtube"]],
}, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
"""


def announcement_bar(lang: str, page_key: str, g: dict) -> str:
    a = g["announcement"]
    target = "#katha" if page_key == "home" else href(lang, "home") + "#katha"
    return f"""<div class="announcement">
<div class="container announcement__inner">
<a class="announcement__link" href="{target}">
<span class="announcement__dot" aria-hidden="true"></span>
<span class="announcement__label">{a['label']}</span>
<span class="announcement__when">{a['when']}</span>
<span class="announcement__where">{a['where']}</span>
<span class="announcement__cta"><span class="announcement__cta-text">{a['cta']}</span> <span aria-hidden="true">→</span></span>
</a>
</div>
</div>"""


def topbar(lang: str, page_key: str, g: dict) -> str:
    other = LANGS[lang]["other"]
    en_url = href(lang, page_key) if lang == "en" else switch_url(lang, page_key)
    hi_url = switch_url(lang, page_key) if lang == "en" else href(lang, page_key)
    return f"""<div class="topbar">
<div class="container topbar__inner">
<span class="topbar__place">{g['place']}</span>
<span class="topbar__mantra">{g['mantra']}</span>
<div class="topbar__links">
<div class="topbar__lang">
<a href="{en_url}" class="{'is-active' if lang == 'en' else ''}" lang="en" hreflang="en">EN</a>
<span>·</span>
<a href="{hi_url}" class="{'is-active' if lang == 'hi' else ''}" lang="hi" hreflang="hi">हिंदी</a>
</div>
<a class="topbar__donate" href="{href(lang, 'donate')}">{g['nav']['donate']}</a>
</div>
</div>
</div>"""


def masthead(lang: str, page_key: str, g: dict) -> str:
    def nav_link(key: str) -> str:
        active = " is-active" if page_key == key else ""
        return f'<a class="nav__link{active}" href="{href(lang, key)}">{g["nav"][key]}</a>'

    return f"""<header class="masthead" data-header>
<div class="container masthead__inner">
<nav class="nav nav--left" aria-label="Primary">
{nav_link('about')}
{nav_link('seva')}
</nav>
<a class="brand" href="{href(lang, 'home')}" aria-label="{e(g['name'])} — {e(g['nav']['home'])}">
{brand_mark()}
<span class="brand__text"><span class="brand__name">{g['name']}</span><span class="brand__sub">{g['sub']}</span></span>
</a>
<div class="masthead__end">
<nav class="nav nav--right" aria-label="Secondary">
{nav_link('gallery')}
{nav_link('press')}
{nav_link('contact')}
<a class="nav__cta" href="{href(lang, 'donate')}">{g['donate_cta']} <span aria-hidden="true">→</span></a>
</nav>
<button class="menu-toggle" type="button" data-menu-open aria-controls="site-menu" aria-expanded="false">
<span></span><span class="sr-only">{g['menu_title']}</span>
</button>
</div>
</div>
</header>
"""


def mobile_menu(lang: str, page_key: str, g: dict) -> str:
    links = "".join(
        f'<a class="menu__link" href="{href(lang, key)}">{g["nav"][key]}<span>{i:02d}</span></a>'
        for i, key in enumerate(["home", "about", "seva", "gallery", "press", "donate", "contact"], 1)
    )
    return f"""<div class="menu" id="site-menu" aria-hidden="true">
<div class="menu__head">
<span class="menu__brand">{g['name']}</span>
<button class="menu__close" type="button" data-menu-close aria-label="{e(g['menu_close'])}">×</button>
</div>
<nav class="menu__nav" aria-label="Mobile">{links}</nav>
<div class="menu__meta">
<span>{g['menu_meta_place']}</span>
<span>{g['menu_meta_hours']}</span>
<a href="mailto:{g['contact_email']}">{g['contact_email']}</a>
<div class="topbar__lang"><a href="{switch_url(lang, page_key)}">{g['lang_name']} / {g['switch_label']}</a></div>
</div>
</div>
"""


def footer(lang: str, g: dict) -> str:
    def flink(key: str, label: str) -> str:
        return f'<li><a href="{href(lang, key)}">{label}</a></li>'

    return f"""<footer class="footer">
<div class="container footer__top">
<div class="footer__brand">
<a class="brand" href="{href(lang, 'home')}" aria-label="{e(g['name'])}">
{brand_mark()}
<span class="brand__text"><span class="brand__name">{g['name']}</span><span class="brand__sub">{g['sub']}</span></span>
</a>
<p>{g['footer_about']}</p>
<p class="footer__mantra">{g['footer_mantra']}</p>
{social_row(g, lang)}
</div>
<div class="footer__col">
<h3>{g['footer_explore']}</h3>
<ul>
{flink('home', g['nav']['home'])}
{flink('about', g['nav']['about'])}
{flink('gallery', g['nav']['gallery'])}
{flink('press', g['nav']['press'])}
</ul>
</div>
<div class="footer__col">
<h3>{g['footer_seva']}</h3>
<ul>
{flink('seva', g['nav']['seva'])}
{flink('donate', g['nav']['donate'])}
{flink('contact#volunteer', g['footer_volunteer'])}
{flink('contact#invite', g['footer_invite'])}
</ul>
</div>
<div class="footer__col">
<h3>{g['footer_contact_title']}</h3>
<ul>
{flink('contact', g['place'])}
<li><a href="mailto:{g['contact_email']}">{g['contact_email']}</a></li>
<li><a href="{g['instagram']}" target="_blank" rel="noopener noreferrer">Instagram</a></li>
</ul>
</div>
</div>
<div class="container footer__bottom">
<span>{g['footer_rights']}</span>
<span>{g['footer_made']}</span>
</div>
<div class="footer__watermark" aria-hidden="true"><span>गौ सेवा</span></div>
</footer>
"""


def shell(
    lang: str,
    page_key: str,
    title: str,
    description: str,
    body: str,
    extra: str = "",
) -> str:
    g = LANGS[lang]["content"].GLOBAL
    prefix = LANGS[lang]["prefix"]
    return "".join(
        [
            head(lang, page_key, title, description, g),
            announcement_bar(lang, page_key, g),
            topbar(lang, page_key, g),
            masthead(lang, page_key, g),
            mobile_menu(lang, page_key, g),
            '<main id="main">',
            body,
            "</main>",
            footer(lang, g),
            extra,
            f'<script src="{prefix}assets/js/site.js" defer></script>',
            "</body></html>",
        ]
    )


# ---------------------------------------------------------------------------
# Shared components
# ---------------------------------------------------------------------------


def page_hero(lang: str, g: dict, page_key: str, hero: dict) -> str:
    return f"""<section class="page-hero grain">
<div class="container page-hero__grid">
<div class="reveal">
<nav class="breadcrumb" aria-label="Breadcrumb">
<a href="{href(lang, 'home')}">{g['nav']['home']}</a><span aria-hidden="true">/</span><span aria-current="page">{g['nav'][page_key]}</span>
</nav>
<p class="eyebrow eyebrow--light">{hero['eyebrow']}</p>
<h1>{hero['title']}</h1>
<p class="page-hero__lede">{hero['sub']}</p>
</div>
<figure class="page-hero__figure reveal reveal--delay-1">
<div class="arch">{img(hero['img'], hero['alt'], lang, '(max-width: 760px) 90vw, 430px', cls='arch__img', priority=True)}</div>
<figcaption class="page-hero__caption">{hero['caption']}</figcaption>
</figure>
</div>
</section>"""


def payment_card(lang: str, g: dict, full: bool = False) -> str:
    upi = g["upi"]
    local, at, domain = upi.partition("@")
    upi_link = (
        f"upi://pay?pa={urllib.parse.quote(upi)}"
        "&amp;pn=MSSHREESURBHIKRIPAPARIWAR&amp;cu=INR"
    )
    bank_rows = g["bank_rows"]

    def bank_row(index: int, label: str, value: str) -> str:
        copy = copy_button(value, g["copy"], g["copied"]) if index in (0, 1, 2, 3) else ""
        wide = " bank__row--wide" if len(value) > 48 else ""
        tag = "code" if index in (1, 2, 3) else "span"
        return (
            f'<div class="bank__row{wide}"><dt>{label}</dt>'
            f'<dd><span class="bank__value"><{tag}>{value}</{tag}>{copy}</span></dd></div>'
        )

    def mini_row(index: int, label: str, value: str) -> str:
        copy = copy_button(value, g["copy"], g["copied"]) if index in (0, 1, 2) else ""
        tag = "span" if index == 0 else "code"
        return (
            f'<div class="bank-mini__row"><span class="bank-mini__label">{label}</span>'
            f'<span class="bank-mini__value"><{tag}>{value}</{tag}>{copy}</span></div>'
        )

    if full:
        rows = "".join(bank_row(i, label, value) for i, (label, value) in enumerate(bank_rows))
        copy_all = "\n".join(
            [f"{label}: {value}" for label, value in bank_rows] + [f"UPI ID: {upi}"]
        )
        bank = f"""<section class="bank-details" id="bank" aria-labelledby="bank-title">
<div class="bank-details__head">
<div><span class="bank-details__eyebrow">{g['official_badge']} · ICICI Bank</span><h3 id="bank-title">{g['bank_summary']}</h3></div>
{copy_button(copy_all, g['copy_all'], g['copied'], cls='copy-btn copy-btn--all')}
</div>
<dl class="bank__table">{rows}</dl>
<p class="payment-card__trust">{g['official_note']}</p>
</section>"""
        head = f"""<div class="official-banner"><span class="official-banner__icon" aria-hidden="true">✓</span><p>{g['official_banner']}</p></div>
<div class="payment-card__head"><h2>{g['payment_title']}</h2><span>{g['official_badge']} · ICICI Bank</span></div>"""
        note = ""
        wrapper_cls = "payment-card"
    else:
        mini = "".join(mini_row(i, label, value) for i, (label, value) in enumerate(bank_rows[:3]))
        bank = f"""<div class="bank-mini">
<p class="bank-mini__title"><span>{g['official_badge']}</span>{g['bank_summary']}</p>
{mini}
<a class="link-arrow bank-mini__link" href="{href(lang, 'donate')}#bank">{g['bank_all']}</a>
</div>"""
        head = f"""<div class="payment-card__head"><h3>{g['payment_title']}</h3><span>{g['official_badge']} · ICICI Bank</span></div>"""
        note = f'<p class="payment-card__trust">{g["official_note"]}</p>'
        wrapper_cls = "donate-card"

    qr = f"""<div class="qr-wrap">
<div class="qr"><span class="qr__official">{g['official_badge']}</span>
<img src="{asset(lang, 'assets/images/qr-official.png')}" alt="{e(g['qr_alt'])}" width="504" height="504" loading="lazy" decoding="async">
</div>
<div class="qr__side">
<p class="scan-label"><strong>{g['scan_label']}</strong></p>
<div class="upi"><span class="upi__label">{g['upi_label']}</span><code>{e(local)}<wbr>{e(at)}{e(domain)}</code>{copy_button(upi, g['copy'], g['copied'])}</div>
<a class="btn btn--dark" href="{upi_link}">{g['open_upi']} <span class="btn__arrow" aria-hidden="true">→</span></a>
<p class="qr__apps">{g['payee_note']}</p>
</div>
</div>"""

    return f"""<aside class="{wrapper_cls}" aria-label="{g['payment_title']}">
{head}
{qr}
{bank}
{note}
</aside>"""


def field(
    label: str,
    name: str,
    *,
    type: str = "text",
    required: bool = False,
    full: bool = False,
    placeholder: str = "",
    options: list[tuple[str, str]] | None = None,
    textarea: bool = False,
    autocomplete: str = "",
) -> str:
    cls = "field field--full" if full else "field"
    req = " required" if required else ""
    star = ' <span aria-hidden="true">*</span>' if required else ""
    ph = f' placeholder="{e(placeholder)}"' if placeholder else ""
    ac = f' autocomplete="{autocomplete}"' if autocomplete else ""
    if textarea:
        control = f'<textarea name="{e(name)}" id="f-{e(name)}" rows="4"{ph}{req}></textarea>'
    elif options:
        opts = "".join(f'<option value="{e(v)}">{e(t)}</option>' for v, t in options)
        control = f'<select name="{e(name)}" id="f-{e(name)}"{req}>{opts}</select>'
    else:
        control = f'<input type="{type}" name="{e(name)}" id="f-{e(name)}"{ph}{ac}{req}>'
    return f'<div class="{cls}"><label for="f-{e(name)}">{label}{star}</label>{control}</div>'


def form(lang: str, g: dict, kind: str, subject: str, fields: list[str], submit: str, success: str) -> str:
    email = g["contact_email"]
    fields_html = "".join(fields)
    # Each form on a page reuses friendly field names; make ids unique per form.
    fields_html = fields_html.replace('id="f-', f'id="f-{kind}-').replace('for="f-', f'for="f-{kind}-')
    return f"""<form class="form" data-form="{kind}" data-subject="{e(subject)}" action="mailto:{email}" method="post" enctype="text/plain">
{fields_html}
<label class="form__consent"><input type="checkbox" name="Consent" required><span>{g['form_consent']}</span></label>
<p class="form__hint">{g['form_required_note']}</p>
<div class="form__actions"><button class="btn btn--dark" type="submit">{submit} <span class="btn__arrow" aria-hidden="true">→</span></button></div>
<div class="form__success" data-success role="status">{success}</div>
</form>"""


def cta_band(lang: str, block: dict, primary: str, secondary: str) -> str:
    return f"""<section class="section section--maroon grain cta-band">
<div class="container--narrow reveal">
<p class="eyebrow eyebrow--light">{block['eyebrow']}</p>
<h2>{block['title']}</h2>
<p class="body-copy">{block['body']}</p>
<div class="cta-band__actions">
<a class="btn btn--primary" href="{href(lang, primary)}">{block['cta1']} <span class="btn__arrow" aria-hidden="true">→</span></a>
<a class="btn btn--ghost" href="{href(lang, secondary)}">{block['cta2']}</a>
</div>
</div>
</section>"""


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------


def event_section(lang: str, g: dict, event: dict) -> str:
    facts = "".join(
        f'<div class="event__fact"><span>{label}</span><strong>{value}</strong></div>'
        for label, value in event["facts"]
    )
    phone_links = " · ".join(
        f'<a href="{tel_href(number)}">{number}</a>' for number in event["phones"]
    )
    poster_full = asset(lang, "assets/images/event-katha-1204.webp")
    return f"""<section class="section event grain" id="katha">
<div class="container event__grid">
<div class="event__copy reveal">
<p class="eyebrow">{event['eyebrow']}</p>
<h2>{event['title']}</h2>
<p class="event__hindi">{event['hindi']}</p>
<p class="body-copy">{event['body']}</p>
<div class="event__facts">{facts}</div>
<div class="event__actions">
<a class="btn btn--dark" href="{href(lang, 'contact')}">{event['cta1']} <span class="btn__arrow" aria-hidden="true">→</span></a>
<a class="btn btn--outline" href="{g['youtube']}" target="_blank" rel="noopener noreferrer">{event['cta2']} <span aria-hidden="true">↗</span></a>
</div>
<p class="event__note">{event['note']}</p>
<p class="event__contact"><span>{event['contact_label']}</span> {phone_links}</p>
</div>
<figure class="event__poster reveal reveal--delay-1">
<a class="event__poster-link" href="{poster_full}" target="_blank" rel="noopener noreferrer" aria-label="{e(event['view_poster'])}">
{img('event-katha', event['poster_alt'], lang, '(max-width: 760px) 86vw, 420px')}
<span class="event__poster-zoom">{event['view_poster']} <span aria-hidden="true">↗</span></span>
</a>
<span class="event__date">{event['label']}</span>
<figcaption>{event['facts'][2][1]}</figcaption>
</figure>
</div>
</section>"""


def build_home(lang: str) -> str:
    g = LANGS[lang]["content"].GLOBAL
    p = LANGS[lang]["content"].PAGES["home"]
    h = p["hero"]
    stats = "".join(f"<div class=\"hero__stat\"><strong>{s}</strong><span>{l}</span></div>" for s, l in h["stats"])

    marquee_items = "".join(
        f'<span class="marquee__item">{item}<span class="marquee__dot" aria-hidden="true"></span></span>'
        for item in p["marquee"] * 2
    )

    m = p["manifesto"]
    mbody = "".join(f"<p>{para}</p>" for para in m["body"])
    mstats = "".join(f"<div class=\"stat\"><strong>{s}</strong><span>{l}</span></div>" for s, l in m["stats"])

    pil = p["pillars"]
    pillar_imgs = "".join(
        img(item["img"], item["alt"], lang, "(max-width: 760px) 92vw, 500px",
            cls="pillar__img" + (" is-active" if i == 0 else ""))
        for i, item in enumerate(pil["items"])
    )
    pillars = ""
    for i, item in enumerate(pil["items"]):
        pillars += f"""<article class="pillar" data-pillar="{i}" tabindex="0">
<span class="pillar__num">{item['num']}</span>
<div><h3>{item['title']}<span>{item['hindi']}</span></h3><p>{item['body']}</p></div>
<a class="pillar__link" href="{href(lang, item['href'])}" aria-label="{e(item['link'])}">→</a>
</article>"""

    mosaic = ""
    letters = ["a", "b", "c", "d", "e"]
    for i, item in enumerate(p["mosaic"]["items"]):
        mosaic += f"""<a class="mosaic__item mosaic__item--{letters[i]} reveal" href="{href(lang, 'gallery')}">
{img(item['img'], item['alt'], lang, '(max-width: 760px) 92vw, 40vw')}
<span class="mosaic__caption"><span>{item['caption']}</span><span>{item['tag']}</span></span>
</a>"""

    feat = p["feature"]
    fbody = "".join(f"<p class=\"body-copy\">{para}</p>" for para in feat["body"])

    press = p["press"]
    press_cards = "".join(
        f'<article class="press__quote"><blockquote>{q}</blockquote><p class="press__source">{src}</p></article>'
        for q, src in press["quotes"]
    )

    d = p["donate"]
    tiers = "".join(f'<a class="tier" href="{href(lang, "donate")}">{t}</a>' for t in d["tiers"])
    tiers += f'<a class="tier" href="{href(lang, "donate")}">{d["tier_note"]}</a>'

    strip = "".join(
        f'<figure class="strip__item reveal">{img(item["img"], item["alt"], lang, "(max-width: 760px) 90vw, 33vw")}<figcaption>{item["caption"]}</figcaption></figure>'
        for item in p["strip"]["items"]
    )

    v = p["visit"]
    vdetails = "".join(f"<span>{item}</span>" for item in v["details"])

    body = f"""
<section class="hero grain">
<div class="container hero__inner">
<div class="hero__copy">
<p class="eyebrow eyebrow--light hero__eyebrow">{h['eyebrow']}</p>
<h1 class="hero__title">{h['title_1']}<em>{h['title_2']}</em></h1>
<p class="hero__lede">{h['lede']}</p>
<p class="hero__body">{h['body']}</p>
<div class="hero__actions">
<a class="btn btn--primary" href="{href(lang, 'donate')}">{h['cta1']} <span class="btn__arrow" aria-hidden="true">→</span></a>
<a class="btn btn--ghost" href="{href(lang, 'seva')}">{h['cta2']}</a>
</div>
<div class="hero__meta">{stats}</div>
</div>
<figure class="hero__figure">
<div class="arch arch--hero">{img('acharya-river', 'GauPremi Acharya Manish Ji standing by a mountain river with folded hands, wearing a yellow kurta and rudraksha malas.', lang, '(max-width: 760px) 90vw, 420px', cls='arch__img', priority=True)}</div>
<div class="hero__overlap">
{img('cow-embrace', 'Acharya Manish Ji embracing a white cow in a forest clearing.', lang, '220px')}
<span>{h['overlap_caption']}</span>
</div>
<figcaption class="hero__caption"><span>{h['caption_left']}</span><span>{h['caption_right']}</span></figcaption>
</figure>
</div>
<span class="hero__rail" aria-hidden="true">गौ सेवा · परम सेवा · सनातन</span>
<span class="hero__petal" aria-hidden="true"></span><span class="hero__petal hero__petal--two" aria-hidden="true"></span>
</section>

<div class="marquee" aria-hidden="true"><div class="marquee__track">{marquee_items}</div></div>

{event_section(lang, g, p['event'])}

<section class="section manifesto grain">
<div class="container manifesto__grid">
<div class="manifesto__side reveal">
<p class="eyebrow">{m['eyebrow']}</p>
<p class="manifesto__side-note">{g['tagline']}</p>
</div>
<div class="manifesto__main reveal reveal--delay-1">
<h2 class="manifesto__statement display">{m['title']}</h2>
<div class="manifesto__body">{mbody}</div>
<div class="manifesto__sign">{signature()}<div><strong>{m['sign']}</strong><span>{m['sign_role']}</span></div></div>
<div class="stat-row">{mstats}</div>
</div>
</div>
</section>

<section class="section section--raised pillars grain">
<div class="container">
<div class="pillars__head reveal">
<div><p class="eyebrow">{pil['eyebrow']}</p><h2>{pil['title']}</h2></div>
<p class="pillars__head-note">{pil['note']}</p>
</div>
<div class="pillars__grid">
<div class="pillars__media reveal reveal--scale">
<div class="pillars__images">{pillar_imgs}</div>
<span class="pillars__caption">{pil['caption']}</span>
</div>
<div class="pillar-list reveal reveal--delay-1">{pillars}</div>
</div>
</div>
</section>

<section class="section mosaic">
<div class="container">
<div class="mosaic__head reveal">
<div><p class="eyebrow">{p['mosaic']['eyebrow']}</p><h2>{p['mosaic']['title']}</h2></div>
<p>{p['mosaic']['intro']}</p>
</div>
<div class="mosaic__grid">{mosaic}</div>
<div class="mosaic__link"><a class="link-arrow" href="{href(lang, 'gallery')}">{p['mosaic']['link']}</a></div>
</div>
</section>

<section class="section section--maroon feature grain">
<div class="container feature__grid">
<div class="feature__portrait reveal reveal--scale">
<span class="feature__portrait-label">{feat['label']}</span>
<div class="arch">{img(feat['img'], feat['alt'], lang, '(max-width: 760px) 80vw, 430px', cls='arch__img')}</div>
</div>
<div class="feature__copy reveal reveal--delay-1">
<p class="eyebrow eyebrow--light">{feat['eyebrow']}</p>
<h2>{feat['title']}</h2>
{fbody}
<div class="feature__quote">
<blockquote>{feat['quote']}</blockquote>
<p class="feature__translation">{feat['translation']}</p>
<p class="feature__sign">{feat['sign']}</p>
</div>
<div class="feature__actions">
<a class="btn btn--primary" href="{href(lang, 'about')}">{feat['cta1']} <span class="btn__arrow" aria-hidden="true">→</span></a>
<a class="btn btn--ghost" href="{href(lang, 'contact#invite')}">{feat['cta2']}</a>
</div>
</div>
</div>
</section>

<section class="section press">
<div class="container">
<div class="press__head reveal">
<div><p class="eyebrow">{press['eyebrow']}</p><h2>{press['title']}</h2></div>
<p class="pillars__head-note">{press['intro']}</p>
</div>
<div class="press__grid reveal">{press_cards}</div>
<p class="press__note">{press['note']}</p>
<div class="mosaic__link"><a class="link-arrow" href="{href(lang, 'press')}">{press['link']}</a></div>
</div>
</section>

<section class="section section--maroon donate-band grain">
<div class="container donate-band__grid">
<div class="donate-band__copy reveal">
<p class="eyebrow eyebrow--light">{d['eyebrow']}</p>
<h2>{d['title']}</h2>
<p class="body-copy">{d['body']}</p>
<div class="tiers">{tiers}</div>
<div class="donate-band__actions">
<a class="btn btn--primary" href="{href(lang, 'donate')}">{d['cta']} <span class="btn__arrow" aria-hidden="true">→</span></a>
<a class="donate-band__hint" href="{href(lang, 'donate#bank')}">{d['hint']} →</a>
</div>
</div>
<div class="reveal reveal--delay-1">
{payment_card(lang, g)}
</div>
</div>
</section>

<section class="section section--raised strip">
<div class="container">
<div class="strip__head reveal">
<div><p class="eyebrow">{p['strip']['eyebrow']}</p><h2>{p['strip']['title']}</h2><p class="body-copy">{p['strip']['body']}</p></div>
<a class="link-arrow" href="{href(lang, 'gallery')}">{p['strip']['link']}</a>
</div>
<div class="strip__grid">{strip}</div>
</div>
</section>

<section class="visit">
<div class="visit__media" aria-hidden="true">{img('community-event', '', lang, '100vw')}</div>
<div class="visit__panel reveal">
<p class="eyebrow eyebrow--plain">{v['eyebrow']}</p>
<h2>{v['title']}</h2>
<p class="hindi">{v['hindi']}</p>
<p class="body-copy">{v['body']}</p>
<div class="visit__details">{vdetails}</div>
<div class="visit__actions">
<a class="btn btn--dark" href="{href(lang, 'contact')}">{v['cta1']} <span class="btn__arrow" aria-hidden="true">→</span></a>
<a class="btn btn--outline" href="{href(lang, 'contact#volunteer')}">{v['cta2']}</a>
</div>
</div>
</section>
"""
    return shell(lang, "home", p["meta_title"], p["meta_desc"], body)


def build_about(lang: str) -> str:
    g = LANGS[lang]["content"].GLOBAL
    p = LANGS[lang]["content"].PAGES["about"]
    story = p["story"]
    sbody = "".join(f"<p class=\"body-copy\">{para}</p>" for para in story["body"])
    guide = p["guide"]
    gbody = "".join(f"<p class=\"body-copy\">{para}</p>" for para in guide["body"])

    values = "".join(
        f'<article class="value reveal"><span class="value__num">{num}</span><h3>{title}</h3><p>{body}</p></article>'
        for num, title, body in p["values"]["items"]
    )
    timeline = ""
    for title, body in p["timeline"]["items"]:
        timeline += f'<div class="timeline__item reveal"><h3>{title}</h3><p>{body}</p></div>'

    press_cards = "".join(
        f'<article class="press__quote"><blockquote>{q}</blockquote><p class="press__source">{src}</p></article>'
        for q, src in p["press"]["quotes"]
    )

    body = f"""
{page_hero(lang, g, 'about', p['hero'])}

<section class="section about-story grain">
<div class="container about-story__grid">
<figure class="about-story__aside reveal">
<div class="arch">{img(story['img'], story['alt'], lang, '(max-width: 760px) 90vw, 420px', cls='arch__img')}</div>
<figcaption><span>{story['caption_left']}</span><span>{story['caption_right']}</span></figcaption>
</figure>
<div class="about-story__copy reveal reveal--delay-1">
<p class="eyebrow">{story['eyebrow']}</p>
<h2>{story['title']}</h2>
{sbody}
<div class="about-story__quote">
<blockquote>{story['quote']}</blockquote>
<cite>{story['cite']}</cite>
</div>
</div>
</div>
</section>

<section class="section section--raised">
<div class="container">
<div class="seva-block">
<figure class="seva-block__media reveal">
<div class="arch">{img(guide['img'], guide['alt'], lang, '(max-width: 760px) 90vw, 460px', cls='arch__img')}</div>
<span class="seva-block__index">{guide['caption']}</span>
</figure>
<div class="seva-block__copy reveal reveal--delay-1">
<p class="eyebrow">{guide['eyebrow']}</p>
<h2>{guide['title']}</h2>
{gbody}
<div class="about-story__quote">
<blockquote>{guide['quote']}</blockquote>
<cite>{guide['translation']} — {guide['sign']}</cite>
</div>
<div class="seva-block__actions">
<a class="btn btn--dark" href="{href(lang, 'contact#invite')}">{guide['cta1']} <span class="btn__arrow" aria-hidden="true">→</span></a>
<a class="btn btn--outline" href="{href(lang, 'press')}">{guide['cta2']}</a>
</div>
</div>
</div>
</div>
</section>

<section class="section values">
<div class="container">
<div class="values__head reveal">
<div><p class="eyebrow">{p['values']['eyebrow']}</p><h2>{p['values']['title']}</h2></div>
</div>
<div class="values__grid">{values}</div>
</div>
</section>

<section class="section section--raised">
<div class="container">
<div class="values__head reveal">
<div><p class="eyebrow">{p['timeline']['eyebrow']}</p><h2>{p['timeline']['title']}</h2></div>
<p class="pillars__head-note">{p['timeline']['note']}</p>
</div>
<div class="timeline">{timeline}</div>
</div>
</section>

<section class="section press">
<div class="container">
<div class="press__head reveal">
<div><p class="eyebrow">{p['press']['eyebrow']}</p><h2>{p['press']['title']}</h2></div>
<a class="link-arrow" href="{href(lang, 'press')}">{p['press']['link']}</a>
</div>
<div class="press__grid reveal">{press_cards}</div>
</div>
</section>

{cta_band(lang, p['cta'], 'donate', 'contact#volunteer')}
"""
    return shell(lang, "about", p["meta_title"], p["meta_desc"], body)


def build_seva(lang: str) -> str:
    g = LANGS[lang]["content"].GLOBAL
    p = LANGS[lang]["content"].PAGES["seva"]
    blocks = ""
    for b in p["blocks"]:
        includes = "".join(f"<li>{i}</li>" for i in b["includes"])
        media_cls = "seva-block__media seva-block__media--wide" if b["wide"] else "seva-block__media"
        rev = " seva-block--reverse" if b["reverse"] else ""
        blocks += f"""<div class="seva-block{rev}">
<figure class="{media_cls} reveal">
<span class="seva-block__index">{b['index']}</span>
<div class="arch">{img(b['img'], b['alt'], lang, '(max-width: 760px) 90vw, 510px', cls='arch__img')}</div>
</figure>
<div class="seva-block__copy reveal reveal--delay-1">
<p class="eyebrow">{b['eyebrow']}</p>
<h2>{b['title']}</h2>
<p class="body-copy">{b['body']}</p>
<ul class="checklist">{includes}</ul>
<div class="seva-block__actions"><a class="link-arrow" href="{href(lang, b['href'])}">{b['cta']}</a></div>
</div>
</div>"""

    aside_cards = "".join(
        f"<article class=\"reveal\"><h3>{title}</h3><p>{body}</p></article>"
        for title, body in p["aside"]["items"]
    )

    body = f"""
{page_hero(lang, g, 'seva', p['hero'])}

<section class="section section--tight">
<div class="container--narrow seva-intro reveal">
<p class="eyebrow eyebrow--plain">{p['intro']['eyebrow']}</p>
<h2>{p['intro']['title']}</h2>
<p>{p['intro']['body']}</p>
</div>
<div class="container">
{blocks}
</div>
</section>

<section class="section section--raised">
<div class="container">
<div class="values__head reveal">
<div><p class="eyebrow">{p['aside']['eyebrow']}</p><h2>{p['aside']['title']}</h2></div>
</div>
<div class="seva-aside">{aside_cards}</div>
</div>
</section>

{cta_band(lang, p['cta'], 'donate', 'contact#volunteer')}
"""
    return shell(lang, "seva", p["meta_title"], p["meta_desc"], body)


def build_gallery(lang: str) -> str:
    g = LANGS[lang]["content"].GLOBAL
    p = LANGS[lang]["content"].PAGES["gallery"]
    filters = "".join(
        f'<button class="filter{" is-active" if i == 0 else ""}" type="button" data-filter="{key}">{label}</button>'
        for i, (key, label) in enumerate(p["filters"])
    )
    items = ""
    for name, cat, caption in p["items"]:
        alt = caption
        if name in MANIFEST:
            alt = f"{caption} — Shree Surbhi Kripa Pariwar"
        items += f"""<figure class="gallery-item" data-cat="{cat}" data-full="{asset(lang, 'assets/images/' + MANIFEST[name]['default'])}" data-caption="{e(caption)}" tabindex="0" role="button" aria-label="{e(caption)}">
{img(name, alt, lang, '(max-width: 480px) 92vw, (max-width: 760px) 46vw, 30vw')}
<figcaption>{caption}</figcaption>
</figure>"""

    lightbox = """<div class="lightbox" id="lightbox" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Gallery viewer">
<div class="lightbox__bar"><span class="lightbox__count" data-lb-count></span><button class="lightbox__close" type="button" data-lb-close aria-label="Close">×</button></div>
<div class="lightbox__stage">
<button class="lightbox__nav" type="button" data-lb-prev aria-label="Previous image">←</button>
<figure class="lightbox__figure"><img data-lb-img alt=""></figure>
<button class="lightbox__nav" type="button" data-lb-next aria-label="Next image">→</button>
</div>
<div class="lightbox__foot"><p class="lightbox__caption" data-lb-caption></p><span class="lightbox__cat" data-lb-cat></span></div>
</div>"""

    body = f"""
{page_hero(lang, g, 'gallery', p['hero'])}

<section class="section">
<div class="container">
<div class="filters" data-filters>{filters}</div>
<div class="gallery-grid" data-gallery>{items}</div>
<p class="gallery-empty" data-gallery-empty hidden>{p['empty']}</p>
<div class="mosaic__link"><a class="link-arrow" href="{href(lang, p['cta_href'])}">{p['cta']}</a></div>
</div>
</section>
"""
    return shell(lang, "gallery", p["meta_title"], p["meta_desc"], body, extra=lightbox)


def build_press(lang: str) -> str:
    g = LANGS[lang]["content"].GLOBAL
    p = LANGS[lang]["content"].PAGES["press"]
    f = p["featured"]
    cards = "".join(
        f'<article class="press-card reveal"><blockquote>“{q}”</blockquote><p class="press-card__meta"><span>{who}</span><span>{src}</span></p></article>'
        for q, who, src in p["quotes"]
    )
    clippings = "".join(
        f'<figure class="clipping reveal">{img(name, caption, lang, "(max-width: 760px) 46vw, 300px")}<figcaption>{caption}</figcaption></figure>'
        for name, caption in p["clippings"]["items"]
    )
    kit = p["kit"]

    body = f"""
{page_hero(lang, g, 'press', p['hero'])}

<section class="section section--tight">
<div class="container">
<div class="seva-intro reveal">
<p class="eyebrow eyebrow--plain">{p['intro']['eyebrow']}</p>
<h2>{p['intro']['title']}</h2>
<p>{p['intro']['body']}</p>
</div>
<div class="press-feature reveal" style="margin-top:56px">
<span class="press-feature__label">{f['label']}</span>
<div><blockquote>{f['quote']}</blockquote><p class="press-feature__summary">{f['summary']}</p></div>
<p class="press-feature__meta">{f['meta']}</p>
</div>
<div class="press-grid" style="margin-top:56px">{cards}</div>
</div>
</section>

<section class="section section--raised">
<div class="container">
<div class="values__head reveal">
<div><p class="eyebrow">{p['clippings']['eyebrow']}</p><h2>{p['clippings']['title']}</h2></div>
</div>
<div class="clippings">{clippings}</div>
<p class="press-disclaimer">{p['disclaimer']}</p>
</div>
</section>

<section class="section">
<div class="container">
<div class="values__head reveal">
<div><p class="eyebrow">{kit['eyebrow']}</p><h2>{kit['title']}</h2></div>
</div>
<div class="media-kit reveal">
<div><h3>{kit['boilerplate_title']}</h3><p>{kit['boilerplate']}</p></div>
<div><h3>{kit['contact_title']}</h3><p>{kit['contact']}</p><p style="margin-top:14px"><a class="link-arrow" href="mailto:{g['contact_email']}">{kit['download']}</a></p></div>
</div>
</div>
</section>

{cta_band(lang, p['cta'], 'contact', 'about')}
"""
    return shell(lang, "press", p["meta_title"], p["meta_desc"], body)


def build_donate(lang: str) -> str:
    g = LANGS[lang]["content"].GLOBAL
    p = LANGS[lang]["content"].PAGES["donate"]
    why = p["why"]
    wbody = "".join(f"<p class=\"body-copy\">{para}</p>" for para in why["body"])
    tiers = "".join(
        f'<div class="donation-tier"><span class="donation-tier__amount">{amount}</span><div class="donation-tier__body"><strong>{title}</strong><span>{body}</span></div><span class="donation-tier__arrow" aria-hidden="true">→</span></div>'
        for amount, title, body in p["tiers"]["items"]
    )
    steps = "".join(f"<div class=\"donate-step\"><h3>{t}</h3><p>{b}</p></div>" for t, b in p["steps"]["items"])
    after = "".join(
        f'<li class="aftercare__step"><span class="aftercare__num">{n:02d}</span><p>{i}</p></li>'
        for n, i in enumerate(p["after"]["items"], 1)
    )
    others = "".join(
        f'<article class="value reveal"><h3>{t}</h3><p>{b}</p></article>' for t, b in p["other"]["items"]
    )
    faq = "".join(
        f'<details><summary>{q}</summary><p class="faq__answer">{a}</p></details>' for q, a in p["faq"]["items"]
    )
    promise = "".join(f"<li>{i}</li>" for i in p["promise"]["items"])

    body = f"""
{page_hero(lang, g, 'donate', p['hero'])}

<section class="section">
<div class="container">
<div class="donate-layout">
<div class="donate-layout__intro reveal">
<p class="eyebrow">{why['eyebrow']}</p>
<h2>{why['title']}</h2>
{wbody}
<figure class="pillars__media" style="margin-top:30px;aspect-ratio:4/3">
{img(why['img'], why['alt'], lang, '(max-width: 1024px) 92vw, 560px')}
<span class="pillars__caption">{why['caption']}</span>
</figure>

<div style="margin-top:44px">
<p class="eyebrow">{p['tiers']['eyebrow']}</p>
<h2 style="margin-top:14px">{p['tiers']['title']}</h2>
<p class="body-copy" style="margin-top:14px">{p['tiers']['note']}</p>
<div class="donation-tiers">{tiers}</div>
<p class="press__note">{p['tiers']['disclaimer']}</p>
</div>

<div style="margin-top:44px">
<p class="eyebrow">{p['steps']['title']}</p>
<div class="donate-steps">{steps}</div>
</div>
</div>
<aside class="donate-layout__aside reveal reveal--delay-1">
{payment_card(lang, g, full=True)}
</aside>
</div>
</div>
</section>

<section class="section section--raised aftercare">
<div class="container">
<div class="aftercare__head reveal">
<p class="eyebrow">{p['after']['eyebrow']}</p>
<h2>{p['after']['title']}</h2>
</div>
<ol class="aftercare__grid reveal">{after}</ol>
<div class="aftercare__note reveal">
<p class="aftercare__receipt">{p['after']['receipt']}</p>
<p class="aftercare__tax">{p['after']['tax']}</p>
</div>
</div>
</section>

<section class="section">
<div class="container">
<div class="values__head reveal">
<div><p class="eyebrow">{p['other']['eyebrow']}</p><h2>{p['other']['title']}</h2></div>
</div>
<div class="values__grid">{others}</div>
</div>
</section>

<section class="section section--raised">
<div class="container--narrow">
<div class="values__head reveal">
<div><p class="eyebrow">{p['faq']['eyebrow']}</p><h2>{p['faq']['title']}</h2></div>
</div>
<div class="faq">{faq}</div>

<div style="margin-top:54px">
<h3 style="font-size:var(--step-2);color:var(--color-maroon)">{p['promise']['title']}</h3>
<ul class="checklist" style="margin-top:18px">{promise}</ul>
</div>
</div>
</section>

<section class="section section--maroon grain cta-band">
<div class="container--narrow reveal">
<p class="eyebrow eyebrow--light">{p['closing']['eyebrow']}</p>
<h2 class="hindi" style="font-family:var(--font-hindi);font-size:var(--step-3);line-height:1.3">{p['closing']['title']}</h2>
<p class="body-copy">{p['closing']['body']}</p>
<div class="cta-band__actions">
<a class="btn btn--primary" href="#bank">{p['closing']['cta1']} <span class="btn__arrow" aria-hidden="true">→</span></a>
<a class="btn btn--ghost" href="{href(lang, 'contact')}">{p['closing']['cta2']}</a>
</div>
</div>
</section>
"""
    return shell(lang, "donate", p["meta_title"], p["meta_desc"], body)


def build_contact(lang: str) -> str:
    g = LANGS[lang]["content"].GLOBAL
    p = LANGS[lang]["content"].PAGES["contact"]
    details = p["details"]
    rows = "".join(
        f'<div class="contact-detail"><dt>{label}</dt><dd>{value}<span>{note}</span></dd></div>'
        for label, value, note in details["items"]
    )

    f = p["form"]
    contact_fields = [
        field(g["form_name"], "Name", required=True, autocomplete="name"),
        field(g["form_email"], "Email", type="email", required=True, autocomplete="email"),
        field(g["form_phone"], "Phone", type="tel", autocomplete="tel"),
        field(f["subject_label"], "Subject", options=f["subjects"], required=True),
        field(g["form_message"], "Message", textarea=True, full=True, required=True, placeholder=f["message_placeholder"]),
    ]

    v = p["volunteer"]
    volunteer_fields = [
        field(g["form_name"], "Name", required=True, autocomplete="name"),
        field(g["form_phone"], "Phone", type="tel", required=True, autocomplete="tel"),
        field(g["form_email"], "Email", type="email", autocomplete="email"),
        field(v["fields"]["city"], "City", autocomplete="address-level2"),
        field(v["fields"]["age"], "Age", options=[(a, a) for a in v["ages"]]),
        field(v["fields"]["interest"], "Interest", options=v["interests"]),
        field(v["fields"]["availability"], "Availability", full=True, placeholder=v["availability_placeholder"]),
        field(g["form_message"], "Message", textarea=True, full=True, placeholder=v["message_placeholder"]),
    ]

    inv = p["invite"]
    invite_fields = [
        field(g["form_name"], "Name", required=True, autocomplete="name"),
        field(inv["fields"]["org"], "Organisation"),
        field(g["form_phone"], "Phone", type="tel", required=True, autocomplete="tel"),
        field(g["form_email"], "Email", type="email", autocomplete="email"),
        field(inv["fields"]["programme"], "Programme", options=inv["programmes"], required=True),
        field(inv["fields"]["date"], "Date", placeholder="DD / MM / YYYY"),
        field(inv["fields"]["location"], "Location", full=True),
        field(inv["fields"]["audience"], "Audience", placeholder=inv["audience_placeholder"]),
        field(g["form_message"], "Message", textarea=True, full=True, placeholder=inv["message_placeholder"]),
    ]

    subject_map = {
        "en": ("Website enquiry", "Volunteer with Shree Surbhi Kripa Pariwar", "Invitation for Acharya Ji"),
        "hi": ("वेबसाइट पूछताछ", "सेवा के लिए स्वयंसेवा", "आचार्य जी के लिए आमंत्रण"),
    }
    subjects = subject_map[lang]

    body = f"""
{page_hero(lang, g, 'contact', p['hero'])}

<section class="section">
<div class="container contact-grid">
<div class="reveal">
<p class="eyebrow">{details['eyebrow']}</p>
<h2>{details['title']}</h2>
<dl class="contact-details" style="margin-top:30px">{rows}</dl>
<div class="contact-cta">
<p class="note">{p['visit']['note']}</p>
<div class="visit__actions" style="justify-content:flex-start">
<a class="btn btn--dark" href="mailto:{g['contact_email']}">{details['cta']} <span class="btn__arrow" aria-hidden="true">→</span></a>
</div>
</div>
<div style="margin-top:34px">
<h3 style="text-transform:uppercase;font-family:var(--font-body);font-size:.62rem;letter-spacing:.16em;color:var(--color-ink-faint);margin-bottom:12px">{details['social_label']}</h3>
{social_row(g, lang)}
</div>
<div class="map-card reveal" style="margin-top:38px">
<div class="map-card__inner">
{pin_icon()}
<h3>{p['map']['title']}</h3>
<p>{p['map']['body']}</p>
<a class="link-arrow" href="#contact-form">{p['map']['cta']}</a>
</div>
</div>
</div>
<div class="contact-form-wrap reveal reveal--delay-1" id="contact-form">
<div class="form-head">
<p class="eyebrow">{f['eyebrow']}</p>
<h2>{f['title']}</h2>
<p>{f['body']}</p>
</div>
{form(lang, g, 'contact', subjects[0], contact_fields, f['submit'], f['success'])}
</div>
</div>
</section>

<section class="section section--raised">
<div class="container--narrow">
<div class="values__head reveal">
<div><p class="eyebrow">{v['eyebrow']}</p><h2>{v['title']}</h2><p class="body-copy" style="margin-top:14px">{v['body']}</p></div>
</div>
<div class="accordion-forms">
<details class="accordion-form" id="{v['anchor']}">
<summary>{v['submit']}</summary>
<div class="accordion-form__body">
{form(lang, g, 'volunteer', subjects[1], volunteer_fields, v['submit'], v['success'])}
<p class="press__note">{v['safety']}</p>
</div>
</details>
<details class="accordion-form" id="{inv['anchor']}">
<summary>{inv['eyebrow']}</summary>
<div class="accordion-form__body">
{form(lang, g, 'invite', subjects[2], invite_fields, inv['submit'], inv['success'])}
<p class="press__note">{inv['note']}</p>
</div>
</details>
</div>
</div>
</section>

<section class="section">
<div class="container">
<div class="donate-band__grid" style="align-items:center">
<div class="reveal">
<p class="eyebrow">{p['visit']['eyebrow']}</p>
<h2>{p['visit']['title']}</h2>
<p class="body-copy" style="margin-top:18px">{p['visit']['body']}</p>
<div class="visit__actions" style="justify-content:flex-start;margin-top:26px">
<a class="btn btn--dark" href="mailto:{g['contact_email']}">{p['visit']['cta']} <span class="btn__arrow" aria-hidden="true">→</span></a>
</div>
</div>
<div class="visit__panel reveal reveal--delay-1" style="width:100%;padding:clamp(24px,4vw,44px)">
{pin_icon()}
<h3 style="font-size:var(--step-2);color:var(--color-maroon)">{p['map']['title']}</h3>
<p class="body-copy" style="margin-top:10px">{p['map']['body']}</p>
<p class="press__note" style="margin-top:16px">{p['visit']['note']}</p>
</div>
</div>
</div>
</section>
"""
    return shell(lang, "contact", p["meta_title"], p["meta_desc"], body)


BUILDERS = {
    "home": build_home,
    "about": build_about,
    "seva": build_seva,
    "gallery": build_gallery,
    "press": build_press,
    "donate": build_donate,
    "contact": build_contact,
}


def validate() -> None:
    """Fail loudly if the two languages drift apart."""
    def keys(obj, prefix=""):
        out = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                out.add(prefix + k)
                out |= keys(v, prefix + k + ".")
        elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
            out |= keys(obj[0], prefix + "[].")
        return out

    en = keys({"GLOBAL": content_en.GLOBAL, "PAGES": content_en.PAGES})
    hi = keys({"GLOBAL": content_hi.GLOBAL, "PAGES": content_hi.PAGES})
    if en != hi:
        print("Content key mismatch:")
        for key in sorted(en - hi):
            print("  missing in hi:", key)
        for key in sorted(hi - en):
            print("  missing in en:", key)
        raise SystemExit(1)


def main() -> None:
    validate()
    for lang, config in LANGS.items():
        out_dir: Path = config["dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        for page_key, filename in PAGE_FILES:
            page = BUILDERS[page_key](lang)
            (out_dir / filename).write_text(page, encoding="utf-8")
            print(f"  · {lang}/{filename}")
    print(f"Built {len(PAGE_FILES) * len(LANGS)} pages.")


if __name__ == "__main__":
    main()
