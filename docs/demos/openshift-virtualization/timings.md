# Timings

**Measured, not estimated.** Every number here came off the AAP API after a real
run on a real cluster. Where a figure is quoted in the run sheet or a talk track,
this page is where it came from.

Numbers move. `vm_count` was capped at 10 until it became 2; the OS split changed
what a "build" even means; a survey that said one question now asks four. A
timing with no date and no environment beside it is a claim, not evidence — so
each table below carries both.

---

## The headline

**Building the machine is the fast part. Making it useful is the rest.**

| | Linux | Windows |
|---|---:|---:|
| Provision (Terraform apply) | **64s** | **73s** |
| Everything after it | 644s | 1615s |
| **Total** | **715s** (~12 min) | **1688s** (~28 min) |

Provision is **9%** of the Linux build and **4%** of the Windows one. The VM
exists in about a minute in both cases; the remaining ten to twenty-seven minutes
are registration, patching, configuration and verification — the judgment calls
that make a machine usable rather than merely present.

That is the demo's actual argument, and it is worth saying out loud rather than
letting the audience assume the clock is measuring virtualization.

---

## Linux Day 1 — 2 × small

`Linux Day 1 - 0 Workflow`, workflow job 572, sandbox, 2026-09-09.
Launched from `Self-Service - Request Linux Server`.

| Node | Elapsed | Share |
|---|---:|---:|
| 1 Provision | 63.9s | 9% |
| 2 Register | **331.8s** | **46%** |
| 3 Configure | 198.0s | 28% |
| 4 Compliance Scan | 99.0s | 14% |
| 5 Check | 15.5s | 2% |
| **Total** | **715s** | |

**Register dominates, and that is not a defect.** The CNV RHEL 9 image ships with
no repositories at all, so the guest has to attach to the Red Hat CDN before a
single `dnf` task can run. Nearly half the build is the machine being entitled to
content. It is also why the chain cannot be reordered — Configure fails outright
on an unregistered guest.

---

## Windows Day 1 — 2 × small

`Windows Day 1 - 0 Workflow`, workflow job 587, sandbox, 2026-09-09.
Launched from `Self-Service - Request Windows Server`.

| Node | Elapsed | Share |
|---|---:|---:|
| 1 Provision | 72.7s | 4% |
| 2 Patch | **696.0s** | **41%** |
| 3 Configure | 542.4s | 32% |
| 4 Compliance Scan | 330.8s | 20% |
| 5 Check | 39.4s | 2% |
| **Total** | **1688s** | |

**Windows is roughly 2.4× Linux**, and Patch is the largest single piece even in
its *bounded* mode — `windows_patching_state: one` installs exactly one update.

What that one update was, this run:

```
Found by the search: 2
Installed: 1        2026-09 Cumulative Update for .NET Framework 3.5, 4.8
                    and 4.8.1 ... (KB5126149)
Failed: 0
Still behind by 1 update(s).
```

Note the pick landed on a *Cumulative* update even though the role prefers to
avoid those. Both pending updates matched the cumulative pattern, so there was
nothing smaller to choose — the documented fallback, working correctly.

---

## Tier and count barely move the needle

The same two workflows, at a different tier and count, three hours earlier:

| Run | Tier × count | Total |
|---|---|---:|
| Linux, workflow 516 | large × 3 | 645s |
| Linux, workflow 572 | small × 2 | **715s** |
| Windows, workflow 530 | large × 3 | 1509s |
| Windows, workflow 587 | small × 2 | **1688s** |

**Three large VMs finished faster than two small ones — in both families.** Do
not read that as "bigger is faster". Read it as: within this range, tier and
count are *not* what determines wall-clock time, and run-to-run variance is
comparable to the difference between them.

The reason is that the guest-facing nodes run against all hosts in parallel, so
adding a VM adds almost nothing; what varies is per-host work. The clearest case
is Windows Patch — **1071.8s at large × 3 versus 696.0s at small × 2** — which
had nothing to do with size and everything to do with which updates Microsoft had
published and how big they were.

**So do not quote a build time as a function of size.** Quote a range, and know
that the variable part is patch content, not hardware.

---

## Teardown

| | Elapsed | VMs destroyed |
|---|---:|---|
| `Linux Day 1 - Teardown` (job 578) | 85.5s | 2 |
| `Windows Day 1 - Teardown` (job 581) | 160.9s | 3 |

Both destroy the VMs and deregister them from AAP while preserving OpenShift
Virtualization, the boot-source DataSources, the Terraform state namespace, the
VM namespace, and the `sd1.*` instance type catalog.

---

## Self-service launcher overhead

| | Elapsed |
|---|---:|
| `Self-Service - Request Linux Server` (job 571) | 16.4s |
| `Self-Service - Request Windows Server` (job 584) | 18.0s |

The launcher validates its inputs, fires the workflow and returns — it does not
wait. Roughly seventeen seconds is the entire cost of the portal entry point;
everything after that is the same workflow an SE runs from the Templates page.

---

## Pacing a demo with these

- **Launch before you talk.** The Linux build needs ~12 minutes and the cold open
  plus context is about 13. Start the workflow, then present over it.
- **Windows is not a live-build demo at 28 minutes.** Show it pre-built, or run
  it before the call and narrate the job list.
- **The number that lands is the ratio, not the total.** "The machine existed in
  sixty-four seconds; the other eleven minutes are the decisions" is a better
  beat than any single figure — and it stays true when the totals move.

---

## Method

Durations are the `elapsed` field on each job and workflow job from
`/api/controller/v2/`, not stopwatch readings. Reproduce with:

```bash
curl -sk -u admin:$AAP_PASSWORD \
  "https://<aap_hostname>/api/controller/v2/workflow_jobs/<id>/workflow_nodes/" \
  | jq -r '.results[].summary_fields.job | "\(.name)\t\(.status)\t\(.elapsed)s"'
```

**Environment for every run above:** sandbox, AAP 2.7 (controller 4.8.6),
`Sales Demos - OCP Virt EE` v1.2.0, 2026-09-09. Cluster had no other demo VMs
running. Re-measure after an environment rebuild — RHDP hardware has changed
under this demo before.
