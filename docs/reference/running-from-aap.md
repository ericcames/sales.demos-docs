# Running from AAP

Every phase runs two ways — as a Claude Code skill on a laptop, and as an AAP
job template — driving the same `playbooks/<phase>.yml`. The AAP objects are
config-as-code in
[`inventory/group_vars/aap/`](https://github.com/ericcames/sales.demos/tree/main/inventory/group_vars/aap),
applied by `playbooks/config.yml` like everything else.

Measured against `main` on 2026-09-10: **32 job templates and 4 workflows.**
The counts here come from `controller_templates.yml` and
`controller_workflows.yml`, ignoring entries carrying `state: absent` — those
are tombstones that *delete* superseded objects, not things AAP runs.

---

## The four workflows

A workflow is the entry point. Launch the workflow, not the templates inside
it — the survey collects every input once and the nodes chain on success.

### `Cluster Day 0`

Bare cluster to demo-ready.

```
Cluster Day 0 - 1 Install OpenShift Virtualization
  └─> Golden Image - Link RHEL 9 CIS L1
        └─> Cluster Day 0 - 2 Verify Environment
```

### `Linux Day 1 - 0 Workflow`

```
Linux Day 1 - 1 Provision
  └─> Linux Day 1 - 2 Register
        └─> Linux Day 1 - 3 Configure
              └─> Linux Day 1 - 4 Compliance Scan
                    └─> Linux Day 1 - 5 Check
```

### `Windows Day 1 - 0 Workflow`

Same shape, with a patch stage where Linux registers:

```
Windows Day 1 - 1 Provision
  └─> Windows Day 1 - 2 Patch
        └─> Windows Day 1 - 3 Configure
              └─> Windows Day 1 - 4 Compliance Scan
                    └─> Windows Day 1 - 5 Check
```

### `Windows Day 2 - 0 Break Fix`

The compliance story — scan either side of a deliberate regression, so the
audience sees the score move rather than being told it would:

```
Windows Day 2 - Break Compliance
  └─> Windows Day 2 - Compliance Scan     (the broken score)
        └─> Windows Day 2 - Fix Compliance
              └─> Windows Day 2 - Compliance Scan   (the restored score)
```

---

## Job templates by family

| Family | Count | Covers |
|---|---|---|
| `Cluster Day 0` | 3 | Install CNV, verify the environment, probe capacity |
| `Golden Image` | 2 | Link the RHEL 9 and Windows 2022 CIS L1 images |
| `Linux Day 1` | 7 | Provision, register, configure, scan, check, repair, teardown |
| `Windows Day 1` | 7 | Provision, patch, configure, scan, check, repair, teardown |
| `Windows Day 2` | 6 | Break/fix compliance, scan, patch, check SMB, .NET patch report |
| `AAP Ecosystem` | 3 | Automation Orchestrator, self-service portal, MCP server |
| `AAP Observability` | 2 | Deploy Alloy, deploy dashboards |
| `Self-Service` | 2 | Request a Linux or Windows server via the portal |

Every template maps to one playbook. A few playbooks back more than one
template — `provision_vm.yml` serves both the Linux and Windows provision
steps, `teardown.yml` both teardowns, and `windows_compliance_scan.yml` is
reused at three points in the Windows story.

---

## One working inventory, not two

`Sales Demo VMs` holds both populations: `sandbox-local` / `demo-local`, synced
from the repo's own `inventory/hosts.yml` by an SCM inventory source, and the
demo VMs registered at run time. That sync is what lets a job template use
`connection.yml` instead of a second copy of every hostname.

**`Sales Demo VMs - Control` holds no VM hosts, and only teardown points at
it** — two templates, `Linux Day 1 - Teardown` and `Windows Day 1 - Teardown`.
Teardown cannot run in the inventory whose hosts it deletes; AAP holds a
running-job lock on that inventory. From `controller_inventories.yml`:

> Nothing but teardown should reference this. If another job template points
> here, that is a bug.

---

## How AAP reaches the VMs

**Plain `ssh` on port 22.** AAP runs on the same cluster, each VM has a
headless Service giving it stable in-cluster DNS, and there is no NetworkPolicy
between the namespaces. No bastion is involved, and `virtctl` is not either —
that is the laptop path, and the execution environment does not ship the
binary. The only requirement is the `Sales Demos - Linux Machine` credential,
holding the private half of `demo_ssh_public_key`.

!!! warning "`demo_ssh_public_key` must not be empty"
    cloud-init then emits `ssh_pwauth: true` with no authorized key *and* no
    password, and the guest has no credentials at all. Because cloud-init writes
    authorized keys only on first boot, a VM created that way must be
    **re-created**, not restarted.

---

## Testing a job template before its playbook has merged

A job template validates `playbook:` against the project's current checkout, so
an unmerged playbook cannot otherwise be wired up. Override the project branch:

```bash
ansible-playbook playbooks/config.yml -i inventory --limit sandbox \
  -e target_env=sandbox -e sales_demos_branch=my-branch \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Re-apply without the override before calling anything done.
