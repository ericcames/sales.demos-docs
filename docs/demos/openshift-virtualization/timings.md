# Timings

**Measured, not estimated.** Every number here came off the AAP API after a real
run on a real cluster. Where a figure is quoted in the run sheet or a talk track,
this page is where it came from.

Numbers move. `vm_count` was capped at 10 until it became 2; the OS split changed
what a "build" even means; a survey that said one question now asks four; the
sandbox itself was rebuilt. A timing with no date and no environment beside it is
a claim, not evidence — so each table below carries both.

---

## The headline

**Building the machine is the fast part. Making it useful is the rest.**

The latest pair, one `large` VM each on the rebuilt sandbox (2026-09-15):

| | Linux | Windows |
|---|---:|---:|
| Provision (Terraform apply) | **29s** | **30s** |
| Everything after it | 344s | 690s |
| **Total** | **373s** (~6 min) | **720s** (~12 min) |

Provision is **8%** of the Linux build and **4%** of the Windows one. The VM
exists in about half a minute in both cases; the rest is registration, patching,
configuration and verification — the judgment calls that make a machine usable
rather than merely present.

**Across every run on this page, quote a range:** Linux **6–12 minutes**,
Windows **12–28 minutes**. The spread comes from the environment and from patch
content, not from the automation changing — see
[Tier and count barely move the needle](#tier-and-count-barely-move-the-needle).

That is the demo's actual argument, and it is worth saying out loud rather than
letting the audience assume the clock is measuring virtualization.

---

## Linux and Windows Day 1 — 1 × large, rebuilt sandbox

Sandbox `cluster-v9n68`, rebuilt from RHDP. Both launched from the Templates
page, not the self-service launcher.

### Linux

`Linux Day 1 - 0 Workflow`, workflow job 57, 2026-09-14.

| Node | Elapsed | Share |
|---|---:|---:|
| 1 Provision | 29.4s | 8% |
| 2 Register | **173.2s** | **46%** |
| 3 Configure | 114.1s | 31% |
| 4 Compliance Scan | 49.7s | 13% |
| 5 Check | 5.1s | 1% |
| **Total** | **373s** | |

Register is still nearly half the build, for the reason given under the
2026-09-09 run below.

### Windows

`Windows Day 1 - 0 Workflow`, workflow job 79, 2026-09-15.

| Node | Elapsed | Share |
|---|---:|---:|
| 1 Provision | 29.7s | 4% |
| 2 Patch | **466.3s** | **65%** |
| 3 Configure | 140.1s | 19% |
| 4 Compliance Scan | 63.7s | 9% |
| 5 Check | 17.6s | 2% |
| **Total** | **720s** | |

**Patch is mostly not patching.** Its job events, task by task:

| Task in node 2 | Elapsed |
|---|---:|
| Wait for the guest to accept WinRM — first boot after sysprep | **301.9s** |
| Gather facts | 11.2s |
| Search Windows Update (found 2) | 64.1s |
| Install one update (KB5126149, .NET Framework cumulative) | 85.1s |

Five of Patch's eight minutes are Windows finishing its first boot —
specialize, oobeSystem, and the WinRM listener coming up — before Ansible can
reach the guest at all. That wait is the floor of any Windows cold build.

**Configure did not reboot.** Installing IIS took 88.1s and reported
`reboot_required: False`, so the reboot task was skipped. The 12-minute reboot in
the [performance budget](../../plan/ocpvirt-demo-plan.md) did not recur.

The compliance scan returned **28 of 28** controls compliant.

**Not attributed, and deliberately so:** Configure took 140s here against 542s
on 2026-09-09, and the compliance scan 64s against 331s. The cluster, the VM
count and the WinRM round-trip collapse in `windows_configure` all changed in
between, and none of them was measured on its own. Treat these as a faster run
of the same chain, not as proof of any one cause.

---

## Linux Day 1 — 2 × small

`Linux Day 1 - 0 Workflow`, workflow job 572, earlier sandbox, 2026-09-09.
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

`Windows Day 1 - 0 Workflow`, workflow job 587, earlier sandbox, 2026-09-09.
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

The same two workflows at different tiers and counts, and on two sandboxes:

| Run | Sandbox | Tier × count | Total |
|---|---|---|---:|
| Linux, workflow 516 | earlier, 2026-09-09 | large × 3 | 645s |
| Linux, workflow 572 | earlier, 2026-09-09 | small × 2 | 715s |
| Linux, workflow 57 | rebuilt, 2026-09-14 | large × 1 | **373s** |
| Windows, workflow 530 | earlier, 2026-09-09 | large × 3 | 1509s |
| Windows, workflow 587 | earlier, 2026-09-09 | small × 2 | 1688s |
| Windows, workflow 79 | rebuilt, 2026-09-15 | large × 1 | **720s** |

**Three large VMs finished faster than two small ones — in both families.** Do
not read that as "bigger is faster". Read it as: within this range, tier and
count are *not* what determines wall-clock time, and run-to-run variance is
comparable to the difference between them.

The reason is that the guest-facing nodes run against all hosts in parallel, so
adding a VM adds almost nothing; what varies is per-host work. The clearest case
is Windows Patch — **1071.8s at large × 3 versus 696.0s at small × 2** — which
had nothing to do with size and everything to do with which updates Microsoft had
published and how big they were.

**One VM on the rebuilt sandbox took roughly half as long as either earlier run,
in both families.** The sandbox and the count changed together, so this does not
say which one mattered — only that the environment moves the number far more than
the tier does.

**So do not quote a build time as a function of size.** Quote a range, and know
that the variable parts are the environment and patch content, not the size you
picked.

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

- **Launch before you talk.** The Linux build needs 6 to 12 minutes and the cold
  open plus context is about 13. Start the workflow, then present over it.
- **Windows needs 12 to 28 minutes.** At the low end it finishes over a cold open
  and some context if you launch it first; at the high end it does not. Check how
  the environment ran that day, and if you cannot afford the high end, show it
  pre-built or run it before the call and narrate the job list.
- **The number that lands is the ratio, not the total.** "The machine existed in
  thirty seconds; the rest of the time is the decisions" is a better beat than
  any single figure — and it stays true when the totals move.

---

## Method

Durations are the `elapsed` field on each job and workflow job from
`/api/controller/v2/`, not stopwatch readings. Reproduce with:

```bash
curl -sk -u admin:$AAP_PASSWORD \
  "https://<aap_hostname>/api/controller/v2/workflow_jobs/<id>/workflow_nodes/" \
  | jq -r '.results[].summary_fields.job | "\(.name)\t\(.status)\t\(.elapsed)s"'
```

Per-task figures, such as the WinRM wait inside Patch, are the `duration` of
each `runner_on_ok` event under `/api/controller/v2/jobs/<id>/job_events/`.

**Environments:**

- **Rebuilt sandbox** (workflow jobs 57 and 79): `cluster-v9n68`, AAP 2.7
  (controller 4.8.6), `Sales Demos - OCP Virt EE` v1.2.0, sales.demos at
  `068a247`, 2026-09-14/15. The Linux VM was still running when the Windows run
  started; nothing else was.
- **Earlier sandbox** (every other run): AAP 2.7 (controller 4.8.6),
  `Sales Demos - OCP Virt EE` v1.2.0, 2026-09-09. Cluster had no other demo VMs
  running.

Re-measure after an environment rebuild — RHDP hardware has changed under this
demo before, and the two sandboxes above are the evidence.
