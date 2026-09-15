# Troubleshooting — Automation Orchestrator

**Every error the #470 rehearsal hit**, with the exact text AO showed, the
cause, the fix, and the issue. The [run sheet](run-sheet.md)'s recovery table is
the one-line version of this page, for use on stage.

Measured on sandbox, 2026-09-15 —
[evidence](https://github.com/ericcames/sales.demos/issues/470#issuecomment-5674156533).

---

## Check first

Most of what follows can no longer surprise you if you rehearse first.
[`/sales-demos-orchestrator-rehearse`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-orchestrator-rehearse/SKILL.md)
(or AAP: `AAP Ecosystem - Rehearse Automation Orchestrator Demo`) asks the
component that failed each time, not the one that looked fine:

| Check | How | Catches |
|---|---|---|
| `ao-worker` allows AAP through the SSRF check | `printenv` inside the pod | [SSRF policy](#base_url-is-not-permitted-by-ssrf-policy) |
| The workflow's credential works for the user running it | AO's organizations proxy with that credential | [AAP Authentication Failed](#aap-authentication-failed) |
| The workflow exists | By name | — |
| The Windows guest is running | The VirtualMachine's status | [AAP job fails](#an-aap-step-fails-inside-the-workflow) |
| `windemo` holds exactly one host | AAP's API | [AAP job fails](#an-aap-step-fails-inside-the-workflow) |

**Before rehearsal every one of these looked fine** — SSO worked, the
integration was Enabled, AO listed 36 templates — while three were broken.

---

## Setting up

### `base_url is not permitted by SSRF policy`

- **Where:** the first AAP step of a run, which fails in under a second with no
  AAP job launched (execution `7a4723b0`, 0.6 s).
- **Cause:** AO blocks integration URLs that resolve to private addresses, and
  AAP's hostname does from inside the cluster. **Browsing templates happens in
  `ao-backend`; running a step happens in `ao-worker`.** Configure used to allow
  AAP on `ao-backend` only, so the builder worked and every run failed.
- **Fix:** re-run
  [`/sales-demos-orchestrator-config`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-orchestrator-config/SKILL.md)
  or `AAP Ecosystem - Configure Automation Orchestrator`. It writes
  `APP_INTEGRATION_URL_ALLOWED_HOSTS` to the ConfigMap `ao-admin-settings`,
  which both Deployments load, restarts the pods and checks the value inside
  `ao-worker`. About 30 s for the pods to return.
- **Issue:** [sales.demos#621](https://github.com/ericcames/sales.demos/issues/621)

### `AAP Authentication Failed`

- **Where:** an AAP step's **Organization** dropdown in the builder.
- **Cause:** **AO lets only a credential's creator browse AAP with it.**
  `configure_ao.yml` creates `AAP Admin` as the local AO `admin`; a presenter
  logged in through SSO is a different AO user. The credential itself is fine —
  the first theory, an empty token, was wrong, and the backend log showed the
  ownership check.
- **Runs are not affected.** A workflow run does not check credential ownership
  against the user who starts it, so a workflow using `AAP Admin` runs for
  anyone.
- **Fix:** as your SSO user, create a credential of your own once — AAP, Basic
  Auth, the AAP admin username and password — then click **Change** under the
  step's credential and pick it.
- **Issue:** [sales.demos#622](https://github.com/ericcames/sales.demos/issues/622)

### The integration shows Status `Unknown` and Enabled resources `0`

- **Where:** Configuration → Integrations.
- **Cause:** how this AO build reports an AAP integration.
- **Fix:** none needed. The integration still lists every job template — **36**
  on sandbox, the 33 sales.demos defines plus 3 from the RHDP catalog item. If
  it really lists none, re-run Configure and wait 60 s.

### Group approvers have no groups to pick

- **Where:** an Approval step's approver groups.
- **Cause:** the AAP identity provider has no team→group mapping, so only AO's
  built-in groups exist.
- **Fix:** name approver users instead.

---

## Building

### `references unknown activity or scope`

- **Where:** Save.
- **Cause:** a reference was typed by step name — `${scan.artifacts…}`. **AO
  references a step by its internal ID** (`activity_…`), whatever the AO docs'
  `${step_name.field}` examples suggest.
- **Fix:** delete the reference and insert it with the copy icon in the
  condition's Input panel. The committed workflow chooses readable IDs, so
  its condition reads `${activity_scan.artifacts.windows_compliance.fail} > 0`.

### "Saved with N issues"

- **Where:** Save.
- **Cause:** the build can be saved unfinished; the banner lists what is not.
- **Fix:** expand the banner. Issues on an intentionally unconnected output —
  **False** and **Rejected** in this demo — are expected.

### A renamed step still shows "Launch AAP job template"

- **Where:** a new AAP step.
- **Cause:** the first rename does not always stick.
- **Fix:** open the step again, set the name, click outside the box, **Update**.

### A step connected to nothing

- **Cause:** it was added with the **Add step** button at the top of the canvas.
- **Fix:** add steps with the ⊞ on the output of the step before, or drag an
  edge to it.

---

## Running

### The condition fails: `references "false"`

- **Where:** the condition step, after `scan` succeeded (execution `6df4f502`,
  after scan job 89).
- **Cause:** AO has no boolean literals. `… .compliant} == false` is read as a
  reference to a step named `false`.
- **Fix:** compare a number: `${activity_<id>.artifacts.windows_compliance.fail} > 0`.
- **To check a condition without a full run**, open it and click **Run step**.
  It re-runs the steps before it and shows `evaluated_result` (execution
  `47aa8132`, `mode: test`, AAP job 92).

### The run ends at the condition without asking for approval

- **Cause:** the guest is already compliant, `fail` is `0`, and **False** is
  unconnected.
- **Fix:** run `Windows Day 2 - Break Compliance` (limit `windemo`, about 7 s),
  or let `/sales-demos-orchestrator-rehearse` do it.

### An AAP step fails inside the workflow

- **Where:** the step shows failed with a **View job in AAP** link.
- **Cause:** read the job in AAP. The two seen here: no Windows VM, or a stale
  host left in `windemo` by a failed teardown, which makes every Windows job
  fail
  ([sales.demos#616](https://github.com/ericcames/sales.demos/issues/616)).
- **Fix:** build the VM with the Windows Day 1 - 0 Workflow, or delete the dead
  host in AAP.

### Retry run opened a new execution

- **Cause:** by design. **Retry run** starts a new execution and links it to the
  failed one (`retried_from_execution_id`), so both stay in the history.

---

## Approving

### The approval looks stuck after Approve

- **Cause:** **Approve** (or **Reject**) only selects the decision.
- **Fix:** click **Submit decision**. An unanswered approval waits a day by
  default.

### A run's history and approval record are gone

- **Cause:** **removing a workflow deletes its executions and approval
  records.** Measured on sandbox: its executions returned 404 afterwards.
- **Fix:** none after the fact. Screenshot the record, or run
  `/sales-demos-orchestrator-rehearse -e ao_rehearse_report_execution=<id>`,
  before removing a workflow. To refresh the committed workflow, re-run
  `/sales-demos-orchestrator-workflow` with the default `present` — that saves
  a new version and keeps history.

---

## AO itself

| Symptom | Fix |
|---|---|
| AO login page returns 502 | The Route or backend pod is down. Re-run `AAP Ecosystem - Deploy Automation Orchestrator` — it converges |
| AO unreachable (503 or timeout) | Same — re-run the Deploy workflow |
| OIDC redirect fails | **Sign in using local account**: `admin` and the AAP admin password. `APP_OIDC_ALLOW_PRIVATE_NETWORKS` should prevent it ([sales.demos#492](https://github.com/ericcames/sales.demos/issues/492)) |
