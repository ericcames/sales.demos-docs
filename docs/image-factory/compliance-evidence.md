# Compliance evidence

Hardening an image is the straightforward half. **Proving it stayed hardened is
the half that gets asked about with a customer in the room.**

This page is the argument for why anything here can be believed — including the
time it could not be.

## What counts as evidence

Three things that look like proof and are not:

**A green build.** A pipeline that completes says the automation ran, not that
it worked. In this repo every defect found during the Windows phase was found by
running the thing; `ansible-lint` passed at the production profile through all
of them. **Lint executes nothing.**

**A compliance label.** A tag carrying `cis.level=L1` is a claim by whoever
published it. It is worth exactly as much as the check standing behind it — and
for a while, there was none.

**A green compliance scan in the demo workflow.** The consumer's
`Windows Day 1 - 4 Compliance Scan` defaults to *report*, not *gate*
(`windows_compliance_fail_on_noncompliant: false`), deliberately, so a red node
never appears in front of a customer. Turn it on when you want it to gate. Until
you do, a green run means the scan completed.

What does count: **a number from a scanner that could have failed**, or **a
reading taken from the artifact itself by something that refuses to guess**.

## RHEL 9 — a scanner that can fail

The AMI is deployed to a throwaway EC2 instance and scanned with OpenSCAP. The
XCCDF results are parsed into a score with a numeric gate.

| | |
|---|---|
| Score | **98.07** against a gate of **95** |
| Breakdown | 254 pass, 5 fail, 33 N/A, 0 not-checked |
| Formula | `pass / (pass + fail)`, excluding N/A and not-checked |

Two properties make this real evidence:

**The gate could have failed.** The baseline run scored 94.94 against the same
95 gate — 13 failures, not 5. The number moved because the image changed, which
is what a measurement is supposed to do.

**Exempt rules still count against the raw score.** The pipeline does not remove
its own exemptions from the denominator. Effective compliance (~99.6%) is
computed later by OPA, at policy-evaluation time, from a separate curated list —
so the flattering number and the honest number are produced by different systems
and both are visible.

The five remaining failures, their severities and their written rationale are in
[RHEL 9](rhel9.md#the-five-failures-are-documented-not-hidden).

## Windows 2022 — read off the disk, by something that refuses to guess

OpenSCAP ships no Windows agent, so there is no score to quote. The evidence is
built differently.

`playbooks/scripts/verify_cis_disk.py` opens the qcow2 **about to be packaged**,
reads the `SOFTWARE` and `SYSTEM` registry hives, and decides whether the disk
supports a CIS level. It **refuses to apply the label when it cannot reach a
verdict** — an inconclusive read fails the publish rather than passing it.

Two design choices carry the weight:

**It runs inside the publish, so the label is an output of verification, not an
input to it.** The operator cannot assert a level; the disk reports one.

**It only checks properties that cannot exist on a clean install.** This is the
trick that makes offline verification meaningful. A setting that a default
Windows install would also have proves nothing. Ten such controls are checked on
the media, and again on the booted, sysprepped guest's own disk.

The result for the current image: **10 of 10** impossible-on-default controls,
and **27 of 27** across the full control set, on a guest confirmed rebuilt from
the DataSource serving that exact tag.

A second, independent reader — `utilities/inspect-golden-image.py` in
`sales.demos` — checks a published tag before a cluster is pointed at it. Two
implementations, two repos, so agreement means something.

## The time the label was false

This is the most useful thing on this page, and it is worth telling in full.

A Windows image was published as `win2k22-cis-l1-golden:20260907-0516`, carrying
a `cis.level=L1` label. The disk underneath was the **unhardened** build from
two days earlier — byte-identical to the deliberately unhardened image — because
a `creates:`-guarded conversion step had repackaged a stale local qcow2 rather
than the freshly hardened one.

The label recorded what the operator intended. Nothing read the media back.

Downstream, a consumer cluster advertised the hardened tag while every clone
booted the unhardened one. The demo guest scored **9 of 27**, and the talk track
was inviting customers to read that report.

Three things had to be true at once for it to survive:

- `creates:` tests **existence, not currency**. A stale intermediate satisfied it
- The consumer decided whether to import from **whether the DataSource was
  `Ready`**, never from *which image it served*. After the first successful
  import, every environment is Ready forever
- Every verification asked "Ready?" and "Bound?" — both true of the wrong image

### What was built because of it

| Change | Effect |
|---|---|
| `verify_cis_disk.py` gates the label | The level is read from the disk, and an inconclusive read fails |
| Intermediates are purged before conversion | A stale qcow2 cannot be repackaged |
| The consumer's import decision is **identity**, not readiness | The served image is re-read and asserted on every run, including runs that import nothing |
| A DataVolume's source is immutable | A changed tag deletes and re-imports rather than editing in place |

**The lesson, stated once: `Ready` and `Bound` were both true of the wrong
image. Desired state is tested, never trusted.**

That is the same principle as the secret guard in `sales.demos`, which does not
trust its own `.gitignore` rule but verifies it with `git check-ignore` — a rule
that is merely present can be silently wrong.

## Things this factory does not prove

Volunteered, because they come up:

**The containerDisk lineage is not independently scanned.** The RHEL
containerDisk inherits the same CIS profile and packages as the scanned AMI,
applied by Image Builder at compose time, but no separate OpenSCAP run is
performed on it. The 98.07 belongs to the AMI lineage. Say so.

**Windows has no scanner score, and never will** without a Windows OpenSCAP
agent. 27 of 27 is a control-by-control measurement, not a benchmark score.

**A CIS level is not an audit.** These are benchmark controls measured by
tooling. Nobody has certified anything.

**Pinned collections are not a pinned environment.** Every collection pin can
match exactly while the laptop runs one `ansible-core` and the execution
environment runs another. Quote which layer you mean.

## Related

- [RHEL 9](rhel9.md) — the scanner path in detail
- [Windows](windows.md) — the offline verification path, and the four controls that had to be disabled
- [SNO installer](sno-kit.md) — where the honest number is 186 of 188
