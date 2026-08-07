#!/usr/bin/env python3
"""
Generates a photographs/<name>.html page for every image in
images/photographs/ that doesn't already have one.

You never run this yourself — GitHub Actions runs it on every push,
before build_index.py rebuilds the gallery listing. So the whole
workflow for adding a photo is:

    drop the file in images/photographs/  ->  git push

Title, date and caption are worked out like this:

  TITLE   the filename, tidied up. "old-delhi-rooftops.jpg" becomes
          "Old Delhi Rooftops". Override it with a sidecar file
          (see below).

  DATE    EXIF DateTimeOriginal if the image has it (most phone and
          camera shots do), otherwise a YYYY-MM-DD prefix on the
          filename ("2026-08-01-rooftops.jpg"), otherwise the sidecar,
          otherwise today's date with a warning printed in the build log.

  CAPTION nothing by default. Add one with a sidecar.

A sidecar is an optional .txt file sitting next to the image with the
same name — images/photographs/rooftops.txt — looking like this:

    title: Rooftops at dusk
    date: 2026-08-01
    caption: Shot from the roof of the hostel, about ten minutes
             after the power cut started.

Every field is optional; anything you leave out falls back to the
rules above.

Pages that already exist are never touched, so if you want to hand-edit
one, just edit it — this script will leave it alone from then on.
"""
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "images" / "photographs"
PAGES = ROOT / "photographs"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif",
              ".heic", ".heif", ".tif", ".tiff", ".bmp", ".jfif"}
# Formats browsers can't display, even though we can read them.
UNSUPPORTED_IN_BROWSER = {".heic", ".heif", ".tif", ".tiff"}
DATE_PREFIX = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[-_]?(.*)$")


def read_sidecar(img: Path) -> dict:
    """Optional <name>.txt beside the image: title/date/caption."""
    side = img.with_suffix(".txt")
    if not side.exists():
        return {}
    data, key = {}, None
    for line in side.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(title|date|caption)\s*:\s*(.*)$", line.strip(), re.I)
        if m:
            key = m.group(1).lower()
            data[key] = m.group(2).strip()
        elif key and line.strip():
            data[key] += " " + line.strip()
    return data


def exif_date(img: Path):
    """DateTimeOriginal, if the image carries one."""
    try:
        from PIL import Image, ExifTags
    except ImportError:
        return None
    try:
        with Image.open(img) as im:
            exif = im.getexif()
            if not exif:
                return None
            raw = None
            # DateTimeOriginal lives in the Exif sub-IFD (0x8769), not the
            # top-level one, so check there first and fall back to the
            # top-level DateTime.
            try:
                sub = exif.get_ifd(0x8769)
                if sub:
                    named = {ExifTags.TAGS.get(k, k): v for k, v in sub.items()}
                    raw = named.get("DateTimeOriginal") or named.get("DateTimeDigitized")
            except Exception:
                pass
            if not raw:
                top = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
                raw = top.get("DateTimeOriginal") or top.get("DateTime")
            if raw:
                # EXIF format: "2026:08:01 17:42:03"
                return str(raw).split()[0].replace(":", "-")
    except Exception:
        pass
    return None


def titleize(stem: str) -> str:
    m = DATE_PREFIX.match(stem)
    if m and m.group(4):
        stem = m.group(4)
    words = re.split(r"[-_\s]+", stem.strip())
    small = {"a", "an", "and", "the", "of", "in", "on", "at", "to", "from", "with"}
    out = []
    for i, w in enumerate(words):
        if not w:
            continue
        out.append(w if (w.isupper() and len(w) > 1)
                   else (w.lower() if (i and w.lower() in small) else w.capitalize()))
    return " ".join(out) or stem


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} · Deepayan Mukherjee</title>
  <link rel="icon" href="../icons/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="../icons/favicon-32.png" sizes="32x32" type="image/png">
  <link rel="icon" href="../icons/favicon-16.png" sizes="16x16" type="image/png">
  <link rel="apple-touch-icon" href="../icons/apple-touch-icon.png">
  <link rel="manifest" href="../site.webmanifest">
  <meta name="post-date" content="{iso}">
  <meta name="post-kind" content="photograph">
  <meta name="post-image" content="../images/photographs/{filename}">
  <meta name="generated-by" content="generate_photo_pages">
  <meta name="source-image" content="{filename}">
  <link rel="stylesheet" href="../css/style.css?v=23">
  <link rel="preload" href="../fonts/pinyon-script.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="../fonts/cinzel.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="../fonts/eb-garamond.woff2" as="font" type="font/woff2" crossorigin>
  <script>
    if (localStorage.getItem('theme') === 'light') {{
      document.documentElement.setAttribute('data-theme', 'light');
    }}
  </script>
