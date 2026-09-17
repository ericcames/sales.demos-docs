---
name: docs-check
description: "Run site quality checks that CI does not — strict mkdocs build, broken relative links, dead external URLs, and the Python-Markdown heading trap. TRIGGER when: the user asks to check, lint, or validate the docs site, wants to find broken links, asks why a page TOC is wrong, or is about to push a docs change and wants a pre-merge check. SKIP: if the user wants to build and serve the site locally for reading — just run mkdocs serve."
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
2. **Broken relative links** — resolves every relative link in every markdown
   file and reports ones that point to files that do not exist.
3. **Dead external URLs** — HEAD-checks every `https://` URL in the docs and
   reports ones that return non-200.
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

echo ""
echo "=== 2. Broken relative links ==="
python3 - <<'PY'
import pathlib, re

docs = pathlib.Path("docs")
bad = 0
for md in sorted(docs.rglob("*.md")):
    content = md.read_text(errors="replace")
    for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', content):
        target = m.group(2)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        frag = ""
        if "#" in target:
            target, frag = target.rsplit("#", 1)
        if not target:
            continue
        resolved = (md.parent / target).resolve()
        if not resolved.exists():
            print(f"  BROKEN: {md}  ->  {m.group(2)}")
            bad += 1
if bad:
    print(f"\n{bad} broken relative link(s)")
else:
    print("All relative links resolve.")
PY

echo ""
echo "=== 3. Dead external URLs ==="
python3 - <<'PY'
import pathlib, re, urllib.request, ssl, sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

docs = pathlib.Path("docs")
seen = set()
dead = 0
for md in sorted(docs.rglob("*.md")):
    for url in re.findall(r'https?://[^\s)\]>"]+', md.read_text(errors="replace")):
        url = url.rstrip(".,;:!?")
        if url in seen:
            continue
        seen.add(url)
        try:
            req = urllib.request.Request(url, method="HEAD",
                headers={"User-Agent": "docs-check/1.0"})
            resp = urllib.request.urlopen(req, context=ctx, timeout=10)
            if resp.status >= 400:
                print(f"  {resp.status}: {url}")
                dead += 1
        except Exception as e:
            print(f"  FAIL: {url}  ({e})")
            dead += 1
if dead:
    print(f"\n{dead} dead or unreachable URL(s)")
else:
    print("All external URLs reachable.")
PY

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
- **Check 2 (relative links)**: every `BROKEN` line is a link whose target
  does not exist on disk. Usually a renamed or deleted file.
- **Check 3 (external URLs)**: `FAIL` means the URL is unreachable or timed
  out. Some sites block HEAD requests — verify manually before removing a link.
- **Check 4 (heading trap)**: every match is a real heading on the published
  page that nobody wrote, sitting in the right-hand table of contents. The
  printed text is the start of the promoted line — grep the source for it. Fix
  by re-wrapping so the `#` reference is not the first character on its line,
  or by writing it as `sales.demos#357`. `mkdocs build` never warns about
  this, `--strict` included, which is why CI cannot catch it.

## When it finishes

Report any failures found. If all four checks are clean, say so — that is the
signal to push.
