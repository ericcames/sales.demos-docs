# Architecture — Policy as Code

Reference for the presenter. What exists, what builds what, and how long each
part takes.

This describes the demo as it is *shown*. For **why** it is built this way —
including what was measured and what was reversed — read
[sales.demos#841](https://github.com/ericcames/sales.demos/issues/841).

---

## The flow

```mermaid
flowchart TD
    L["<b>Launch</b><br/>a Policy as Code template<br/><i>extra vars and labels as prompted</i>"] --> C
    C["<b>AAP controller</b><br/>job created, before it starts<br/><i>template has an opa_query_path</i>"] -->|"POST /v1/data/&lt;path&gt;<br/>{input: the job}"| O
    O["<b>OPA</b><br/>opa.policy-as-code.svc:8181<br/><i>one pod, ClusterIP only</i>"] --> P["<b>Policies</b><br/>rego_policy_libraries v2.0.0<br/>enforcement/aap"]
    O --> D["<b>Our settings</b><br/>data.aac.aap.config"]
    O --> M["<b>Decision log</b><br/>pod stdout, extra_vars masked"]
    O -->|"{allowed, violations}"| C
    C -->|allowed| R["Job runs"]
    C -->|"not allowed, with a reason"| E["Job ends <b>Error</b><br/>reason in Explanation"]
```

Non-obvious things about the flow:

- **AAP sends the whole job.** Who launched it, the template, inventory,
  organization, credentials, labels, extra vars and creation time. Each rule
  reads only the fields it needs.
- **A job is blocked only when `allowed` is false *and* `violations` is
  non-empty.** A policy answering `{"allowed": false, "violations": []}` lets
  the job run.
- **No Route.** AAP runs on the same cluster and reaches OPA by Service DNS.
  Nothing about the policy server is exposed outside the cluster.
- **Launch labels are merged with the template's.** A job launched with
  `break-glass` carries `break-glass` *and* `policy`, and OPA sees both.
- **Fail-closed, but only where attached.** No query path, no call. A dead
  OPA cannot affect a template that has no rule attached.

---

## Act 2: the evidence path

```mermaid
flowchart LR
    S["<b>Day 1 compliance scan</b><br/>Linux: OpenSCAP CIS L1<br/>Windows: control verification"] --> R
    R["<b>Recorder</b><br/>in the job's EE<br/><i>record_compliance_evidence.yml</i>"] -->|"k8s_cp + psql<br/>via the Kubernetes API"| DB
    DB["<b>policy-db</b><br/>CloudNativePG, PostgreSQL 18<br/><i>assessments · host_facts</i>"] -->|"grafana_ro<br/>SELECT only"| G
    G["<b>Grafana</b><br/>policy-dashboard<br/><i>provisioned from the repo</i>"] --> W["<b>Public Route</b><br/>anonymous Viewer<br/><i>anyone with the link</i>"]
```

Non-obvious things about it:

- **Every scan appends to `assessments`.** That table is the history. `host_facts`
  holds the latest per-rule input per host and framework, the raw material OPA
  grading will read later.
- **Opt-in by presence, and never the reason a scan fails.** If the evidence
  store isn't installed, the scan says so and carries on. If a write fails, it
  warns and the scan still succeeds.
- **No database password anywhere.** The recorder writes through the
  Kubernetes API with the credential the job already has. Grafana's read-only
  password is generated in the cluster and never leaves it.
- **The database is the security boundary, not Grafana.** Grafana lets any
  viewer send a query, so `grafana_ro` may only `SELECT` the two evidence
  tables. Every install proves a write is refused.
- **The data is on shared Ceph, not the node disk.** A 9.1 GiB test write to
  a 10 GiB volume moved the node's free space by 16 MB.

---

## Inputs

| Question | Variable | Choices | Default |
|---|---|---|---|
| Which policy library release | `policy_library_version` | any tag of `rego_policy_libraries` | `v2.0.0` |
| Whose clock the change window uses | `policy_change_window_timezone` | any IANA zone, set per SE in `local.yml` | `America/Phoenix` |

Deliberately absent: an option to attach rules at **organization** level. The
library denies superuser launches by default and this platform runs as admin,
so an org-level rule would block `config.yml` and every VM workflow.

---

## What gets created

| Resource | Purpose |
|---|---|
| Namespace `policy-as-code` | Holds everything below |
| ConfigMap `opa-policies` | The library's `enforcement/aap/` files at the pinned tag, plus its tests |
| ConfigMap `opa-config` | Our settings (`data.json`) and the decision-log mask with its tests |
| Deployment `opa` | One pod. Two initContainers run the library's tests (47) and the mask's tests (4); a failure stops the rollout and the old pod keeps serving |
| Service `opa` | ClusterIP on 8181 |
| Cluster `policy-db` (Act 2) | CloudNativePG PostgreSQL, one instance, 10 GiB on the default Ceph storage class; database `compliance` |
| Role `grafana_ro` (Act 2) | `SELECT` on `assessments` and `host_facts`; read-only transactions; 10 s statement timeout |
| Deployment, Service, Route `policy-dashboard` (Act 2) | Grafana 13.1.7, anonymous Viewer, edge TLS. Datasource and dashboard provisioned from files |
| Secret `policy-dashboard` (Act 2) | Grafana admin and `grafana_ro` passwords, generated once in the cluster |

---

## What AAP holds

| Type | Name |
|---|---|
| Setting | `OPA_HOST` = `opa.policy-as-code.svc.cluster.local`, `OPA_PORT` = `8181` |
| Job template | `Policy as Code - Hello` → `extra_vars_control` |
| Job template | `Policy as Code - Canary` → `deny_all` |
| Job template | `Policy as Code - Change Window` → `maintenance_window` |
| Job template | `Policy as Code - Change Ticket` → `required_labels` |
| Job template | `AAP Ecosystem - Install Policy Server` |
| Job template | `AAP Ecosystem - Install Policy Evidence Store` (Act 2) |
| Job template | `AAP Ecosystem - Install Policy Compliance Dashboard` (Act 2) |
| Job template | `Linux Day 1 - 4 Compliance Scan`, `Windows Day 1 - 4 Compliance Scan`: unchanged, now also record evidence |
| Label | `policy` (on every demo template), `break-glass`, `change-ticket:CHG0012345` (launch-time only) |
| User / team | `policy-demo` in `app-team`, Execute on the four demo templates only |

The `opa_query_path` on each template is set by `install_opa.yml` through the
controller API — no collection module accepts the field yet.

---

## Timing

Measured on sandbox, 2026-10-02.

| Step | Time |
|---|---|
| OPA evaluating one decision | 0.4–0.6 ms (`timer_server_handler_ns` in the decision log) |
| Blocked launch, created → finished | 0.75 s (job 164); 6.4 s to reach OPA on job 141 — the difference is AAP's own queue, not the policy |
| `install_opa.yml`, end to end | Not measured |
| Linux compliance scan, including the evidence write | 52 s (job 321, 2026-10-08) |
| `Windows Day 2 - 0 Break Fix`, all four steps | About 2 minutes (workflow 332: scans recorded 15:58:15Z and 15:58:53Z) |
| Windows compliance scan, including the evidence write | 31 s (job 322) |
| Install the evidence store (already present) | 8.8 s (job 314) |
| Install the dashboard (already present) | 14 s (job 328) |

Footprint: the OPA image is 85 MB; the pod requests 50m CPU and 128 MiB.
Act 2 adds PostgreSQL (100m / 256 MiB; its image is already on the node for
Automation Orchestrator) and Grafana (50m / 128 MiB; a 365 MiB image pull).

---

## What does not work yet

- **`owner_scope` (team-based rules)** — waits for a library release that
  includes [ynotbhatc/rego_policy_libraries#161](https://github.com/ynotbhatc/rego_policy_libraries/pull/161),
  which taught the library AAP 2.7's team format.
- **A label is a marker, not a permission** — anyone who can see the
  organization can apply `break-glass`. See [objections](objections.md).
- **Overnight change windows** — the library checks day and hour separately
  against the calendar date, so a window spanning midnight into Monday cannot
  be expressed. Raised upstream on #841.
- **The UI launch prompts** have not been rehearsed; every beat was proven
  through the API.
- **Act 2 scores come from the scanners, not OPA.** Grading the same facts
  with the library's `cis_rhel9` waits on its input shape, and three of its
  sections report compliant when their input is missing (sales.demos#851).
- **Evidence dies with the environment.** Exporting a dated bundle off-cluster
  (Phase 3 §3d) isn't built.

---

## Cleanup

| Destroyed | Preserved |
|---|---|
| Clear `opa_query_path` on a template and it runs unguarded | `OPA_HOST` — harmless with nothing attached |
| Delete namespace `policy-as-code` to remove the server — **clear the paths first**, or the guarded templates fail closed | The templates, labels and `policy-demo` user (config-as-code) |
| `-e policy_dashboard_state=absent` removes Grafana and drops `grafana_ro` | The evidence in `policy-db` |
| `-e policy_db_state=absent` removes `policy-db` **and all recorded evidence** | The scans themselves, which skip recording without it |
