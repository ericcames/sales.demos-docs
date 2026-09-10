# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This repo publishes a site rather than a release artifact, so there are no
version tags — the deployed site always reflects `main`. Entries record what
changed and why, in the order it merged.

## [Unreleased]

### Changed -- README omitted the cross-repo working shape (#10)

- **This repo's `## Getting started` is the model the other two just copied**,
  and was the only one of the three left without the cross-repo pointer. It
  already segments by audience -- *"Presenting a demo? You do not need this
  repo"* / *"Editing the docs?"* -- which is the shape applied in sales.demos#418
  and image.builder.pipeline#114. Added a third case: changing the automation
  and the words in one sitting, which is normal here, since every claim in a
  talk track is sourced back to a file in `sales.demos`.
- **It points the agent session at `sales.demos`, not here.** That repo's
  `.mcp.json` is project-scoped, so its cluster servers load only in a session
  started in that directory; this repo has no `.mcp.json` at all and needs none.
  Working here is `mkdocs serve` alongside it.
- Kept to one paragraph that links out rather than duplicating either repo's
  instructions -- the value of this section is that it is short and tells most
  readers they can leave.

### Added -- Community Standards: the repo had a README and a LICENSE and nothing else (#7)

- **This repo scored 42% on GitHub's Community Standards.** The community
  profile returned `["license","readme"]` and nothing more. The conventions
  were not missing -- they were in `CLAUDE.md`, which is written for an agent,
  not for a person. Someone landing here had no documented way in.
- Added `CONTRIBUTING.md`, carrying the human-facing half of `CLAUDE.md`: the
  three-tier documentation split, what never gets committed, `mkdocs serve`,
  how to add a demo, the issue-before-code workflow, branch naming, protected
  `main`, the two CI checks, worktrees, and post-merge cleanup. `CLAUDE.md`
  now links to it instead of duplicating it.
- Added `CODE_OF_CONDUCT.md` -- full Contributor Covenant 2.1, contact
  `ames@redhat.com`. Byte-identical to `sales.demos` and
  `image.builder.pipeline`.
- Added `.github/SECURITY.md`. **Screenshots get their own paragraph**: a
  credential in a file is grep-able, one in a PNG is not, and neither
  `check-no-secrets.sh` nor a diff review will catch it.
- Added `.github/ISSUE_TEMPLATE/{bug_report.md,feature_request.md,config.yml}`,
  `.github/PULL_REQUEST_TEMPLATE.md` and `.github/CODEOWNERS`. The chooser sets
  `blank_issues_enabled: false` and links the site, the automation repo, the
  security policy and the contributing guide.
- Added this changelog.

### Changed

- **`README.md` rewritten.** It was 27 lines, opened with a one-sentence
  description, and had **no getting-started section at all** -- nothing said
  this was an mkdocs-material site, that `mkdocs serve` previews it, or how to
  add a demo. It now opens with a value-first executive summary and an
  at-a-glance table, then `## Getting started`, split by what the reader came
  for: presenting a demo needs no clone at all.
- **`docs/demos/README.md` was missing Edge / SNO from its use-case table.**
  The directory has existed since #6 and is in the site nav; only the table
  that claims to list every use case had not caught up. Fixed here because the
  new README asserts four demos and the two would otherwise disagree.
