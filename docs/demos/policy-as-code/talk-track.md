# Talk track — Policy as Code

**Rehearse from this. Present from [`run-sheet.md`](run-sheet.md).**

Nothing is rendered offline yet — every beat needs AAP with the OPA server
deployed. The verbatim AAP messages below were captured on sandbox, so you
can rehearse the words without a cluster.

---

## Who is in the room

**You are the pre-sales engineer.** Every document in this folder is written to
you.

**They are one of three rooms**, and the same four beats serve all three. Decide
which room you are in before you start, and spend your extra minute there.

| Room | Who | Lean on | They care intensely about |
|---|---|---|---|
| **Governance** | Automation leads, change managers, the CAB | Change Window, Change Ticket | Change control that is enforced, not requested; an audit trail that needs no reconstruction |
| **Platform** | Platform engineers who would run it | Canary, What OPA saw | How it fails, what it costs, who owns the rules, and that it does not slow every job |
| **Security** | Security and compliance | Hello, What OPA saw | Secrets kept out of records and logs; evidence a control actually ran |

| Nobody in any room cares about | Everyone cares about |
|---|---|
| Rego syntax | That the rule is enforced before the job starts, not reported after |
| OPA internals | That the reason is readable by the person who was blocked |
| A library of 638 policies | That *their* rule could be written down this way |

Three delivery notes:

- **Do not open with OPA.** Open with the question AAP asks. OPA is the answer
  to "where do the rules live", and only the platform room asks it unprompted.
- **Never call `break-glass` RBAC-protected.** It is a marker. The honest-bits
  beat says so; do not undermine it earlier.
- **Do not claim a support status** for AAP's Policy as Code feature unless you
  have checked it for the version in front of you. This demo proves it works
  on AAP 2.7 (controller 4.8.6); it does not prove what Red Hat supports.

---

## Beat 1 · The question AAP now asks (0–2)

On screen: the Templates page filtered on `policy`.

> **"Before any of these starts, AAP asks a policy server one question: may
> this job run? If the answer is no, it does not start — and it tells you
> why."**

> **"The rules are not in AAP. They are in a separate policy engine — Open
> Policy Agent — and they are written as code, tested, versioned and reviewed
> like anything else you automate."**

**Why this beat exists.** It names the whole idea in two sentences before
anything is shown, so each later beat is an instance of it rather than a new
concept. The second sentence is the one the platform room remembers.

**Transition:** *"Let me show you the simplest rule there is."*

---

## Beat 2 · A secret in extra vars (2–5)

Launch **Policy as Code - Hello** with `greeting: hello` — it runs. Launch it
again with `db_password: not-a-real-one` added — it ends **Error** before any
pod starts, and the Explanation reads:

```
This job cannot be executed due to a policy violation or error. See the following details:
{'Violations': {'Job template': ["extra_var 'db_password' looks like a secret "
                                 '— pass it through a credential or Ansible '
                                 'Vault, not extra_vars.']}}
```

> **"Same template, same person. The only difference is what was typed. That
> password would have sat in the job record for ever — now the job never
> starts, and the person who typed it is told exactly what to do instead."**

**Why this beat exists.** It is the smallest possible proof: one rule, two
launches, one difference. Everyone in every room has seen a password in an
extra var. The *reason* — readable, actionable, aimed at the person who was
blocked — is the thing to point at; it is what separates a control from an
error.

**Security room:** stay here an extra minute. The rule matches on the
variable's *name*, so it catches the habit before the value matters.

**Transition:** *"Now — how would you know if this stopped working?"*

---

## Beat 3 · The canary (5–7)

Launch **Policy as Code - Canary** — **Error**: *"All automation is blocked:
this is the Policy as Code wiring canary — if you can read this in AAP, OPA is
answering."*

> **"This one is wired to say no to everything. If it ever runs, the
> enforcement is off — and we find out from the canary, not from a rule that
> quietly let something through."**

**Why this beat exists.** Policies here default a missing field to *allowed*,
so broken wiring looks exactly like a permissive policy. The canary is the
answer to the platform room's first real question — "how do I know it's on?"
— asked before they ask it. The idea came from the policy library's
maintainer.

**Platform room:** the same rule, attached to an *organization*, is an
incident switch — one change halts every job in it. Say it; never do it live.

**Transition:** *"That's wiring. Here's a rule your change board would write."*

---

## Beat 4 · The change window, and break glass (7–11)

Launch **Policy as Code - Change Window** with no labels — **Error**:

> *"Friday is not an approved day for automation (allowed: ["Saturday", "Sunday"])."*

> **"Production changes happen at the weekend. It's a weekday, so this job
> waits — no matter who launches it, no matter how urgent it feels."**

Launch again, choose the label **`break-glass`** — it runs, and the finished
job carries labels `break-glass` and `policy`.

> **"Emergencies happen, so the override exists. It's one label — and the
> label stays on the job. Every time someone broke glass is on the record,
> with who and when."**

**Why this beat exists.** It turns a policy document — "no production changes
during the week" — into something the platform enforces. The break-glass half
matters as much as the block: a control with no override gets routed around,
and an override that leaves a record is the one an auditor accepts.

**Governance room:** this is your beat. Ask what their change window is.

