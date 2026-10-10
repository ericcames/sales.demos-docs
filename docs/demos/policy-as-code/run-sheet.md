# Run sheet — Policy as Code

**This is the page you hold while presenting.** The narrative behind each beat,
with the actual words, is in [`talk-track.md`](talk-track.md) — rehearse from
that, present from this.

| | |
|---|---|
| **Length** | 20 minutes (16 + 4 for questions), plus an optional **5-minute Act 2** |
| **Audience** | Automation leads and change governance, platform engineers, security and compliance — one arc, a different beat to lean on for each ([talk track](talk-track.md#who-is-in-the-room)) |
| **Needs an environment?** | **Yes** — AAP 2.7 with the OPA server deployed; for Act 2, the evidence store and dashboard too. Only the dashboard is rendered offline ([image](../../images/policy-compliance-dashboard.png)) |
| **Assets** | AAP Templates page, a blocked job's Details page, the OPA pod log; for Act 2, the compliance dashboard link |
| **Rehearsed** | Every beat proven **through the AAP API** on sandbox, 2026-10-02 (jobs 141, 164–166, 179–180 — [evidence](https://github.com/ericcames/sales.demos/issues/841)). **The UI launch prompts are not yet rehearsed** |

---

## Before you start (10 minutes)

1. **Deploy and prove it** —
   [`/sales-demos-policy`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-policy/SKILL.md),
   or `AAP Ecosystem - Install Policy Server` from AAP after `config.yml`.
   It asserts every answer below against OPA before you rely on it.
2. **Check the day in `policy_change_window_timezone`** (default
   `America/Phoenix`). **On a Saturday or Sunday there, the Change Window
   beat runs instead of blocking.** Set your own zone in `local.yml` if you
   present from elsewhere, and re-run `config.yml` and `install_opa.yml`.
3. **Launch the Canary once.** It must end **Error** with the canary message.
   If it *runs*, AAP is not reaching OPA — stop and fix before the room
   arrives (see Recovery moves).
4. Open these in tabs:
   1. AAP → **Templates**, filtered on label `compliance` (Policy and Compliance as Code share it, sales.demos#893)
   2. AAP → **Jobs**
   3. OPA pod log (OpenShift console → project `policy-as-code` → pod `opa-*` → Logs), or keep `oc logs -f deploy/opa -n policy-as-code | grep 'Decision Log'` ready
   4. This run sheet
5. Decide your close before you begin — see **Landing it**.
6. **Act 2 only:**
   1. Install the evidence store, then the dashboard: `AAP Ecosystem - Install
      Policy Evidence Store`, then `AAP Ecosystem - Install Policy Compliance
      Dashboard`. The second job prints the link.
   2. Make sure **at least one compliance scan has run since** (the Day 1
      workflows include one, or launch `Linux Day 1 - 4 Compliance Scan` /
      `Windows Day 1 - 4 Compliance Scan`). An empty dashboard is the most
      likely way Act 2 fails.
   3. Open the dashboard link in a **private window**. That's exactly what
      your audience will see, with no login.

---

## The arc

| Time | Beat | On screen |
|---|---|---|
| 0–2 | The question AAP now asks | Templates page, four `Policy as Code -` templates |
| 2–5 | A secret in extra vars | Launch **Hello** twice → blocked job's **Explanation** |
| 5–7 | The canary | Launch **Canary** → blocked |
| 7–11 | The change window, and break glass | Launch **Change Window** → blocked; again with `break-glass` → runs |
| 11–14 | The change ticket | Launch **Change Ticket** → blocked; again with a ticket → runs |
| 14–16 | What OPA saw | OPA decision log, values redacted |
| 16–18 | The honest bits | (conversation, no screen) |
| 18–20 | Close — or bridge to Act 2 | Templates page |
| *20–21* | *Act 2:* Every scan leaves evidence | Jobs page, last compliance scan |
| *21–24* | *Act 2:* The dashboard anyone can open | Dashboard link, no login |
| *24–25* | *Act 2:* The honest bits | (conversation) |

---

## 0–2 · The question AAP now asks

**Templates**, filtered on `compliance`, then search `Policy as Code`. Four
templates, nothing special about any of them in the UI. (The label alone also
lists the Compliance as Code and install templates, sales.demos#893.)

> **"Before any of these starts, AAP asks a policy server one question: may
> this job run? If the answer is no, it does not start — and it tells you
> why."**

---

## 2–5 · A secret in extra vars

**Policy as Code - Hello** → Launch. The prompt asks for variables.

1. Leave `greeting: hello` → Launch → **Successful**.
2. Launch again, add `db_password: not-a-real-one` → **Error**, before any
   pod starts. Open **Details** → **Explanation**:

```
This job cannot be executed due to a policy violation or error. See the following details:
{'Violations': {'Job template': ["extra_var 'db_password' looks like a secret "
                                 '— pass it through a credential or Ansible '
                                 'Vault, not extra_vars.']}}
```

> **"Same template, same person. The only difference is what was typed. That
> password would have sat in the job record for ever — now it never starts."**

Point at: status is **Error**, not Failed, and **no output** — it never ran.

---

## 5–7 · The canary

**Policy as Code - Canary** → Launch → **Error**: *"All automation is
blocked: this is the Policy as Code wiring canary — if you can read this in
AAP, OPA is answering."*

> **"This one is wired to say no to everything. If it ever runs, we know the
> enforcement is off — and we know before a real rule fails silently."**

Platform room: say the same rule attached to an **organization** is an
incident switch that halts all automation. **Do not do it live.**

---

## 7–11 · The change window, and break glass

**Policy as Code - Change Window** → Launch (no labels) → **Error**:

> *"Friday is not an approved day for automation (allowed: ["Saturday", "Sunday"])."*

> **"Production changes happen at the weekend. It's Friday, so this job waits
> — no matter who launches it."**

Launch again → **Labels** prompt → `break-glass` → **Successful**. Open
the job: labels **`break-glass`, `compliance`**.

> **"Emergencies happen. The override exists, it's one label — and the label
> stays on the job. Every break-glass is on the record."**

**Do not say only admins can break glass.** See the honest bits.

---

## 11–14 · The change ticket

**Policy as Code - Change Ticket** → Launch (no labels) → **Error**:

> *"Label 'change-ticket' is required in 'key:value' form matching ^CHG[0-9]{7}$, but no value was supplied."*

Launch again → **Labels** → `change-ticket:CHG0012345` → **Successful**,
ticket on the job.

> **"No change record, no change. And the job carries the ticket number, so
> audit can go from the job to the change and back."**

A malformed ticket (`change-ticket:12345`) is refused with the format in the
reason — describe it rather than create the label live (labels cannot be
deleted from AAP).

---

## 14–16 · What OPA saw

OPA pod log, one `"msg":"Decision Log"` line for the Hello launch you blocked.
Point at:

- the full job input — who, which template, which inventory, labels
- `"db_password":"**REDACTED**"` — the key is kept, the value never logged
- `"result":{"allowed":false,"violations":[...]}`

> **"Every decision is logged with what it was asked. The value you typed is
> not — the key is enough to know what happened."**

---

## 16–18 · The honest bits

No screen. Pick **two**:

1. **A label is a marker, not a permission.** Anyone who can see the
   organization can apply `break-glass`. Making it a privilege needs the
   policy to check *who* — not built yet.
2. **Only jobs are checked.** Workflows, project syncs and inventory syncs
   are not — though every job inside a workflow is.
3. **Fail-closed where attached.** If OPA is down, guarded templates do not
   run. That is the right default, and it is why we never attach at
   organization level in this demo.

---

## Landing it

Pick **one** question:

- *"Which of your change rules lives in a document today, rather than in the
  platform?"* — governance room
- *"Who would own the rules — your platform team, or security?"* — platform
  room
- *"What would you want blocked first?"* — security room

---

## Act 2 · Prove the state (optional, 20–25)

Bridge from the close:

> **"That's half of it. Stopping a bad change is one thing — proving what your
> machines actually look like is the other half."**

### 20–21 · Every scan leaves evidence

**Jobs** → the last **Linux Day 1 - 4 Compliance Scan**. Say every scan now
writes a dated row and every rule's result to an evidence store.

*Optional live moment:* launch the **Windows Day 2 - 0 Break Fix** workflow
now. It takes about 2 minutes (break → scan → fix → scan), so the dip and
recovery are on the dashboard by the end of 21–24. Quicker: the Linux scan
alone, about 50 s.

### 21–24 · The dashboard anyone can open

Switch to the private window with the dashboard link. Point at, in order:

1. **No login.** *"I can send this to your audit team."*
2. **Latest score:** RHEL 97%, Windows 100%.
3. **What is failing now:** 6 rules on RHEL.
   > **"Five are exceptions the image factory made on purpose, each with a
   > written reason. The sixth is `package_httpd_removed`: we installed a web
   > server, because that's this machine's job."**
4. **Compliance % over time / Assessment history:** the Windows line steps
   100% → 96% → 100%. CIS 2.3.6.6 broken, caught (found `0`, expected `1`),
   fixed, re-proven. Refresh if you launched the workflow at 20–21.

### 24–25 · The honest bits

Pick one: scores come from the scanners, not the policy engine yet · the link
is open, and the database is what makes it read-only · the evidence dies with
this demo environment.

**Close for Act 2:** *"Where does the evidence you hand an auditor come from
today, and how old is it when they get it?"*

---

## Running it live

Every beat above **is** live — there is no offline version yet.

| Beat | What makes it work |
|---|---|
| Hello | `ask_variables_on_launch` — the prompt is the demo |
| Change Window | It must be a weekday in `policy_change_window_timezone` |
| Change Window / Ticket | `ask_labels_on_launch`; `break-glass` and `change-ticket:CHG0012345` exist as code |
| What OPA saw | Console decision logs are on; health checks fill the log every 5 s — filter on `Decision Log` |
| Act 2 dashboard | The evidence store exists **and** a compliance scan has run since it was installed |

### Recovery moves

| Symptom | Move |
|---|---|
| Canary or Hello-with-password **runs** | AAP is not reaching OPA. Check `OPA_HOST` (controller settings category `policyascode`, e.g. `mcp__aap-<env>__settings_retrieve`) is `opa.policy-as-code.svc.cluster.local`, port 8181, and the template's `opa_query_path`. Re-run `install_opa.yml` |
| Change Window **runs** without a label | It is the weekend in `policy_change_window_timezone`. Say so — that is the policy working — and move on to Change Ticket |
| Every guarded job errors, even clean ones | OPA unreachable — fail-closed. `oc get pods -n policy-as-code`; re-run `install_opa.yml` |
| HTTP 403 launching with a label | You are not an org member (the `policy-demo` user is not). Launch as an org member or admin |
| Labels prompt missing | `config.yml` has not run since the template gained `ask_labels_on_launch` |
| Dashboard panels empty | No compliance scan has run since the evidence store was installed. Launch `Linux Day 1 - 4 Compliance Scan` (about 50 s) and refresh |
| Dashboard link 503s | The `policy-dashboard` pod isn't ready. Re-run `AAP Ecosystem - Install Policy Compliance Dashboard`. If the cluster is gone, show the [committed image](../../images/policy-compliance-dashboard.png) instead |
| Scan finished but no new row | Its log says *"policy-db is not installed"* or *"was NOT recorded"*. The scan itself still passed; re-run `AAP Ecosystem - Install Policy Evidence Store` |

---

## Screenshots still worth capturing

- [ ] Hello launch prompt with `db_password` added
- [ ] Blocked job Details page, Explanation visible (Hello)
- [ ] Change Window Labels prompt with `break-glass` selected
- [ ] Successful break-glass job showing both labels
- [ ] Change Ticket blocked Explanation
- [ ] OPA decision log line with `**REDACTED**`
- [x] Compliance dashboard, Act 2 ([`policy-compliance-dashboard.png`](../../images/policy-compliance-dashboard.png), sandbox 2026-10-08)
