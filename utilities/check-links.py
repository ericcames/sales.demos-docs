#!/usr/bin/env python3
"""Resolve every in-content link against the PUBLISHED site, not the filesystem.

The distinction is the whole point. A link written relative to the source
directory can resolve on disk and still 404 once published, because
`use_directory_urls` puts every page one level deeper than its source file.
MkDocs rewrites `.md` links and media `src` attributes to account for that,
but passes a bare directory path (`../demos/edge-sno/`) through untouched.

The check that lived inline in the docs-check skill did
`(md.parent / target).resolve().exists()` against `docs/`, so
`docs/demos/edge-sno` existing on disk made a link to `/image-factory/demos/
edge-sno/` look fine. Four such links were live on the site (#108). Reading
the built `site/` tree is the only thing that knows.

  python3 utilities/check-links.py                 # build, then check internal links
  python3 utilities/check-links.py --no-build      # reuse an existing site/
  python3 utilities/check-links.py --external      # also status-check http(s)
  python3 utilities/check-links.py --published URL # crawl the live site instead
"""

import argparse
import concurrent.futures
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ARTICLE = re.compile(r"<article[^>]*>(.*?)</article>", re.S)
REF = re.compile(r'(?:href|src)="([^"]+)"')
SKIP = ("mailto:", "tel:", "data:", "javascript:")


def article_refs(html):
    """Links inside the page body. Nav and theme chrome are generated, not ours."""
    m = ARTICLE.search(html)
    if not m:
        return []
    return [r for r in REF.findall(m.group(1)) if not r.startswith(("#",) + SKIP)]


def check_local(site, build):
    if build:
        print("Building site/ ...")
        r = subprocess.run(["mkdocs", "build", "--strict"], capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        if r.returncode:
            print("mkdocs build --strict failed; not checking links against a stale site/")
            return 1, set()
    if not site.is_dir():
        print(f"{site}/ not found — run without --no-build")
        return 1, set()

    pages = sorted(site.rglob("*.html"))
    known = {p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()}
    bad, external = [], set()

    for page in pages:
        # The URL this page is served at, as a path relative to the site root.
        url_dir = page.relative_to(site).parent.as_posix()
        for ref in article_refs(page.read_text(errors="replace")):
            if ref.startswith(("http://", "https://", "//")):
                external.add(ref.split("#")[0])
                continue
            target = urllib.parse.urlsplit(ref).path
            if not target:
                continue
            resolved = urllib.parse.urljoin(url_dir + "/", target)
            resolved = resolved.lstrip("/")
            if resolved.startswith(".."):
                bad.append((page, ref, "escapes the site root"))
                continue
            candidates = [resolved, resolved.rstrip("/") + "/index.html", resolved + "index.html"]
            if not any(c in known for c in candidates):
                bad.append((page, ref, f"/{resolved}"))

    print(f"\n=== Internal links ({len(pages)} pages) ===")
    for page, ref, why in bad:
        print(f"  BROKEN  {page.relative_to(site).parent}/  ->  {ref}   ({why})")
    print(f"{len(bad)} broken" if bad else "All internal links resolve.")
    return len(bad), external


def crawl_published(base):
    """Check the live site. GitHub Pages is what was actually broken, not the build."""
    base = base.rstrip("/") + "/"
    try:
        sm = urllib.request.urlopen(base + "sitemap.xml", timeout=30).read().decode()
    except Exception as e:
        print(f"could not read {base}sitemap.xml: {e}")
        return 1, set()
    pages = re.findall(r"<loc>([^<]+)</loc>", sm)
    known, bad, external = {}, [], set()

    def alive(url):
        if url not in known:
            known[url] = status(url) < 400
        return known[url]

    for p in pages:
        try:
            html = urllib.request.urlopen(p, timeout=30).read().decode("utf-8", "replace")
        except Exception as e:
            print(f"  FETCHFAIL  {p}  ({e})")
            bad.append((p, "", str(e)))
            continue
        for ref in article_refs(html):
            if ref.startswith(("http://", "https://", "//")):
                external.add(ref.split("#")[0])
                continue
            tgt = urllib.parse.urljoin(p, urllib.parse.urlsplit(ref).path)
            if not tgt.startswith(base):
                bad.append((p, ref, "escapes the site root"))
            elif not alive(tgt):
                bad.append((p, ref, tgt))

    print(f"\n=== Published links ({len(pages)} pages) ===")
    for page, ref, why in bad:
        print(f"  BROKEN  {page}  ->  {ref}   ({why})")
    print(f"{len(bad)} broken" if bad else "All published links resolve.")
    return len(bad), external


# An honest tool User-Agent first. docs.redhat.com serves `curl/*` with a 200
# and 403s a browser-like UA that arrives without the rest of a browser's
# headers — measured 2026-09-21, when a "Mozilla/5.0 (check-links)" UA reported
# 19 perfectly good Red Hat pages as dead. Second UA is a fallback for hosts
# that do the opposite.
AGENTS = (
    "curl/8.5.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36",
)


def status(url):
    """GET, not HEAD: several redhat.com pages reject HEAD with a 4xx.

    Retries once under a different User-Agent before calling anything dead. A
    checker that cries wolf gets ignored, which is worse than not having one.
    """
    code = 0
    for agent in AGENTS:
        req = urllib.request.Request(url, headers={"User-Agent": agent})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status
        except urllib.error.HTTPError as e:
            code = e.code
            if e.code not in (403, 405, 429):
                return e.code
        except Exception:
            code = code or 0
    return code


def check_external(urls):
    print(f"\n=== External URLs ({len(urls)}) ===")
    dead = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for url, code in sorted(zip(urls, pool.map(status, urls))):
            if code >= 400 or code == 0:
                print(f"  {code or 'FAIL'}  {url}")
                dead += 1
    print(f"{dead} dead or unreachable" if dead else "All external URLs reachable.")
    return dead


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-build", action="store_true", help="reuse an existing site/")
    ap.add_argument("--external", action="store_true", help="also status-check http(s) links")
    ap.add_argument("--published", metavar="URL", help="crawl the live site instead of site/")
    ap.add_argument("--site", default="site", type=pathlib.Path)
    args = ap.parse_args()

    if args.published:
        failures, external = crawl_published(args.published)
    else:
        failures, external = check_local(args.site, not args.no_build)

    if args.external:
        failures += check_external(sorted(external))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
