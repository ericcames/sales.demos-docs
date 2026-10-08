# Objections and questions — Policy as Code

Rules for using this:

- **Answer the question that was asked**, then stop. A long answer to a short
  question reads as evasion.
- **If the answer is "it doesn't do that", say so first**, then say what it does
  do. Never lead with the workaround.
- Everything here is checkable in a public repository. If you are not sure, say
  "let me check" and check — you can, live, in front of them.

---

## "We already do this with approvals / our CAB / a ServiceNow gate."

Do not compete with the change process. Show where it lands.

> **"Keep the CAB. This is what makes its decision stick: the window and the
> ticket the board already requires, checked by the platform at launch instead
> of by a person afterwards. The ticket ends up on the job, so the two systems
> point at each other."**

---

## "Can only admins break glass?"

**No — say that first.**

> **"No. In AAP a label is a marker, not a permission: anyone who can see the
> organization can apply it at launch. What you get today is a record — every
> break-glass is on the job, with who and when. Making it a privilege means
> the policy also checks who launched, which we've proposed to the library."**

Source: `LabelAccess` in `awx/main/access.py`, measured on sandbox in
[sales.demos#846](https://github.com/ericcames/sales.demos/pull/846).

---

## "What happens if the policy server is down?"

> **"Where a rule is attached, the job fails closed — it does not run, and
> AAP reports 'a policy violation or error'. Where no rule is
> attached, AAP never calls the server, so nothing else is affected. That is
> why rules are attached deliberately, per template."**

The canary is the early warning: if it ever *runs*, AAP is not reaching OPA.

---

## "Does this cover workflows?"

**Not as a whole — say that first.**

> **"Only jobs are evaluated. A workflow itself, project syncs and inventory
> syncs are not. Every job node inside a workflow is, so a workflow cannot
> route around a rule on one of its templates."**

---

## "Where are the credentials? Will secrets end up in the policy logs?"

> **"The decision log records the whole job AAP sent, but extra-var values are
> redacted — the key is kept, the value never written. We found the gap by
> looking: before the mask, the demo's own password was in that log. The
> install now reads the log back and fails if a value gets through."**

Survey password answers already arrive masked from AAP. Credentials are never
in the input as values — only their names and types.

---

## "Does it slow every job down?"

> **"OPA evaluates a decision in under a millisecond — 0.4 to 0.6 ms measured.
> Anything you notice is AAP's own queue."**

---

## "Can we write our own rules?"

> **"Yes — rules are Rego, plain text in git. This demo uses an open library,
> pinned to a release and tested every time the server starts, plus our own
> settings file. Yours would sit beside it the same way."**

---

## "Is this Gatekeeper / Kubernetes admission control?"

> **"No. Gatekeeper decides what may be created in a cluster. This decides
> whether an automation job may start, using the job's details — who, what,
> where, when."**

Both use OPA; they answer different questions.

---

## "Is this supported?"

**Do not guess.** Check the AAP documentation for the version in front of you
and say what it says. What this demo proves is that the feature works on AAP
2.7 (controller 4.8.6), on sandbox, on 2026-10-02.

---

## "Who can launch this?"

> **"Whoever has Execute on the template — the policy does not replace RBAC,
> it adds a check after it. Our demo user, `policy-demo` in `app-team`, can
> launch all four demo templates and nothing else."**

---

## "What does this cost us to run?"

> **"One small pod: 85 MB image, 50 millicores and 128 MiB requested. No
> licence for OPA — it is open source, as is the policy library."**

---

## "Can I have it?"

> **"Yes. The automation is public — `install_opa.yml` and the
> `/sales-demos-policy` skill in sales.demos — and the policies are
> Apache-2.0."**

---

## Act 2: proving the state

### "Is the policy engine grading this?"

**Not yet — say that first.**

> **"No. These scores come from the scanners: OpenSCAP on Linux, and a
> configuration check on Windows. Grading the same facts with the policy
> library is the next step. We held it back because the library's RHEL 9
> benchmark can't yet tell 'no data' from 'compliant' in three of its
> sections, and a compliance score has to fail closed."**

Source: sales.demos#851 (an empty input scores 21.4%, with `filesystem`,
`network` and `user_group` compliant).

### "Your hardened image fails six rules?"

> **"Five are exceptions the image factory made on purpose, each with a
> written reason. A boot-loader password and a root password do nothing on a
> cloud VM, and the users some rules check don't exist yet when the image is
> built. The sixth is the web server we installed, because serving a page is
> that machine's job. What matters is that every gap is known and owned."**

Source: `image.builder.pipeline/playbooks/vars/exempt_controls.yml`.

### "Anyone with the link can see it?"

> **"Yes, by design for this demo: it's meant for a team without accounts. The
> database is what makes it safe. The dashboard can only read the two evidence
> tables, and every install proves a write is refused. It shows host names and
> rule names, never credentials. In production you'd put your SSO in front of
> it."**

### "Where does the evidence live, and what happens when this environment goes away?"

> **"In PostgreSQL on the same cluster, on its own storage volume. Today it
> goes away with the environment. Exporting a dated evidence bundle somewhere
> permanent is designed but not built."**

### "Can our Grafana, or Grafana Cloud, read it instead?"

> **"Yes. It's a plain PostgreSQL datasource with a read-only role, and the
> dashboard is a JSON file in the repo. We run Grafana in the cluster here
> only so the demo is self-contained."**

---

## Questions to ask *them*

**After the change window:**
- *"What is your change window today — and who enforces it?"*

**After Hello:**
- *"Where do passwords end up in your job records today?"*

**After the dashboard (Act 2):**
- *"Where does the evidence you hand an auditor come from today, and how old
  is it when they get it?"*

**Before the close:**
- *"Who would own the rules — the platform team, or security?"* The answer
  tells you whether the next meeting is technical or organizational.

---

## Things not to say

- That `break-glass` is restricted to admins. It is not.
- A support status for AAP's Policy as Code feature you have not checked.
- That it covers workflows, project syncs or inventory syncs.
- That the library's 638 policies are all wired to AAP — this demo attaches four
  rules.
- Any date for team-based rules (`owner_scope`); it waits on an upstream
  release.
- That the policy engine graded the Act 2 scores. The scanners did.
- That the hardened image is "100% compliant". It isn't, and the five
  documented exceptions are the better story.
