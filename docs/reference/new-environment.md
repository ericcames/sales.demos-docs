# New environment

Repointing [sales.demos](https://github.com/ericcames/sales.demos) at a fresh
RHDP cluster after the old one expires. About 15 minutes of operator work, then
10 minutes of automation.

This page assumes [first-time setup](first-time-setup.md) is already done — the
vault, collections, CLI tools, and `~/.ansible.cfg` token are in place. If any
of those are missing, do that page first.

It also assumes you are tracking the upstream repo, not a fork. If you forked
and want to point at your own cluster, see
[Reusing this repo](reusing-this-repo.md) instead — the mechanism is different
(`connection.yml` on your branch, not `local.yml`).

!!! info "Scope: RHDP environments only"
    This covers `sandbox` and `demo` — ephemeral RHDP environments that expire
    and get replaced. `edge` is a persistent bare-metal SNO on a home network;
    it is rebuilt deliberately, not rotated by RHDP expiry. The same playbooks
    target it via `--limit edge`, but the "environment expired" trigger does not
    apply.

---

## What changes and what does not

| Changes | Stays the same |
|---|---|
| Cluster hostnames (3 values) | Vault password |
| `aap_password` | `rhsm_org_id` / `rhsm_activation_key` |
| `openshift_api_token` | `demo_ssh_private_key` |
| Kubeconfig | Collections, CLI tools, `~/.ansible.cfg` |
| AAP MCP token and URL | Everything in first-time setup |

---

## Phase A — Update sources of truth

Two inputs to update: `local.yml` (cluster identity) and the vault
(credentials).

### 1. `local.yml`

Create or edit the gitignored overlay for the environment you are repointing.
If it does not exist yet, copy the example:

```bash
ENV=sandbox   # or demo
cp inventory/group_vars/$ENV/local.yml.example \
   inventory/group_vars/$ENV/local.yml
```

Fill in three values from the RHDP provisioning email or the environment's
OpenShift console:

```yaml
aap_hostname: "aap-aap.apps.cluster-<id>.dyn.redhatworkshops.io"
openshift_api_url: "https://api.cluster-<id>.dyn.redhatworkshops.io:6443"
openshift_apps_domain: "apps.cluster-<id>.dyn.redhatworkshops.io"
```

Also set `demo_ssh_public_key` if this is a fresh `local.yml`. The matching
private key is in the vault.

!!! danger "The name must be `local.yml`"
    `connection.local.yml` sorts *before* `connection.yml` and therefore loses:
    it would be loaded, silently overridden, and leave you on the committed
    cluster.

### 2. Vault credentials

Two keys under `env_secrets.<env>`:

| Key | Where to get it |
|---|---|
| `aap_password` | RHDP provisioning email |
| `openshift_api_token` | OpenShift console → *Copy login command* → the `sha256~` or `eyJ` value |

```bash
ansible-vault edit playbooks/group_vars/all/secrets.yml \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

**RHDP tokens are short-lived.** Expect to refresh `openshift_api_token` far
more often than anything else on this page.

---

## Phase B — Verify reachability

Both must succeed before proceeding. No credentials needed.

```bash
# AAP gateway
curl -sk https://<aap_hostname>/api/gateway/v1/ping/
# Expect: {"status":"good","version":"2.7",...}

# OpenShift API
curl -sk https://api.cluster-<id>.dyn.redhatworkshops.io:6443/healthz
# Expect: ok
```

!!! warning "A new RHDP environment can take hours to settle"
    A freshly provisioned environment can peg CPU and flap `503` for hours,
    then fix itself. If the ping fails on a brand-new environment, wait and
    retry before debugging.

---

## Phase C — Regenerate derived files

Three utilities, in this order. Each depends on the one before it.

### 1. Propagate `local.yml` into `connection.yml`

AAP reads `connection.yml` from its SCM checkout — `local.yml` is gitignored
and invisible to it. This script bridges the gap
([#513](https://github.com/ericcames/sales.demos/issues/513)):

```bash
bash utilities/update-connection.sh $ENV
```

It reports which keys changed and their old/new values.

### 2. Regenerate kubeconfig

Synthesises a per-environment kubeconfig from `connection.yml` (plaintext API
URL) and the vault (encrypted API token):

```bash
bash utilities/make-kubeconfig.sh $ENV
```

**Output:** `.kube/<env>.kubeconfig` (repo-local, gitignored, `0600`).

### 3. Regenerate AAP MCP token

Creates a personal access token via the AAP gateway API and writes the
credential files the stdio bridge needs:

```bash
bash utilities/make-aap-mcp.sh $ENV
```

**Output:** `.aap/<env>.token` and `.aap/<env>.url` (gitignored, `0600`).

!!! warning "Requires the AAP MCP server to be deployed"
    `make-aap-mcp.sh` discovers the MCP route via `oc get route aap-mcp`. On
    a repoint the server is already running and this works immediately. On a
    **fresh** environment the server does not exist yet — run Phase E first
    (which includes `mcp_server.yml`), then come back here.

---

## Phase D — Connect MCP servers

Start Claude Code (or restart it if it is already running). Startup discovery
reads the credential files from Phase C and connects all five servers:

| Server | Credential source |
|---|---|
| `openshift-sandbox` | `.kube/sandbox.kubeconfig` |
| `openshift-demo` | `.kube/demo.kubeconfig` |
| `openshift-edge` | `.kube/edge.kubeconfig` |
| `aap-sandbox` | `.aap/sandbox.token` + `.aap/sandbox.url` |
| `aap-demo` | `.aap/demo.token` + `.aap/demo.url` |

**Credential files must exist before Claude Code starts.** Claude Code does
startup discovery for all `.mcp.json` servers; a server that fails at startup
stays failed for the session. If the files already existed before this session
started, no restart is needed — Claude Code spawns the stdio bridge on demand.

Verify by calling a tool on the server you just repointed:

```
mcp__aap-<env>__me_list
mcp__openshift-<env>__namespaces_list
```

The first should return the admin user; the second should list namespaces on the
new cluster.

---

## Phase E — Set up the cluster

Two steps, by design. `config.yml` creates the job templates, so it cannot be
one of them — it runs from the laptop. Everything else runs from AAP, which is
the product being sold.

### 1. Apply configuration from the laptop

```bash
mkdir -p ~/ansible-logs
export ANSIBLE_LOG_PATH=~/ansible-logs/config-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/config.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

This creates the organization, project, credentials, inventories, job templates,
schedules, execution environment mirror, and gateway branding.

### 2. Run Cluster Day 0 from AAP

Launch the **Cluster Day 0** workflow from the AAP UI. It installs OpenShift
Virtualization, links the RHEL 9 CIS L1 golden image, and verifies the
environment (boot source, csi-clone, ingress, test VM build and timing).

!!! warning "`connection.yml` must be committed before AAP jobs work"
    AAP reads the SCM checkout, not `local.yml`. If `connection.yml` still
    points at the old cluster, job templates fail with a DNS or `401` error.
    Run `update-connection.sh` (Phase C step 1), commit, push, and sync the
    AAP project before launching.

---

## Phase F — Measure memory budget

```bash
export ANSIBLE_LOG_PATH=~/ansible-logs/probe-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/probe_env.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Or use
[`/sales-demos-probe-env`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-probe-env/SKILL.md).

Update `local.yml` with the reported `available_memory_gb` value, then
propagate it:

```bash
bash utilities/update-connection.sh $ENV
```

---

## Phase G — Commit the repoint

Only `connection.yml` needs committing. The vault is local-only and `local.yml`
is gitignored.

```bash
git add inventory/group_vars/$ENV/connection.yml
git commit -m "fix: repoint $ENV to cluster-<id>"
git push
```

Then sync the AAP project so job templates pick up the new cluster identity.
From the AAP UI: **Projects → Sales Demos → Sync**, or via MCP:

```
mcp__aap-<env>__projects_list
```

---

## Compact checklist

For repeat use. Every command assumes `ENV` is set.

```bash
ENV=sandbox

# A — sources of truth
vi inventory/group_vars/$ENV/local.yml          # 3 URLs + SSH key
ansible-vault edit playbooks/group_vars/all/secrets.yml \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
                                                # aap_password + openshift_api_token

# B — reachability
curl -sk "https://$(grep aap_hostname inventory/group_vars/$ENV/local.yml \
  | awk -F'"' '{print $2}')/api/gateway/v1/ping/"

# C — derived files
bash utilities/update-connection.sh $ENV
bash utilities/make-kubeconfig.sh $ENV
bash utilities/make-aap-mcp.sh $ENV             # needs MCP server deployed

# D — MCP servers
# restart Claude Code (or start fresh)

# E — cluster setup
ansible-playbook playbooks/config.yml -i inventory --limit $ENV \
  -e target_env=$ENV --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
# commit + push connection.yml, sync AAP project, launch Cluster Day 0

# F — memory budget
ansible-playbook playbooks/probe_env.yml -i inventory --limit $ENV \
  -e target_env=$ENV --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
# update local.yml with available_memory_gb, then:
bash utilities/update-connection.sh $ENV

# G — commit
git add inventory/group_vars/$ENV/connection.yml
git commit -m "fix: repoint $ENV to cluster-<id>"
git push
```
