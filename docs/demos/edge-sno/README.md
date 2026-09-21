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

**This is a Red Hat tested topology, not a home-lab approximation.** AAP 2.7's
[Operator growth topology](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/plan-ref_ocp_a_env_a)
— the documented getting-started deployment model for Ansible Automation
Platform on OpenShift — says *"Red Hat tests a Single Node OpenShift (SNO)
cluster"*. That is what is running on the NUC.

---

## Red Hat links

Start here before presenting. Confirmed publicly available as of 2026-09-21.

| Link | What it is |
|---|---|
| [Choosing the right edge platform](https://developers.redhat.com/articles/2026/09/11/red-hat-edge-platforms-choosing-right-one-your-use-case) | Daniel Froehlich, 2026-09-11, part 1 of 3. Podman → MicroShift → single-node → 2-node → compact, with the hardware floor for each. **Read this before an edge conversation** |
| [Matching edge topologies to your physical footprint](https://developers.redhat.com/articles/2026/09/18/matching-openshift-edge-topologies-your-physical-footprint) | Same author, 2026-09-18, part 2. The four OpenShift topologies, and the current single-node minimum: 4 vCPU, 16 GB, 120 GB |
| [OpenShift edge computing](https://www.redhat.com/en/technologies/cloud-computing/openshift/edge-computing) | Product page — the surface to send a customer to |
| [Installing on a single node](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/installing_on_a_single_node/index) | OCP 4.20 docs. The supported procedure this kit automates |
| [Agent-Based Installer](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/installing_an_on-premise_cluster_with_the_agent-based_installer/index) | What `generate-iso.sh` wraps |
| [Zero Touch Provisioning](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/edge_computing/ztp-deploying-far-edge-clusters-at-scale) | The fleet answer to *"how do I manage fifty of these"* |
| [Red Hat Advanced Cluster Management](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.14) | What ZTP runs on |
| [Disconnected environments](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/disconnected_environments/index) | Backs the disconnected-install answer |
| [Deploy SNO at the edge](https://www.redhat.com/en/blog/deploy-openshift-at-the-edge-with-single-node-openshift) | Eran Cohen, 2021-08-11. The original announcement — **do not quote its numbers**. It says developer preview and 8 vCPU, both superseded |
| [SNO at the manufacturing edge](https://www.redhat.com/en/blog/single-node-openshift-manufacturing-edge) | 2021. A named vertical use case; still a useful story |

### Deploying AAP on it — the supported path

For the customer who wants to do this themselves, rather than clone our repos.

| Link | What it is |
|---|---|
| [Operator growth topology](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/plan-ref_ocp_a_env_a) | **The one to open first.** Red Hat's getting-started model for AAP on OpenShift, tested on Single Node OpenShift: 32 GB, 16 CPUs, 128 GB disk, 3000 IOPS. Every AAP component is a separate container on the one node |
| [Plan your installation on OpenShift](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/install-assembly_operator_install_planning) | Prerequisites and decisions before the operator goes on |
| [Choose an installation type](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/install-con_choosing_installation_type) | Operator vs. containerized vs. RPM |
| [Install the AAP Operator through OperatorHub](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/install-assembly_install_aap_operator) | The procedure our Day 0 manifest automates |
| [Customize your AAP Operator](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/install-assembly_operator_customize_aap) | The `AnsibleAutomationPlatform` CR reference behind [`architecture.md`](architecture.md)'s snippet |

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

For how the installer ISO itself is produced — the Day 0 manifests, the CIS
posture of stock RHCOS, and why the kit is not published to a registry — see
[Image Factory → SNO Installer](../../image-factory/sno-kit.md).

---

## The 60-second version

Two repos. Three phases. One command per phase.

1. **Build the ISO** (`image.builder.pipeline`) — `generate-iso.sh` takes your
   hardware details (IP, MAC, disk, NIC), your pull secret, and your SSH key,
   and produces a bootable Agent-Based Installer ISO. Day 0 manifests bake in
   AAP 2.7, OpenShift Virtualization, LVMS, and the Compliance Operator.
2. **Boot the hardware** — write the ISO to USB, boot from it, wait ~45 minutes.
   The cluster installs itself, fully unattended.
3. **Configure the platform** (`sales.demos`) — install LVMS storage, deploy AAP
   from its operator, install CNV, run a compliance scan, and prove the
   environment by building and timing a real VM. Five playbooks today; a single
   `setup_edge.yml` that chains them is
   [sales.demos#406](https://github.com/ericcames/sales.demos/issues/406).

After phase 3, the environment is identical to an RHDP sandbox — same playbooks,
same job templates, same demo. The difference is you own it.

**What the demo is actually about** is not that we automated a NUC. It is that
the same automation that runs in the cloud runs on hardware under a desk, and
the customer can hold both in their hands.

---

## Why bare metal

**And it is the documented topology.** The strongest thing to say about this
box is not that we automated it — it is that Red Hat's own getting-started
deployment model for AAP on OpenShift is
[tested on Single Node OpenShift](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/plan-ref_ocp_a_env_a).
A customer looking at the NUC is looking at the shape Red Hat tests, not a
scaled-down imitation of a real deployment.

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
- x86_64 hardware with at least 32 GB RAM, 120 GB disk, 8 CPUs. Red Hat's
  tested AAP-on-SNO configuration is 16 CPUs and 128 GB —
  see [hardware minimums](architecture.md#hardware-minimums) for which
  number to quote when
- A laptop on the same network running Fedora or RHEL (for DNS)
- A USB drive (8 GB minimum)

---

## Related

- [OpenShift Virtualization demo](../openshift-virtualization/README.md) — the
  demo you run once the environment is up
- [`../../plan/ocpvirt-demo-plan.md`](../../plan/ocpvirt-demo-plan.md) — why the
  OCP Virt automation is built this way
