# Extending it

**"Does this work for our OS, our benchmark, our hypervisor?"**

The honest answer is three different answers, because the factory generalises
along three axes and it has got further on some than others. This page names
which is which, including where a variable change turns into a code change.

## The three axes

Any image in this factory is a point in **OS × benchmark × target**:

- **OS** — RHEL 9 today, RHEL 8/10 planned, Windows Server 2022, and the
  Ubuntu/Rocky/Amazon Linux family on the roadmap
- **Benchmark** — CIS Level 1 today; CIS L2 and STIG are sibling profiles
- **Target** — an AWS AMI, an OpenShift Virtualization containerDisk, or a
  bare-metal installer ISO

## Where each axis actually lives

| Axis | Where it is set today | Adding one is |
|---|---|---|
| **OS** — RHEL, AMI path | A `platform_config` dict in `build_cis_image.yml`, selected by the `TARGET_PLATFORM` env var and asserted against the dict's keys | **A variable change** — add a dict entry |
| **OS** — containerDisk path | **Hardcoded.** `distribution: "rhel-9"`, the output directory and the default Quay repo are literals in `build_cis_containerdisk.yml` | **A code change.** This is the real gap |
| **OS** — Windows | `roles/requirements.yml` pins the `windows_2022_cis` role; the build is a single large playbook | **A code change** — a new role and a new branch |
| **Benchmark** — RHEL | `cis_profile: xccdf_org.ssgproject.content_profile_cis_server_l1`, a play variable in both build playbooks | **One string.** L2 and STIG are sibling profile IDs — but not yet exposed as a knob |
| **Benchmark** — Windows | `playbooks/vars/cis_profile.yml` sets `win22cis_l1_ms_gpo: true`, with the L2, domain-controller and user variants present and `false` | **A flag flip**, plus a fresh exception review |
| **Benchmark** — exemptions | `playbooks/vars/exempt_controls.yml`, curated for **RHEL 9 on AWS** specifically | **One curated set per OS × benchmark × target.** Not inheritable |
| **Target** — AWS | `image_type: "aws"` inside the same `platform_config` entry | **A dict entry.** Image Builder also emits `vsphere`, `azure`, `gcp` and `guest-image` |
| **Target** — OpenShift Virt | qcow2 → containerDisk wrap → `podman push` | **Already generic** — the wrap is OS- and benchmark-agnostic |
| **Target** — bare metal | `build_sno_installer.yml` and its Day 0 manifests | A deliberately separate lineage — a platform installer, not a guest image |

## The headline, in three sentences

**The hypervisor and cloud axis is the cheapest to extend.** Red Hat Image
Builder emits VMware, Azure, GCP and raw guest images from the same blueprint
API that already produces the AMI and the qcow2. For a RHEL guest, a new
hypervisor is one `image_type` value.

**The benchmark axis is a string on RHEL and a flag on Windows.** Both are
close. What is *not* close is the exempt list: exemptions are specific to an OS,
a benchmark and a target, and a new combination needs its own curated set with
written reasons. That is analyst work, not plumbing.

**The OS axis is the one that is blocked**, and on something small: the
containerDisk playbook hardcoded what the AMI playbook parameterised. The AMI
path can already take RHEL 8 by adding a dict entry; the containerDisk path
cannot, because the distribution, the output path and the destination repository
are literals. **Fixing that is the highest-leverage change in the factory**, and
it unblocks every RHEL-family OS for the target the demos actually use.

!!! tip "If you are asked this in a meeting"
    "Adding VMware or Azure is a configuration change. Adding CIS L2 is a
    profile string plus an exemption review. Adding RHEL 8 is a configuration
    change for AWS and a small refactor for OpenShift Virtualization — we
    parameterised one path and not the other, and we know exactly which line it
    is." That answer is more convincing than a claim of total generality, and it
    is true.

## Adding a new OS

**A RHEL-family OS, AMI target** — add an entry to `platform_config` naming the
Image Builder distribution, image type and architecture, then run with
`TARGET_PLATFORM` set to it. Curate an exempt list for it; do not inherit
RHEL 9's.

**A RHEL-family OS, containerDisk target** — first parameterise
`build_cis_containerdisk.yml`, which currently hardcodes three things. The
cleanest shape mirrors the AMI playbook: the same `platform_config` dict, with
the Quay repository and output directory derived from the selected entry.

**A non-RHEL Linux** (Ubuntu, Rocky, Amazon Linux) — Image Builder does not
build these, so the compose stage has no equivalent. It needs a different build
mechanism, with the scan and policy-data stages reusable as-is because they
consume XCCDF, not an image.

**Another Windows** (2019, 2025) — a different `ansible-lockdown` role and a
build path that branches on version. The answer file, the ISO remaster and the
publish machinery are all reusable.

## Adding a new benchmark

1. **Change the profile.** RHEL: the `cis_profile` string to the L2 or STIG
   profile ID. Windows: flip the level flag in `playbooks/vars/cis_profile.yml`.
2. **Re-curate the exemptions.** Non-negotiable. A CIS L2 run on a cloud image
   will fail different controls for different reasons, and an inherited L1
   rationale will be wrong in ways that read as sloppy under scrutiny.
3. **Re-check what the benchmark breaks.** Windows L1 already needed four
   controls disabled because they kill the WinRM session mid-build. L2 is
   stricter and should be expected to need more.
4. **Separate the outputs.** L1 and L2 are different lineages — different image
   tags, different policy data. Not a flag on one artifact.

!!! warning "Level assignment is a per-layer decision"
    CIS L2 is not simply "better". The Satellite host OS stays at L1 because L2
    fights Satellite's own installer over the firewall and the ports it needs.
    Pick the level per workload, and be able to say why.

## Adding a new target

For a RHEL guest, change `image_type` in the platform entry. Image Builder
supports `aws`, `vsphere`, `azure`, `gcp` and `guest-image` — the last being the
qcow2 that becomes a containerDisk.

What has to follow the new format:

- **A discovery contract.** AMIs use tags, containerDisks use OCI labels. A new
  target needs the equivalent — the thing a consumer matches on instead of a
  name
- **A scan path**, or an honest statement that there is not one. The AMI path
  scans on EC2; the containerDisk path inherits its hardening and says so
- **An exempt list** for that target. `partition_for_tmp` is exempt on EBS
  because of how cloud-init expands the root partition; that reasoning does not
  transfer to a VMware image

## Known gaps, named

Not a roadmap — the things a reader would otherwise discover the hard way.

| Gap | Impact |
|---|---|
| `build_cis_containerdisk.yml` is RHEL-9-only in code | Blocks the OS axis for the target the demos actually use |
| The CIS profile is not exposed as a variable on the RHEL path | L2 is a one-line edit rather than a parameter |
| **Windows has no scheduled rebuild** | The RHEL image refreshes monthly; the Windows image only moves when someone runs it. Windows security updates land on a monthly cadence too |
| One Windows SKU | Standard/GUI only. Datacenter and Core are not built, though the WIM parser that would select them already exists |
| The containerDisk lineage is not independently scanned | Its compliance is inherited from the profile, not measured. See [Compliance evidence](compliance-evidence.md) |

## Related

- [Architecture](architecture.md) — the tagging contracts a new target has to satisfy
- [Compliance evidence](compliance-evidence.md) — why a new exempt list is not optional
- [Operations](operations.md) — what a new scheduled build would have to fit into
