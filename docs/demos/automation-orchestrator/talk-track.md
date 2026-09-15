# Talk track — Automation Orchestrator

**Rehearse from this. Present from [`run-sheet.md`](run-sheet.md).**

The key screens from the rehearsal on sandbox (2026-09-15) are embedded below,
so the whole track can be read with no cluster.

---

## Who is in the room

**You are the pre-sales engineer.** Every document in this folder is written to
you.

**They are platform engineers and automation leads** — people who already run
AAP and are evaluating what Automation Orchestrator adds to their stack. They
have built workflows in AAP's controller. They have opinions about approval
gates, and most of those opinions were formed by watching a Slack-based process
fail silently at 2 AM.

| They do not care about | They care intensely about |
|---|---|
| Another product to install | Whether this changes how they work day to day |
| Marketing claims about "agentic" | Whether their existing templates survive the transition |
| Feature checklists | Who approves what, and whether the audit trail is real |

**Do not lead with "AI" or "agentic."** This audience has heard those words used
loosely. Lead with what they can see: a canvas, their templates, an approval
that blocks until a human says yes.

**Do not disparage AAP's built-in workflows.** Many in the room use them daily
and they work. The reframe is: AAP workflows chain on success/failure; AO adds
branches and gates.

**The interactive demo on redhat.com shows EDA triggers and LLM analysis.** This
demo does not have those wired up. Say so before they ask — beat 5 exists for
exactly this.

---

## Beat 1 · The login

Show the AO login page. Click "Log in with Ansible Automation Platform". AAP's
sign-in page appears — same credentials, same environment badge. Land back in
AO, logged in.

> **"Same credentials you already use. AO authenticates through AAP's gateway —
> it is not a separate identity store."**

**Why this beat exists.** It defuses the "another system to manage" objection
before it forms. The audience sees their own login page appear inside a product
they have never opened, and the implication lands without you spelling it out:
this thing knows about the AAP they already run.

**Transition:** *"Let me show you what it sees."*

---

## Beat 2 · The integration

Navigate to Integrations. Show the AAP integration, then open an AAP step's
template picker — the 36 job templates AO discovered from AAP.

> **"These are your existing AAP templates — nothing was migrated, nothing was
> duplicated. AO connected to AAP and discovered them."**

Let them scan the list. If they ask about a specific template, answer from the
list — the names match the AAP UI exactly.

**Why this beat exists.** It proves zero migration cost. The audience needs to
believe their investment is preserved before they will listen to what is new. A
platform engineer who thinks "we would have to rebuild everything" has already
decided, and nothing after this will change it.

**Transition:** *"Now let me build something with them."*

---

## Beat 3 · The canvas

Build a workflow live on the AO canvas. This is the centerpiece — everything
before sets it up, everything after lands it.

### Preferred story: Windows Day 2 compliance

Use this when demo VMs are running. The compliance break/fix is short, safe
mid-demo, and shows logic nodes and human oversight together.

1. `scan` — **Windows Day 2 - Compliance Scan**
2. `compliance_check` — a condition on the scan's result: did any CIS control
   fail?
3. On the **True** branch: `security_approval` — a named approver must say yes
4. On **Approved**: `fix` — **Windows Day 2 - Fix Compliance**
5. `rescan` — **Windows Day 2 - Compliance Scan** again, to prove the fix

Run `Windows Day 2 - Break Compliance` beforehand to set up the failure.

![The rehearsed workflow on the AO canvas](../../images/ao-canvas-complete.png)

**The condition reads the scan's own result.** The scan publishes
`windows_compliance` — pass, fail, score, compliant — as AAP job artifacts, and
AO hands those to the next step. Nothing is parsed out of log text.

### Fallback story: Linux Day 1 chain

Use this when no VMs exist yet — building the workflow also provisions one. Not
rehearsed.

1. `Linux Day 1 - 1 Provision`
2. `Linux Day 1 - 2 Register`
3. Add an approval node ("Ops team approves before configuring")
4. `Linux Day 1 - 3 Configure`
5. `Linux Day 1 - 4 Compliance Scan`

### The line that lands it

> **"Three things AAP workflows cannot express: a branch based on a result, a
> gate that waits for a human, and both in the same sequence."**

Do not rush this sentence. It is the argument. The canvas is the evidence.

**Why this beat exists.** This is the demo. The audience watches you build — not
show a pre-built artifact — a workflow that does something they recognize
(compliance, provisioning) using templates they just saw are theirs, with
constructs their current platform does not have.

**Transition:** *"Let me run it."*

---

## Beat 4 · The execution

Run the workflow. Show the execution view — the scan finishing, the condition
taking the True branch, the approval waiting.

When the approval node is reached, pause. Let them see the workflow blocked:
the header reads **Paused** and **Pending approval**, and the message already
carries the scan's numbers — *"1 failed control(s), score 96%"*.

![The workflow paused at the approval gate](../../images/ao-execution-approval-waiting.png)

Then approve it with a note. Show the audit trail — who approved, when, which
execution, and why.

![The approval record](../../images/ao-approval-record.png)

> **"That approval is not a Slack message someone might miss. It is a gate in
> the workflow engine. The job does not run until the gate opens, and the gate
> records who opened it."**

