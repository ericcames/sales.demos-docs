# Automation Orchestrator

Issue [#108](https://github.com/ericcames/sales.demos/issues/108) (experiment),
[#141](https://github.com/ericcames/sales.demos/issues/141) (install),
[#457](https://github.com/ericcames/sales.demos/issues/457) (configure),
[#468](https://github.com/ericcames/sales.demos/issues/468) (deploy workflow),
[#464](https://github.com/ericcames/sales.demos/issues/464) (MCP server).

## Context

Automation Orchestrator is Red Hat's workflow orchestration add-on for Ansible
Automation Platform. It provides a visual canvas for building workflows that
chain AAP job templates with conditional logic, human approvals, and (eventually)
cross-platform integrations. It shipped as GA in version 2026.8 (August 2026),
after being announced as a technology preview at Red Hat Summit in May 2026.

This repo automates AO's full lifecycle: install, configure (AAP SSO +
integration), deploy via AAP workflow, and a 32-tool read-only MCP server. The
work happened in five issues across three weeks, and the plan below records the
decisions in the order they were made.

**Why Automation Orchestrator:** The same thesis as the MCP servers (#102) — stop
paying a manual process every time. AO's value in a demo is that it is a canvas
over existing AAP job templates: no migration, no duplication, and the approval
nodes give regulated-environment customers something AAP workflows do not express
natively.

---

## Phase 1: The experiment (#108)

Split out of #102 so an entitlement failure could not block MCP work.

**Question:** Can AO even be installed on an RHDP cluster? The operator was in
the catalog (#92), but catalog presence is not entitlement — the
`valid-subscription` annotation says `Red Hat Ansible Automation Orchestrator`,
which is a separate subscription.

**Answer: yes.** All five product images pulled under the environment's existing
pull secret. No separate pull secret was needed. Entitlement is a closed question
and not the obstacle.

**The real blocker was PostgreSQL.** The CRD requires `spec.postgres` with no
embedded option — bring-your-own PostgreSQL for two databases (backend and
temporal). Getting the operator installed without being able to instantiate it
was automating the wrong half. This finding shaped Phase 2.

**Footprint of the operator alone:** +0.01 vCPU / +0.07 GiB (cpu: 10m,
memory: 64Mi).

---

## Phase 2: Install as part of every build (#141, #143)

Took the #108 result and made AO part of every environment build. `setup.yml`
installs it by default; skip with `-e install_ao=false`.

### CloudNativePG for the database

AAP's own `aap-postgres-15` was considered and rejected:

- Owned by the `AnsibleAutomationPlatform` CR with `blockOwnerDeletion` —
  databases added by hand live inside something another operator recreates at
  will.
- Temporal's write volume does not belong on the database the whole demo platform
  depends on.

CloudNativePG: `certified: true`, v1.30.0, no `valid-subscription` annotation.
AllNamespaces install mode.

### Three databases, not two

The CRD requires exactly two secretRefs — `backendDatabase` and
`temporalDatabase`. Build two, and then `ao-temporal-migration` crash-loops:

```
pq: database "temporal_visibility" does not exist
```

Temporal keeps its visibility store in a **separate database with a fixed
name**: literally `temporal_visibility`. Nothing in the CRD, the `alm-examples`
sample, or the operator description says so. Found by reading migration logs on
the first live install.

The playbook creates three databases: `ao_backend` (via initdb), `ao_temporal`
and `temporal_visibility` (via Database resources).

### Admin password (#143)

AO's admin password is seeded from `aap_password` — one credential, not two.
The CRD says the secret "is used only during initial database seeding to create
the admin user. Once the admin user exists, this secret is ignored."

### Footprint of the full install

| | Requested CPU | Requested memory |
|---|---|---|
| Before | 15.00 vCPU | 50.30 GiB |
| After | 16.91 vCPU | 52.77 GiB |
| **Delta** | **+1.91 vCPU** | **+2.47 GiB** |

Nine AO pods (backend x2, UI x2, worker x2, background-worker, temporal, redis)
at 1.80 vCPU / 1.91 GiB, plus one PostgreSQL instance at 0.10 vCPU / 0.50 GiB
and a 10Gi PVC.

### Two smaller traps

- **`postgresql.cnpg.io`, NOT `postgresql.cnpg.noobaa.io`.**  ODF's Multicloud
  Object Gateway ships a vendored CloudNativePG under that private API group, and
  its CRDs are present on any cluster with ODF. They will not serve these
  resources.
- **Never wait on `items[0]` of a ClusterServiceVersion list.**  An
  AllNamespaces operator has its CSV copied into every namespace, so `items[0]`
  in a given namespace is as likely to be another operator's copy.

### Teardown leaves AO alone

`teardown.yml` destroys demo VMs. AO and its database are setup-time
infrastructure, not per-demo state. Manual removal:

```bash
oc delete namespace automation-orchestrator                  # instance + database + PVC
oc delete namespace automation-orchestrator-operator-system  # the AO operator
oc delete namespace cnpg-system                              # CloudNativePG
oc delete crd automationorchestrators.aap.ansible.com
```

---

## Phase 3: Configure — AAP SSO and integration (#457)

AO ships installed but unconnected — it cannot see AAP's job templates, and
users can only log in with a local admin account. `configure_ao.yml` fixes both:

1. **SSRF allowlist** — AO uses langchain_core's SSRF protection to block
   private IP addresses on integration URLs. The AAP hostname resolves to a
   private IP inside the cluster. The fix: patch
   `APP_INTEGRATION_URL_ALLOWED_HOSTS` as an env var on the `ao-backend`
   Deployment. The CR's `workflowHttpRequestAllowedHosts` only affects
   `ao-worker`, NOT `ao-backend`.

2. **OIDC identity provider** — `POST /api/v1/identity_providers/setup_aap_oidc`
   creates an OAuth2 application named "Syntara" on AAP and configures AO to use
   it. NOT idempotent: returns 502 if the application already exists. The
   playbook checks first and skips.

3. **AAP credential** — username/password stored in AO for the integration.

4. **AAP integration** — connects to AAP and discovers job templates. On
   sandbox, 33 templates are visible.

### Token rule

This playbook creates NO token. It uses `aap_password` directly for API auth,
and the OIDC setup uses it to create the OAuth application. Nothing to clean up
in an `always:` block.

---

## Phase 4: Deploy workflow (#468/#469)

The AAP workflow `AAP Ecosystem - Deploy Automation Orchestrator` chains:

```
AAP Ecosystem - Install Automation Orchestrator
  └─> AAP Ecosystem - Configure Automation Orchestrator
```

Both templates already existed; the workflow is the one-button entry point.
Survey inherits from `install_ao.yml` and `configure_ao.yml` — `target_env` is
required, everything else has defaults.

---

## Phase 5: MCP server (#464/#465, #466/#467)

`utilities/ao-mcp-server.py` — a custom Python MCP server wrapping the AO REST
API. 32 read-only tools covering workflows, executions, integrations, projects,
credentials, users, settings, and AAP proxy endpoints.

Registered via `utilities/make-ao-mcp.sh`, which:

1. Reads the AO Route from the cluster (via kubeconfig)
2. Logs in with admin credentials to get an access token
3. Registers the server with `claude mcp add --scope local`

### Design decisions

- **Custom server, not generated.** The AO API is OpenAPI 3.1 and could have
  been auto-generated, but the pagination model (cursor-based, not offset) needed
  custom handling (#471), and the tool descriptions needed to be written for an
  AI consumer, not a Swagger reader.
- **Read-only.** No create, update, or delete tools. The demo story is "look at
  what AO orchestrates," not "let the AI build workflows."
- **`--scope local`, not `.mcp.json`.** Same pattern as the AAP MCP server — the
  token is a credential, stored in the operator's local Claude config rather than
  the tracked file.
- **stdio transport.** Runs as a local process. No in-cluster deployment, unlike
  the AAP MCP server.

### Bug: offset pagination (#471/#475)

The AO API uses cursor-based pagination. The initial implementation sent
`offset=0` on list endpoints, which the API rejected with 422. Fixed by removing
the offset parameter and using the `next` cursor from the response.

### Skill drift (#472/#476)

Three drift instances found and fixed:

1. The orchestrator skill referenced `env_secrets[<env>].aap_password` instead
   of `aap_password`.
2. The MCP skill's verify section had no AO check.
3. `.claude/settings.json` allowlisted `mcp__ao-edge__*`, but no `ao-edge`
   server exists.

---

## Open items

- [ ] **Demo guide and run sheet** —
  [#470](https://github.com/ericcames/sales.demos/issues/470), the parent issue.
  Run-sheet timings pending rehearsal.
- [ ] **Workflow as code** —
  [#474](https://github.com/ericcames/sales.demos/issues/474). AO supports YAML
  export/import; committing the demo workflow would make it reproducible.
  Document and stop.
- [ ] **AO branding** —
  [#426](https://github.com/ericcames/sales.demos/issues/426),
  [#477](https://github.com/ericcames/sales.demos/issues/477). No
  `custom_login_info` on the CR. Browser extension workaround filed.
- [ ] **CLAUDE.md plan table** —
  [#473](https://github.com/ericcames/sales.demos/issues/473). Add AO row after
  the docs PR merges.
- [ ] **`aap-edge` server** — No AAP MCP server for edge.
  `make-aap-mcp.sh` only takes sandbox and demo.

---

## What was moved here

The AO section in
[`platform-addons-plan.md`](platform-addons-plan.md) (lines 297-475) covered
the #108 experiment and the #141 install. That content is now here; the
platform-addons plan retains a summary and a link. The move is deliberate: AO
has its own demo guide, its own issues, and its own lifecycle — keeping the plan
inline with MCP server design decisions was organizational debt.
