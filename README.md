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
css/style.css                 all styling, one file
js/main.js                    footer year, photo lightbox, reading aids
scripts/build_index.py        rebuilds the listings above, run by CI
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

1. Drop the image file into `images/photographs/`.
2. Duplicate `photographs/sample-photograph.html`, rename it, and edit
   the `<title>`, `post-date`, `post-image` (point it at your new
   image), the `<h1>`, and the caption text in `<div class="content">`.
3. Push. The gallery grid on `photographs/index.html` rebuilds itself
   from every file in the folder, same as essays and poetry — clicking
   a thumbnail still opens the full-size lightbox view, and the
   caption links through to that photo's own page.

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

## Adding a photograph

1. Put the image file in `images/photographs/`.
2. In `photographs/index.html`, copy one `<figure>...</figure>` block,
   point both the `href` and `src` at your new file, edit the caption.

Clicking a photo opens it full-size (that's the one bit of JavaScript
on the site, in `js/main.js`) — nothing to configure, it works
automatically for any photo added this way.

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

## Changing the design

Everything visual lives in `css/style.css` — colors are CSS variables
at the very top of the file, so a palette change is a few line edits,
not a rewrite.
