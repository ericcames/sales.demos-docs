# Demo: Policy as Code

**Start here.** A customer watches AAP refuse to start a job — a password
typed into extra vars, a change outside the weekend window, a change with no
ticket — each time with a readable reason, and then watches the same job run
once the rule is satisfied. About 15 minutes of screen time.

| | |
|---|---|
| **Length** | 20 minutes (16 + 4 for questions), plus an optional 5-minute Act 2 |
| **Audience** | Automation leads and change governance, platform engineers, security and compliance — one arc, with the beat to lean on named per room |
| **Reader** | The Ansible pre-sales engineer presenting it |
| **Needs a live environment?** | **Yes** — AAP 2.7 with the OPA server deployed; Act 2 also needs the evidence store and dashboard. Only the dashboard is rendered offline |
| **Status** | **Draft** — every beat proven through the AAP API; the UI launch prompts are not yet rehearsed ([#841](https://github.com/ericcames/sales.demos/issues/841)) |

---

## The four documents

| File | Read it when |
|---|---|
| [`run-sheet.md`](run-sheet.md) | **While presenting.** Minute markers, what is on screen, exact commands, recovery moves |
| [`talk-track.md`](talk-track.md) | **While rehearsing.** The narrative and the actual words, beat by beat |
| [`architecture.md`](architecture.md) | **When asked "how does that work".** The moving parts, the timing table |
| [`objections.md`](objections.md) | **Before you go in.** What this audience asks, answered from the code |

Present from the run sheet. Rehearse from the talk track. The other two are
reference.

---

## The 60-second version

1. Before any guarded job starts, AAP asks an Open Policy Agent server *"may
   this job run?"* and sends it the job's details.
2. **Hello** is blocked when launched with `db_password` in its extra vars,
   and runs without it.
3. **Canary** is always blocked — if it ever runs, enforcement is off.
4. **Change Window** is blocked on weekdays, and runs when launched with the
   `break-glass` label, which stays on the job.
5. **Change Ticket** is blocked without a `change-ticket:CHG<7 digits>` label,
   and runs with one, which stays on the job.
6. OPA logs every decision with what it was asked — extra-var values redacted.

**Act 2, optional (+5 min): prove the state.**

7. Every Day 1 compliance scan writes a dated result and every rule's outcome
   to an evidence store.
8. A dashboard anyone can open with a plain link shows the latest score per
   machine, what's failing now (with each rule's title and severity), and
   the scan history. Of the six RHEL failures, five are documented
   image-factory exceptions and one is the web server the machine exists to
   run.
9. The Windows break/fix workflow shows in the trend as 100% → 96% → 100%:
   a control broken, caught by the next scan, fixed and re-proven.

![The compliance dashboard](../../images/policy-compliance-dashboard.png)

**What the demo is actually about** is moving rules out of documents and into
the platform: written once as code, tested and versioned, enforced *before*
the job starts, with the reason shown to the person who was stopped.

---

## Why it does not work without a cluster (yet)

Every Act 1 beat is an AAP job launch against a live OPA server, and none of
it is rendered offline. Act 2's dashboard is, as the image above, captured
from sandbox on 2026-10-08. The verbatim AAP messages in the talk track were captured on
sandbox, so the words can be rehearsed anywhere. Screenshots are listed as
outstanding in the [run sheet](run-sheet.md#screenshots-still-worth-capturing).

---

## If you want to run it live

1. `config.yml` for the environment — creates the four templates, the labels,
   `OPA_HOST`/`OPA_PORT`, and the `policy-demo` user.
2. [`/sales-demos-policy`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-policy/SKILL.md)
   — deploys OPA, attaches each rule to its template, and asserts every answer
   in this demo against OPA before you rely on it. From AAP:
   `AAP Ecosystem - Install Policy Server`.
3. Launch **Policy as Code - Canary** once. It must be blocked.
4. **For Act 2:** `AAP Ecosystem - Install Policy Evidence Store`, then
   `AAP Ecosystem - Install Policy Compliance Dashboard`, then run a Day 1
   compliance scan so there is something to show.

---

## What comes next: Compliance as Code (built, not yet demoable)

Policy as Code answers *"may this job run?"*. Compliance as Code (AAC)
answers *"how compliant is this host?"* with the assessment half of the same
policy library, on the same cluster, writing to the same `policy-db`. Most
of it is built and running on sandbox (measured 2026-10-10), but it **cannot
be shown end to end yet**. Until it can, it has no run sheet of its own.

| Piece | What exists | Installed by |
|---|---|---|
| Assessment OPA | One pod behind `opa-security`, `opa-compliance`, `opa-ot`, serving the same pinned `rego_policy_libraries` release | `AAP Ecosystem - Install Compliance Assessment Servers` |
| Routing OPA | `opa-routing`, which decides the route inside the AAC Automation Orchestrator workflows | `AAP Ecosystem - Install Compliance Routing Server` |
| Evidence database | A second database, `aac`, in `policy-db`, beside the Act 2 evidence | `AAP Ecosystem - Install Compliance Evidence Database` |
| AAP content | Ten `Compliance as Code -` templates and the `Golden Image Enforcement` workflow, run from an `AAC` project pinned to a tag of [`ynotbhatc/aac-pack`](https://github.com/ynotbhatc/aac-pack) | `config.yml` |
| Automation Orchestrator | Three `Compliance as Code - … (as code)` workflows: Golden Image, GPU Cross-Domain Flex, Tanium Comparison | `ao_workflows.yml` |

**What blocks it:** several pack playbooks query tables that nothing creates
yet, and the Golden Image family targets a container rather than this
platform's VMs ([sales.demos#883](https://github.com/ericcames/sales.demos/issues/883)).
Until that is fixed, the templates and workflows can be opened and shown,
but not run. Collecting and assessing the demo VMs themselves (the fact
shaper) is not built yet.

**For this demo:** the `compliance` label now covers both halves
([sales.demos#893](https://github.com/ericcames/sales.demos/issues/893)), so
the Templates page needs a name search to show only the four
`Policy as Code -` templates. Nothing in Act 1 or Act 2 changed. The policy
library is still pinned at `v2.0.0`. `v2.1.0` is released and leaves
`enforcement/aap` unchanged, but nothing here has adopted it yet.

Phase status: [`ROADMAP.md` → Compliance as Code](https://github.com/ericcames/sales.demos/blob/main/ROADMAP.md#compliance-as-code--aac-on-this-platform).

---

## Related

- [sales.demos#841](https://github.com/ericcames/sales.demos/issues/841) — the build, every measurement, and what is still open
- [`ynotbhatc/rego_policy_libraries`](https://github.com/ynotbhatc/rego_policy_libraries) — the policies (Apache-2.0)
- [`ynotbhatc/aac-pack`](https://github.com/ynotbhatc/aac-pack) — the Compliance as Code playbooks, routing policies, AO workflows and evidence schema, published from the AAC product and pinned by tag (`aac_pack_version`, MIT)
- [`ROADMAP.md`](https://github.com/ericcames/sales.demos/blob/main/ROADMAP.md) — what is done and what is not