After the approval, the fix and the re-scan take under a minute together; the
re-scan comes back 28 of 28 controls passing. The whole run is under three
minutes, and all but about 76 seconds of it is the time you spend talking at
the gate.

**Why this beat exists.** Approval is the feature that justifies AO for
regulated environments. A compliance officer who hears "we track approvals in
Slack" and one who hears "the workflow engine enforces the gate and logs it" are
having two different conversations about audit readiness.

---

## Beat 5 · The honest bits

> **"Two things this demo does not show, and I want to be straight about
> them."**

> **"First — the interactive demo on redhat.com shows EDA triggers and
> LLM-based analysis. Those integrations exist in the product but are not wired
> up in this environment. We can talk about what that would look like for your
> use case."**

> **"Second — the AO MCP server, the thing that lets an AI assistant query this
> system, is read-only today. You can inspect workflows and executions but not
> create them programmatically."**

**Why this beat exists.** These are the questions someone will discover in
evaluation. Volunteering them first — before anyone asks — is worth more than
the features you just showed. A sysadmin who has sat through demos where the
hard parts were skipped will trust the working parts more once you have been
straight about the broken ones.

---

## Beat 6 · Close

> **"You saw your templates — the ones you have today — orchestrated with
> branches and approvals, running on a workflow engine that survives a pod
> restart. The question is: what sequence in your environment would benefit from
> a gate that is not a Slack message?"**

One question, chosen to fit what you heard earlier:

- If they asked about compliance: *"Which of your compliance workflows today
  depend on someone remembering to check the result?"*
- If they asked about approvals: *"Who in your organization would need to
  approve a production change, and how do they do it today?"*

Pick one. A presenter who offers three questions gets no answer to any of them.

---

## If you only get ten minutes

Keep beats 1, 3, and 5. The login proves integration. The canvas proves value.
The honest bits prove trust.

Skip the execution — describe it: *"If I ran this, the approval node would
block until a named human approves it, and the audit trail would record who and
when."* That is credible because they just watched you build the workflow with
the approval node in it.

---

## Where the words come from

| Claim | Source |
|---|---|
| AO is GA, version 2026.8 | [Release notes](https://docs.redhat.com/en/documentation/automation_orchestrator/2026.8/whats_new-automation_orchestrator_release_notes) |
| Add-on to AAP 2.7 or later | [GA blog](https://www.redhat.com/en/blog/unify-it-workflows-scale-new-automation-orchestrator-ansible-automation-platform), Justin Braun, 2026-08-21 |
| 36 job templates visible through integration | Measured on sandbox via `ao-sandbox` MCP `proxies_aap_job_templates`, 2026-09-15 |
| Same credentials via SSO | [`playbooks/configure_ao.yml`](https://github.com/ericcames/sales.demos/blob/main/playbooks/configure_ao.yml) — OIDC identity provider setup |
| The scan publishes `windows_compliance` as job artifacts | [sales.demos#613](https://github.com/ericcames/sales.demos/issues/613) — both `compliant: true` and `compliant: false` verified from AAP |
| AO passes AAP job artifacts to later steps | [Use job output in a downstream step](https://docs.redhat.com/en/documentation/automation_orchestrator/2026.8/develop-use_job_output_in_a_downstream_step); measured on sandbox, 2026-09-15 ([#470](https://github.com/ericcames/sales.demos/issues/470#issuecomment-5674156533)) |
| Condition branches, one branch per run | [Add a conditional step](https://docs.redhat.com/en/documentation/automation_orchestrator/2026.8/develop-add_a_conditional_step_to_a_workflow) |
| Approval message carried "1 failed control(s), score 96%"; the record holds decision, approver, time and note | `ao-sandbox` MCP `approvals_list`, measured on sandbox, 2026-09-15 ([#470](https://github.com/ericcames/sales.demos/issues/470#issuecomment-5674156533)) |
| Whole run 2 m 48 s, about 76 s of automation; re-scan 28 of 28 | Execution `76e8be52`, AAP jobs 93–95, measured on sandbox, 2026-09-15 ([#470](https://github.com/ericcames/sales.demos/issues/470#issuecomment-5674156533)) |
| 1.91 vCPU / 2.47 GiB footprint | Measured in [#141](https://github.com/ericcames/sales.demos/issues/141), before/after `probe_env.yml` |
| Three databases required (not two) | [`playbooks/install_ao.yml`](https://github.com/ericcames/sales.demos/blob/main/playbooks/install_ao.yml) header comment |
| The May press release said tech preview | [Summit press release](https://www.redhat.com/en/about/press-releases/red-hat-establishes-ansible-automation-platform-trusted-execution-layer-it-operations-agentic-era), 2026-05-12 |
| MCP server is read-only | [`utilities/ao-mcp-server.py`](https://github.com/ericcames/sales.demos/blob/main/utilities/ao-mcp-server.py) — 32 tools, no create/update/delete |
| No branding on AO login page | [#426](https://github.com/ericcames/sales.demos/issues/426), `AutomationOrchestrator` CR spec has no branding fields |
| Interactive demo shows EDA + LLM | [Interactive demo](https://www.redhat.com/en/interactive-demo/automation-orchestrator) — CVE remediation with EDA trigger and AI analysis |
| AO API docs at the instance | `https://<ao-host>/api_docs/v1/docs` (Swagger), confirmed 2026-09-11 |
