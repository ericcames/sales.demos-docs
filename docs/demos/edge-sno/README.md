# Demo: Edge / Single Node OpenShift

**Start here.** Take bare x86_64 hardware from power-on to a running OCP Virt
demo — AAP provisioning VMs on OpenShift Virtualization, with CIS L1 hardening,
Grafana Cloud observability, and nightly teardown — using two public repos and
no cloud dependency.

| | |
|---|---|
| **Length** | Setup: ~90 minutes hands-on, ~45 minutes waiting. Demo: same 30-minute OCP Virt talk track |
| **Audience** | Platform engineers and edge infrastructure architects evaluating SNO for edge deployments |
| **Reader** | The Red Hat pre-sales engineer setting up and presenting it |
| **Needs a live environment?** | **Yes** — this IS the environment. The whole point is showing it on hardware you own |
| **Status** | Ready — proven end-to-end on a NUC, 2026-09-09 |

---

## The four documents

| File | Read it when |
|---|---|
| [`run-sheet.md`](run-sheet.md) | **While building.** Step-by-step checklist from bare hardware to demo-ready |
| [`talk-track.md`](talk-track.md) | **Before the meeting.** Why bare metal matters, and the words that land |
| [`architecture.md`](architecture.md) | **When asked "how does that work".** The flow, the timing, the storage layout |
| [`objections.md`](objections.md) | **Before you go in.** What this audience asks, answered from what the kit really does |

Build from the run sheet. Present the OCP Virt demo from its own
[run sheet](../openshift-virtualization/run-sheet.md) once the environment is up.

---

## The 60-second version

Two repos. Three phases. One command per phase.

1. **Build the ISO** (`image.builder.pipeline`) — `generate-iso.sh` takes your
   hardware details (IP, MAC, disk, NIC), your pull secret, and your SSH key,
   and produces a bootable Agent-Based Installer ISO. Day 0 manifests bake in
   AAP 2.7, OpenShift Virtualization, LVMS, and the Compliance Operator.
2. **Boot the hardware** — write the ISO to USB, boot from it, wait ~45 minutes.
   The cluster installs itself, fully unattended.
3. **Configure the platform** (`sales.demos`) — `setup_edge.yml` installs LVMS
   storage, deploys AAP from its operator, installs CNV, runs a compliance scan,
   and proves the environment by building and timing a real VM.

After phase 3, the environment is identical to an RHDP sandbox — same playbooks,
same job templates, same demo. The difference is you own it.

**What the demo is actually about** is not that we automated a NUC. It is that
the same automation that runs in the cloud runs on hardware under a desk, and
the customer can hold both in their hands.

---

## Why bare metal

Three things RHDP cannot show:

1. **Persistence.** RHDP environments expire. This one does not. You can build
   a demo on Monday and show it on Friday without re-provisioning.
2. **The install.** RHDP gives you a running cluster. A customer evaluating edge
   wants to see how the cluster gets there — the ABI ISO, the unattended boot,
   the Day 0 operators appearing without intervention.
3. **The physical thing.** A NUC on the table is a different conversation than a
   URL on a slide. *"That box is running everything you just saw"* is a sentence
   you cannot say with RHDP.

---

## If you want to run it

Two repos, both public, both cloned to your laptop:

```bash
git clone https://github.com/ericcames/image.builder.pipeline.git
git clone https://github.com/ericcames/sales.demos.git
```

Then follow the [run sheet](run-sheet.md) — it is a step-by-step checklist
with exact commands.

**Prerequisites you will need:**

- A Red Hat pull secret from `console.redhat.com`
- An SSH key pair
- x86_64 hardware with at least 32 GB RAM, 120 GB disk, 8 CPUs
- A laptop on the same network running Fedora or RHEL (for DNS)
- A USB drive (8 GB minimum)

---

## Related

- [OpenShift Virtualization demo](../openshift-virtualization/README.md) — the
  demo you run once the environment is up
- [`../../plan/ocpvirt-demo-plan.md`](../../plan/ocpvirt-demo-plan.md) — why the
  OCP Virt automation is built this way