**Careful.** The window is evaluated in `policy_change_window_timezone` (Phoenix
by default) against the job's creation time. On a weekend there, this job
runs. Say so if it happens — that is the rule working.

**Transition:** *"A window says when. Most change processes also say which
change."*

---

## Beat 5 · The change ticket (11–14)

Launch **Policy as Code - Change Ticket** with no labels — **Error**:

> *"Label 'change-ticket' is required in 'key:value' form matching ^CHG[0-9]{7}$, but no value was supplied."*

Launch again with **`change-ticket:CHG0012345`** — it runs, with the ticket on
the job.

> **"No change record, no change. And because the ticket is on the job, audit
> can go from a job to its change record — and from a change record to every
> job that ran under it."**

A malformed ticket — `change-ticket:12345` — is refused with the expected
format in the reason. Describe it rather than create it: AAP labels cannot be
deleted.

**Why this beat exists.** It connects AAP to the system the governance room
already lives in. The format is ServiceNow's change-number shape on purpose.

**Transition:** *"So where does all this go?"*

---

## Beat 6 · What OPA saw (14–16)

The OPA pod log, filtered on `Decision Log`. One line per decision, carrying
the full input AAP sent — who launched, which template, inventory,
organization, labels — and the answer.

> **"Every decision is logged with exactly what it was asked. Notice the
> password: the key is there, the value is not. We know what happened without
> keeping what was typed."**

**Why this beat exists.** It answers "prove it ran" for the security room and
"how do I debug a rule" for the platform room in one screen. The masking is
ours, not OPA's default — unmasked, the demo's own password sat in this log in
plain text, and we found it by looking.

**Transition:** *"Let me tell you what this doesn't do."*

---

## Beat 7 · The honest bits (16–18)

Step away from the keyboard. Pick two.

> **"First: a label is a marker, not a permission. Anyone who can see the
> organization can apply `break-glass`. Today it buys you a record, not a
> restriction. Making it a privilege means the policy also checks who
> launched — we've proposed exactly that upstream."**

> **"Second: only jobs are checked. Workflows, project syncs and inventory
> syncs are not — although every job inside a workflow is."**

> **"Third: where a rule is attached, it fails closed. If the policy server is
> down, guarded jobs don't run. That's the right default for a control — and
> it's why you attach rules deliberately, template by template, not to a
> whole organization on day one."**

**Why this beat exists.** The first point is the one a sharp governance
person finds on their own in the next meeting; being first to it is worth more
than the break-glass beat itself.

---

## Beat 8 · Close (18–20)

> **"Your change rules, your secret-handling rules — written down once, tested,
> versioned, and enforced before the job starts, with the reason in front of
> the person who was stopped."**

Then **one** question, chosen for the room:

- Governance: *"Which of your change rules lives in a document today, rather
  than in the platform?"*
- Platform: *"Who would own the rules — your platform team, or security?"*
- Security: *"What would you want blocked first?"*

---

## If you only get ten minutes

Keep **Beat 1**, **Beat 2** (Hello) and **Beat 4** (Change Window with break
glass), then the first honest bit. Drop the canary, the ticket and the log.

---

## Where the words come from

| Claim | Source |
|---|---|
| AAP asks OPA before a job starts; only jobs are evaluated; fail-closed where a path is attached | `inventory/group_vars/aap/opa_policy.yml` (header, read from [`awx/main/tasks/policy.py`](https://github.com/ansible/awx/blob/devel/awx/main/tasks/policy.py), #841) |
| The rules come from `ynotbhatc/rego_policy_libraries`, pinned to a tag, tested on every rollout | `inventory/group_vars/aap/opa_policy.yml` (`policy_library_version`), `playbooks/install_opa.yml` (`opa-test` initContainer) |
| Hello is blocked with `db_password`, runs without it | `inventory/group_vars/aap/controller_templates.yml`, `playbooks/policy_demo_hello.yml`, sales.demos#841 jobs 115/116 and 141 |
| The canary always blocks; `deny_all` at org level halts everything | `inventory/group_vars/aap/opa_policy.yml` (`deny_all`), sales.demos#841 jobs 131/133 |
| Change window is weekends only in `policy_change_window_timezone`; Friday message verbatim | `inventory/group_vars/aap/opa_policy.yml` (`maintenance_window`), sales.demos#841 job 164 |
| `break-glass` lets the job run and stays on the job | `inventory/group_vars/aap/controller_labels.yml`, sales.demos#841 job 165 |
| A label is a marker, not a permission | `inventory/group_vars/aap/controller_labels.yml` (launch-time labels comment, `LabelAccess` in [`access.py`](https://github.com/ansible/awx/blob/devel/awx/main/access.py)), sales.demos#846 |
| Change ticket required in `CHG` + 7 digits form; message verbatim | `inventory/group_vars/aap/opa_policy.yml` (`labels`), `playbooks/install_opa.yml` (change-ticket asserts), sales.demos#841 jobs 179/180 |
| The decision log keeps the key and redacts the value | `playbooks/files/opa/decision_log_mask.rego`, `playbooks/install_opa.yml` (log assert), sales.demos#844 |
| Rules are attached per template, never at organization level | `inventory/group_vars/aap/opa_policy.yml` (`opa_policy_associations`) |
| The canary was the library maintainer's suggestion | sales.demos#841 (review comment) |
