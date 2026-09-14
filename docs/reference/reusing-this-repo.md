# Reusing this repo

[sales.demos](https://github.com/ericcames/sales.demos) is public and meant to
be reusable. Two things stand between a clone and a working demo: pointing it at
*your* cluster, and — only if you want to carry your own code changes — pointing
AAP at *your* fork.

---

## Pointing it at your own environment

`inventory/group_vars/<env>/connection.yml` is committed with working RHDP
values. Those URLs are a documented non-secret here, not an oversight. Three
lines identify a cluster:

```yaml
aap_hostname:          "aap-aap.apps.cluster-<id>.dyn.redhatworkshops.io"
openshift_api_url:     "https://api.cluster-<id>.dyn.redhatworkshops.io:6443"
openshift_apps_domain: "apps.cluster-<id>.dyn.redhatworkshops.io"
```

**One input covers both places you run from: a gitignored `local.yml`.** It
reaches AAP too — not through git, but through `config.yml`.

| You run from | How your `local.yml` values get there |
|---|---|
| A laptop | Ansible loads `local.yml` directly, after `connection.yml` |
| An AAP job template | `config.yml` writes the effective values into the AAP inventory as host variables ([#528](https://github.com/ericcames/sales.demos/issues/528)) |

### From a laptop: the `local.yml` overlay

Create it beside the `connection.yml` you want to change, holding **only the
keys that differ** — not a copy of the file:

```bash
cat > inventory/group_vars/sandbox/local.yml <<'YAML'
---
aap_hostname: "aap-aap.apps.cluster-<id>.dyn.redhatworkshops.io"
openshift_api_url: "https://api.cluster-<id>.dyn.redhatworkshops.io:6443"
openshift_apps_domain: "apps.cluster-<id>.dyn.redhatworkshops.io"
YAML
```

Ansible loads every file in a `group_vars/<group>/` directory in sorted order
and the **last one wins**, so this overrides `connection.yml` with no code
change at all.

**What it buys is conflict avoidance, and that is worth quantifying.** Ten
commits have touched those two files since March, and eighteen of those edits
were to the three identity lines above — roughly monthly, as RHDP environments
are rebuilt. Edit `connection.yml` directly and you conflict on every pull. Keep
your values in `local.yml` and you never do.

!!! danger "The name must be `local.yml`"
    `connection.local.yml` sorts *before* `connection.yml` and therefore loses:
    it would be loaded, silently overridden, and leave you running against the
    committed cluster while believing you had repointed it. Measured, not
    assumed.

Confirm what is actually in effect rather than trusting the file you edited:

```bash
ansible -i inventory --limit sandbox aap -m debug -a 'msg={{ aap_hostname }}'
```

### From AAP: `config.yml` carries `local.yml` for you

A job template gets its playbooks from the SCM project checkout, and a
gitignored file is not in it — so the checkout alone would target the committed
cluster. **You do not fix that by committing `connection.yml`.** Run
`config.yml` from the laptop, where `local.yml` *is* loaded:

```bash
ansible-playbook playbooks/config.yml -i inventory --limit sandbox \
  -e target_env=sandbox \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

`inventory/group_vars/aap/controller_hosts.yml` has it write your cluster
identity — `aap_hostname`, `openshift_api_url`, `openshift_apps_domain`, the
golden image tags, `available_memory_gb`, and a few more — as **host variables**
on the `<env>-local` host in the *Sales Demo VMs* inventory. Host variables
outrank the group variables that arrive from the checkout, and that inventory's
SCM source does not overwrite them on sync, so every job template targets your
cluster. No push, no fork, no conflict on your next pull.

Two things follow:

- **Re-run `config.yml` whenever `local.yml` changes.** AAP only learns your
  values when it runs; editing the file alone changes nothing in AAP.
- **Check the host, not the file.** In AAP, open *Inventories → Sales Demo VMs →
  Hosts → `<env>-local` → Variables* and confirm the hostnames are yours.

Credentials are not among those variables — they still arrive at run time
through the *Sales Demos - Env Secrets* credential.

!!! note "Collaborators with push access"
    `connection.yml` is still the upstream reference for fresh clones, so when
    an environment is stable a collaborator commits it with
    `utilities/update-connection.sh <env>`
    ([#513](https://github.com/ericcames/sales.demos/issues/513)). That is a
    separate, deliberate step — not how you repoint AAP.

---

## Forking

You only need a fork to run **your own changes** — targeting your own cluster
does not need one (see above). If you do fork, four things in the repo name
*that* repo or its author. Two are variables; two are deliberately left alone
([#132](https://github.com/ericcames/sales.demos/issues/132)).

**Point AAP's project at your fork.** This is the one that bites, because
nothing looks wrong when it is missed — AAP happily syncs upstream, and your
changes simply never take effect:

```bash
ansible-playbook playbooks/config.yml -i inventory --limit sandbox \
  -e sales_demos_scm_url=https://github.com/<you>/sales.demos.git
```

**Mirror your own execution environment,** if you build one. Pulls from the
default namespace are public and work for anyone, so this matters only once you
push your own image:

```bash
EE_IMAGE=quay.io/<you>/sales-demos-ee:v1.2.0 ./utilities/build-ee.sh
ansible-playbook playbooks/config.yml -i inventory --limit sandbox \
  -e sales_demos_ee_upstream=<you>/sales-demos-ee
```

Both default to the upstream values, so nothing changes if you ignore them.

| Baked-in identity | Status |
|---|---|
| AAP project `scm_url` | **Variable** — `sales_demos_scm_url` |
| PAH EE `upstream_name` | **Variable** — `sales_demos_ee_upstream` |
| `EE_IMAGE` in `utilities/build-ee.sh` | Already env-overridable |
| `linux_configure_repo_url` (demo page footer) | Already a role default — override it in `group_vars`; CI fails if `render-demo-assets.py` is not updated to match |
| `.github/CODEOWNERS` | **Left alone.** Correct for the upstream repo; a fork's own to rewrite |

If your vault password lives somewhere other than the default path, export
`SALES_DEMOS_VAULT_PASS`. Both `utilities/make-kubeconfig.sh` and the AAP Vault
credential in `inventory/group_vars/aap/main.yml` read that same variable, so
they cannot disagree.
