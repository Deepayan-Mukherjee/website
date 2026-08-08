#!/usr/bin/env python3
"""
Generates sitemap.xml at the site root by scanning every .html file
in the repo and reading its <meta name="post-date"> if it has one.

You never run this yourself — GitHub Actions runs it automatically on
every push, after build_index.py and generate_photo_pages.py, so it
always reflects whatever essays/poems/photos exist at deploy time.

Why this exists: a brand-new site has no other pages linking to it,
so Google's crawler has nothing to follow to discover your content.
Search Console's "Request Indexing" solves this one URL at a time,
but a sitemap solves it for the whole site at once — submit it once
in Search Console, and every future push updates the file, so new
essays/poems/photos get picked up on Google's next crawl without you
manually requesting each one.

URLs are written without the .html extension, matching how the site
actually links internally (see build_index.py's pretty_href) — GitHub
Pages resolves /foo the same as /foo.html, so this is what the
canonical URL should be.
"""
import re
from pathlib import Path
from datetime import date, datetime

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://deepayanmukherjee.in"

# Folders that hold individual content pages (auto-generated or not).
CONTENT_DIRS = ["essays", "poetry", "photographs"]

# Static top-level pages worth listing explicitly, with a rough
# priority/changefreq — these rarely change once written.
STATIC_PAGES = [
    # (path relative to root, changefreq, priority)
    ("", "weekly", "1.0"),  # homepage
    ("about.html", "monthly", "0.6"),
]

DATE_RE = re.compile(r'<meta\s+name="post-date"\s+content="([^"]+)"')
NOINDEX_RE = re.compile(r'<meta\s+name="robots"\s+content="[^"]*noindex', re.I)


def pretty_url(rel_path: str) -> str:
    """Turn a filesystem path into the canonical clean URL for it."""
    if rel_path in ("", "index.html"):
        return f"{BASE_URL}/"
    if rel_path.endswith("/index.html"):
        return f"{BASE_URL}/{rel_path[:-len('index.html')]}"
    if rel_path.endswith(".html"):
        return f"{BASE_URL}/{rel_path[:-len('.html')]}"
    return f"{BASE_URL}/{rel_path}"


def lastmod_for(path: Path) -> str:
    """post-date meta tag if present, else the file's mtime, else today."""
    try:
        text = path.read_text(encoding="utf-8")
        if NOINDEX_RE.search(text):
            return None  # signal: skip this page entirely
        m = DATE_RE.search(text)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    except Exception:
        return date.today().isoformat()


def collect_urls():
    entries = []  # (url, lastmod, changefreq, priority)

    for rel, changefreq, priority in STATIC_PAGES:
        p = ROOT / rel if rel else ROOT / "index.html"
        if not p.exists():
            print(f"  ! static page missing, skipped: {rel or 'index.html'}")
            continue
        lastmod = lastmod_for(p)
        if lastmod is None:
            continue
        entries.append((pretty_url(rel), lastmod, changefreq, priority))

    for folder_name in CONTENT_DIRS:
        folder = ROOT / folder_name
        if not folder.is_dir():
            continue

        index_page = folder / "index.html"
        if index_page.exists():
            lastmod = lastmod_for(index_page) or date.today().isoformat()
            entries.append((pretty_url(f"{folder_name}/"), lastmod, "weekly", "0.7"))

        for f in sorted(folder.glob("*.html")):
            if f.name == "index.html":
                continue
            lastmod = lastmod_for(f)
            if lastmod is None:
                print(f"  skipping {folder_name}/{f.name} — marked noindex")
                continue
            entries.append((pretty_url(f"{folder_name}/{f.name}"), lastmod, "monthly", "0.5"))

    return entries


def build_xml(entries) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lastmod, changefreq, priority in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <changefreq>{changefreq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main():
    entries = collect_urls()
    entries.sort(key=lambda e: e[1], reverse=True)  # newest first, cosmetic only

    xml = build_xml(entries)
    out = ROOT / "sitemap.xml"
    out.write_text(xml, encoding="utf-8")
    print(f"sitemap.xml written — {len(entries)} URL(s)")
    for url, lastmod, *_ in entries:
        print(f"  {lastmod}  {url}")


if __name__ == "__main__":
    main()
