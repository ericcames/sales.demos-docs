# Repo layout

Where things are in
[sales.demos](https://github.com/ericcames/sales.demos), and the handful that
are not where you would guess. Start with the repo's
[Getting started](https://github.com/ericcames/sales.demos#-getting-started) if
you have not cloned it yet.

---

## The tree

```
.claude/skills/<name>/SKILL.md   in-repo skills, discovered when the repo is open
assets/aap-branding/             AAP gateway config inputs — NOT documentation
collections/requirements.yml     what your laptop and the EE install
env-urls.yml                     GITIGNORED, generated — product URLs + credentials per env
hub/                             what Private Automation Hub SYNCS (generated)
inventory/
  hosts.yml                        one host per environment — never share one
  group_vars/
    aap/                             shared config: job templates, workflows, credentials
    sandbox/  demo/  edge/           per-environment connection settings:
      connection.yml                   committed — hostnames, API URLs, namespaces
      local.yml.example                copy to local.yml and fill in your cluster
      local.yml                        GITIGNORED per-SE repoint overlay
playbooks/                       the work: one playbook per phase
  group_vars/all/
    secrets.yml                      GITIGNORED, vault-encrypted — the ONLY secrets file
    secrets.yml.example              the contract you build it from
terraform/ocpvirt/               keyed by PLATFORM, not demo — demos reuse platforms
utilities/                       build, check and generate scripts
```

**`env-urls.yml` is at the root, not in `inventory/`.** Every command passes
`-i inventory`, and Ansible parses every file in that directory as an inventory
source — the generated file used to live there and printed
`Skipping key (portal) in group (sandbox)` warnings on every run
([#582](https://github.com/ericcames/sales.demos/issues/582)). Regenerating
removes a leftover copy at the old path.

**AAP objects are config-as-code in `inventory/group_vars/aap/`.**
`controller_templates.yml` and `controller_workflows.yml` hold the job templates
and workflows, applied by `playbooks/config.yml`. What AAP ends up with is listed
in [Running from AAP](running-from-aap.md).

**There is no `docs/` directory.** Documentation lives on this site.

---

## Not where you would guess

### `hub/` is not `collections/`

`collections/requirements.yml` is what your laptop and the execution environment
*install*. `hub/*-requirements.yml` is what Private Automation Hub *syncs from
upstream*. Different direction, different lifecycle — mixing them up is the
likeliest mistake in the PAH use case.

### `assets/aap-branding/` is not documentation

However much it looks like screenshots. `gateway_settings.yml` reads
`logo-<env>.png.b64` from there at playbook run time, including from AAP's SCM
checkout, so deleting any of it breaks `config.yml`. See
[its README](https://github.com/ericcames/sales.demos/blob/main/assets/aap-branding/README.md).

### `secrets.yml` sits beside the playbooks, not the inventory

AAP's SCM inventory sync runs `ansible-inventory`, which parses every
`group_vars` file next to the inventory. A vaulted file there fails the sync
with `ERROR! Attempting to decrypt but no vault secrets found`, and AAP refuses
Vault credentials on SCM inventory sources, so it cannot be given the password.
Beside the playbooks, it loads for every play and stays out of the sync.

### The overlay is `local.yml`, not `connection.local.yml`

Ansible loads a `group_vars/<group>/` directory in sorted order and the *last*
file wins. `connection.local.yml` sorts **before** `connection.yml` and loses
silently — you would run against the committed cluster believing you had
repointed. How the overlay reaches AAP is in
[Reusing this repo](reusing-this-repo.md).

---

## Working across the image factory and this repo

The golden images are split across two repos on purpose.
[image.builder.pipeline](https://github.com/ericcames/image.builder.pipeline)
builds and publishes them; sales.demos points a cluster at a published image.
The only thing binding them is a containerdisk tag, carried in
`quay_windows_image` and `quay_rhel9_image` in
`inventory/group_vars/<env>/connection.yml`.

Most work needs only one repo. When it spans both — the edge / SNO demo does by
construction — **start the agent in sales.demos**:

```bash
cd sales.demos && claude .
```

`.mcp.json` there is project-scoped, so the cluster MCP servers load only in a
session started in that directory, and the factory repo has none. From there you
can `cd ../image.builder.pipeline` and run its playbooks anyway — the working
directory does not restrict shell access.

**Its skills are the exception.** Skills are discovered from the directory the
agent starts in, so the factory's own skills are not reachable from a session
started in sales.demos. Open a second session there to use them.
