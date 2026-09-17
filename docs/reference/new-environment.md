# New environment

Standing up a fresh RHDP cluster after the old one expires. When an RHDP
environment expires, the replacement is a bare cluster — nothing from the old
environment carries over. About 15 minutes of operator work, then 20 minutes of
automation.

This page assumes [first-time setup](first-time-setup.md) is already done — the
vault, collections, CLI tools, and `~/.ansible.cfg` token are in place. If any
of those are missing, do that page first.

No push access is needed. Your cluster identity lives in a gitignored
`local.yml`, and `config.yml` writes it into the AAP inventory as host
variables, so AAP job templates target the new cluster without a commit. The
optional commit steps below only refresh `connection.yml` as the upstream
reference for fresh clones. See [Reusing this repo](reusing-this-repo.md) for
the full clone-vs-fork guide.

!!! info "Scope: RHDP environments only"
    This covers `sandbox` and `demo` — ephemeral RHDP environments that expire
    and get replaced. `edge` is a persistent bare-metal SNO on a home network;
    it is rebuilt deliberately, not rotated by RHDP expiry. The same playbooks
    target it via `--limit edge`, but the "environment expired" trigger does not
    apply.

---

## Quick start

This is the whole procedure with Claude Code. The phases below are what
[`/sales-demos-bootstrap`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-bootstrap/SKILL.md) does for you, written out for when you want to run a piece by hand.

**1. Copy three values from the RHDP environment page.**

| Value | Where it goes |
|---|---|
| AAP URL — `https://aap-aap.apps.cluster-<id>.dyn.redhatworkshops.io` | The prompt in step 3. The cluster ID in it gives the API URL and apps domain. |
| AAP admin password | The vault, `env_secrets.<env>.aap_password` (step 2) |
| kubeadmin password | The vault, `env_secrets.<env>.kubeadmin_password` (step 2). `openshift_api_token` is derived from it — never pasted. |

**2. Put the two passwords in the vault.** Run this in a terminal in your
`sales.demos` checkout. The prompts hide what you type, so it needs a real
terminal, and the passwords never enter a Claude transcript. Press Enter on a
prompt to keep the value already there.

```bash
bash utilities/set-env-passwords.sh sandbox
```

**3. Paste the prompt into Claude Code**, started in the `sales.demos`
checkout. Replace `sandbox` with `demo` if that is the environment, and the URL
with yours:

```text
/sales-demos-bootstrap sandbox https://aap-aap.apps.cluster-<id>.dyn.redhatworkshops.io
```

It writes `local.yml`, derives the API token, runs `setup.yml` (~25–30
minutes), connects the MCP servers, and tells you when to restart Claude Code.

!!! warning "Never paste a password into the prompt"
    Anything in the prompt is kept in the session transcript. The passwords
    belong in step 2; the URL is the only value the prompt needs.

---

## What changes and what does not

| Changes | Stays the same |
|---|---|
| Cluster hostnames (3 values) | Vault password |
| `aap_password`, `kubeadmin_password` | `rhsm_org_id` / `rhsm_activation_key` |
| `openshift_api_token` (derived) | `demo_ssh_private_key` |
| `available_memory_gb` | Collections, CLI tools, `~/.ansible.cfg` |
| Kubeconfig | Everything in first-time setup |
| AAP MCP token and URL | |

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

Two keys under `env_secrets.<env>`, both from the RHDP environment page:

| Key | Where to get it |
|---|---|
| `aap_password` | AAP admin password |
| `kubeadmin_password` | OpenShift kubeadmin password |

```bash
bash utilities/set-env-passwords.sh $ENV
```

Then derive `openshift_api_token` from `kubeadmin_password` — it needs the
`local.yml` from step 1, because it logs in to that cluster:

```bash
bash utilities/derive-ocp-token.sh $ENV --update-vault
```

