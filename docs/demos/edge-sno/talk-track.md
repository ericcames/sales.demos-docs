# Talk track — Edge / Single Node OpenShift

**This is the story behind the kit, not a script.** The OCP Virt demo has its
own [talk track](../openshift-virtualization/talk-track.md) for the customer
session. This document is about why bare metal matters and what it proves that
RHDP cannot.

Read this before the meeting. Use it when the conversation turns to edge
strategy, on-prem deployment, or "what does this look like outside the cloud."

---

## Who is in the room

**You are the pre-sales engineer.** You have a NUC (or similar hardware) that
is running everything the customer is about to see.

**They are platform engineers, infrastructure architects, or operations leads**
evaluating OpenShift for edge or on-prem workloads. They have probably run
VMs on traditional hypervisors (VMware, Hyper-V, KVM). They may be skeptical
that Kubernetes belongs at the edge.

| They do not care about | They care intensely about |
|---|---|
| How many YAML files you wrote | Whether this actually runs on constrained hardware |
| The Ansible module names | Whether they can reproduce this without your help |
| Cloud-scale numbers | What happens when the network goes down |
| Product roadmap slides | Whether the thing they are looking at is real |

**Do not oversell the edge story.** SNO is a specific topology for a specific
use case. It is not "OpenShift everywhere" — it is OpenShift where you need
one node and cannot afford three. Say that.

---

## Beat 1 -- The physical thing (before the demo)

If the hardware is in the room, start there. Point at it.

> **"That box is running everything I'm about to show you. Single Node
> OpenShift, Ansible Automation Platform, OpenShift Virtualization — the same
> stack you'd run in a datacenter, on hardware that fits under a desk."**

**Why this beat exists.** A physical thing changes the conversation. A URL
on a slide is a demo. A box on the table is a proof of concept. The customer
can ask "what are its specs" and you can answer from the BIOS, not a catalog
page.

If the hardware is not in the room (remote meeting), show the node detail
in the OpenShift console instead. The CPU/memory/storage numbers are real
either way.

**Transition:** *"Let me show you what it's running."*

---

## Beat 2 -- The install story (2 minutes)

> **"This cluster installed itself. I wrote the hardware details into a
> script, burned a USB, and walked away. Forty-five minutes later it was
> running OpenShift with four operators already installed — no human
> interaction after the boot."**

Walk through the inputs table from `generate-iso.sh --help`. Nine hardware
values, a pull secret, an SSH key. That is the entire interface.

> **"Everything that makes this cluster different from any other SNO is in
> those nine values. The rest — which operators to install, which channels to
> track, how to partition the disk — is in the kit, and the kit is in a
> public repo."**

**Why this beat exists.** Edge customers ask "how do I deploy at scale."
The answer is: the ISO generation is parameterized and scriptable. One ISO
per site, one USB per site, no manual steps after boot. Say that, and then
say the honest caveat:

> **"Scaling this to fifty sites is a different problem — you'd use RHACM
> and Zero Touch Provisioning rather than USB drives. What this shows is that
> the platform itself deploys unattended, which is the prerequisite for any
> of those tools."**

**Transition:** *"Once the cluster is up, it gets the same automation as
our cloud environments."*

---

## Beat 3 -- Same automation, different hardware (3 minutes)

This is the pivot from "edge story" to "OCP Virt demo." Open AAP and show
the job templates.

> **"These are the same job templates that run on our RHDP demo
> environments. Same playbooks, same survey, same workflow. The only thing
> that changed is the cluster's connection URL in one YAML file."**

Show `connection.yml` briefly — the three lines that differ per environment.
Then launch the Build Demo VM workflow.

**Why this beat exists.** The claim is portability: one set of automation,
multiple targets. The evidence is that you are running it, right now, on
hardware that is visibly different from a cloud instance. Do not belabor the
point — launch the workflow and let it prove itself.

**Transition to the OCP Virt talk track.** From here, the session is the
standard OCP Virt demo. Switch to the
[OCP Virt talk track](../openshift-virtualization/talk-track.md#beat-1-cold-open-on-the-destination-03).

---

## Beat N-1 -- The honest bits

Volunteer these before anyone asks:

- **Single node means no live migration.** The VM is eligible
  (`LiveMigratable=True`) but has nowhere to go. Multi-node edge topologies
  exist — this demo does not show them.
- **The install is not zero-touch.** Someone has to write the USB and change
  the boot order. Real edge-at-scale uses RHACM + ZTP. This proves the
  platform deploys unattended, not that the delivery mechanism scales.
- **Network dependency at install time.** The ABI ISO pulls container images
  during install. A fully disconnected install needs a mirror registry, which
  this kit does not set up.
- **This is a home lab, not a production edge site.** DNS is dnsmasq on a
  laptop. Storage is one disk. There is no redundancy. Say so — it is more
  credible than pretending otherwise.

---

## Beat N -- Close

> **"Everything you just saw — the installer kit, the Ansible playbooks, the
> Terraform, the demo itself — is in two public repositories. The kit is
> parameterized for your hardware. If you want to try this on your own box,
> the run sheet is published and it works."**

Then pick one:

- *"What does your edge footprint look like today?"*
- *"Would it be useful to run this against hardware in your environment?"*
- *"Who on your team would own the Day 2 operations side of this?"*

---

## If you only get ten minutes

Keep beats 1, 2, and the honest bits. Skip beat 3 (the live OCP Virt demo)
and replace it with the OCP Virt screenshots — the demo page, the workflow
graph, the survey. The edge story stands on its own without a live VM build.

---

## Where the words come from

| Claim | Source |
|---|---|
| "Nine values" for the ISO | `generate-iso.sh` required flags |
| "Forty-five minutes" install time | Measured on NUC, 2026-09-08 |
| "Same job templates" across environments | `inventory/group_vars/aap/` — shared across sandbox, demo, edge |
| "One YAML file" difference per environment | `inventory/group_vars/<env>/connection.yml` |
| Partition layout and `growpart` behavior | `image.builder.pipeline/docs/design.md` section 11.6 |
| DNS setup | `image.builder.pipeline/docs/design.md` section 11.9 |
