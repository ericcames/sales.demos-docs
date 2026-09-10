# Running playbooks

**Nothing deploys from CI.** GitHub Actions is a pull-request gate only — lint,
secret hygiene, skill portability. Everything that touches an environment runs
through `ansible-playbook`, either wrapped by a skill or as an AAP job template.

That is deliberate: keeping deploys out of CI means no runner ever needs the
vault password, and there is no second copy of it in GitHub Environment secrets
([#7](https://github.com/ericcames/sales.demos/issues/7)).

---

## Running a phase

```bash
ansible-galaxy collection install -r collections/requirements.yml

ansible-playbook playbooks/setup.yml \
  -i inventory --limit sandbox -e target_env=sandbox \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

**`--vault-id` is required** — credentials come from the vault-encrypted
`playbooks/group_vars/all/secrets.yml`. Without it the run fails with
*"Attempting to decrypt but no vault secrets found"*.

**`--limit` selects the environment and is mandatory.** Playbooks target
`hosts: aap`, so without a limit they match every environment at once — they
assert on that and fail closed rather than configuring two environments in one
run. Adding `-e target_env=<env>` makes the play verify the inventory resolved
to the environment you meant.

---

## Applying the AAP configuration

Always run `validate.yml` first; it is the same play in check mode.

```bash
ansible-playbook playbooks/validate.yml --check -i inventory --limit sandbox \
  -e target_env=sandbox --vault-id sales.demos@~/secrets/.vault_pass_sales_demos

ansible-playbook playbooks/config.yml -i inventory --limit sandbox \
  -e target_env=sandbox --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

!!! warning "`validate.yml` needs `--check` and refuses to run without it"
    A play-level `check_mode: true` sets the task's check mode but leaves the
    `ansible_check_mode` variable False, and `infra.aap_configuration`'s entire
    check-mode handling keys off that variable
    ([#173](https://github.com/ericcames/sales.demos/issues/173)).

`config.yml` reports `changed` on **every** run. AAP returns
`SUBSCRIPTIONS_CLIENT_SECRET` as `$encrypted$` and never in the clear, so the
role cannot compare desired against actual and rewrites it each time. That is
the platform refusing to hand back a secret, not drift.

---

## Verify it in the EE

That command runs on **your laptop**, against `~/.ansible/collections` and your
system python. An AAP job template runs the same playbook inside
`sales-demos-ee`, against whatever that image baked in. Two dependency sets, and
only one of them is what production uses.

Nothing else can tell them apart — CI executes nothing, so a local run is the
only pre-merge verification and by default it verifies the wrong one. Before a
playbook change merges, run it in the image as well:

```bash
utilities/run-in-ee.sh playbooks/probe_env.yml \
  -i inventory --limit sandbox -e target_env=sandbox \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

**Everything after the playbook is byte-identical to the `ansible-playbook`
command above.** The wrapper adds `ansible-navigator`, the right image, and two
read-only mounts; it changes none of your arguments. `~/` paths resolve inside
the container because the mounts are placed where the container's home is.

Add `--with-hub-token` for `config.yml`, `validate.yml`, `setup.yml`,
`sync_hub.yml` and `curate_hub.yml`, which read the Red Hat offline token from
`~/.ansible.cfg`. The wrapper refuses rather than warns if you forget — without
the mount the `ini` lookup **raises** (`Invalid filename: 'None'`) rather than
returning an empty string.

This is a verification path, not a replacement: `ansible-playbook` stays the
everyday command. `/sales-demos-verify-ee` walks the whole thing.

It has already earned it.
[#122](https://github.com/ericcames/sales.demos/issues/122) (a hijacked python
interpreter) and [#173](https://github.com/ericcames/sales.demos/issues/173)
(`validate.yml` failing on the EE's older ansible-core) were both invisible to
CI, to a laptop run, and to `build-ee.sh`. See
[Execution environment](execution-environment.md).

---

## Keep the run log

Phase 0 takes 10–20 minutes. If it fails and the terminal is gone, so is the
evidence. Set a log path before running:

```bash
export ANSIBLE_LOG_PATH=~/ansible-logs/sales-demos-$(date +%F).log
```

Logs go to `~/ansible-logs/`, **outside the repo** — it is public, and keeping
them out entirely beats relying on an ignore rule.

!!! danger "Do not pipe through `tee`"
    In a pipeline the exit status comes from `tee`, not from
    `ansible-playbook`, so a failed run reports success. That is not
    hypothetical: it caused a real misread during Phase 0, where the harness
    showed exit 0 for a playbook that had actually failed.
