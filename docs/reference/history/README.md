# Project History

Three repos each kept a `CHANGELOG.md` that every pull request was required to
update. All three were retired on **2026-09-10**, and their accumulated content
is published here, frozen and verbatim.

| Archive | Lines | Covers |
|---|---|---|
| [sales.demos](sales-demos.md) | 5,394 | 2026-07-22 → 2026-09-10 |
| [image.builder.pipeline](image-builder-pipeline.md) | 444 | the image factory, to 2026-09-10 |
| [sales.demos-docs](sales-demos-docs.md) | 232 | this site, to 2026-09-10 |

**Nothing is appended to these pages again.** They exist so that references
written before the retirement still resolve.

## Where each kind of information lives now

| Question | Answer |
|---|---|
| What changed, and when | `git log`, plus that repo's closed issues and merged pull requests |
| Why a convention exists | that repo's `CLAUDE.md` |
| What is planned | [`ROADMAP.md`](https://github.com/ericcames/sales.demos/blob/main/ROADMAP.md) in sales.demos |
| What happened before 2026-09-10 | these pages |

## Why they were retired

Not because changelogs are a bad idea — because these three had stopped being
changelogs. Measured on 2026-09-10:

- **No releases, ever.** Zero git tags and zero GitHub releases across all three
  repos. 5,386 of sales.demos' 5,394 lines sat under a single `[Unreleased]`
  heading that had been true, and meaningless, since the repo's first commit. The
  file also claimed to adhere to Semantic Versioning, and there were no versions.
- **Every pull request touched the file** — 60 of the last 60 commits in
  sales.demos, adding ~31 lines each and deleting none, ever.
- **The same prose was written three times**: once in the issue, once in the
  commit message, once in the changelog entry.
- **A one-line-per-PR version would have transcribed `git log --oneline`.** Commit
  subjects in these repos already read as changelog lines.

What the files had genuinely become was a **decision record** — long-form
rationale for why things are the way they are. That is documentation, and since
[sales.demos#422](https://github.com/ericcames/sales.demos/issues/422)
documentation lives in this repo. Hence these pages.

Durable conventions still get written down; they go to each repo's `CLAUDE.md`,
which is curated rather than append-only. No per-PR artifact replaced the
changelog, because that would have renamed the work rather than retired it.

## Reading them

Bare issue numbers do **not** autolink here. Each page names the repo its `#N`
references belong to, and gives the URL shape.

That is deliberate. The obvious fix — `pymdownx.magiclink` — resolves a bare
`#N` against one configured repository, and these are three different repos'
histories on three pages. Two-thirds of the references would have pointed
silently at the wrong tracker.

## Related

- [sales.demos#432](https://github.com/ericcames/sales.demos/issues/432)
- [image.builder.pipeline#119](https://github.com/ericcames/image.builder.pipeline/issues/119)
- [sales.demos-docs#18](https://github.com/ericcames/sales.demos-docs/issues/18)
