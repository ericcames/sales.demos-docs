# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This repo publishes a site rather than a release artifact, so there are no
version tags — the deployed site always reflects `main`. Entries record what
changed and why, in the order it merged.

## [Unreleased]

### Changed -- this repo is now the canonical home for the docs (#12)

- **`docs/plan/` and `docs/demos/` existed in both repos with nothing keeping
  them in step, and 20 of the 35 shared files had drifted apart.** Two copies
  and no mechanism is the same failure class as #85 and #87: a reader cannot
  tell which is current, and neither can CI. `sales.demos` now links here
  (ericcames/sales.demos#422).
- **The drift was not cosmetic, and it was not one-directional.** Resolved file
  by file rather than by picking a winner wholesale, because neither copy was
  uniformly newer:
    - **Taken from `sales.demos`** -- `openshift-virtualization/` and
      `mcp-servers/`, plus `plan/ocpvirt-demo-plan.md`. The copies here named
      job templates the automation now *deletes* (`Sales Demos - Build Demo VM`
      and `Sales Demos - Provision VM` both carry `state: absent`), playbooks
      that were renamed (`register_vm.yml` -> `register_linux_vm.yml`), and a
      `Sales Demos - Vault` credential superseded in #129.
    - **Kept from here** -- all of `edge-sno/`, which was authored here and is
      two to three times longer than the pointer stubs `sales.demos` carries,
      and `demos/README.md`, whose framing is correct for a docs site.
- **The worst of it was a run sheet telling presenters Windows "cannot be
  logged into yet"** and citing image.builder.pipeline#59 as the blocker. That
  was proven working end to end on 2026-09-06 -- clone reaches the desktop,
  `win_ping` succeeds from AAP (sales.demos#257). A presenter reading this page
  would have talked a customer out of a feature that works.
- **`server-inventory.md` was the pre-#414 version, missing `openshift-edge`
  entirely** and counting "five servers" in eight places. The fix landed in
  `sales.demos` and never crossed. Stale enumerations are the recurring bug
  class here.
- **`demo-page.png` here was the 2026-09-06 original**; `sales.demos` had
  regenerated it in #389. Refreshed.

### Added -- `docs/reference/`, the operator material evicted from the sales.demos README (#12)

- Five pages: `environments.md`, `running-playbooks.md`, `running-from-aap.md`,
  `execution-environment.md`, `reusing-this-repo.md`, plus an index.
- **`running-from-aap.md` is the one that did not exist in any form.** The
  `sales.demos` README documented 2 Linux job templates; the automation defines
  **32 live templates and 4 live workflows**, of which 13 Windows templates and
  the entire `Windows Day 1` / `Windows Day 2` stories were undocumented. Counts
  taken from `controller_templates.yml` and `controller_workflows.yml`, ignoring
  `state: absent` tombstones.

### Fixed -- links that pointed at the wrong repo, or at nothing (#12)

- Six relative links reached for `../../../` -- `ROADMAP.md`, `.mcp.json`,
  `.claude/skills/pah-sync/SKILL.md` -- which resolves outside this repo. Now
  absolute URLs into `sales.demos`. Three were pre-existing here, three arrived
  with the copied files.
- **Two links resolved and were still wrong.** `../../../README.md` labelled
  "the repo itself" lands on *this* repo's README from `docs/demos/<x>/`, not on
  `sales.demos`. An existence check passes; the reader still goes to the wrong
  page.
- Four anchors into `server-inventory.md` were dead (`#aap--bearer-token` for
  `#aap-bearer-token`, and three more). `mkdocs build` reports these at INFO and
  exits 0, so nothing was failing.
- **The Day 1 table in `edge-sno/architecture.md` was headed "applied by
  `setup_edge.yml`", and that playbook does not exist.** Replaced with the real
  per-playbook table. The rest of that page's `setup_edge.yml` references, and
  the run sheet's `tee` pipelines, are sales.demos#424 -- wrong in both copies
  identically, so not drift.

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
