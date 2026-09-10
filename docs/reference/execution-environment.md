# Execution environment

AAP runs this repo's playbooks on a custom image, `quay.io/zigfreed/sales-demos-ee`,
defined by
[`execution-environment.yml`](https://github.com/ericcames/sales.demos/blob/main/execution-environment.yml).

It exists for one reason: Phase 3 drives `terraform/ocpvirt/` by shelling out to
the terraform CLI, and no stock execution environment ships that binary.
Everything else in the image is `ee-supported-rhel9` (AAP 2.7, pinned by digest)
plus the same `collections/requirements.yml` a laptop installs — so the skill
path and the job-template path resolve identical collection *code*.

**Current tag: `v1.2.0`.** It adds the helm 3.21.4 binary, without which
`kubernetes.core.helm` — and therefore `playbooks/portal.yml` — could not run
from AAP at all
([#324](https://github.com/ericcames/sales.demos/issues/324)). `v1.1.0` was the
2.7-base rebuild ([#122](https://github.com/ericcames/sales.demos/issues/122));
`v1.0.0` came before it. Both stay mirrored, so rolling back is changing one
line — no re-mirror, no quay round trip.

---

## Identical collections is not an identical environment

The difference is underneath them. Measured 2026-09-04: the laptop ran
ansible-core `2.18.18rc1` on python 3.14 while the EE ran core `2.16.19` on
python 3.12 — two minor versions of core apart, with every collection pin
matching exactly.

That gap is invisible to CI, to a laptop run, and to `build-ee.sh`'s drift
check, and it held a real defect
([#173](https://github.com/ericcames/sales.demos/issues/173)). **Pinned
collections are not a pinned environment.** See
[Running playbooks](running-playbooks.md#verify-it-in-the-ee).

---

## The published image carries no credential

The image is public. It holds **no token**, and that is checkable rather than
asserted:

```bash
podman run --rm --entrypoint /bin/bash quay.io/zigfreed/sales-demos-ee:v1.2.0 \
  -c 'ls /etc/ansible 2>&1; ansible --version | grep "config file"'
# ls: cannot access '/etc/ansible': No such file or directory
#   config file = None

podman history --no-trunc quay.io/zigfreed/sales-demos-ee:v1.2.0 | grep ansible.cfg
# (no match)
```

`execution-environment.yml` stages `~/.ansible.cfg` — which carries the Red Hat
offline token — into the **galaxy build stage only**. The final image is built
`FROM base` and copies the installed collections out, not that file.

Anything needing a credential at run time gets it **mounted read-only from the
laptop for that run and never persisted**, which is why `utilities/run-in-ee.sh`
prints every mount before it starts. Making the build *enforce* the emptiness
rather than merely achieve it is
[#172](https://github.com/ericcames/sales.demos/issues/172).

---

## Building it

```bash
./utilities/build-ee.sh          # build + verify
./utilities/build-ee.sh --push   # build + verify + publish
```

Use the script, not `ansible-builder` directly. It stages `~/.ansible.cfg` —
which holds the Automation Hub token the build needs for certified collections —
into the gitignored `.ee-build/`, because the EE definition cannot portably
reference a path in `$HOME` and **a tracked `ansible.cfg` at the repo root would
shadow `~/.ansible.cfg` and break certified installs machine-wide**.

The script then verifies the built image **as UID 1000**, which is who AAP runs
a job as: `terraform version` must execute, and every pinned collection must be
present at exactly its pinned version. `Complete!` from ansible-builder is not
verification — `==> Verified` is.

---

## AAP pulls it from Private Automation Hub, not from quay

[#35](https://github.com/ericcames/sales.demos/issues/35). quay stays the
published artifact and the source of truth; PAH mirrors it into a local
`sales_demos_ee` repository and Controller pulls that, which takes quay.io out
of the demo's runtime dependencies and makes the pull cluster-local. The mirror
is config-as-code in `hub_ee_registries.yml` and `hub_ee_repositories.yml`.

!!! warning "The sync has two gates and needs both"
    The repository item must carry `sync: true`, *and* a variable named
    `hub_ee_repository_sync` must be **defined** — dispatch includes that role
    on `... is defined` and never reads the value. Miss either and there is no
    error: the repository is created, stays empty, and Controller later fails to
    pull an image that was never mirrored.

The image reference is `{{ aap_hostname }}/sales_demos_ee:v1.2.0` — templated
because PAH is fronted by the AAP gateway on the AAP hostname, which differs per
environment, and underscored because Hub repository names allow only
alphanumerics and underscores.

**Tags are immutable. Never re-push one.** Job templates pin a tag with
`pull: missing`, so re-pushing changes what a job runs with no corresponding
change in git — a failure that surfaces mid-demo. Publish a new tag and bump the
reference. The `sales-demos-ee-build` skill has the bump rules and the build
gotchas.

**Prove it before flipping it.** `v1.2.0` changes the image *every* template runs
on, not just the portal's, so its gate was both: the portal template completing,
**and** `Linux Day 1 - 0 Workflow` still green end to end on the new image. A
helm binary should not disturb terraform or `kubernetes.core`, but "should not"
is not evidence.
