# deepayanmukherjee.in

A plain HTML/CSS/JS site — every essay, poem, and photo page is a
hand-written file, no framework. The one exception: a small script
auto-generates each section's listing page so you never have to
manually add a link when you publish something new (see "How the
auto-indexing works" below). Open any `.html` file directly in a
browser to preview it exactly as it'll look live.

## Structure

```
index.html                    home page, "Recent" list is auto-generated
about.html
essays/
  index.html                   auto-generated list of all essays
  why-i-write-here.html        one essay = one file
poetry/
  index.html                   auto-generated list of all poems
  a-placeholder.html           one poem = one file
photographs/
  index.html                   auto-generated gallery grid
  sample-photograph.html       one photo's own page = one file
images/
  photographs/                  the actual photo files go here
icons/                        favicon + app icons (all sizes)
fonts/                        self-hosted webfonts (see below)
site.webmanifest              app icon metadata
css/style.css                 all styling, one file
js/main.js                    footer year, photo lightbox, reading aids
scripts/build_index.py        rebuilds the listings above, run by CI
scripts/generate_photo_pages.py  makes a page per image, run by CI
```

## Adding a new essay

1. Duplicate `essays/why-i-write-here.html`, rename it to something like
   `essays/my-new-essay.html`.
2. Edit the `<title>`, the two meta tags near the top of `<head>` —
   `<meta name="post-date" content="YYYY-MM-DD">` — and the
   `<div class="content">` itself: wrap paragraphs in `<p>...</p>`,
   sub-headings in `<h2>...</h2>`.
3. Push. That's it — you don't touch `essays/index.html` or the home
   page by hand. A script reads every file in `essays/` and rebuilds
   both listings automatically each time you push (see "How the
   auto-indexing works" below).

Same pattern for a new poem — duplicate `poetry/a-placeholder.html` —
except: put each line of a stanza on its own line ending in `<br>`,
and leave a blank line between stanzas.

**The two meta tags matter.** `post-date` controls sort order (newest
first) and `post-kind` controls the little "essay" / "poem" label on
the home page. Miss the date tag and the build script will skip the
file with a warning rather than guess — check the Actions tab on
GitHub if a piece doesn't show up after pushing.

## Adding a photograph

Drop the image into `images/photographs/` and push. That's the whole
thing — a page for it is generated automatically, and the gallery
listing picks it up.

Title, date and caption are worked out like this:

- **Title** — from the filename, tidied up. `old-delhi-rooftops.jpg`
  becomes "Old Delhi Rooftops".
- **Date** — the photo's EXIF shooting date if it has one (most phone
  and camera files do). Failing that, a date at the front of the
  filename: `2026-06-02-monsoon-arrives.jpg`. Failing that, today's
  date, with a warning in the build log telling you to pin it.
- **Caption** — none by default.

To override any of those, put a `.txt` file next to the image with the
same name — `images/photographs/rooftops.txt`:

```
title: Rooftops at dusk
date: 2026-05-19
caption: Shot from the roof of the hostel, about ten minutes
         after the power cut started.
```

Every field is optional; anything you leave out falls back to the rules
above. Captions can wrap across lines like the example — they get
joined back together.

You can add or change a sidecar at any time — before or after the image
goes up. The page is regenerated whenever its title, date or caption
changes, so adding a `.txt` later works exactly as well as having it
there from the start.

**If you want to edit a photo page by hand**, delete the line
`<meta name="generated-by" content="generate_photo_pages">` from it.
That marks the page as yours, and the script stops touching it —
no more regenerating from the sidecar, and it will never be
auto-deleted either.

**Deleting a photo**: remove the image from `images/photographs/` and
push. Its page is deleted automatically and it disappears from the
gallery. (Delete the `.txt` sidecar too, if it had one.)

The exception is again a page you've adopted by hand — that's never
auto-deleted. The build log prints a warning that its image is missing
and leaves the file for you to remove, so nothing you wrote can vanish
because a file got renamed.

## How the auto-indexing works

`scripts/build_index.py` scans `essays/`, `poetry/`, and
`photographs/` for `.html` files (skipping each folder's own
`index.html`), reads the `<title>` and meta tags from each one, and
rewrites everything between these two lines in `essays/index.html`,
`poetry/index.html`, `photographs/index.html`, and the "Recent" list
on `index.html`:
```html
<!-- AUTO-INDEX:essays -->
...
<!-- /AUTO-INDEX -->
```
(Home's "Recent" list only pulls from essays and poetry, not
photographs — text and photos don't read the same way in a list, so
photographs get their own gallery page instead of mixing in there.)

Nothing outside those markers is touched — the rest of each file is
exactly as you wrote it. You never run this script yourself; GitHub
Actions runs it automatically on every push, before deploying (see
`.github/workflows/deploy.yml`). If you want to see it work locally
first, `python3 scripts/build_index.py` from the project root does
the same thing the workflow does.

## Writing math (LaTeX)

`essays/why-i-write-here.html` already has this wired up — write math
right in the text, same syntax as normal LaTeX:

- inline: `$y = mx + c$`
- its own line: `$$\sum_{i=1}^{n} x_i$$`

It renders automatically, no extra step. If you duplicate that file to
start a new essay, the two `<script>` tags near the bottom of the file
(the MathJax config and the library itself) come along with it — leave
them in if the piece has any math, delete them if it doesn't (skipping
them makes the page load very slightly faster).

