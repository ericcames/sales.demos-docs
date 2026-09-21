# Demo: Observability with Grafana Cloud

**Start here.** Ansible instruments OpenShift, OpenShift Virtualization and AAP,
pushes a dashboard and alert rules into Grafana Cloud as code, and Claude reads
the result through a read-only MCP server — "Ansible writes, AI reads" — in about
twenty minutes.

| | |
|---|---|
| **Length** | 20 minutes (15 + 5 for questions) |
| **Audience** | Platform engineers, SREs and automation leads who already run monitoring and want to see it managed as code and read by an assistant |
| **Reader** | The Ansible pre-sales engineer presenting it |
| **Needs a live environment?** | **No, but there is one.** Every beat is captured in screenshots here. The Grafana Cloud stack keeps running: on 2026-09-20 the trial ends and the account moves to the **Free plan**, which this demo fits inside |
| **Status** | **Ready** — built, rehearsed and captured on sandbox, 2026-09-15 |

**New to Grafana?** Read [`grafana-101.md`](grafana-101.md) first. It assumes
nothing.

---

## The documents

| File | Read it when |
|---|---|
| [`grafana-101.md`](grafana-101.md) | **First, if Grafana is new to you.** A screen-by-screen tour, metrics vs logs vs traces, and a glossary |
| [`run-sheet.md`](run-sheet.md) | **While presenting.** Minute markers, what is on screen, recovery moves |
| [`talk-track.md`](talk-track.md) | **While rehearsing.** The narrative and the actual words |
| [`playbooks.md`](playbooks.md) | **When asked "what did Ansible actually do".** Every playbook, job template, credential and resource |
| [`mcp-server.md`](mcp-server.md) | **When asked "what can the AI do with it".** The 81 tools, real answers, and the proof it cannot write |
| [`architecture.md`](architecture.md) | **When asked "how does that work".** Data flow, the three tokens, timings, what the free plan changes |
| [`usage-and-cost.md`](usage-and-cost.md) | **When asked "what does this cost" or "how do we send less".** Measured volumes and reduction options |
| [`rebuild.md`](rebuild.md) | **When you want it running again.** A new free account to a working demo in about 45 minutes |
| [`objections.md`](objections.md) | **Before you go in.** What this audience asks, answered honestly |

---

## The 60-second version

1. **AAP deploys Grafana Alloy** onto the OpenShift cluster. It copies selected
   metrics from OpenShift's own Prometheus, scrapes AAP's metrics, and streams
   pod logs — all tagged with the cluster's name — to Grafana Cloud.
2. **AAP pushes a dashboard from git.** *Sales Demos - Cluster Health*: nodes,
   VMs, AAP, logs, with a dropdown for each environment.
3. **AAP pushes five alert rules from git.** A cluster going quiet, AAP metrics
   failing, VMs disappearing, jobs stuck pending, the free-tier budget.
4. **Claude connects with a Viewer token** and answers questions from the data:
   what is running, how big, where the logs come from, what is firing.
5. **Claude tries to write, and Grafana says 403.** The AI reads everything and
   can change nothing; changes go through the playbooks.

**What the demo is actually about** is where the line between an assistant and
automation belongs. Monitoring is configured from a repository, reviewed as a
pull request and applied by AAP. The assistant makes that data conversational
without being given the keys to it.

![Sales Demos - Cluster Health on sandbox](../../../images/grafana-dashboard-full.png)

---

## Why it works without an instance

Every beat is captured, so a lost cluster or a dead conference network costs
you nothing:

- **Dashboard and panel images** were rendered by Grafana itself, through the
  image renderer, for the sandbox cluster with a full day of data behind them.
- **UI screenshots** for the beginner's tour were taken in a browser and cropped
  to remove the account address.
- **MCP answers** in [`mcp-server.md`](mcp-server.md) are real tool calls against
  the live stack, trimmed but not edited.
- **The automation itself** is unchanged in git, and was run from AAP.

**The honest caveat:** screenshots are pictures of a working system. The stack
itself is still up, so a live run is possible — but check it first with the
question below rather than assuming.

---

## If you want to run it live

Rebuild first: [`rebuild.md`](rebuild.md). Then, in AAP, filter templates by the
label `observability` and launch:

1. `AAP Observability - 1 Deploy Alloy` — once per cluster
2. `AAP Observability - 2 Deploy Dashboards`
3. `AAP Observability - 3 Deploy Alerts`

Prove it before relying on it — ask Claude, do not trust the job colour:

```text
"Which clusters are sending metrics to Grafana, and is anything firing?"
```

Two clusters answering and five rules at *Normal* means you are ready.

---

## Red Hat and Grafana links

| Link | What it is |
|---|---|
| [Grafana Cloud free tier](https://grafana.com/pricing/) | What the free account includes |
| [Grafana Alloy](https://grafana.com/docs/alloy/latest/) | The collector the playbook deploys |
| [grafana/mcp-grafana](https://github.com/grafana/mcp-grafana) | The MCP server Claude uses |
| [Alerting provisioning API](https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/http-api-provisioning/) | What `deploy_alerts.yml` calls |
| [OpenShift monitoring](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/monitoring/index) | The built-in Prometheus Alloy federates from |
| [AAP metrics](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/) | Where the `awx_*` metrics come from |

---

## Related

- [`../../mcp-servers/`](../../mcp-servers/README.md) — the wider MCP story this demo is one server of
- [`../../../plan/grafana-plan.md`](../../../plan/grafana-plan.md) — why the automation is built this way
- [`ROADMAP.md`](https://github.com/ericcames/sales.demos/blob/main/ROADMAP.md) — what is done and what is not
