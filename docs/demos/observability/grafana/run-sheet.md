# Run sheet — Observability with Grafana Cloud

**This is the page you hold while presenting.** The narrative behind each beat,
with the actual words, is in [`talk-track.md`](talk-track.md) — rehearse from
that, present from this.

| | |
|---|---|
| **Length** | 20 minutes — 15 presenting, 5 questions |
| **Audience** | Platform engineers, SREs, automation leads |
| **Needs an environment?** | **No** — the screenshots carry it. Live works too: the stack stays up on the Free plan after 2026-09-20 |
| **Assets** | the images in this folder's pages; the three committed files in sales.demos |

---

## Before you start (5 minutes, offline)

Open these tabs, in this order. **This is the slide deck.**

1. [`README.md`](README.md) — the dashboard image, full width
2. [`playbooks.md`](playbooks.md) — scrolled to the AAP templates image
3. GitHub: [`playbooks/files/grafana/alert-rules.json`](https://github.com/ericcames/sales.demos/blob/main/playbooks/files/grafana/alert-rules.json)
4. [`grafana-101.md`](grafana-101.md) — scrolled to **Alerts**
5. [`mcp-server.md`](mcp-server.md) — scrolled to **The read-only design, proven**
6. [`usage-and-cost.md`](usage-and-cost.md) — for the cost question

---

## The arc

| Time | Beat | On screen |
|---|---|---|
| 0–2 | The problem: monitoring configured by hand | README, top |
| 2–5 | Ansible instruments the cluster | `playbooks.md` — AAP templates, the Alloy flow diagram |
| 5–8 | The dashboard, from git | README — dashboard image; `grafana-101.md` overview row |
| 8–11 | Alerts, from git — and one firing | `alert-rules.json` on GitHub; `grafana-101.md` firing image |
| 11–14 | Claude reads it | `mcp-server.md` — real questions and answers |
| 14–15 | Claude tries to write: 403 | `mcp-server.md` — the proof |
| 15–16 | The honest bits | `architecture.md` → What does not work yet |
| 16–20 | Close and questions | — |

---

## 0–2 · Monitoring configured by hand

On screen: README, top.

> **"Most monitoring is configured the way servers were configured fifteen years
> ago — someone clicks, and nobody can tell you afterwards what changed or why."**

Point at: nothing yet. One sentence, move on.

---

## 2–5 · Ansible instruments the cluster

On screen: `playbooks.md` — the three AAP templates, then the flow diagram.

> **"Three job templates, numbered because they're a chain. The first puts a
> collector on the cluster. It doesn't scrape anything twice — it asks
> OpenShift's own Prometheus for a filtered copy."**

Point at:

- the `observability` label on the templates
- **"once per cluster"** for template 1, **"one Grafana"** for 2 and 3
- the three arrows into Alloy: metrics, AAP, logs

---

## 5–8 · The dashboard, from git

On screen: README dashboard image, then `grafana-101.md` → Overview row.

> **"That dashboard is a JSON file in the repository. Change it in a pull
> request, and AAP applies it — Grafana's version history even says which
> playbook did it."**

Point at:

- the **Cluster** dropdown — one dashboard, every environment
- **VMs Running**, **AAP Controller UP**, **Series Budget**
- the VM table: guest OS, 4 vCPU, 16 GiB

---

## 8–11 · Alerts, from git

On screen: `alert-rules.json` on GitHub, then the firing screenshot.

> **"Five rules, same pattern. Delete one from git, and the next run deletes it
> from Grafana — then checks Grafana holds exactly what's committed."**

Then the rehearsal story:

> **"We stopped a VM at 18:01. It fired at 18:08. That seven minutes isn't the
> demo breaking — Prometheus waits five minutes before believing a series is
> really gone."**

Point at: the rule name, `cluster=sandbox`, the summary text.

---

## 11–14 · Claude reads it

On screen: `mcp-server.md` → Real questions, real answers.

Walk three of them, no more:

1. "What VMs are running, and how big are they?" → the table
2. "Where are our logs coming from?" → `aap` 25.5 MB, `openshift-cnv` 15.5 MB
3. "Show me the VM table" → the rendered panel image

> **"None of those needed a dashboard someone had built for that question."**

---

## 14–15 · The 403

On screen: `mcp-server.md` → The read-only design, proven.

> **"Then we asked it to write. Grafana said no — 403, annotations:create. The
> refusal is in Grafana, not in a list of allowed tools. The AI reads. Ansible
> writes."**

**Pause here.** This is the line people remember.

---

## 15–16 · The honest bits

On screen: `architecture.md` → What does not work yet.

Pick two:

- **No traces** — nothing here emits them
- **"Nodes Ready: 3"** is wrong on a single-node cluster
- **The free plan is a real limit** — 10,000 metric series and 50 GB of logs a month, and two clusters use about a quarter of the series
- **Alerts don't notify anyone** — deliberately, because this repo is public

---

## Landing it

> **"Monitoring config in git, applied by AAP, read by an assistant that can't
> change it."**

Then **one** question — pick one:

- "Where does your monitoring configuration live today?"
- "What would you need to see before letting an assistant act on an alert?"

---

## Running it live

| Beat | Live version |
|---|---|
| 2–5 | Launch `AAP Observability - 1 Deploy Alloy` **before** the meeting; show the finished job |
| 5–8 | The real dashboard, Cluster = your environment, **Last 6 hours** |
| 8–11 | **Stop a VM 10 minutes before this beat**, so the alert is firing when you arrive |
| 11–15 | Ask Claude the questions live; ask it to add an annotation for the 403 |

Prove first — ask Claude: *"Which clusters are sending metrics, and is anything
firing?"*

**Keep the screenshots open in a tab regardless.** If a query stalls, do not
debug in front of them — cut to the tab and carry on.

### Recovery moves

| Symptom | Move |
|---|---|
| Every panel says *No data* | Wrong **Cluster** selected. Change it |
| Graphs empty for the first hours | Alloy was deployed recently. Set time to **Last 1 hour** |
| Stopped a VM, alert not firing | It takes ~7 minutes. Say so; move to the MCP beat; come back |
| MCP call errors | Cut to `mcp-server.md` — same questions, captured answers |
| The 403 doesn't happen | **Stop.** The MCP server has the wrong token. Do not present the governance claim |

---

## Screenshots still worth capturing

Capture from **sandbox**. Alloy has been sending since 2026-09-15 17:35 UTC, so
there is a full day of data from 2026-09-16 evening onwards. The trial ends
**2026-09-20 15:32 UTC**, so everything must be captured by 2026-09-19.

- [ ] `grafana-dashboard-full.png` — full dashboard, Cluster = sandbox, Last 24 hours
- [ ] `grafana-overview-row.png`, `grafana-nodes-row.png`, `grafana-vm-row.png`, `grafana-aap-row.png`, `grafana-logs-panel.png`
- [ ] `grafana-vm-status-panel.png` — rendered by the MCP server
- [ ] `grafana-home-menu.png`, `grafana-dashboards-list.png`, `grafana-dashboard-controls.png`
- [ ] `grafana-explore-metrics.png`, `grafana-explore-logs.png`
- [ ] `grafana-alert-firing.png` — repeat the VM stop
- [ ] `grafana-service-accounts.png`, `grafana-access-policy.png` — tokens masked
- [ ] `grafana-usage-dashboard.png` — account IDs cropped
- [ ] `grafana-aap-templates.png` — the three templates in AAP
