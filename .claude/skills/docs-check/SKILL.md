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
4. **The `- #N` heading trap** — Python-Markdown's `lenient` ATX heading
   parser (which mkdocs-material enables by default) treats `- #357` as a
   heading, not a list item with a GitHub issue reference. This once truncated
   a page TOC from 263 entries to 42. Grep for `^\s*- #[0-9]` and flag every
   match.

## Run

Run from the repo root:

```bash
echo "=== 1. Strict build ==="
pip install mkdocs-material -q
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
echo "=== 4. Heading trap (- #N) ==="
python3 - <<'PY'
import pathlib

docs = pathlib.Path("docs")
bad = 0
for md in sorted(docs.rglob("*.md")):
    for i, line in enumerate(md.read_text(errors="replace").splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("- #") and len(stripped) > 3 and stripped[3].isdigit():
            print(f"  {md}:{i}: {line.strip()}")
            bad += 1
if bad:
    print(f"\n{bad} line(s) where '- #N' will render as a heading, not a list item")
    print("Fix: escape the hash (- \\#N) or rephrase (- issue #N)")
else:
    print("No heading-trap lines found.")
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
- **Check 4 (heading trap)**: every match is a line that Python-Markdown will
  turn into a heading instead of a list item. The fix is to escape the hash
  (`\#N`) or rephrase (`issue #N`).

## When it finishes

Report any failures found. If all four checks are clean, say so — that is the
signal to push.
