# Objections and questions — Automation Orchestrator

What this audience actually asks, and answers grounded in what the repo really
does — including the questions where the honest answer is "not yet".

Rules for using this:

- **Answer the question that was asked**, then stop. A long answer to a short
  question reads as evasion.
- **If the answer is "it doesn't do that", say so first**, then say what it does
  do. Never lead with the workaround.
- Everything here is checkable in a public repository. If you are not sure, say
  "let me check" and check — you can, live, in front of them.

---

## "AAP already has workflows and approvals. Why this?"

AAP workflows chain job templates on success or failure — linear or branching,
but always defined in YAML with a fixed graph. AO adds:

- A **visual canvas** — drag nodes, connect them, run the result
- **Conditional logic nodes** that branch on a previous step's output
- **Approval nodes** with configurable policies — who approves, how many, what
  happens on timeout
- A **Temporal-based execution engine** — workflow state is durable and survives
  pod restarts
- **Cross-platform potential** — the node type catalog includes HTTP request,
  script, and integrations beyond AAP

> **"If your workflows are linear chains of job templates, AAP's built-in
> workflow visualizer is enough. AO earns its place when the orchestration needs
> conditionals, human gates, or when the audience wants to see the sequence
> before trusting it."**

Sources:
[GA blog](https://www.redhat.com/en/blog/unify-it-workflows-scale-new-automation-orchestrator-ansible-automation-platform),
[Add AAP to workflows](https://docs.redhat.com/en/documentation/automation_orchestrator/2026.8/develop-add_ansible_automation_platform_to_automation_orchestrator_workflows),
[Node type catalog](https://docs.redhat.com/en/documentation/automation_orchestrator/2026.8/reference-node_type_catalog)

---

## "Do we have to migrate our job templates?"

**No.** AO connects to AAP as an integration and sees every job template the
connected credential can see. On sandbox, that is 33 templates — every one this
repo defines. No migration, no duplication. Your templates stay in AAP, where
they are version-controlled and tested.

> **"AO orchestrates your existing templates. It does not replace them or copy
> them."**

Source:
[GA blog](https://www.redhat.com/en/blog/unify-it-workflows-scale-new-automation-orchestrator-ansible-automation-platform)

---

## "Is it GA?"

**Yes.** Version 2026.8, generally available as an add-on to AAP 2.7 or later.

The May 2026 Red Hat Summit press release said "technology preview". The August
GA release superseded that. If someone cites the press release, point them to:

- [Release notes](https://docs.redhat.com/en/documentation/automation_orchestrator/2026.8/whats_new-automation_orchestrator_release_notes)
- [GA blog](https://www.redhat.com/en/blog/unify-it-workflows-scale-new-automation-orchestrator-ansible-automation-platform) (2026-08-21)

---

## "What does it cost to run?"

Measured on sandbox (cluster-kbjvc): **1.91 vCPU** and **2.47 GiB** of
requested resources. Nine AO pods (backend x2, UI x2, worker x2,
background-worker, temporal, redis) plus one PostgreSQL instance with a 10Gi
PVC. That is roughly the footprint of two medium demo VMs.

Source: `playbooks/install_ao.yml`, measured in
[#141](https://github.com/ericcames/sales.demos/issues/141)

---

## "Where does its data live?"

Its own CloudNativePG PostgreSQL cluster — three databases:

| Database | Purpose |
|---|---|
| `ao_backend` | Application state |
| `ao_temporal` | Workflow execution engine |
| `temporal_visibility` | Temporal's visibility store — fixed name, not documented in the CRD |

**Deliberately not in AAP's database.** AAP's postgres is owned by the AAP
operator with `blockOwnerDeletion`, so databases added to it live inside
something another operator recreates at will. Temporal is write-heavy, and
putting that load on the database the whole demo platform depends on trades a
working AAP for a working AO.

Source: `playbooks/install_ao.yml` header comment,
[#141](https://github.com/ericcames/sales.demos/issues/141)

---

## "Where are the credentials?"

> **"Four credentials, all created by automation, none in a tracked file."**

| Credential | Where it lives | How it is created |
|---|---|---|
| AO admin password | Kubernetes Secret `ao-admin-password` | `install_ao.yml` — seeded from `aap_password`, so the two match |
| OIDC client | AAP OAuth2 application named "Syntara" | `configure_ao.yml` — `POST setup_aap_oidc` |
| AAP integration credential | AO's database | `configure_ao.yml` — `POST /credentials` |
| MCP server token | Operator's local Claude config (not tracked) | `make-ao-mcp.sh` — gateway personal access token |

Source: `playbooks/configure_ao.yml`, `playbooks/install_ao.yml`

---

## "Is it really idempotent?"

**The install and configure playbooks are.** The one exception: `POST
setup_aap_oidc` returns 502 if the OAuth2 application "Syntara" already exists
on AAP. The playbook checks for an existing identity provider first and skips
the call — so a second run is safe, it just cannot self-heal a half-created OIDC
setup.

> **"If the OIDC setup is partially broken, delete the 'Syntara' OAuth
> application in AAP's gateway UI and re-run the configure playbook."**

Source: `playbooks/configure_ao.yml` header, lines 29-31

---

## "What happens when it breaks?"

**The most common failure is the SSRF allowlist.** AO uses `langchain_core`'s
SSRF protection to block private IP addresses on integration URLs, and the AAP
hostname resolves to a private IP from inside the cluster. The configure
playbook patches `APP_INTEGRATION_URL_ALLOWED_HOSTS` on the `ao-backend`
deployment. If the operator reconciles and drops it, re-run the configure
playbook.

| Symptom | Fix |
|---|---|
| AO login page loads but "Log in with AAP" fails | Re-run `configure_ao.yml` — the SSRF allowlist was reconciled away |
| AO shows 0 job templates | Re-run `configure_ao.yml` — the integration credential or allowlist is stale |
| AO is unreachable (503 / no Route) | Re-run `AAP Ecosystem - Deploy Automation Orchestrator` — it converges |
| Database gone | `oc delete namespace automation-orchestrator` and re-deploy from scratch |

---

## "Who can launch this?"

Anyone who can launch a workflow in AAP. The `AAP Ecosystem - Deploy Automation
Orchestrator` workflow needs the `Sales Demos - Vault` and `Sales Demos - Env
Secrets` credentials, which are scoped to the `IT Service Automation`
organization.

---

## "Can I have it?"

> **"Yes. The playbooks are in a public repository."**

The only prerequisites are an AAP 2.7 or later subscription and an OpenShift
cluster with the Automation Orchestrator operator available in the catalog.
`playbooks/install_ao.yml` and `playbooks/configure_ao.yml` are the whole
install. The operator is separately subscribed — "Red Hat Ansible Automation
Orchestrator" — but installs under the environment's existing pull secret with
no extra credential.

---

## Questions to ask *them*

**After the canvas beat:**

- "What does your approval process look like today — Slack messages, email
  threads, or something else?"

**Before the close:**

- "Is the next conversation about orchestrating your existing AAP workflows, or
  about bringing in systems AAP does not manage today?" — this reveals whether
  the next meeting is technical (more integrations) or organizational
  (adoption). They are very different meetings.

---

## Things not to say

- Do not say "replaces AAP workflows" — it orchestrates them, it does not
  replace them
- Do not say "AI-powered" unless they ask about the LLM integration — it is not
  wired up in this demo
- Do not compare to ServiceNow Orchestrator, Camunda, or Temporal directly —
  let them make the comparison
- Do not promise EDA integration — it exists in the interactive demo but is not
  wired up here
- Do not claim the login page can be branded — it cannot; `#426` confirmed AO
  has no `custom_login_info` or `custom_logo` equivalent