</head>
<body id="top">

  <div class="site-top" id="site-top">
    <header class="site-header">
      <div class="site-header-inner">
        <a class="site-mark" href="../">
          <span class="wordmark"><span class="initial">D</span><span class="smallcaps">eepayan</span><span class="initial">M</span><span class="smallcaps">ukherjee</span></span>
        </a>
        <button class="theme-toggle" id="theme-toggle" aria-label="Toggle light and dark mode">Light</button>
      </div>
    </header>
    <nav class="site-nav">
      <div class="site-nav-inner">
        <a href="../essays/">Essays</a>
        <a href="../poetry/">Poetry</a>
        <a href="./" class="active">Photographs</a>
        <a href="../about.html">About</a>
      </div>
    </nav>
  </div>

  <main>
    <article class="essay">
      <div class="article-head">
        <h1>{title}</h1>
        <p class="meta-row">{human}</p>
      </div>
      <img src="../images/photographs/{filename}" alt="{title}" style="border:1px solid var(--rule); margin-bottom:1.8rem;">
{caption_block}    </article>
  </main>

  <footer class="site-footer">
    <div class="site-footer-inner">
      <span>&copy; <span id="year">2026</span> Deepayan Mukherjee</span>
      <span><!-- PARTIAL:footer-location -->Patna · Pilani<!-- /PARTIAL --></span>
    </div>
  </footer>

  <script src="../js/main.js?v=24"></script>
</body>
</html>
"""


def human_date(iso: str) -> str:
    try:
        y, m, d = (int(x) for x in iso.split("-"))
        months = ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December"]
        return f"{d} {months[m-1]} {y}"
    except Exception:
        return iso


def prune_orphans(existing_images: set) -> int:
    """Remove generated pages whose image is gone.

    Only touches pages carrying the generated-by marker, so a page you
    wrote or edited by hand is never deleted — it just gets a warning.
    """
    removed = 0
    for page in sorted(PAGES.glob("*.html")):
        if page.name == "index.html":
            continue
        text = page.read_text(encoding="utf-8")

        src_m = re.search(r'<meta\s+name="source-image"\s+content="([^"]+)"', text)
        generated = 'name="generated-by" content="generate_photo_pages"' in text

        if src_m:
            source = src_m.group(1)
        else:
            # older/hand-written pages: fall back to the post-image path
            img_m = re.search(r'<meta\s+name="post-image"\s+content="[^"]*?([^/"]+)"', text)
            if not img_m:
                continue
            source = img_m.group(1)

        if source in existing_images:
            continue

        if generated:
            page.unlink()
            print(f"  removed photographs/{page.name} — its image ({source}) is gone")
            removed += 1
        else:
            print(f"  ! photographs/{page.name} points at {source}, which no longer "
                  f"exists — left alone because it wasn't auto-generated. Delete it "
                  f"yourself if you don't want it.")
    return removed


def main():
    if not IMAGES.is_dir():
        print("no images/photographs/ directory — nothing to do")
        return
    PAGES.mkdir(exist_ok=True)

    created = updated = skipped = 0
    files = sorted(p for p in IMAGES.iterdir() if p.is_file())
    print(f"scanning {IMAGES.relative_to(ROOT)}/ — {len(files)} file(s) found")

    for img in files:
        ext = img.suffix.lower()

        if ext == ".txt":
            continue  # sidecar, handled alongside its image

        if ext not in IMAGE_EXTS:
            print(f"  ! {img.name}: '{ext}' is not a recognised image extension — ignored")
            continue

        if ext in UNSUPPORTED_IN_BROWSER:
            print(f"  ! {img.name}: browsers can't display {ext} files. Convert it to "
                  f".jpg and re-upload, or the page will show a broken image.")

        page = PAGES / f"{img.stem}.html"

        # A page that exists but no longer carries the generated-by marker
        # has been adopted by hand — never touch it again.
        if page.exists():
            existing = page.read_text(encoding="utf-8")
            if 'name="generated-by" content="generate_photo_pages"' not in existing:
                print(f"    {img.name}: page was hand-edited, left alone")
                skipped += 1
                continue
        else:
            existing = None

        side = read_sidecar(img)

        iso = side.get("date") or exif_date(img)
        if not iso:
            m = DATE_PREFIX.match(img.stem)
            if m:
                iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if not iso:
            iso = date.today().isoformat()
            print(f"  ! {img.name}: no EXIF date, no date in filename, no sidecar — "
                  f"using today ({iso}). Add a date to pin it.")

        title = side.get("title") or titleize(img.stem)
        caption = side.get("caption", "").strip()
        caption_block = (f'      <div class="content">\n        <p>{esc(caption)}</p>\n'
                         f'      </div>\n') if caption else ""

        rendered = PAGE.format(
            title=esc(title),
            iso=iso,
            human=human_date(iso),
            filename=img.name,
            caption_block=caption_block,
        )

        if existing is None:
            page.write_text(rendered, encoding="utf-8")
            print(f"  created photographs/{page.name}  ({title}, {iso})")
            created += 1
        elif existing != rendered:
            page.write_text(rendered, encoding="utf-8")
            print(f"  updated photographs/{page.name}  ({title}, {iso})")
            updated += 1
        else:
            skipped += 1

    image_names = {p.name for p in files if p.suffix.lower() in IMAGE_EXTS}
    removed = prune_orphans(image_names)

    print(f"photo pages: {created} created, {updated} updated, "
          f"{skipped} unchanged, {removed} removed")


if __name__ == "__main__":
    main()
