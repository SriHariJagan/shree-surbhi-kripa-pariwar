# Shree Surbhi Kripa Pariwar — website

A static, bilingual (English / हिन्दी) website built from Python content files.
English lives at the project root and Hindi lives under `hi/`.

```
index.html  about.html  seva.html  gallery.html  press.html  donate.html  contact.html
hi/index.html  hi/about.html  hi/seva.html  hi/gallery.html  hi/press.html  hi/donate.html  hi/contact.html
```

## Quick start

```powershell
python build.py                 # regenerate all 14 pages
python tools\check_site.py      # validate links, srcsets, ids and metadata
python -m http.server 8000      # preview at http://localhost:8000
```

All pages are plain HTML/CSS/JS — no server-side runtime is required.

Repository: <https://github.com/SriHariJagan/shree-surbhi-kripa-pariwar>
Live site: <https://sriharijagan.github.io/shree-surbhi-kripa-pariwar/>

## 1. Change the colours, fonts and spacing

Everything visual is driven by **`assets/css/theme.css`**. This is the only file
that should contain palette values.

| Variable | Used for |
| --- | --- |
| `--color-maroon`, `--color-maroon-deep` | headings, dark panels, footer |
| `--color-saffron`, `--color-marigold` | accents, links, event highlights |
| `--color-green`, `--color-gold` | trust / official badges, borders |
| `--color-paper`, `--color-paper-warm`, `--color-paper-raised` | page and card backgrounds |
| `--font-display`, `--font-body`, `--font-hindi` | typography |
| `--gutter`, `--section-space`, `--header-height` | layout rhythm |

Change a value there, rebuild, and the whole site updates.
`assets/css/main.css` uses those variables (and `color-mix`) only — avoid adding
raw hex values to it.

## 2. Update bank / UPI / QR details

Payment content is stored once per language in `content_en.py` and
`content_hi.py`, inside `GLOBAL`:

- `upi` — the UPI ID
- `bank_rows` — label/value pairs for the full bank table
- `official_banner`, `official_note`, `payee_note` — trust copy
- `contact_email`, `instagram`, `facebook`, `youtube`

The UPI deep link and the “copy all details” text are generated automatically
from these values in `payment_card()` in `build.py`.

### Replace the QR image

1. Put the new QR image in the project root as `qrCode.png`.
2. If the QR is not already cropped to its modules, adjust the crop box in
   `build_official_qr()` inside `tools/prepare_assets.py`.
3. Run:

   ```powershell
   python tools\prepare_assets.py
   ```

   This writes `assets/images/qr-official.png` (used by the site) and
   `assets/images/qr-official.txt`.

Always scan-test the new QR before publishing:

```powershell
python -c "import cv2;print(cv2.QRCodeDetector().detectAndDecode(cv2.imread('assets/images/qr-official.png'))[0])"
```

## 3. Edit page copy

- English: `content_en.py`
- Hindi: `content_hi.py`

Both files must contain the **same dictionary keys**. `build.py` validates this
and stops with an error if one language drifts. After editing, run
`python build.py`.

Page-specific copy lives under `PAGES[...]`; shared labels (navigation, buttons,
bank rows, announcement) live under `GLOBAL`.

The home hero `h1` is localised: the English site shows the English headline
("Cow service is the ultimate service.") and the Hindi site keeps the
Devanagari headline. The Hindi motto still appears in the top bar on both.

## 4. Update the Bhagwat Katha event

In both content files:

- `GLOBAL["announcement"]` — ribbon label, dates, venue and CTA text.
- `PAGES["home"]["event"]` — title, description, facts, helpline numbers,
  poster alt text and button labels.

The home section is `#katha` (built by `event_section()` in `build.py`).
The ribbon on every page links to it.

### Replace the event poster

1. Save the new poster as `currentEvent.png` in the project root.
2. Run `python tools\prepare_assets.py`.
3. It generates `assets/images/event-katha-480.webp`, `-800.webp`,
   `-1204.webp` and the default image, and updates `manifest.json`.

## 5. Photos and image pipeline

Source photos stay untouched in `images/`. `tools/prepare_assets.py` creates
optimised WebP variants, the favicon, the event poster and the cropped QR, then
writes `assets/images/manifest.json`. `img()` in `build.py` reads that manifest
to produce responsive `srcset`/`sizes` markup.

Do not publish the two private account screenshots in `images/`.

## 6. Responsive and quality checks

```powershell
python tools\check_site.py          # links, ids, srcsets, metadata
python tools\responsive_audit.py    # overflow check at 320–1440 px, EN + HI
python tools\smoke_test.py          # copy buttons, UPI links, menu, gallery
python tools\qa_event.py            # event/payment section screenshots
python tools\qa.py                  # full section screenshots
```

Screenshots are written to `tools/qa/` and are development-only.

The responsive audit covers **1440, 1280, 1024, 900, 834, 768, 600, 480, 430,
390, 360 and 320 px** on all 14 pages. Keep it passing after any CSS change.

## 7. Deployment

Upload the repository root (including `assets/` and `hi/`) to any static host.
No build step is needed on the server. HTTPS is recommended, especially for the
`upi:` links and the copy-to-clipboard buttons.

The generated HTML is committed and GitHub Pages is already configured to serve
the site from **`main` / `(root)`** at
<https://sriharijagan.github.io/shree-surbhi-kripa-pariwar/>. Pushing to `main`
publishes the update automatically.

Source photography (`images/`), local QA screenshots (`tools/qa/`) and the
original `image.png`, `qrCode.png` and `currentEvent.png` are kept out of Git by
`.gitignore`. Rebuild the optimised assets and favicons with
`python tools\prepare_assets.py` when working from the source material.

## Known placeholders

- Exact Facebook page URL is not confirmed; a Facebook search URL is used.
- 80G / FCRA status is unverified, so the site does not claim 80G exemption.
- The gaushala's exact address is shared on request.
- Press publication names and dates in `press.html` are marked for later
  completion.
