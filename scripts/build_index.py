#!/usr/bin/env python3
"""
Scans essays/ and poetry/ for .html files (skipping index.html),
reads each one's <title>, <meta name="post-date">, <meta name="post-kind">,
and rewrites the auto-index section of essays/index.html, poetry/index.html,
and index.html (home page's "Recent" list) to match.

You never run this yourself — GitHub Actions runs it automatically on
every push (see .github/workflows/deploy.yml). It only touches the text
between the <!-- AUTO-INDEX:... --> and <!-- /AUTO-INDEX --> markers;
everything else in these files is left exactly as you wrote it.
"""
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

TITLE_RE = re.compile(r"<title>(.*?)(?:\s*·.*)?</title>", re.S)
DATE_RE = re.compile(r'<meta\s+name="post-date"\s+content="([^"]+)"')
KIND_RE = re.compile(r'<meta\s+name="post-kind"\s+content="([^"]+)"')
IMAGE_RE = re.compile(r'<meta\s+name="post-image"\s+content="([^"]+)"')


def read_posts(folder: Path):
    posts = []
    for f in sorted(folder.glob("*.html")):
        if f.name == "index.html":
            continue
        text = f.read_text(encoding="utf-8")
        title_m = TITLE_RE.search(text)
        date_m = DATE_RE.search(text)
        kind_m = KIND_RE.search(text)
        image_m = IMAGE_RE.search(text)
        if not (title_m and date_m):
            print(f"  skipping {f} — missing <title> or post-date meta tag")
            continue
        posts.append({
            "title": title_m.group(1).strip(),
            "date": date_m.group(1).strip(),
            "kind": kind_m.group(1).strip() if kind_m else folder.name.rstrip("s"),
            "image": image_m.group(1).strip() if image_m else None,
            "filename": f.name,
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def fmt_date(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %Y")
    except ValueError:
        return iso


def render_section_li(post, href_prefix=""):
    return (
        '      <li>\n'
        f'        <span class="entry-date">{fmt_date(post["date"])}</span>\n'
        f'        <a class="entry-title" href="{href_prefix}{post["filename"]}">{post["title"]}</a>\n'
        '      </li>'
    )


def render_home_li(post, href_prefix):
    return (
        '      <li>\n'
        f'        <span class="entry-date">{fmt_date(post["date"])}</span>\n'
        f'        <a class="entry-title" href="{href_prefix}{post["filename"]}">{post["title"]}</a>\n'
        f'        <span class="entry-kind">{post["kind"]}</span>\n'
        '      </li>'
    )


def render_photo_figure(post):
    image = post["image"] or ""
    return (
        '      <figure>\n'
        f'        <a class="gallery-link" href="{image}" data-page="{post["filename"]}">\n'
        f'          <img src="{image}" alt="{post["title"]}" loading="lazy">\n'
        '        </a>\n'
        f'        <figcaption><a href="{post["filename"]}">{post["title"]}</a> · {fmt_date(post["date"])}</figcaption>\n'
        '      </figure>'
    )


def replace_block(html: str, marker: str, new_inner: str) -> str:
    pattern = re.compile(
        rf'(<!-- AUTO-INDEX:{marker} -->\n)(.*?)(\n\s*<!-- /AUTO-INDEX -->)',
        re.S,
    )
    if not pattern.search(html):
        print(f"  warning: no AUTO-INDEX:{marker} block found — skipping")
        return html
    return pattern.sub(lambda m: m.group(1) + new_inner + m.group(3), html)


def main():
    essays = read_posts(ROOT / "essays")
    poems = read_posts(ROOT / "poetry")
    photos = read_posts(ROOT / "photographs")

    # essays/index.html
    p = ROOT / "essays" / "index.html"
    html = p.read_text(encoding="utf-8")
    inner = "\n".join(render_section_li(e) for e in essays) if essays else "      <!-- no essays yet -->"
    p.write_text(replace_block(html, "essays", inner), encoding="utf-8")
    print(f"essays/index.html — {len(essays)} essay(s)")

    # poetry/index.html
    p = ROOT / "poetry" / "index.html"
    html = p.read_text(encoding="utf-8")
    inner = "\n".join(render_section_li(e) for e in poems) if poems else "      <!-- no poems yet -->"
    p.write_text(replace_block(html, "poetry", inner), encoding="utf-8")
    print(f"poetry/index.html — {len(poems)} poem(s)")

    # photographs/index.html
    p = ROOT / "photographs" / "index.html"
    html = p.read_text(encoding="utf-8")
    inner = "\n".join(render_photo_figure(ph) for ph in photos) if photos else "      <!-- no photographs yet -->"
    p.write_text(replace_block(html, "photographs", inner), encoding="utf-8")
    print(f"photographs/index.html — {len(photos)} photograph(s)")

    # index.html — combined "Recent", newest 8, essays + poetry only
    combined = essays + poems
    combined.sort(key=lambda p: p["date"], reverse=True)
    combined = combined[:8]
    p = ROOT / "index.html"
    html = p.read_text(encoding="utf-8")
    lines = []
    for post in combined:
        prefix = "essays/" if post in essays else "poetry/"
        lines.append(render_home_li(post, prefix))
    inner = "\n".join(lines) if lines else "      <!-- nothing published yet -->"
    p.write_text(replace_block(html, "home", inner), encoding="utf-8")
    print(f"index.html — {len(combined)} recent entr(y/ies)")


if __name__ == "__main__":
    main()