Do not copy the token from the OpenShift console. The RHDP portal renders it
with em dashes in place of hyphens, which corrupts the JWT
([#559](https://github.com/ericcames/sales.demos/issues/559)). If derivation
fails with a 401, `kubeadmin_password` is still the old environment's — re-run
`set-env-passwords.sh`.

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

`connection.yml` is the committed upstream reference that fresh clones start
from. This script copies your `local.yml` values into it
([#513](https://github.com/ericcames/sales.demos/issues/513)), so collaborators
can commit it once the environment is stable. It is **not** how AAP learns your
cluster — `config.yml` does that in Phase E, from `local.yml` directly (see
[Reusing this repo](reusing-this-repo.md)):

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

**Output:** `.kube/<env>.kubeconfig` (repo-local, gitignored, `0600`). A copy
is also written to `~/.kube/<env>.kubeconfig` for tools outside the repo.

### 3. Regenerate AAP MCP token

Creates a personal access token via the AAP gateway API and writes the
credential files the stdio bridge needs:

```bash
bash utilities/make-aap-mcp.sh $ENV
```

**Output:** `.aap/<env>.token` and `.aap/<env>.url` (gitignored, `0600`).

!!! warning "Requires the AAP MCP server to be deployed"
    `make-aap-mcp.sh` discovers the MCP route via `oc get route aap-mcp`.
    RHDP does not ship the MCP server pre-deployed. On a fresh environment,
    run Phase E steps 1–2 first (which deploy the MCP server), then come back
    here. On a repoint where the MCP server is already running, this works
    immediately.

---

## Phase D — Connect MCP servers

Run
[`/sales-demos-mcp`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-mcp/SKILL.md)
to regenerate credentials and verify all MCP servers in one step. Or follow the
manual steps below.

Start Claude Code (or restart it if it is already running). Startup discovery
reads the credential files from Phase C and connects all servers:

| Server | Credential source |
|---|---|
| `openshift-sandbox` | `.kube/sandbox.kubeconfig` |
| `openshift-demo` | `.kube/demo.kubeconfig` |
| `openshift-edge` | `.kube/edge.kubeconfig` |
| `aap-sandbox` | `.aap/sandbox.token` + `.aap/sandbox.url` |
| `aap-demo` | `.aap/demo.token` + `.aap/demo.url` |
| `portal-sandbox` | `.portal/sandbox.token` + `.portal/sandbox.url` |
| `portal-demo` | `.portal/demo.token` + `.portal/demo.url` |

**Credential files must exist before Claude Code starts.** Claude Code does
startup discovery for all `.mcp.json` servers; a server that fails at startup
stays failed for the session. If the files already existed before this session
started, no restart is needed — Claude Code spawns the stdio bridge on demand.

Verify by calling a tool on the server you just repointed:

```
mcp__openshift-<env>__namespaces_list   (fieldSelector=metadata.name=default)
mcp__aap-<env>__me_list
mcp__portal-<env>__fetch-catalog-entities   (limit=1)
```

!!! warning "\"Connected\" does not mean \"Live\""
    A stdio server reports "Connected" if its local process starts — it does
    not prove the remote cluster is alive. Report **Live** only if actual data
    comes back from the tool call above.

---

## Phase E — Set up the cluster

Every bootstrap playbook runs from the laptop — they all target `hosts: aap`,
authenticate via the vault, and use `kubernetes.core` modules. `config.yml`
creates the AAP job templates, so it runs first; the rest use the same
`ansible-playbook` pattern. Once bootstrap is done, the same playbooks are
available as AAP job templates for day-2 use.

### 1. Commit and push `connection.yml` (collaborators only, optional)

This keeps the upstream reference current for fresh clones. It does **not**
repoint AAP — `config.yml` (next step) writes your cluster identity into the AAP
inventory as host variables, and those outrank whatever the checkout carries.
Skip it while the environment is still settling; a stale `connection.yml` during
active work is expected.

```bash
git add inventory/group_vars/$ENV/connection.yml
git commit -m "fix: repoint $ENV to cluster-<id>"
git push
```

!!! info "Cloners: skip this step"
    Without push access there is nothing to do here — the next step carries your
    `local.yml` into AAP. See [Reusing this repo](reusing-this-repo.md).

### 2. Apply configuration from the laptop

```bash
mkdir -p ~/ansible-logs
export ANSIBLE_LOG_PATH=~/ansible-logs/config-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/config.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

This creates the organization, project, credentials, inventories, job templates,
schedules, execution environment mirror, and gateway branding. If you pushed
in step 1, sync the AAP project after the push lands:
**Projects → Sales Demos → Sync**.

### 3. Install OpenShift Virtualization

```bash
export ANSIBLE_LOG_PATH=~/ansible-logs/install-cnv-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/install_cnv.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

### 4. Link the RHEL 9 golden image

```bash
export ANSIBLE_LOG_PATH=~/ansible-logs/link-rhel9-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/link_rhel9_image.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

!!! tip "Windows demos"
    If this environment runs Windows, also run
    `playbooks/link_windows_image.yml` after this step. It pulls from a
    private Quay repo and takes longer than the RHEL 9 link.

### 5. Verify the environment

```bash
export ANSIBLE_LOG_PATH=~/ansible-logs/prepare-env-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/prepare_env.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Checks boot source, csi-clone, ingress, and times a test VM build.

### 6. Deploy the AAP MCP server

```bash
export ANSIBLE_LOG_PATH=~/ansible-logs/mcp-server-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/mcp_server.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Deploys the MCP server CR and creates the `aap-mcp` route that
`make-aap-mcp.sh` needs (Phase C step 3). If you deferred `make-aap-mcp.sh`
earlier, run it now.

### 7. Deploy Automation Orchestrator

```bash
export ANSIBLE_LOG_PATH=~/ansible-logs/install-ao-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/install_ao.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos

export ANSIBLE_LOG_PATH=~/ansible-logs/configure-ao-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/configure_ao.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Installs CloudNativePG, creates the AO databases, deploys the operator, and
connects AO to AAP via OIDC SSO.

### 8. Deploy self-service portal

```bash
export ANSIBLE_LOG_PATH=~/ansible-logs/portal-${ENV}-$(date +%F-%H%M).log

ansible-playbook playbooks/portal.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Deploys Red Hat Developer Hub with the AAP plugin (~11 minutes). After it
completes, the launcher templates are visible in the portal.

!!! note "Helm required"
    `portal.yml` needs the `helm` binary on the laptop. The execution
    environment includes it since
    [#324](https://github.com/ericcames/sales.demos/issues/324).

!!! note "Grafana Cloud"
    No automated deployment exists yet. Alloy and dashboard configuration are
    manual for now.

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

## Phase G — Generate environment URLs

Regenerate the gitignored URL reference file so Claude and operators can look up
every product URL without MCP token lookups
([#525](https://github.com/ericcames/sales.demos/issues/525)):

```bash
ansible-playbook playbooks/generate_env_urls.yml -i inventory --limit $ENV \
  -e target_env=$ENV \
  -e generate_env_urls_with_creds=true \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Or use
[`/sales-demos-env-urls`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-env-urls/SKILL.md).

---

## Phase H — Final commit (collaborators only)

`connection.yml` changed again in Phase F (`available_memory_gb`). Commit and
push so AAP picks up the updated value.

```bash
git add inventory/group_vars/$ENV/connection.yml
git commit -m "fix: update $ENV available_memory_gb after probe"
git push
```

Then sync the AAP project: **Projects → Sales Demos → Sync**, or via MCP:

```
mcp__aap-<env>__projects_list
```

!!! info "Cloners: skip this step"
    `config.yml` already wrote `available_memory_gb` as a host variable in the
    AAP inventory. Re-run `config.yml` after updating `local.yml` with the new
    value to push it to AAP — no commit or push needed.

---

## Compact checklist

For repeat use. Every command assumes `ENV` is set. The `VAULT` shorthand
keeps the lines readable.

```bash
ENV=sandbox
VAULT="--vault-id sales.demos@~/secrets/.vault_pass_sales_demos"
AP="ansible-playbook"
COMMON="-i inventory --limit $ENV -e target_env=$ENV $VAULT"
mkdir -p ~/ansible-logs

# A — sources of truth
vi inventory/group_vars/$ENV/local.yml          # 3 URLs + SSH key
bash utilities/set-env-passwords.sh $ENV         # aap_password + kubeadmin_password
bash utilities/derive-ocp-token.sh $ENV --update-vault   # openshift_api_token

# B — reachability
curl -sk "https://<aap_hostname>/api/gateway/v1/ping/"

# C — derived files
bash utilities/update-connection.sh $ENV
bash utilities/make-kubeconfig.sh $ENV
bash utilities/make-aap-mcp.sh $ENV             # needs MCP server (step E6)

# D — MCP servers
# restart Claude Code, or run /sales-demos-mcp

# E — cluster setup (all from the laptop)
git add inventory/group_vars/$ENV/connection.yml        # collaborators only
git commit -m "fix: repoint $ENV to cluster-<id>"       # skip if cloner
git push                                                # skip if cloner
$AP playbooks/config.yml $COMMON
$AP playbooks/install_cnv.yml $COMMON
$AP playbooks/link_rhel9_image.yml $COMMON
# $AP playbooks/link_windows_image.yml $COMMON          # optional: Windows
$AP playbooks/prepare_env.yml $COMMON
$AP playbooks/mcp_server.yml $COMMON
$AP playbooks/install_ao.yml $COMMON
$AP playbooks/configure_ao.yml $COMMON
$AP playbooks/portal.yml $COMMON                        # needs helm

# F — memory budget
$AP playbooks/probe_env.yml $COMMON
# update local.yml with available_memory_gb, then:
bash utilities/update-connection.sh $ENV

# G — environment URLs
$AP playbooks/generate_env_urls.yml $COMMON -e generate_env_urls_with_creds=true

# H — final commit (collaborators only)
git add inventory/group_vars/$ENV/connection.yml
git commit -m "fix: update $ENV available_memory_gb after probe"
git push
```
