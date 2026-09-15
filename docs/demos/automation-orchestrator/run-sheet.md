# Run sheet — Automation Orchestrator

**This is the page you hold while presenting.** The narrative behind each beat,
with the actual words, is in [`talk-track.md`](talk-track.md) — rehearse from
that, present from this.

| | |
|---|---|
| **Length** | 20 minutes (15 + 5 for questions) |
| **Audience** | Platform engineers and automation leads |
| **Needs an environment?** | **Yes** — the compelling beats are live workflow builds on the canvas |
| **Assets** | AO login page, AAP sign-in page, AO canvas, AO execution view, AO approval record |
| **Rehearsed** | End to end on sandbox (`cluster-v9n68`), 2026-09-15 — [evidence](https://github.com/ericcames/sales.demos/issues/470#issuecomment-5674156533) |

---

## Before you start (10 minutes)

1. Open these in tabs:
   1. AO: `https://ao-automation-orchestrator.apps.<cluster>.dyn.redhatworkshops.io/`
   2. AAP: `https://aap-aap.apps.<cluster>.dyn.redhatworkshops.io/`
   3. This run sheet
2. Verify AO is reachable — the login page should render.
3. Verify the integration sees templates: from a Claude Code session with
   `ao-sandbox`, call `proxies_aap_job_templates` — expect **36** templates
   (the 33 this repo defines plus 3 the RHDP catalog item pre-installs).
4. Decide whether to run the **Windows Day 2** story (needs a running Windows
   VM) or the **Linux Day 1** fallback. Check the VMs:
   `openshift-sandbox` → `resources_list` (VirtualMachine, namespace
   `sales-demos-<env>`).
5. **Break the guest so the workflow has something to fix.** Launch
   `Windows Day 2 - Break Compliance` from AAP (limit `windemo`, about 7 s). A
   `Windows Day 2 - Compliance Scan` afterwards should report
   `fail: 1`, `compliant: false`.
6. **Check the two known configuration gaps** before you are on stage — both
   make the build or the run fail in front of the audience:
   1. The ConfigMap `ao-admin-settings` exists in namespace
      `automation-orchestrator` and `ao-worker` has
      `APP_INTEGRATION_URL_ALLOWED_HOSTS` set
      ([sales.demos#621](https://github.com/ericcames/sales.demos/issues/621)).
   2. An AAP step's **Organization** dropdown loads. If it errors, create a
      Basic Auth credential for the step
      ([sales.demos#622](https://github.com/ericcames/sales.demos/issues/622)).
7. **Build the workflow once, privately, and keep it.** It stays in AO's
   database for the life of the environment and is your fallback if the live
   build goes wrong. Nothing commits it as code yet
   ([sales.demos#474](https://github.com/ericcames/sales.demos/issues/474)).
8. Decide your close before you begin — see **Landing it** at the bottom.

---

## The arc

| Time | Beat | On screen |
|---|---|---|
| 0–2 | Login through AAP SSO | AO login → AAP sign-in → AO dashboard |
| 2–4 | Show the integration | AO Integrations page, template list |
| 4–10 | Build the workflow on the canvas | AO workflow builder |
| 10–14 | Run the workflow | AO execution view, approval gate, approval record |
| 14–17 | The honest bits | (conversation, no screen) |
| 17–20 | Close | AO dashboard |

---

## 0–2 · Login through AAP SSO

![AO login page — SSO button, SANDBOX badge at the top](../../images/ao-login-page.png)

**Show the AO login page.** Point at "Log in with Ansible Automation Platform".

Click it. The redirect lands on the AAP sign-in page — point at the
environment badge.

![AAP login page — SANDBOX badge and prelogin warning](../../images/aap-login-page-sandbox.png)

Log in with the AAP admin credentials. Land in AO — the green SANDBOX badge
persists in the AO masthead after login.

> **"Same credentials. One identity store. Automation Orchestrator delegates
> authentication to the AAP gateway — no separate user database."**

---

## 2–4 · Show the integration

Navigate to **Configuration → Integrations**. One row: Ansible Automation
Platform, Enabled.

![AO Integrations page — AAP connected and enabled](../../images/ao-integrations.png)

**Status reads `Unknown` and Enabled resources reads `0`.** That is expected on
this build — the integration still lists every template. Do not stop to
explain it unless someone asks.

Click the AAP integration. Point at three things:

- State: Enabled
- URL: the AAP gateway hostname
- Connection credential: AAP Admin

![AO integration detail — AAP URL, credential, scope](../../images/ao-integration-detail.png)

> **"These are your existing job templates. Nothing was migrated, nothing was
> copied. AO sees them through the integration and can use them as workflow
> steps."**

---

## 4–10 · Build the workflow on the canvas

Click **Create Workflow**. The canvas opens with trigger options on the right.

![AO workflow builder — empty canvas with trigger options](../../images/ao-workflow-builder.png)

Pick **Manual trigger**. Name the workflow `Windows Day 2 - Compliance
Remediation` and set **Project** to `default`.

### Preferred story: Windows Day 2 compliance (if VMs are running)

Add every step with the **⊞ on the output of the step before it**, not the
**Add step** button at the top — that one adds a step connected to nothing.

1. **`scan`** — ⊞ on the trigger → **AAP Execution**.
   Organization `IT Service Automation`, job template
   **Windows Day 2 - Compliance Scan**, limit `windemo`. Rename the step from
   "Launch AAP job template" to `scan`.

   ![AO AAP step — organization and the template picker listing AAP's job templates](../../images/ao-job-templates.png)

2. **`compliance_check`** — ⊞ on `scan` → **Logic → Condition**. Choose
   **Custom expression**. In the Input panel, click the copy icon on **scan →
   artifacts**, paste, and finish it as:

   ```
   ${activity_<id>.artifacts.windows_compliance.fail} > 0
   ```

   **Insert the reference with the copy icon; never type it.** AO references a
   step by its internal `activity_…` ID, not its name, and compare a number —
   `== false` fails at run time.

   ![AO condition step — the expression, the scan step's real output, evaluated_result true](../../images/ao-condition-node.png)

3. **`security_approval`** — ⊞ on **True** → **Approval**. Approver users: your
   own SSO user. Message:
   `Security lead: approve remediation of CIS 2.3.6.6 (RequireStrongKey) on web-win-1.`
4. **`fix`** — ⊞ on **Approved** → **AAP Execution**,
   **Windows Day 2 - Fix Compliance**, same organization and limit.
5. **`rescan`** — ⊞ on `fix` → **AAP Execution**,
   **Windows Day 2 - Compliance Scan** again.
6. Leave **False** and **Rejected** unconnected, then **Save**. The yellow ⚠ on
   those two outputs is expected.

![AO canvas — trigger, scan, compliance_check, security_approval, fix, rescan](../../images/ao-canvas-complete.png)

> **"Three things you cannot express in an AAP workflow: a conditional branch,
> a human gate, and both in the same sequence. That is what you are looking at."**

### Fallback story: Linux Day 1 (if no Windows VM)

**Not rehearsed.** The Windows story is the one with measured timings.

1. Add: **Linux Day 1 - 1 Provision**
2. Connect: **Linux Day 1 - 2 Register**
3. Add an **approval node** — "Ops team approves configuration"
4. Connect: **Linux Day 1 - 3 Configure**
5. Connect: **Linux Day 1 - 4 Compliance Scan**
6. Save the workflow

> **"Provision and register happen automatically. Configuration waits for a
> person. The scan proves it worked. That is one workflow, not four tickets."**

---

## 10–14 · Run the workflow

Click **Run** → **Run now**. Point at each node as it progresses:

- `scan` dispatches to AAP — about **32 s**
- `compliance_check` takes the **True** branch immediately
- `security_approval` **waits**: the header shows **Paused** and
  **Pending approval**

![AO execution — scan and compliance_check done, security_approval pending, fix not started](../../images/ao-execution-approval-waiting.png)

> **"This is blocking. The job will not proceed until someone with the right
> permissions approves it. That is not a notification — it is a gate."**

Click **Review approval**. Point at the message — the failed-control count and
score came from the scan. Click **Approve**, type a note, then click **Submit
decision**. **Approve alone does nothing** until you submit.

![AO review approval — Approved selected, a decision note, the message with the scan's numbers](../../images/ao-approval-decision.png)

`fix` runs (about **11 s**), then `rescan` (about **32 s**). The run ends
**Completed**.

![AO execution — every step green, Completed in 2 m 48 s](../../images/ao-execution-complete.png)

Open **Details → security_approval**. Show the audit entry: decision, who
decided, when, and the note.

![AO approval record — Approved by the SSO user, decision time, decision notes](../../images/ao-approval-record.png)

The **Overview** tab lists every step with its duration and a **View job in
AAP** link on each AAP step — click through to show the same job in AAP.

![AO run details — six steps with start, end and duration](../../images/ao-execution-timeline.png)

In AAP, the same run is three ordinary jobs — 93, 94 and 95 — in the Jobs list
next to everything else AAP runs.

![AAP Jobs — the workflow's scan, fix and rescan jobs (93–95) beside the rehearsal's setup jobs](../../images/aap-jobs-from-ao.png)

---

## 14–17 · The honest bits

No screen needed. Step away from the keyboard for this beat.

Two points, volunteered:

1. **The redhat.com interactive demo shows EDA triggers and LLM analysis** —
   those are not wired up here. This demo shows the canvas and the gate, which
   are the parts that are GA and running.
2. **The MCP server is read-only** — it queries AO, it does not create or run
   workflows. The governance model for AI-initiated workflows is a separate
   conversation.

> **"I show you the gaps because every one of them has an issue number. The
> things I showed you working are the things that are working."**

---

## 17–20 · Landing it

> **"Your templates, your credentials, your RBAC. The orchestration adds
> conditional branches and human gates — the two things that turn a chain of
> jobs into a governed process."**

Then ONE question. Pick based on what they asked during the demo:

- If they asked about compliance: *"Which of your remediation sequences needs
  a gate that is not a Slack message?"*
- If they asked about multi-team handoffs: *"Where does work stop today
  because someone has to approve something and there is no governed way to do
  it?"*
- If they asked about the canvas: *"What is the first workflow you would build
  on this?"*

---

## Running it live

Every beat in this run sheet is already live — there is no offline version of
this demo. The canvas build is the demo.

| Beat | What to verify first |
|---|---|
| Login | AO login page loads; "Log in with Ansible Automation Platform" button is present |
| Integration | `proxies_aap_job_templates` returns 36 templates |
| Canvas | An AAP step's Organization dropdown loads ([#622](https://github.com/ericcames/sales.demos/issues/622)) |
| Execution | A Windows VM is running and `Windows Day 2 - Break Compliance` has run |

### Budget for job execution time

Measured on sandbox, 2026-09-15, execution `76e8be52`:

| Step | AO step | AAP job runtime |
|---|---|---|
| `scan` — Windows Day 2 - Compliance Scan | 32 s | 26.9 s |
| `compliance_check` | 0 s | — |
| `security_approval` | as long as you talk (1 m 31 s in rehearsal) | — |
| `fix` — Windows Day 2 - Fix Compliance | 11 s | 6.6 s |
| `rescan` — Windows Day 2 - Compliance Scan | 32 s | 27.1 s |
| **Whole run** | **2 m 48 s**, of which about **76 s** is automation | |

Each AAP step costs about 5 s more than the job itself — AAP starting the job
pod, then AO noticing the job finished.

**Keep a fallback.** If AO stalls during the live build, open the workflow you
built privately before the session. If the run stalls, describe the workflow
verbally and show the integration page as evidence. Do not debug in front of
the customer.

### Recovery moves

| Symptom | Move |
|---|---|
| AO login page returns 502 | The Route or backend pod is down. Describe the demo verbally and show AAP directly |
| OIDC redirect fails | Click "Sign in using local account" — use `admin` / the AAP admin password. Unlikely since `APP_OIDC_ALLOW_PRIVATE_NETWORKS` was set (#492) |
| Integration shows 0 templates | Re-run `AAP Ecosystem - Configure Automation Orchestrator` from AAP, wait 60 seconds |
| AAP step's Organization dropdown: "AAP Authentication Failed" | The credential `configure_ao.yml` created does not authenticate ([#622](https://github.com/ericcames/sales.demos/issues/622)). Click **Change** under the credential and use a Basic Auth credential with the AAP admin user |
| Save shows "references unknown activity or scope" | A reference was typed by step name. Re-insert it with the copy icon in the Input panel — AO references steps by ID |
| Save shows "Saved with N issues" | The build can be saved unfinished. Expand the banner — issues on an unconnected output are expected |
| Run fails in under a second: "base_url is not permitted by SSRF policy" | `ao-worker` cannot reach AAP ([#621](https://github.com/ericcames/sales.demos/issues/621)). Create ConfigMap `ao-admin-settings` with `APP_INTEGRATION_URL_ALLOWED_HOSTS` and restart `ao-worker` — about 30 s |
| Run fails at the condition: 'references "false"' | The expression used a boolean literal. Compare a number: `… .fail} > 0` |
| The approval looks stuck after Approve | Click **Submit decision** — Approve only selects the decision |
| A renamed step still shows "Launch AAP job template" | Re-open the step, set the name again, click outside the box, **Update** |
| Condition needs checking without a full run | Open the condition and click **Run step** — it re-runs the steps before it and shows `evaluated_result` |
| AO unreachable (503 or timeout) | Re-run `AAP Ecosystem - Deploy Automation Orchestrator` from AAP — it converges |
| AAP job fails inside the workflow | Open the job in AAP to see the error. The most common cause is a missing VM — provision first |
