# sales.demos-docs — project history

!!! note "Frozen archive — retired 2026-09-10"

    This is this repo's own `CHANGELOG.md` as it stood when the per-PR changelog
    obligation was retired
    ([sales.demos-docs#18](https://github.com/ericcames/sales.demos-docs/issues/18)).
    Nothing is appended to it again.

    **Bare issue numbers refer to `ericcames/sales.demos-docs`.** They do not
    autolink on this site — read `(#14)` as
    `https://github.com/ericcames/sales.demos-docs/issues/14`. References to
    `sales.demos` are written out in full.

    Entries are verbatim and newest first. For anything after 2026-09-10, see
    [where things live now](README.md).

### Fixed -- Phase 3 of the edge run sheet was not runnable (sales.demos#424)

- **`playbooks/setup_edge.yml` does not exist**, and the run sheet gave it as the
  first command of Phase 3. A presenter following the page on the NUC got "the
  playbook could not be found" before doing anything. It is
  [sales.demos#406](https://github.com/ericcames/sales.demos/issues/406), blocked
  on [#395](https://github.com/ericcames/sales.demos/issues/395)
  (`install_aap.yml`), so it is not imminent.
- **Replaced with the four playbooks that do exist**, in order, which is what the
  page's own stage table already listed: `install_lvms.yml`, then AAP by hand,
  then `install_cnv.yml`, `install_compliance.yml`, `prepare_env.yml`. Nothing
  invented -- these are the same playbooks #406 will chain. A note says the
  wrapper is coming and links both issues.
- **The manual AAP step could not have worked as written either.** Step 2 said
  *"`install_aap.yml` prints the operator-generated admin password"* -- a
  playbook that does not exist cannot print anything, and the CR path produces no
  such output. The password is in a secret; the command is now given, with the
  name and key **read off the live edge cluster** rather than assumed:

    ```bash
    oc get secret aap-admin-password -n aap -o jsonpath='{.data.password}' | base64 -d
    ```

- **Both `ansible-playbook ... | tee` pipelines are gone**, replaced with
  `ANSIBLE_LOG_PATH` under `~/ansible-logs/`. `sales.demos`' README has said why
  since Phase 0: in a pipeline the exit status comes from `tee`, so a failed run
  reports success -- and it caused a real misread. The run sheet was teaching the
  opposite. The two `sudo tee` uses for writing dnsmasq config are untouched;
  they are not pipelines.
- `edge-sno/README.md` and `architecture.md` also described `setup_edge.yml` as
  a thing you run. Both now describe it as proposed, pointing at #406.

**Not drift.** These were wrong identically in both copies of the docs before the
repo split, which is why they survived the #12 reconciliation -- that pass
compared the two copies against each other, and agreeing copies look correct.

### Fixed -- the edge run sheet launched a job template the automation deletes (#1)

- **`edge-sno/run-sheet.md` told a presenter to launch `Sales Demos - Build Demo
  VM`**, in the Phase 3 steps and again in the verification checklist. That name
  carries `state: absent` in `controller_workflows.yml` -- `config.yml` actively
  *removes* it. Now `Linux Day 1 - 0 Workflow`, with a note that workflows are
  shared config, so `config.yml` creates it on `edge` too.
- **#13 missed this**, and the reason is worth recording: that PR resolved the
  drifted files by taking whichever copy was newer per directory, and `edge-sno/`
  was taken from here wholesale because it is two to three times longer than the
  stub in `sales.demos`. Longer was the right call and is not the same as
  current -- the OCP Virt pages got their retired template names corrected in the
  same PR only because *those* came across from `sales.demos`.
- **Swept the whole class rather than the two lines.** All 15 `state: absent`
  objects checked against every page: the only remaining hits are the two
  screenshot caveats in `openshift-virtualization/`, which say the *image* shows
  the old title and to retake it from `Linux Day 1 - 0 Workflow`. Those are
  correct and stay.

### Fixed -- a command that cannot run where the document sits (#9)

- `openshift-virtualization/README.md` gave `python3 utilities/render-demo-assets.py`
  as if it were runnable from this repo. It lives in `sales.demos` -- it reads
  templates from the `linux_configure` role -- and this repo's `utilities/` holds
  only `check-no-secrets.sh`.
- Now says so, links to the script, and shows it run from a sibling checkout
  including the `--no-png` form. The `--out` flag added in sales.demos#422 means
  the PNG lands back in this repo.
- The eight broken `../../../` links this issue was opened for were fixed in #13;
  this was the remaining half. Verified: **0 broken relative links** across
  `docs/`.

### Fixed -- sizing tables described tiers as they were before they were resized (#14)

- **`large` was documented as 2 vCPU / 6 GiB. It is 4 / 16.** `small` is 2 / 4
  and `medium` is 2 / 8, per `terraform/ocpvirt/tiers.yaml`, since
  ericcames/sales.demos#348. A presenter reading the old tables told a customer
  the VM was under a third of its real size.
- **The old names survive as aliases, which is what made it read plausibly.**
  `tiers.yaml` still maps `large-2cpu-6gb` -> `large`, so nothing errored and
  nothing failed -- the label is a legacy key, and the docs read it as a
  description. Said explicitly now, in the architecture page and the plan, so
  the old numbers do not get "helpfully" restored.
- **The AAP surveys had already moved on**, offering plain `small` / `medium` /
  `large`, so the docs were also showing an interface the audience would not see.
  Presenter-facing pages now use the plain names, including the runnable
  `vm_size_tier=` in the edge run sheet.
- **`available_memory_gb` was given as 67. It is 63** -- it went to 67 in #118
  and back when Automation Orchestrator started drawing on the same budget
  (#141).
- **The plan is annotated, not rewritten.** `ocpvirt-demo-plan.md` records *why*
  the tiers are repo-owned and why `u1.large` did not fit a 14 GiB cluster; that
  reasoning still holds and is worth keeping. A superseded note above the table
  carries the current figures instead.
- **One occurrence deliberately left alone.** The `vm_size_tier` in
  `talk-track.md`'s `facts.json` sits inside a `<!-- rendered: facts.json -->`
  block that CI verifies against `render-demo-assets.py`. It is an explicitly
  representative fixture, not a claim about tier sizes, and changing it means a
  paired PR in `sales.demos` -- real cross-repo cost for a sample value.

### Fixed -- this page said `edge` had no badged logo (#14)

- True when `docs/reference/environments.md` was written, and false four commits
  later: ericcames/sales.demos#426 added the purple one along with
  `inventory/group_vars/edge/gateway_settings.yml`.
- Replaced with a three-row colour table -- green `sandbox`, red `demo`, purple
  `edge` -- and a note on what must move together when a fourth environment
  appears: a colour in `env_colors.py`, a generated pair in
  `assets/aap-branding/`, and a `gateway_settings.yml`. `check-env-logos.py`
  catches the last two; nothing catches a missing colour.

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
