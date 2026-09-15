# Objections and questions — Grafana Cloud

What platform engineers and SREs ask about this demo, answered from what the
repository actually does — including the answers that are "no".

Rules for using this:

- **Answer the question that was asked**, then stop.
- **If the answer is "it doesn't do that", say so first**, then what it does do.
- Everything here is checkable in
  [sales.demos](https://github.com/ericcames/sales.demos). If unsure, say "let me
  check" and check.

---

## "We already have monitoring. Why would we move?"

**Don't ask them to.** The demo is not about Grafana.

> **"You don't have to — and I'd be suspicious of anyone who said you should
> swap monitoring tools off a twenty-minute demo. What I'm showing is two
> patterns that work with whatever you run: the monitoring configuration lives
> in git and AAP applies it, and an assistant reads the data without being able
> to change it. We used Grafana because it has a free tier and an official MCP
> server. The same playbook shape works for Dynatrace, Datadog or your own
> Prometheus."**

---

## "OpenShift already ships Prometheus and dashboards. Why add this?"

> **"It does, and we use it — Alloy copies from OpenShift's own Prometheus rather
> than scraping anything twice. What the built-in stack doesn't give you is one
> place across clusters that outlives any one of them. Our demo clusters are
> rebuilt every couple of weeks; the Grafana data wasn't. If you run one
> long-lived cluster, the built-in monitoring may be all you need."**

---

## "Can the AI change our monitoring? Or our cluster?"

**No — and show the proof.** This is the question that matters most.

> **"Not through this server. Its token has Grafana's Viewer role. When we asked
> it to add an annotation, Grafana returned a 403 — the refusal comes from
> Grafana, so a new write tool added to the server tomorrow gets refused the same
> way. Dashboards and alerts change through a pull request and an AAP job, with
> a different token. The AI reads; Ansible writes."**

Then volunteer the scope: the *OpenShift* server on the sandbox environment is
write-enabled, deliberately, and the demo environment's is read-only. See
[`../../mcp-servers/objections.md`](../../mcp-servers/objections.md).

---

## "Where are the credentials?"

> **"Three tokens, each limited to one job. Alloy has a push-only token in a
> Kubernetes Secret — it can send data and nothing else. The playbooks use an
> Editor token that can change dashboards and alerts but can't push data. The
> assistant has a Viewer token. All three are in an Ansible Vault file that is
> never committed; AAP receives them through a custom credential at run time.
> The Grafana address itself is treated as private too."**

Detail: [`playbooks.md` → The credentials](playbooks.md#the-credentials).

---

## "Is it really idempotent?"

> **"Yes, and it's stronger than 'run it twice and nothing breaks'. The alerts
> playbook replaces the whole rule group, so a rule you delete from git is
> deleted from Grafana. Then it reads the group back and fails if Grafana
> doesn't hold exactly what's committed. The dashboard is overwritten with a
> version message saying which playbook applied it."**

**Volunteer the exception:** the rules are editable in the Grafana UI on
purpose. An edit there survives until the next run, then git wins. That is a
choice for learning, and a customer might reasonably lock it down.

---

## "What happens when it breaks?"

Be specific:

| What breaks | What happens |
|---|---|
| Alloy stops on a cluster | *Alloy federation down* fires after 5 minutes; the dashboard's Alloy stat goes red |
| AAP's password rotates | *AAP controller metrics down* fires; re-run template 1 with the new vault value |
| A token is revoked | the job fails with `401`; the MCP server errors on its next call |
| Grafana's API changes | the alert playbook uses an API Grafana has marked deprecated — the move is noted in the playbook |
| The free account ends | everything in Grafana is gone; git has all of it except the history |

---

## "Why didn't the alert fire the moment the VM stopped?"

**The one that catches presenters.**

> **"Because Prometheus is being careful. When a series stops arriving it keeps
> the last value for five minutes, in case it was one missed sample. So a stopped
> VM stays on the dashboard for about five minutes, then the alert waits one more
> minute to be sure. In our rehearsal: stopped at 18:01, firing at 18:08. For
> 'is my VM up' you'd want a check that asks OpenShift directly — which is what
> the OpenShift MCP server is for."**

---

## "Do you have traces?"

**Answer the limitation first.**

> **"No. Traces have to be emitted by the application, and nothing in this
> platform does that. Grafana Cloud has a trace store and the assistant has
> trace tools, and they're empty here. Tracing is a conversation for your
> application teams, with OpenTelemetry — it's not something infrastructure
> automation can switch on for you."**

---

## "What does this cost at scale?"

> **"For this demo, nothing — two clusters used about 2,300 metric series of the
> free 10,000 and under 5 GB of logs a month. At scale the bill is driven by the
> number of distinct series, which is why the playbook selects metrics explicitly
> rather than sending everything. The honest answer for your estate is 'measure
> it': the same queries we used are in the usage page."**

Then [`usage-and-cost.md`](usage-and-cost.md).

---

## "Our data can't leave the building."

> **"Then this exact deployment isn't for you — it sends metrics and pod logs to
> a SaaS service. The collection and configuration pattern still is: Alloy can
> push to a Grafana, Mimir and Loki you run yourselves, and the dashboard and
> alert playbooks only need a URL and a token. The log filter already keeps
> OpenShift control-plane namespaces out."**

---

## "Isn't the dashboard wrong? It says three nodes."

**Yes. Say so.**

> **"Good catch — it is. On a single-node cluster that panel counts condition
> values instead of nodes. One is right; three isn't. It's the kind of thing a
> pull request fixes in a line, which is rather the point of having the
> dashboard in git."**

---

## "Can I have it?"

> **"Yes. It's all public: the playbooks, the dashboard JSON, the alert rules and
> these docs. A free Grafana Cloud account and about 45 minutes gets you your own
> copy — the rebuild guide is step by step."**

Link: [`rebuild.md`](rebuild.md).

---

## Questions to ask *them*

**After the dashboard beat:**

- "Where does your monitoring configuration live today — in a repo, or in the UI?"

**After the 403:**

- "What would you need to see before letting an assistant *act* on an alert, not
  just explain it?"

**Before the close:**

- "Who owns observability for you — the platform team, or a separate SRE
  group?" *(Decides whether the next meeting is technical or organizational.)*

---

## Things not to say

- **"Grafana is better than what you have."** Not the claim, and not ours to make.
- **"The AI fixes problems."** It reads and explains. Changes go through AAP.
- **"Real-time."** A stopped VM took seven minutes to alert. Say "minutes".
- **"Free."** The *tier* is free and limited. Production volumes are not.
- **Any date for tracing** — nothing is planned.
