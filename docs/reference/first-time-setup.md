# First-time setup

One-time, per-machine setup for using
[sales.demos](https://github.com/ericcames/sales.demos) from a laptop. About
10 minutes. After this, go straight to [`/sales-demos-setup`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-setup/SKILL.md).

This page is the full reference — every prerequisite, every verification
command.
[`/sales-demos-first-time`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-first-time/SKILL.md)
is the same thing as a Claude Code skill that runs each step interactively.

!!! note "Scope"
    This covers laptop prerequisites only. Pointing at a specific RHDP
    environment and provisioning demo VMs are separate steps that come after.

---

## What setup covers

1. Automation Hub token
2. Vault password and secrets file
3. Pinned collections
4. Python kubernetes client
5. CLI tools
6. Run-log directory
7. Environment values
8. Validation

Estimated time: ~10 minutes.

---

## Step 0 — Audit what already exists

Read-only. Run the whole block, then work only on what is `MISSING` or
`PROBLEM`.

```bash
test -f ~/.ansible.cfg && grep -q 'galaxy_server.rh_certified' ~/.ansible.cfg \
  && echo "EXISTS   Hub token in ~/.ansible.cfg" || echo "MISSING  Hub token"
test -s "${SALES_DEMOS_VAULT_PASS:-$HOME/secrets/.vault_pass_sales_demos}" \
  && echo "EXISTS   vault password" || echo "MISSING  vault password  <-- blocker"
test -f playbooks/group_vars/all/secrets.yml \
  && echo "EXISTS   secrets.yml" || echo "MISSING  secrets.yml  <-- blocker, build it from the .example"
test -f ansible.cfg \
  && echo "PROBLEM  project-local ansible.cfg present" || echo "OK       no project-local ansible.cfg"
ansible-galaxy collection list kubernetes.core 2>/dev/null | grep -q kubernetes.core \
  && echo "EXISTS   collections" || echo "MISSING  collections"
python3 -c "import kubernetes" 2>/dev/null \
  && echo "EXISTS   python kubernetes client" || echo "MISSING  python kubernetes client"
test -d ~/ansible-logs \
  && echo "EXISTS   ~/ansible-logs" || echo "MISSING  ~/ansible-logs"
command -v oc >/dev/null \
  && echo "EXISTS   oc" || echo "MISSING  oc"
ls inventory/group_vars/*/local.yml >/dev/null 2>&1 \
  && echo "EXISTS   local.yml override(s) — you have repointed at least one env" \
  || echo "NONE     no local.yml — you will run against the committed clusters"
```

If you see `PROBLEM  project-local ansible.cfg present`, delete that file
before continuing — it shadows `~/.ansible.cfg` and breaks certified collection
installs (see step 1).

---

## Step 1 — Automation Hub token

`~/.ansible.cfg` needs three galaxy server stanzas — certified, validated, and
community. The `rh_certified` token does two jobs: it is what `ansible-galaxy`
uses to install Red Hat certified collections, **and** it is read at run time as
`automation_hub_token` via an `ini` lookup in
`inventory/group_vars/aap/main.yml`. One copy, no second in the vault to go
stale. The same token authenticates both `rh_certified` and `rh_validated`.

```bash
grep -A3 'galaxy_server.rh_certified' ~/.ansible.cfg | grep -qE '^token=.+' \
  && echo "token present" || echo "no token"
```

If missing, get one from **console.redhat.com → Automation Hub → Connect to
Hub → Load token**, then the whole file should look like this:

```ini title="~/.ansible.cfg"
[defaults]
stdout_callback = protect_data

[callback_protect_data]
sensitive_keywords = vault,pwd,pass,password,secret,token,key

[galaxy]
server_list = rh_certified, rh_validated, community

[galaxy_server.rh_certified]
url=https://console.redhat.com/api/automation-hub/content/published/
auth_url=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
token=<your token>

[galaxy_server.rh_validated]
url=https://console.redhat.com/api/automation-hub/content/validated/
auth_url=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
token=<your token>

[galaxy_server.community]
url=https://galaxy.ansible.com/
```

Use `~/.ansible.cfg`, **not** `~/.ansible/ansible.cfg`. The latter is a stale
leftover on some machines.

!!! danger "Never create a project-local `ansible.cfg`"
    Ansible picks one cfg file and does not merge. A local one shadows
    `~/.ansible.cfg`, which holds the working Automation Hub token, and breaks
    `ansible-galaxy collection install` for Red Hat certified content. Set
    options via CLI flags or environment variables instead.

---

## Step 2 — Vault password and secrets file

`playbooks/group_vars/all/secrets.yml` is **not in this repo**. It is
gitignored
([#130](https://github.com/ericcames/sales.demos/issues/130)),
because the repo is public and shipping one person's encrypted credentials
would hand everyone else a blob they cannot decrypt and cannot replace without
diverging from upstream. Without this file every playbook fails at the first
templated credential.

Work out which situation you are in:

```bash
test -f playbooks/group_vars/all/secrets.yml \
  && echo "file present — you need the password that matches it (case B)" \
  || echo "no file — you are building one (case A)"
```

### Case A — fresh machine

You create both the file and the password. There is nothing to ask anyone for.

```bash
mkdir -p ~/secrets && chmod 700 ~/secrets
printf '%s\n' '<a long random passphrase>' > ~/secrets/.vault_pass_sales_demos
chmod 600 ~/secrets/.vault_pass_sales_demos

cp playbooks/group_vars/all/secrets.yml.example \
   playbooks/group_vars/all/secrets.yml
```

Fill in real values. `playbooks/group_vars/all/secrets.yml.example` documents
every key and where to get it, and CI keeps it honest —
`utilities/check-secrets-example.py` fails the build if the code reads a key
the example does not declare
([#128](https://github.com/ericcames/sales.demos/issues/128)). Then encrypt:

```bash
ansible-vault encrypt playbooks/group_vars/all/secrets.yml \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

!!! warning "The vault-id label matters"
    The `sales.demos` label is baked into the file's header, and
    `inventory/group_vars/aap/controller_credentials.yml` builds the AAP Vault
    credential against that exact label. Encrypt with a different label and AAP
    will not use the credential.

### Case B — inherited environment

You need **both** the encrypted file and the matching password from the person
who shared the environment. Get them over a private channel — never in an
issue, a PR, or this repo.

### Verify

```bash
ansible-vault view playbooks/group_vars/all/secrets.yml \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos >/dev/null 2>&1 \
  && echo "vault password works" \
  || echo "decryption failed — wrong password, or the file was encrypted with a different vault-id"
```

**Back up both the file and the password.** Since
[#130](https://github.com/ericcames/sales.demos/issues/130) neither is in git,
so nothing can restore them.

If you keep vault passwords somewhere other than `~/secrets/`, export
`SALES_DEMOS_VAULT_PASS` with the full path. One variable moves both consumers
that read the file — `utilities/make-kubeconfig.sh` and the AAP Vault
credential built by `inventory/group_vars/aap/main.yml` — so they cannot
disagree
([#131](https://github.com/ericcames/sales.demos/issues/131)). Every command
on this page uses the default path.

---

## Step 3 — Collections

Collections install from `collections/requirements.yml` to
`~/.ansible/collections`. Every collection is pinned to an exact version and
they are never vendored into the repo.

With Claude Code:

```
/sales-demos-collections-sync
```

Without:

```bash
ansible-galaxy collection install -r collections/requirements.yml
```

Verify:

```bash
ansible-galaxy collection list kubernetes.core
```

Your laptop's collections and what the execution environment bakes in are two
different dependency sets — see
[Execution environment](execution-environment.md) for the distinction and how
to verify a playbook against the image AAP actually runs.

---

## Step 4 — Python kubernetes client

`kubernetes.core` needs the `kubernetes` Python library under the same
interpreter that runs `ansible-playbook`:

```bash
python3 -c "import kubernetes" && echo "installed" || pip install --user kubernetes
```

The inventory pins `ansible_python_interpreter` to
`{{ ansible_playbook_python }}` so that discovery cannot pick a different
interpreter that lacks this library.

---

## Step 5 — CLI tools

Ansible collections are not enough. Three binaries are hard requirements, and a
machine without them passes every other step here and still cannot provision a
VM.

| Tool | Required? | Used by |
|---|---|---|
| `oc` | Yes | Playbooks, skills, getting API tokens |
| `terraform` | Yes | `provision_vm.yml`, `teardown.yml` |
| `virtctl` | Yes | SSH into demo VMs from a laptop |
| `podman` + `ansible-builder` | EE builds only | `build-ee.sh` |
| `npx` / `node` | MCP servers only | [`/sales-demos-mcp`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-mcp/SKILL.md) |

```bash
command -v oc >/dev/null && echo "oc: $(oc version --client 2>/dev/null | head -1)" \
  || echo "oc missing — download from the OpenShift console CLI tools page"

command -v terraform >/dev/null && echo "terraform: $(terraform version | head -1)" \
  || echo "terraform missing — https://developer.hashicorp.com/terraform/install"

command -v virtctl >/dev/null && echo "virtctl: present" \
  || echo "virtctl missing — download from the OpenShift console CLI tools page"

command -v podman >/dev/null && echo "podman: $(podman --version)" \
  || echo "podman missing (only needed for EE builds)"

command -v ansible-builder >/dev/null && echo "ansible-builder: present" \
  || echo "ansible-builder missing (only needed for EE builds)"

command -v npx >/dev/null && echo "npx: $(node --version)" \
  || echo "npx missing (only needed for /sales-demos-mcp)"
```

`oc`, `terraform` and `virtctl` are the three that block real work. The others
are optional — `podman` and `ansible-builder` only matter if you rebuild the
execution environment, and `npx` only for the MCP servers (upstream also
publishes a
[standalone binary](https://github.com/containers/kubernetes-mcp-server/releases)
if you prefer not to install Node).

If you plan to build the execution environment, also confirm you are logged
into `registry.redhat.io`:

```bash
podman login --get-login registry.redhat.io >/dev/null 2>&1 \
  && echo "logged in" || echo "not logged in — run: podman login registry.redhat.io"
```

---

## Step 6 — Run-log directory

Phase 0 takes 10–20 minutes. If it fails and the terminal is gone, so is the
evidence.

```bash
mkdir -p ~/ansible-logs
```

Logs live outside the repo on purpose — the repo is public. Every run should
set:

```bash
export ANSIBLE_LOG_PATH=~/ansible-logs/sales-demos-$(date +%F).log
```

**Do not pipe through `tee`** — it masks the exit status from
`ansible-playbook`. See [Running playbooks](running-playbooks.md) for the full
explanation.

---

## Step 7 — Environment values

Two places, by design. Non-secrets are committed in `connection.yml`;
credentials live in the vaulted `secrets.yml`.

### Connection values

```bash
ENV=${ENV:-sandbox}
ansible -i inventory --limit "$ENV" aap -m debug \
  -a 'msg={{ aap_hostname }}' 2>/dev/null | grep msg
```

That prints the value actually in effect. `connection.yml` ships with a working
RHDP cluster — there are no placeholders — so grepping the file tells you
nothing about whether it is *yours*.

If the hostname is not your environment, **ask where you will run from before
changing anything** — there are two correct answers and they are not
interchangeable
([#166](https://github.com/ericcames/sales.demos/issues/166)):

| You will run from | Change |
|---|---|
| `ansible-playbook` on this laptop | A gitignored `local.yml` overlay — you keep pulling upstream without conflicts |
| AAP job templates | `connection.yml`, committed on your own branch — gitignored files are not in the SCM checkout AAP runs from |

Most people setting up a laptop want the first. Create the overlay beside
`connection.yml`, holding only the keys that differ:

```bash
cat > inventory/group_vars/$ENV/local.yml <<'YAML'
---
aap_hostname: "aap-aap.apps.cluster-<id>.dyn.redhatworkshops.io"
openshift_api_url: "https://api.cluster-<id>.dyn.redhatworkshops.io:6443"
openshift_apps_domain: "apps.cluster-<id>.dyn.redhatworkshops.io"
YAML
```

The filename must be `local.yml` — files in a `group_vars/` directory load in
sorted order and the last wins. `connection.local.yml` sorts *before*
`connection.yml` and would be silently ignored.

The full explanation — including the AAP path, forking, and repointing — is in
[Reusing this repo](reusing-this-repo.md). The three environments (`sandbox`,
`demo`, `edge`) and their postures are described in
[Environments](environments.md).

### Credentials in the vault

```bash
ansible-vault edit playbooks/group_vars/all/secrets.yml \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Set `env_secrets.<env>.aap_password` (from the RHDP provisioning email) and
`env_secrets.<env>.openshift_api_token` (from the OpenShift console's "Copy
login command"). RHDP bearer tokens are short-lived — expect to refresh
`openshift_api_token` far more often than anything else here.

`playbooks/group_vars/all/secrets.yml.example` documents every key and where
to get its value.

---

## Step 8 — Validate

Do not declare success until both of these pass. Together they exercise the
real path: inventory resolution, the vault, and the `ini` lookup.

**It takes two commands, and that is not an accident**
([#86](https://github.com/ericcames/sales.demos/issues/86)). The two kinds of
value live in two different `group_vars/` directories:

- `aap_env_name`, `aap_hostname`, `automation_hub_token` come from
  `inventory/group_vars/`, which sits beside the inventory.
- `aap_password` and `openshift_api_token` come from `env_secrets` in
  `playbooks/group_vars/all/secrets.yml`, which sits beside the playbooks.

An ad-hoc `ansible` command has no playbook, so it never loads the second
directory. Trying to read all values in one call dies with
`'env_secrets' is undefined` — by design.

```bash
ENV=${ENV:-sandbox}
VAULT_ID="sales.demos@$HOME/secrets/.vault_pass_sales_demos"

# 1. Inventory-resolved values, plus the ini lookup into ~/.ansible.cfg.
ansible -i inventory --limit "$ENV" aap -m debug --vault-id "$VAULT_ID" \
  -a 'msg="env={{ aap_env_name }} host_set={{ aap_hostname is defined }} hub_set={{ automation_hub_token | length > 20 }}"'
```

`env` must match what you asked for and both `_set` values must be `True`.

```bash
# 2. Vaulted credentials, read through the vault rather than the inventory.
ansible-vault view playbooks/group_vars/all/secrets.yml --vault-id "$VAULT_ID" \
  | ENV="$ENV" python3 -c '
import sys, yaml, os
env = os.environ["ENV"]
doc = yaml.safe_load(sys.stdin) or {}
e = (doc.get("env_secrets") or {}).get(env, {})
def filled(v):
    return bool(v) and "CHANGEME" not in str(v)
pw = e.get("aap_password", "")
tok = e.get("openshift_api_token", "")
pw_set = filled(pw)
token_ok = tok.startswith("sha256~") or (tok.startswith("eyJ") and "." in tok)
rhsm_ok = filled(doc.get("rhsm_org_id")) and filled(doc.get("rhsm_activation_key"))
print("env=%s pw_set=%s token_ok=%s rhsm_ok=%s" % (env, pw_set, token_ok, rhsm_ok))
'
```

All three must be `True`. `token_ok` checks the shape rather than mere
presence — a value that is non-empty but not a recognised token form will fail
later as a confusing `401`. Both `sha256~` OAuth tokens and `eyJ`
ServiceAccount JWTs are accepted.

`rhsm_ok` is checked here because it fails late and far from its cause.
`rhsm_org_id` and `rhsm_activation_key` are top-level keys (not
per-environment) and nothing needs them until Phase 4 registers a guest. Get
them from **console.redhat.com → Inventory → System Configuration →
Activation Keys**.

---

## What comes next

With Claude Code, run [`/sales-demos-setup`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-setup/SKILL.md) to install OpenShift Virtualization and
apply the AAP configuration. Without it, run the playbook directly — see
[Running playbooks](running-playbooks.md) for the command and the flags it
requires.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Decryption failed` | Wrong vault password | Re-check with the verify command in step 2 |
| `Attempting to decrypt but no vault secrets found` | `--vault-id` missing from command | Add `--vault-id sales.demos@~/secrets/.vault_pass_sales_demos` |
| `couldn't resolve module/action` | Collections not installed | Step 3 |
| `Failed to import the required Python library (kubernetes)` | Wrong interpreter or missing client | Step 4 |
| Certified collection install 401 | Hub token missing or stale | Step 1 |
| `env=` shows wrong environment | Wrong `--limit` value | Use `--limit sandbox` or `--limit demo` |
| `'env_secrets' is undefined` | Running an ad-hoc command without a playbook | Expected — use the two-command validation in step 8 |
| `Invalid filename: 'None'` from ini lookup | `~/.ansible.cfg` missing or project-local `ansible.cfg` shadowing it | Delete the project-local file; check step 1 |
