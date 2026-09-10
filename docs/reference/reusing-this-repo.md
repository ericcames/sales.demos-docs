# Reusing this repo

[sales.demos](https://github.com/ericcames/sales.demos) is public and meant to
be reusable. Two things stand between a clone and a working demo: pointing it at
*your* cluster, and — if you run it from AAP — pointing AAP at *your* fork.

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

**There are two legitimate ways to change them, and which is right depends on
where you run from.**

| You are | Repoint by | Why |
|---|---|---|
| On a laptop, tracking this repo for updates | a gitignored `local.yml` overlay | You pull upstream fixes without ever conflicting |
| Forked, running from AAP | editing `connection.yml` on your own branch | Gitignored files are **not** in the SCM checkout a job template runs from |

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

### From AAP: edit `connection.yml`

An AAP job template gets its playbooks and inventory from the SCM project
checkout, and a gitignored file is not in it. So `local.yml` does nothing for a
job template, and repointing one means committing the change:

```bash
git checkout -b my-environment
$EDITOR inventory/group_vars/sandbox/connection.yml
```

You can do both: the overlay for laptop runs, the committed file for AAP. They
do not interfere — `local.yml` simply is not present in the checkout.

---

## Forking

Running from AAP means forking, and four things in the repo name *that* repo or
its author. Two are variables; two are deliberately left alone
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
