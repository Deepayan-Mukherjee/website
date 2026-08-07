#!/usr/bin/env python3
"""
Injects shared snippets from partials/ into every HTML page, so
things repeated on every page — the footer location, eventually a
bio blurb, whatever else — live in exactly one file instead of nine.

You never run this yourself — GitHub Actions runs it automatically on
every push, before build_index.py rebuilds the listings.

How it works: each file in partials/ named <name>.txt is dropped in
wherever a page has this marker pair:

    <!-- PARTIAL:<name> -->
    ...old content...
    <!-- /PARTIAL -->

Only the text between the markers is touched — everything else on
the page is untouched. To change something that appears on every
page (like the footer location), edit the file in partials/ once and
push; every page picks it up on the next build.

To add a new shared snippet:
  1. create partials/whatever.txt with the content
  2. wrap the spot in your HTML with
     <!-- PARTIAL:whatever --> ... <!-- /PARTIAL -->
  3. push — every page with that marker gets the content

A marker with no matching partials/<name>.txt file is left alone
(with a warning in the build log), not deleted.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTIALS = ROOT / "partials"

MARKER_RE = re.compile(
    r'<!-- PARTIAL:(\S+) -->(.*?)<!-- /PARTIAL -->',
    re.S,
)


def main():
    if not PARTIALS.is_dir():
        print("no partials/ directory — nothing to do")
        return

    snippets = {}
    for p in sorted(PARTIALS.glob("*.txt")):
        snippets[p.stem] = p.read_text(encoding="utf-8").strip()

    if not snippets:
        print("partials/ has no .txt files — nothing to inject")
        return

    print(f"loaded {len(snippets)} partial(s): {', '.join(sorted(snippets))}")

    changed_files = 0
    total_replacements = 0

    for f in sorted(ROOT.rglob("*.html")):
        text = f.read_text(encoding="utf-8")
        original = text
        file_replacements = 0

        def replace(m):
            nonlocal file_replacements
            name = m.group(1)
            if name not in snippets:
                print(f"  ! {f.relative_to(ROOT)}: no partials/{name}.txt for "
                      f"marker '{name}' — left as-is")
                return m.group(0)
            file_replacements += 1
            return f'<!-- PARTIAL:{name} -->{snippets[name]}<!-- /PARTIAL -->'

        text = MARKER_RE.sub(replace, text)

        if text != original:
            f.write_text(text, encoding="utf-8")
            changed_files += 1
            total_replacements += file_replacements

    print(f"injected into {changed_files} file(s), "
          f"{total_replacements} replacement(s) total")


if __name__ == "__main__":
    main()
