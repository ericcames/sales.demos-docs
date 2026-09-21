---
name: docs-check
description: "Run site quality checks that CI does not — strict mkdocs build, links resolved against the published site, dead external URLs, and the Python-Markdown heading trap. TRIGGER when: the user asks to check, lint, or validate the docs site, wants to find broken links, asks why a page TOC is wrong, or is about to push a docs change and wants a pre-merge check. SKIP: if the user wants to build and serve the site locally for reading — just run mkdocs serve."
---

# docs-check

Run four site quality checks that CI currently does not enforce. CI runs
`mkdocs build` without `--strict` and checks no links. This skill fills
that gap.

Takes about **30 seconds** for a full run.

## What it checks

1. **Strict build** — `mkdocs build --strict` turns warnings into errors.
   Catches undefined cross-references, missing nav entries, and invalid
   markdown extensions.
2. **Broken links, resolved against the published site** — `utilities/check-links.py`.
   It reads the built `site/` tree and resolves every in-content link against
   the URL each page is *served at*, not against the source file's directory.

   **That distinction is the whole check.** `use_directory_urls` puts every
   page one level deeper than its source file. MkDocs rewrites `.md` links and
   media `src` attributes to compensate, but passes a bare directory path
   through untouched — so `[demo](../demos/edge-sno/)` written in
   `docs/image-factory/sno-kit.md` is served from `/image-factory/sno-kit/`
   and lands on `/image-factory/demos/edge-sno/`, which does not exist.

   The version of this check that lived here until #108 did
   `(md.parent / target).resolve().exists()` against `docs/`. Since
   `docs/demos/edge-sno` exists on disk, it passed. Four links of exactly that
   shape were live on the published site, and no number of runs would ever
   have found them. Only the built tree knows.

3. **Dead external URLs** — `utilities/check-links.py --external`. Uses GET,
   not HEAD: several `redhat.com` pages reject HEAD with a 4xx and a
   HEAD-only check reports them as dead.
4. **The heading trap** — Python-Markdown's `lenient` ATX heading parser
   (which mkdocs-material enables by default) turns a line beginning with `#`
   plus a digit into an `<h1>`, so a wrapped sentence whose line happens to
   start `#357` becomes a top-level heading and enters the page TOC. This once
   truncated a page TOC from 263 entries to 42.

   **Checked against the built HTML, not with a grep**, because a grep is
   wrong in both directions. The previous `^\s*- #[0-9]` pattern matched only
   the list-item form and found **zero** of the 8 live defects #85 fixed —
   those were paragraph continuations and blockquotes (`> #358 ...`). A
   broader pattern then false-positives on lines indented inside a list item,
   which are lazy continuations and never headings. The rendered page is the
   only thing that knows. Any page with more than one `<h1>` in its `<article>`
   has one it did not ask for.

## Run

Run from the repo root:

```bash
echo "=== 1. Strict build ==="
pip install -r requirements.txt -q
mkdocs build --strict 2>&1
# Checks 2 and 4 both read the site/ tree this produces.

echo ""
echo "=== 2 + 3. Links (resolved against the published site) ==="
python3 utilities/check-links.py --no-build --external

echo ""
echo "=== 4. Heading trap (spurious <h1> in the built site) ==="
python3 - <<'PY'
import pathlib, re

# Reads site/ from the strict build in check 1. A page has exactly one <h1>,
# its title; any extra is a sentence Python-Markdown promoted to a heading.
site = pathlib.Path("site")
if not site.is_dir():
    raise SystemExit("  site/ not found — run check 1 (mkdocs build) first")
bad = 0
for html in sorted(site.rglob("index.html")):
    art = re.search(r'<article[^>]*>(.*?)</article>',
                    html.read_text(errors="replace"), re.S)
    if not art:
        continue
    h1s = re.findall(r'<h1\b[^>]*>(.*?)</h1>', art.group(1), re.S)
    for extra in h1s[1:]:
        txt = re.sub(r'<[^>]+>', '', extra).strip().replace("\n", " ")
        print(f"  {html.relative_to(site).parent}: {txt[:64]}")
        bad += 1
if bad:
    print(f"\n{bad} spurious <h1> — a wrapped line starts with '#' plus a digit")
    print("Fix: re-wrap so the reference is not first on the line, or write it")
    print("as sales.demos#357. Search the source for the words printed above.")
else:
    print("No spurious headings.")
PY
```

## Interpreting the results

- **Check 1 (strict build)**: any output line starting with `WARNING` or
  `ERROR` is a real problem. Common: undefined cross-references from a nav
  entry pointing at a page that was moved.
- **Check 2 (links)**: every `BROKEN` line prints the page, the link as
  written, and the URL it actually resolves to. If the target looks like it
  should exist, the link is almost always a bare directory path — point it at
  the `.md` file instead (`../demos/edge-sno/README.md`), which is the form
  mkdocs validates and rewrites. `mkdocs build` also prints
  `unrecognized relative link ... Did you mean 'X/README.md'?` for the
  forward-relative version of the same mistake; that log should stay empty.
- **Check 3 (external URLs)**: a status code or `FAIL` means unreachable.
  `docs.redhat.com` restructures its slugs between versions, so never write
  one from memory — add it, then run this.
- **Check 4 (heading trap)**: every match is a real heading on the published
  page that nobody wrote, sitting in the right-hand table of contents. The
  printed text is the start of the promoted line — grep the source for it. Fix
  by re-wrapping so the `#` reference is not the first character on its line,
  or by writing it as `sales.demos#357`. `mkdocs build` never warns about
  this, `--strict` included, which is why CI cannot catch it.

## When it finishes

Report any failures found. If all four checks are clean, say so — that is the
signal to push.
