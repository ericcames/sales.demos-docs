# Facts and drift

Every Day 1 build already ends by gathering the guest's facts, caching them in
AAP's database and publishing them back to the guest as a page. Day 2 lets you
re-run just that, and report what changed since last time.

This page is the detail behind those buttons: what AAP actually knows, which of
it is safe to promise a customer, and the two fields that look like drift
signals and are not.

Presenting? The buttons are
[`Linux Day 2 - Gather Facts`](running-from-aap.md) and
`Windows Day 2 - Gather Facts`, both labelled `read-only` and safe mid-demo. On
a laptop the same work is
[`/sales-demos-facts`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-facts/SKILL.md).

---

## Nothing writes the cache, and that is the point

There is no task that pushes facts to AAP. Not an `ansible.controller` module,
not a `uri` POST, nothing. The entire mechanism is two settings:

- `gather_facts: true` in the playbook, and
- `use_fact_cache: true` on the job template.

That is worth saying out loud in front of a customer, because the obvious
assumption is that someone wrote code to do it. The role
[says so in a comment](https://github.com/ericcames/sales.demos/blob/main/playbooks/roles/demo_facts/tasks/main.yml)
precisely so that a reader looking for the missing code stops looking.

It is also why the capability went unused for so long. `use_fact_cache` has been
set on the Day 1 check step since sales.demos#47, so every build was already
populating the Facts tab — and nothing in the template name, the docs or the job
output mentioned it. The rename to `… - 5 Check and Gather Facts` exists to make
the plumbing visible.

The *curated* summary reaches the same cache by the same route: the role builds
`demo_facts_summary` with `cacheable: true`, so it is stored beside the raw
facts and is queryable from the API.

---

## The finding: AAP says your KVM guest is "NA"

A KubeVirt guest reports its virtualization facts as the literal string `"NA"`.
Not absent — *the two-character string*. So `| default()` never fires, and
anything reading the raw fact displays `NA`.

Confirmed on the live sandbox on 2026-09-16, both values sitting in the same
host's cache at the same moment:

```json
"ansible_virtualization_type": "NA",
"ansible_virtualization_role": "NA",

"demo_facts_summary": {
  "virtualization": { "type": "KVM", "role": "guest" }
}
```

**Unaided, AAP's Facts tab gives the least convincing possible answer in a Red
Hat virtualization demo.** A customer who clicks into the raw facts to check
your claim finds `NA`. The curated summary is what makes it read `KVM` /
`guest`, and it is only in the database to be found because of `cacheable:
true`.

This is worth showing deliberately rather than avoiding. It is a real property
of the platform, the fix is one normalisation, and the audience gets to watch
you show them the unflattering number first.

!!! note "Why it happens on both operating systems"

    On RHEL the detection falls through to an `NA` default. `ansible.windows`'
    `setup.ps1` ends its own virtual-machine detection with the same literal
    fallback, and its manufacturer map carries a `KubVirt` typo — so a guest
    that identified itself correctly would miss anyway.

### Three consumers, one rule, enforced

The same `"NA"` has to be normalised by the demo page, by `facts.json` and now
by `facts.html`. Three copies of one rule is exactly how sales.demos#160
happened: a live guest served a page reading `KVM (guest)` beside a file it
invited you to curl that said `NA`.

Consolidating them is a refactor of the Day 1 critical path, so instead the
copies stay and **drift is made impossible**:
[`utilities/check-fact-normalisation.py`](https://github.com/ericcames/sales.demos/blob/main/utilities/check-fact-normalisation.py)
compares the three expressions and fails CI if any one moves alone.

It checks that the three **agree**, not that they are **right**. Three identical
copies of a wrong rule still pass — correctness is proven by running against a
real KubeVirt guest, which the Day 1 chain does.

---

## Two artifacts, two snapshots — say this to presenters

The guest serves two fact files, and **they are not the same snapshot**.

| | Written by | When | Refreshed by a Day 2 re-gather? |
|---|---|---|---|
| `<web_url>/facts.json` | the **configure** role | step 3, provisioning time | **No** |
| `<web_url>/facts.html` | the **`demo_facts`** role | step 5, and every re-gather | **Yes** |

Measured on one live pair: `facts.json` said `13:55:00Z` while `facts.html` said
`14:48:12Z` on the same host — **53 minutes apart on Linux, 80 on Windows**.

Both files are honest about themselves. What was wrong, briefly, was the page's
own footer calling `facts.json` "the machine-readable subset", which claims they
are the same data. They share a schema, not a moment.

!!! warning "Do not promise that curling `facts.json` shows what the report shows"

    Say `facts.json` is the provisioning-time snapshot and `facts.html` is
    current. **This matters most on a drift demo:** re-running Gather Facts
    refreshes the page and not the JSON, so a customer following along with
    `curl` sees a timestamp that has not moved.

**This is deliberate, not a gap.** Having `demo_facts` republish `facts.json`
would put two producers on one file — the drift sales.demos#160 warns about —
and would break the `renderer-matches-role` CI contract for no gain.

Where both carry a value, the values must agree. Virtualization must read `KVM`
/ `guest` in the page, in `facts.json` and in the Facts tab.

---

## Drift: what changed since last time

`use_fact_cache` re-stamps the facts every run, so "what is true now" is
available for free. The stronger claim — and the reason to keep facts in a
database rather than a text file — is **what changed**.

### The timing is the mechanism

**AAP writes the fact cache *after* a job finishes.** So a job that reads the
host's `/ansible_facts/` during its own run gets the **previous** run's facts.
That is what makes this a real diff rather than a comparison with itself.

The job reads back through AAP's own API, two calls, delegated to the control
node:

```
GET /api/controller/v2/hosts/?name=<inventory_hostname>   -> id
GET /api/controller/v2/hosts/<id>/ansible_facts/          -> the previous run's facts
```

`/api/controller/v2/`, **not** `/api/v2/`. The legacy standalone-Controller path
returns HTML through the 2.7 gateway, so a caller using it dies on a JSON decode
error that names nothing useful.

It compares curated summary against curated summary — the same shape in both
directions — rather than diffing a megabyte of raw facts dominated by
timestamps.

### It degrades, it never fails

No credential attached, no host record, no previously cached facts, an
unreachable API: each of these ends with **the current facts reported anyway**
and a line saying why there was no comparison.

On a freshly built guest, "no prior facts" is the correct state, not an error.
The report omits its drift section entirely on a first gather rather than
showing an empty one — "Changes: none" on a machine that has never been compared
invites exactly the wrong conclusion.

### Two fields that are not drift signals

Both of these moved on a guest that had done nothing, and both would have made
the report cry wolf on every run.

**`uptime.last_boot` is rounded to the minute on Linux.** It is derived from
`epoch - uptime_seconds`, two facts sampled a moment apart, so the difference
jitters. Job 252 reported `last_boot` moving from `13:19:55Z` to `13:19:56Z` on
a host that had not rebooted. Windows is unaffected — `ansible_lastboot` is
recorded by the OS, not computed.

**`network.domain` is not compared at all.** On Linux it comes from
`ansible_domain`, a reverse lookup, and the guest has several Service DNS
records pointing at it, so which one answers varies. Measured across three runs
with nothing changed on the guest:

```
job 252   web-lnx-1.sales-demos-sandbox.svc.cluster.local
job 258   web-lnx-1-web.sales-demos-sandbox.svc.cluster.local
job 259   web-lnx-1-web.sales-demos-sandbox.svc.cluster.local
```

Unlike `last_boot` it cannot be rounded into stability, so it is out of the
comparison. **It still displays on the report** — the exclusion governs only
what the drift section claims changed.

!!! danger "Do not build a talk track that promises either as a drift signal"

    A reboot *is* worth showing, and `uptime.last_boot` will catch one at
    minute resolution. What it will not do is prove a change that happened
    seconds ago. `network.domain` will not report anything at all.

`gathered` and `uptime.seconds` are excluded for the same reason from the other
direction: they change on every run by definition, and including them would
train the viewer to ignore the report.

**The exclusion has a named cost.** On Windows the same summary key carries
`ansible_windows_domain`, which is stable and meaningful — a guest leaving
`WORKGROUP` for a domain is genuine drift. One key, two facts, so the comparison
is all-or-nothing today. That signal is deferred rather than lost: Active
Directory is Layer 1 🔄 on the roadmap, the demo guests report
`ansible_windows_domain_member: false`, and there is currently nothing to join.

---

## The objects

Four job templates, all carrying `use_fact_cache: true`, all four attached to
the same new credential.

| Template | Playbook | `demo_facts_compare` |
|---|---|---|
| `Linux Day 1 - 5 Check and Gather Facts` | `check_linux_vm.yml` | `false` |
| `Windows Day 1 - 5 Check and Gather Facts` | `check_windows_vm.yml` | `false` |
| `Linux Day 2 - Gather Facts` | `check_linux_vm.yml` | `true` |
| `Windows Day 2 - Gather Facts` | `check_windows_vm.yml` | `true` |

Day 1 and Day 2 run the *same playbook* — see
[why the templates are named the way they are](running-from-aap.md). The Linux
Day 2 family starts here; it did not exist before.

### `Sales Demos - Controller`

A new credential of the managed `Red Hat Ansible Automation Platform` type,
pointed at AAP itself. A job running against `linuxweb` or `windemo` has no
other way to reach the API — those hosts are not in the `aap` group, so the
connection variables never reach them.

**Basic auth, no token minted.** Nothing is stored, so there is nothing to leak
and nothing to clean up in an `always:` block — which keeps the repo's
token-cleanup rule intact instead of carving a third exception into it.

### The inputs are the contract

These names are shared verbatim by the AAP survey, the role defaults and the
skill.

| Variable | Values | Day 1 default | Day 2 default |
|---|---|---|---|
| `demo_facts_show_full` | `"false"` · `"true"` | `"false"` | `"false"` |
| `demo_facts_compare` | `"false"` · `"true"` | `"false"` | `"true"` |
| `check_vm_assert_serving` | `true` · `false` | `true` | `false` (**Windows only**) |

The survey values are the *strings* `"false"` and `"true"`, which is why every
consumer in the role filters them through `| bool`.

`demo_facts_compare` is off on Day 1 because a VM the chain has just built has
nothing to compare against, and on for Day 2 because drift is the entire point.

`check_vm_assert_serving` exists only on the Windows side — `check_linux_vm.yml`
has no Route probe for it to govern. On the Day 1 chain a 503 from the Route is
the failure that node exists to catch, and it must fail. On a read-only Day 2
fact gather it would mean pressing a reporting button and getting nothing back
because of an unrelated fault, so `Windows Day 2 - Gather Facts` sets it
`false`. The 503 is still *reported* either way; only the hard failure is
skipped.

!!! note "Not proven"

    `check_vm_assert_serving` is wired but has never been exercised. Both
    Windows runs returned 200, so the assert would have passed anyway. Proving
    the guard needs a guest whose Route serves 503 while WinRM still answers.
    The plumbing is verified; the scenario is not.

### Which fields are compared

The comparison covers the fields listed in `demo_facts_compare_fields` in
[`demo_facts/defaults/main.yml`](https://github.com/ericcames/sales.demos/blob/main/playbooks/roles/demo_facts/defaults/main.yml)
— hostname, OS, resources, virtualization, addresses and DNS, SELinux, product
and vendor, last boot, provisioning tier and environment, and the golden image.

The job log and the report both count that list at runtime and tell you how many
fields were compared, so read the number off a real run rather than from a
document that can go stale.

### Which changes matter

Each compared field also carries a **severity**, set in the same file, with a
one-line reason next to every entry:

| Severity | Meaning | Examples |
|---|---|---|
| `investigate` | Nothing this repo runs should change it. Find out who did. | resources, addresses and DNS, SELinux, virtualization, hostname, CIS level |
| `notable` | A deliberate act changes it. Worth seeing, not alarming. | provisioning tier and environment, golden image source, firmware strings |
| `expected` | Routine Day 2 work changes it. | OS version, kernel, last boot |

The job log lists changed rows most urgent first, labels each one, and gives the
count at each level. This came from a real run on sandbox, after a reboot booted
a kernel that Day 1 had installed:

```
3 field(s) changed since the last gather (1 investigate, 2 expected):
[INVESTIGATE] resources.memory_mb: 15706 -> 15708
[EXPECTED] os.kernel: 5.14.0-687.44.1.el9_8.x86_64 -> 5.14.0-687.49.1.el9_8.x86_64
[EXPECTED] uptime.last_boot: 2026-09-18T20:28:00Z -> 2026-09-18T20:37:00Z
```

That memory row was a false alarm. The VM's RAM did not change. The new kernel
reserves a slightly different amount of memory, so the memory the guest reports
moved by 2 MB, and every patch cycle would have raised it.
[sales.demos#664](https://github.com/ericcames/sales.demos/pull/664) fixed that
with an optional **`tolerance_pct`** on a compared field: two numbers within that
percentage do not count as a change. `memory_mb` uses 10%. The size tiers are 4,
8 and 16 GiB, so any real resize is at least 50% away and is still reported as
`investigate`. The report still shows the exact values.

`facts.html` shows the same label in a Severity column.

**The severity is decided by Ansible, not by a model.** In
[sales.demos#657](https://github.com/ericcames/sales.demos/issues/657), two
Granite models were given the same drift and the same explicit labelling rules.
The 3B model silently dropped a row. The 8B model labelled an unrequested
doubling of RAM `expected` and made up a reason for it. Any AI narration added
later will explain these labels, not set them.

If you override the list, a plain field name with no severity is still accepted
and counts as `notable`. A severity that is not one of the three fails the job
and names the entry. Guessing would put a field in the wrong group without
telling anyone.

---

## Checking it worked

A green job recap proves the play ran. It says nothing about whether AAP
persisted anything or whether the page renders, so ask both sides.

**Ask the controller** — `ansible_facts_modified` must be non-null, and
`demo_facts_summary` must be present. That key only exists because the role set
it `cacheable: true`:

```
mcp__aap-<env>__hosts_ansible_facts_retrieve  id=<host id>
```

**Ask the guest:**

```bash
curl -sI "<web_url>/facts.html" | head -1     # HTTP/1.1 200 OK
curl -s  "<web_url>/facts.json" | head -20
```

Expect different `gathered` timestamps. That is the two-snapshot behaviour
above, not a bug.

### When it does not work

| Symptom | Cause |
|---|---|
| `ERROR! Attempting to decrypt but no vault secrets found` | The `Sales Demos - Vault` credential is not attached. It is required on every template here even though this playbook reads no secret, because `secrets.yml` is parsed for every play. |
| Facts tab still empty after a green run | The template lost `use_fact_cache: true`. Nothing in the playbook writes the cache, so the toggle is the only thing that can be wrong. |
| `facts.html` 404s but the job was green | The run had no `web_url` host variable, so the report was written to the docroot without a link — or `demo_facts_publish` was `false`. The job log's last task says which. |
| The page and `facts.json` disagree about virtualization | sales.demos#160 reopening. Run `python3 utilities/check-fact-normalisation.py`; it names the copy that moved. |
| A 503 fails a Windows run | `check_vm_assert_serving`, correct on the Day 1 chain and wrong for a fact gather. Add `-e check_vm_assert_serving=false` if you launched step 5 by hand. |

---

## Where the words come from

| Claim | Source |
|---|---|
| Nothing in the role writes the cache | [`demo_facts/tasks/main.yml`](https://github.com/ericcames/sales.demos/blob/main/playbooks/roles/demo_facts/tasks/main.yml) — the comment above the publish block |
| `ansible_virtualization_type` is `"NA"` beside a curated `KVM` | Live sandbox fact cache, `web-lnx-1`, 2026-09-16 |
| Three consumers, agreement enforced in CI | [`check-fact-normalisation.py`](https://github.com/ericcames/sales.demos/blob/main/utilities/check-fact-normalisation.py); [sales.demos#160](https://github.com/ericcames/sales.demos/issues/160) |
| 53 minutes on Linux, 80 on Windows | [sales.demos#649](https://github.com/ericcames/sales.demos/pull/649) — measured on a live pair |
| AAP writes the cache after the job finishes | [`demo_facts/tasks/compare.yml`](https://github.com/ericcames/sales.demos/blob/main/playbooks/roles/demo_facts/tasks/compare.yml) — header comment |
| `last_boot` jittered by a second; `network.domain` flapped | [sales.demos#651](https://github.com/ericcames/sales.demos/pull/651) — jobs 252, 258, 259 |
| `check_vm_assert_serving` never exercised | [sales.demos#649](https://github.com/ericcames/sales.demos/pull/649) — stated in the test report |
| The four templates and the credential | [`controller_templates.yml`](https://github.com/ericcames/sales.demos/blob/main/inventory/group_vars/aap/controller_templates.yml), [`controller_credentials.yml`](https://github.com/ericcames/sales.demos/blob/main/inventory/group_vars/aap/controller_credentials.yml) |
| The naming rule | [sales.demos#647](https://github.com/ericcames/sales.demos/issues/647) |
| Severity levels, per-field reasons, bare-string fallback, fail on unknown | [`demo_facts/defaults/main.yml`](https://github.com/ericcames/sales.demos/blob/main/playbooks/roles/demo_facts/defaults/main.yml), [`demo_facts/tasks/compare.yml`](https://github.com/ericcames/sales.demos/blob/main/playbooks/roles/demo_facts/tasks/compare.yml); [sales.demos#662](https://github.com/ericcames/sales.demos/pull/662) |
| The sample job log and the memory false alarm | sales.demos AAP sandbox job 311, 2026-09-18; [sales.demos#663](https://github.com/ericcames/sales.demos/issues/663) |
| `tolerance_pct`, and 10% for `memory_mb` | [`demo_facts/defaults/main.yml`](https://github.com/ericcames/sales.demos/blob/main/playbooks/roles/demo_facts/defaults/main.yml); [sales.demos#664](https://github.com/ericcames/sales.demos/pull/664) |
| Neither Granite size followed the labelling rules | [sales.demos#657](https://github.com/ericcames/sales.demos/issues/657); [sales.demos#658](https://github.com/ericcames/sales.demos/issues/658) |
