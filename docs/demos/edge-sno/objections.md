# Objections and questions — Edge / Single Node OpenShift

What this audience actually asks, and answers grounded in what the kit really
does.

Rules for using this:

- **Answer the question that was asked**, then stop. A long answer to a short
  question reads as evasion.
- **If the answer is "it doesn't do that", say so first**, then say what it does
  do. Never lead with the workaround.
- Everything here is checkable in a public repository.

---

## "Why not just use RHDP?"

**Answer the question directly.** RHDP is great for what it does — spinning up
a pre-configured environment in minutes. Three things it cannot do:

> **"RHDP gives you a running cluster. It doesn't show you the cluster getting
> there. For an edge conversation, the install story — unattended boot, Day 0
> operators, no manual steps — is the whole point. And RHDP environments expire.
> This one doesn't."**

The third thing — the physical hardware — only matters if it is in the room.
Do not mention it in a remote session unless asked.

---

## "What if my hardware is different?"

> **"The ISO generator takes nine hardware values as required inputs and
> validates them before it touches anything. Every hardware-specific value — IP,
> MAC, disk device, NIC name, hostname — is a parameter, not a hardcoded
> default. If your hardware meets the minimums (32 GB RAM, 120 GB disk, 8 CPUs,
> x86_64), it should work."**

If they ask about ARM: SNO supports ARM, but this kit has not been tested on
it. Say so honestly.

If they ask about NVMe vs SATA: both work. The `--disk` flag takes any block
device — `/dev/nvme0n1` works the same as `/dev/sda`.

---

## "Can I run just Virt without AAP?"

**Answer the limitation first.**

> **"Today the kit installs all four operators. We're adding operator selection
> profiles — `--profile virt-only` would give you CNV and LVMS without AAP.
> That's tracked in the repo and coming soon."**

Link: [image.builder.pipeline#108](https://github.com/ericcames/image.builder.pipeline/issues/108)

In the meantime: they can delete the `aap/` manifests from the generated
`openshift/` directory before building the ISO. It works but is not a
supported path.

---

## "How do I update OCP on this?"

> **"The same way you update any OpenShift cluster — through the console or
> `oc adm upgrade`. SNO does an in-place update: the node cordons itself,
> applies the update, and uncordons. Workloads go down during the reboot.
> That's the trade-off of single-node — no rolling update."**

---

## "What about disconnected installs?"

**Answer the limitation first.**

> **"This kit requires network access at install time — the ABI ISO pulls
> container images from the Red Hat registries during bootstrap. A fully
> disconnected install needs a mirror registry, and this kit does not set
> one up. That's a real gap if your edge sites have no network at install
> time."**

If they need disconnected: point them to the official OpenShift documentation
for mirror registries and disconnected ABI installs. The kit's templates could
be adapted, but it has not been done.

---

## "Where are the credentials?"

> **"The pull secret and SSH key are provided at ISO build time and embedded in
> the Ignition config. They never leave the generated ISO, and the ISO is never
> published — it stays on the USB drive. The installer kit itself — the
> templates, the manifests, the script — is in a public repo with no secrets
> in it."**

For the AAP side, the credentials story is the same as the OCP Virt demo:
vault-encrypted `secrets.yml`, local only, never tracked. See
[OCP Virt objections](../openshift-virtualization/objections.md) for that answer.

---

## "Is this production-ready?"

**Answer honestly.**

> **"This is a demo platform, not a production reference architecture. It runs
> on one disk with no redundancy, DNS is dnsmasq on a laptop, and there's no
> backup strategy. The automation is production-quality — idempotent,
> tested, in version control — but the infrastructure it runs on is a home
> lab. For production edge, you'd add proper DNS, multi-path storage, and
> backup. The playbooks don't change."**

---

## "How do you manage fifty of these?"

> **"You don't, with this tool. This is one cluster, fully automated. At scale
> you'd use Red Hat Advanced Cluster Management and Zero Touch Provisioning —
> ZTP takes the same Agent-Based Installer concept and adds fleet management,
> policy enforcement, and truly zero-touch deployment via BMC/IPMI. What this
> demonstrates is that the platform deploys unattended, which is the prerequisite
> for ZTP."**

Send them to [Zero Touch Provisioning](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/edge_computing/ztp-deploying-far-edge-clusters-at-scale)
and [Red Hat Advanced Cluster Management](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.14).

---

## "Can I have this?"

**Two different people ask this. Hear which one it is.**

*Another SE who wants the demo:*

> **"Yes. Both repos are public. Clone them, follow the run sheet, and you'll
> have your own environment. The run sheet is written for someone doing it for
> the first time."**

*A customer who wants AAP on OpenShift:* they do not want our automation, they
want a supported path. Give them Red Hat's, not ours.

> **"What you're looking at is Red Hat's Operator growth topology — the
> documented getting-started deployment for AAP on OpenShift. Red Hat tests it
> on Single Node OpenShift, 32 gig, 16 CPUs, 128 gig of disk. Start at the
> planning guide, install the operator from OperatorHub, and you're on the same
> path. Our repos just show you what it looks like fully automated."**

| Send them to | For |
|---|---|
| [Operator growth topology](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/plan-ref_ocp_a_env_a) | The topology and its sizing |
| [Plan your installation on OpenShift](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/install-assembly_operator_install_planning) | What to decide before starting |
| [Choose an installation type](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/install-con_choosing_installation_type) | Operator vs. containerized vs. RPM |
| [Install through OperatorHub](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7/install-assembly_install_aap_operator) | The procedure itself |

**If they ask whether all of it really fits on one node:** yes, and that is the
documented shape. Controller, hub, EDA, gateway, metrics, PostgreSQL and Redis
are separate containers on the same node. The operator-managed database is
supported up to 100 connections and 100 GB; past that you move it out.

---

## Questions to ask *them*

**After the install story:**
- *"How are you deploying OpenShift today — IPI, UPI, or something else?"*

**After the live demo:**
- *"What workloads would you run at the edge if the platform was this easy to
  deploy?"*

**Before the close:**
- *"Is the conversation here about running OpenShift at edge sites, or about
  running VMs on the OpenShift you already have?"* — they are very different
  next meetings.

---

## Things not to say

- **"This replaces VMware at the edge."** It might, but that is their conclusion
  to reach, not yours to claim. Show the demo; let them draw the comparison.
- **"Zero touch."** It is not. Someone writes a USB and changes the boot order.
  Say "unattended" — that is accurate and still impressive.
- **"It scales to hundreds of sites."** This kit does not. RHACM + ZTP does.
  Conflating them will cost you credibility with anyone who has deployed at
  scale.
- **"The same as production."** It is the same automation. It is not the same
  infrastructure. Say which one you mean.
