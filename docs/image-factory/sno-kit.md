# Single-Node OpenShift Installer

The newest output, and a different kind of artifact from the others: it builds
**the OpenShift platform itself**, not a guest that runs on top of one.

`playbooks/build_sno_installer.yml` produces an Agent-Based Installer ISO —
bootable on bare metal over UEFI, fully unattended — that turns a bare machine
into a single-node OpenShift cluster with the whole demo stack already on it.

## What comes up

One ISO, one boot, no post-install clicking:

1. **Single Node OpenShift** — control plane and worker on one node
2. **Ansible Automation Platform 2.7** — the `aap-operator`, channel `stable-2.7`
3. **OpenShift Virtualization** — `kubevirt-hyperconverged`
4. **Compliance Operator**
5. **LVM Storage** — with the root partition sized so LVMS has space to use
6. **CIS L1 node hardening** — `ocp4-cis-node` MachineConfigs

Operators arrive as **Day 0 extra manifests**, numbered for ordering, so they
install during bootstrap rather than as a checklist afterwards.

This is the "single-node OpenShift AAP ecosystem" in one artifact: a complete
demo platform on one box.

## Proven on real hardware

Booted on an Intel NUC — 64 GB RAM, 2 TB SSD, UEFI boot from USB. OCP 4.22.13,
every Day 0 operator reporting `Succeeded`.

!!! note "And the compliance number is honest"
    Stock RHCOS scores **186 of 188** on `ocp4-cis-node`, not 188 — the
    bootstrap etcd WAL file is left world-readable
    ([#106](https://github.com/ericcames/image.builder.pipeline/issues/106)).
    Quote 186/188. A demo that claims a perfect score invites the one question
    you cannot answer.

    That measurement also raised a genuine design question: if stock RHCOS is
    already compliant, the Day 0 CIS MachineConfigs may be redundant. Still open.

## Why the ISO is generated locally

The ABI ISO embeds the OpenShift pull secret in its Ignition config. **A pull
secret is a credential**, so the finished ISO can never be published anywhere.

The user supplies their own pull secret and SSH key at generation time, and the
ISO is written to a USB stick. That constraint is real and permanent.

## Why this is not published to Quay

The producer repo's roadmap names a Quay repository for an installer *kit* — the
manifests, templates and generation script, everything except the secrets. That
kit was designed and then **decided against**. Nothing publishes it, and nothing
should. Here is the reasoning, because a reader who finds the roadmap line
deserves to know which one is current.

**The payload is text that is already in a public git repo.** The kit would
contain YAML manifests, Jinja templates and a shell script. Those are exactly
what git distributes well — versioned, diffable, reviewable in a pull request.
The ISO, the only artifact that is expensive to produce, is excluded by the pull
secret constraint above. Publishing would ship the cheap half.

**Every other artifact here is on a registry because a machine demands one.** A
containerDisk lives on Quay because KubeVirt's DataVolume can import from a
registry or HTTP and nothing else. An AMI lives in AWS because EC2 requires it.
Those are machine-to-machine contracts with no alternative. The kit's consumer
is a person, running a script on a laptop, before carrying a USB stick to a
NUC. **Nothing in that path is asking for OCI format.**

**What publishing would cost:** a Quay repository, a push credential in Actions
secrets, a rebuild workflow, tag discipline, six OCI labels to maintain, and a
second copy of the manifests that can drift from the repo they were built from.

**The labels in particular would buy nothing.** The OCI label machinery
elsewhere in this factory exists for a specific reason: a disk image is
**opaque**, so its claims have to be checked independently — which is why
`verify_cis_disk.py` reads the registry hives and gates the
`com.redhat.cis.level` label. A directory of YAML in git is not opaque. You can
read it. Labelling it would be ceremony with no verification behind it, which is
the failure mode this factory is built to avoid, not an instance of its
solution.

**If an immutable, versioned bundle is ever wanted, a GitHub Release is the
better answer** — versioned, immutable, one `gh release download`, no registry,
no push credential, no workflow. The repo is already public.

### The counter-argument, in full

If the kit ever has to be consumed **from inside a cluster** — say an AAP job
template generating ISOs for a fleet of edge sites — then a registry becomes the
natural format and this decision should be revisited. That is a genuinely
different use case from an SE with a USB stick, and it is not today's.

What does **not** change under that scenario is the pull secret constraint: the
generated ISO stays unpublishable regardless.

## Building one

```bash
ansible-playbook playbooks/build_sno_installer.yml
```

The playbook downloads `openshift-install`, renders the install and agent
configs from templates, assembles the Day 0 manifests, and generates the ISO.
Inputs live in `playbooks/vars/sno_defaults.yml` — OCP version and channel,
hardware minimums, operator channels.

| Decision | Choice | Why |
|---|---|---|
| Image type | ABI ISO | Fully unattended bare-metal SNO from a USB drive |
| Operators | Day 0 manifests | Installed during bootstrap, no post-install steps |
| Network | Static IP by default, DHCP optional | DNS records break if the IP moves on reboot |
| OCP version | Configurable, default latest stable | Tracks z-stream updates |

!!! tip "Home-lab DNS"
    A bare-metal SNO on a home network has no public domain. The working setup
    is `dnsmasq` alongside `systemd-resolved`: one `address=` line covers both
    `api.*` and `*.apps.*`, with `systemd-resolved` routing the domain to it.

## Presenting it

This page covers **building** the installer. For running the demo on the cluster
it produces — the run sheet, the talk track, the objections — see the
[Edge / Single Node OpenShift demo](../demos/edge-sno/).

Producer here, consumer there, the same split as everything else in this
factory.
