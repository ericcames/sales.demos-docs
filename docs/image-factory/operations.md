# Operations

Running the factory: the one scheduled build, the secrets behind it, and the
failure modes worth recognising on sight.

For design detail see [Architecture](architecture.md); for the development cycle
see the producer repo's `dev-workflow` skill.

## The scheduled rebuild

The RHEL 9 CIS L1 containerDisk rebuilds **automatically on the 1st of every
month at 06:00 UTC**, via `.github/workflows/containerdisk-rebuild.yml`. This is
what keeps it current with RHEL errata and CIS benchmark updates without anyone
remembering.

To trigger an ad-hoc rebuild:

=== "CLI"

    ```bash
    gh workflow run "Rebuild RHEL 9 CIS containerDisk"

    # check status
    gh run list --workflow=containerdisk-rebuild.yml --limit 5

    # logs for one run
    gh run view <run-id> --log
    ```

=== "GitHub UI"

    Actions tab → **Rebuild RHEL 9 CIS containerDisk** → Run workflow → select
    `main` → Run workflow.

**Expected duration: 20–35 minutes** — Image Builder compose 15–25 min, qcow2
download 2–5 min, `podman build` and push 3–5 min.

!!! note "It is the only scheduled build"
    The Windows containerDisk, the AMI lineage and the SNO ISO are all manual.
    The reason is credentials: this is the one path whose entire credential set
    fits in GitHub Actions secrets. See
    [Extending it](extending.md#known-gaps-named).

## Secrets

Three Actions secrets power the scheduled rebuild:

| Secret | Source | Rotate when |
|---|---|---|
| `RH_OFFLINE_TOKEN` | `~/.ansible.cfg`, `[galaxy_server.rh_certified]` | The token expires — 401s in scheduled runs |
| `QUAY_USERNAME` | Quay.io username | The account changes |
| `QUAY_PASSWORD` | Quay.io password or robot account token | The password changes |

**A new Red Hat token:** console.redhat.com → Automation Hub → Connect to Hub →
API token. Update `~/.ansible.cfg` locally **first**, then sync it up — that file
is the one authoritative copy, shared with everything else that talks to
Automation Hub.

```bash
# read it straight out of the authoritative file, so the two cannot disagree
python3 -c "
import configparser, os
cfg = configparser.ConfigParser()
cfg.read(os.path.expanduser('~/.ansible.cfg'))
print(cfg.get('galaxy_server.rh_certified', 'token'))
" | gh secret set RH_OFFLINE_TOKEN --repo ericcames/image.builder.pipeline

gh secret list --repo ericcames/image.builder.pipeline
```

## Troubleshooting scheduled builds

| Symptom | Cause | Fix |
|---|---|---|
| Fails at "Configure Red Hat token" | `RH_OFFLINE_TOKEN` missing or expired | Rotate the secret |
| Fails at "Log in to Quay.io" | `QUAY_USERNAME` / `QUAY_PASSWORD` wrong | Update secrets; verify locally with `podman login quay.io` first |
| Fails at compose wait, exit 1 | Image Builder compose failed | Check stderr in the run log — often transient, re-trigger |
| Fails at compose wait, exit 2 | Compose timed out (>30 min) | Re-trigger; if persistent check console.redhat.com for service status |
| Fails at `podman push` | Quay repo missing, or auth expired | Verify the repo exists; re-login and update `QUAY_PASSWORD` |
| **Succeeds but no new image** | Tag mismatch, or the push silently failed | Check the run log for the pushed tag, then `podman pull quay.io/zigfreed/rhel9-cis-l1-golden:<tag>` |

That last row is the one to take seriously. A build that reports success while
publishing nothing is the same shape of failure as a label that claims a
hardening level the disk does not have — see
[Compliance evidence](compliance-evidence.md#the-time-the-label-was-false).

## Quay repositories

| Image | Visibility | Why |
|---|---|---|
| `rhel9-cis-l1-golden` | **Public** | Freely redistributable; consumers pull it with no pull secret |
| `win2k22-cis-l1-golden` | **Private** | Microsoft licensing prohibits public redistribution of Windows media |

The private repository is entitled through an Unlimited Repositories
subscription, **active to 2027-08-14**. Nothing needs doing until then.

### If the entitlement lapses

Quay's free Open Source plan includes **zero** private repositories. Without an
entitlement Quay displays a warning banner on the repository — it is a warning,
not a block, and an existing private repo keeps working while it shows.

![Quay.io private repository entitlement notification](../images/quay-private-repo-entitlement.png)

Restoring it needs either the Developer plan (5 private repos) or a Red Hat
developer subscription that includes private-repo access; Red Hat associates
open a support case for the latter.

!!! tip "The symptom arrives on the producer side first"
    A lapsed entitlement breaks a **push** before it breaks any pull. A
    scheduled rebuild fails before a single consumer notices — which is the
    right way round, and worth knowing so the failure is read correctly.

## Manual builds

**RHEL AMI** — laptop only, needs live AWS credentials:

```bash
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCOUNT_ID=<account-id>

ansible-playbook playbooks/build_cis_image.yml         # ~20 min
ansible-playbook playbooks/deploy_and_scan.yml         # ~5 min
ansible-playbook playbooks/generate_policy_data.yml    # seconds
```

Output at `output/rhel9/data.json`, gitignored.

**Windows** — laptop only, and needs an OpenShift **sandbox** cluster with
KubeVirt. The playbook refuses to run against the demo cluster.

```bash
export K8S_AUTH_HOST=https://api.<cluster>:6443
export K8S_AUTH_API_KEY=<bearer-token>
export WINDOWS_ADMIN_PASSWORD=<password>

ansible-playbook playbooks/build_windows_image.yml
ansible-playbook playbooks/publish_windows_containerdisk.yml
```

Roughly 30 minutes. See [Windows](windows.md) for what each phase does.

!!! danger "Credentials go in the environment, never in a file"
    Every command here reads its credentials from environment variables. There
    is no credentials file to create, and the one that used to be documented has
    been deleted. AWS credentials will move into a vault-encrypted `secrets.yml`
    when that work lands.

## Deprovisioning

The AMI scan path creates a temporary EC2 instance and tears it down in an
`always:` block, so a failed scan does not strand AWS resources. If a run is
killed hard enough to skip it, check for a running instance tagged
`Pipeline=image-builder-pipeline` before assuming the account is clean.