**One catch:** the `$` inline delimiter will misfire if you write a
plain dollar amount, e.g. "$500 million in aid" — it'll try to read
that as the start of a math expression. Two ways around it:
- write `\$500 million` instead (the backslash escapes it), or
- use `\(y = mx + c\)` instead of `$y = mx + c$` for inline math, and
  keep bare `$` free for currency

Either is fine — pick whichever you'll remember to do consistently.

## Scroll animations

Page titles, section headings, list rows, and gallery photos fade
and rise gently into place as you scroll to them — applied
automatically by `js/main.js` to those element types, so it works
on every essay/poem/photo without adding anything to the HTML
yourself. Body paragraphs are deliberately left alone — animating
every paragraph of a long essay would get in the way of actually
reading it, so only the structural/navigational elements move.

There's also a faint, fixed background "D" watermark on wide
screens (hidden below ~1200px) that drifts slightly as you scroll,
for a subtle layered-depth effect. Both respect the visitor's OS
`prefers-reduced-motion` setting — if that's on, everything just
appears normally with no animation or drift at all.

To change the feel of it: `.reveal` / `.reveal.visible` in
`css/style.css` control the fade/rise itself (distance, duration,
easing); the element list it applies to is the `selector` line near
the top of the scroll-reveal block in `js/main.js`.

## Previewing before you publish

Just open `index.html` directly in a browser — double-click it, or
drag it into a browser window. Every link on the site is a relative
path, so it all works locally exactly as it will once it's live.

## Publishing to GitHub Pages

1. Create a new **public** repository on GitHub (e.g. `deepayan-site`).
2. Push this whole folder to it:
   ```
   git init
   git add .
   git commit -m "first version of the site"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
   git push -u origin main
   ```
3. In the repo on GitHub: **Settings → Pages → Build and deployment →
   Source**, select **GitHub Actions** (not "Deploy from a branch" —
   the workflow needs to run the indexing script before it deploys).
   The workflow file already in `.github/workflows/deploy.yml` handles
   the rest automatically on every push from here on.
4. Still in **Settings → Pages**, under **Custom domain**, enter
   `deepayanmukherjee.in` and save. GitHub will commit a `CNAME` file
   into the repo for you automatically — there's already one in this
   folder pointing at the same domain, so this just confirms it.

From here, publishing a new essay is: write the file, `git push`, wait
about a minute for the Actions tab to show a green check. No manual
list-editing, no local build step required.

## Pointing the domain at GitHub Pages

In your BigRock DNS management panel for `deepayanmukherjee.in`, add:

**For the root domain** — four A records, all pointing to GitHub:
```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

**For `www.deepayanmukherjee.in`** (optional) — a CNAME record:
```
www    CNAME    YOUR-USERNAME.github.io.
```

DNS changes can take a few minutes to a few hours to propagate. Once
they do, GitHub Pages issues a free HTTPS certificate automatically —
nothing for you to set up.

## Clean URLs

Links between pages never show `.html` or `index.html` in the address
bar — `deepayanmukherjee.in/essays/why-i-write-here`, not
`.../essays/why-i-write-here.html`. The files on disk still end in
`.html` (so double-clicking one still opens correctly in a browser
for local preview); only the *links* are written without the
extension. This works because GitHub Pages automatically serves
`/foo.html` when `/foo` is requested — no configuration needed, and
nothing to maintain. `scripts/build_index.py` generates every list
link this way automatically, so it applies to every essay, poem, and
photo without you doing anything.

## Fonts

All five fonts (Pinyon Script, Cinzel, Playfair Display, EB Garamond
regular and italic) are self-hosted in `fonts/`, not loaded from
Google's CDN. That used to mean an extra DNS lookup, connection, and
two sequential fetches (Google's CSS, then the actual font file)
before the real fonts appeared — visible as a flash of a generic
fallback, which looked especially bad on the wordmark since nothing
else looks like Pinyon Script's swash. Hosting the files ourselves
removes that round-trip; the `<link rel="preload">` tags in each
page's `<head>` tell the browser to start fetching them immediately,
in parallel with everything else.

Each file is subsetted to Latin characters and common punctuation
only — 330KB total across all five. `fonts/LICENSE.txt` has the
license (SIL OFL) and links to the originals, if you ever want to
add a different weight or a second language's character set.

## Changing the design

Everything visual lives in `css/style.css` — colors are CSS variables
at the very top of the file, so a palette change is a few line edits,
not a rewrite.
