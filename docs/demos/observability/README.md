# Observability

Demos about **seeing** what the automation did: metrics, logs and alerts from the
platform, and an AI assistant that can read them.

| Demo | What it shows | Status |
|---|---|---|
| [Grafana Cloud](grafana/README.md) | Ansible instruments OpenShift, OpenShift Virtualization and AAP, pushes a dashboard and alert rules as code, and Claude reads the result through a read-only MCP server | **Ready** — captured on sandbox 2026-09-15 |

Other observability platforms go beside `grafana/` here, one directory each. The
Dynatrace idea is tracked in
[sales.demos#99](https://github.com/ericcames/sales.demos/issues/99).

---

## Metrics, logs and traces in one minute

The three kinds of telemetry answer different questions, and a demo gets more
convincing when you say which one you are showing.

| Signal | The question it answers | Looks like | In the Grafana demo |
|---|---|---|---|
| **Metrics** | *How much, how many, how fast — right now and over time?* | Numbers sampled every minute: CPU %, VMs running, jobs pending | **Yes** — about 2,000 series per cluster |
| **Logs** | *What exactly happened, in the words the software used?* | Timestamped lines of text from each pod | **Yes** — four namespaces, roughly 40 MB a day per cluster |
| **Traces** | *Where did the time go in one request, step by step?* | A tree of timed spans across services | **No** — nothing in this stack emits them; see the Grafana guide |

A useful way to put it to a customer: **metrics tell you that something is
wrong, logs tell you what went wrong, and traces tell you where.**
