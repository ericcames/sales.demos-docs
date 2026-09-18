# Conventions rationale

The rules in
[sales.demos/CLAUDE.md](https://github.com/ericcames/sales.demos/blob/main/CLAUDE.md)
are deliberately terse — an agent reads them on every session. This page holds
the design history and incident narratives behind the rules that need more
explanation than a single sentence.

Each section links back to the rule it explains. If you are deciding whether a
convention should change, read the section here first — the history often
answers the objection.

---

## Why `secrets.yml` is untracked and in `all/`

*Issues:
[#130](https://github.com/ericcames/sales.demos/issues/130),
[#129](https://github.com/ericcames/sales.demos/issues/129),
[#5](https://github.com/ericcames/sales.demos/issues/5)*

`playbooks/group_vars/all/secrets.yml` used to be committed, and untracking it
in #130 is what makes this repo reusable. A public repo that ships one person's
encrypted credentials hands everyone else a blob they cannot decrypt, cannot
replace without diverging from upstream, and that conflicts on every pull.
`secrets.yml.example` is the contract now; each machine builds its own real file
from it. On a fresh clone the file does not exist and you create it — that is
the point, not a gap.

!!! note "Why #129 exists"
    AAP job templates used to receive the vaulted file in the project's SCM
    checkout and decrypt it with the "Sales Demos - Vault" credential. With
    nothing to decrypt, they get their credentials from the
    "Sales Demos - Env Secrets" custom credential type instead, injected as
    `extra_vars`. Untracking the file without that credential type breaks every
    job template — the two changes belong together.

It was `group_vars/aap/` until #5, which is scoped to hosts in the `aap` group.
That was invisible until a playbook targeted something else:
`repair_linux_vm.yml` runs against `linuxweb`, so the guests never received the
registration credentials and failed an assert that looked like a missing Vault
credential. `all` is the only scope that covers every play without a second
secrets file.

---

## Why secrets sit beside playbooks, not inventory

*Issue: [#4](https://github.com/ericcames/sales.demos/issues/4)*

The secrets file sits beside the **playbooks**, not the inventory, and that is
not cosmetic. Ansible loads `group_vars/` adjacent to the playbook as well as
adjacent to the inventory, so it resolves identically either way. What differs
is AAP: a job template's inventory is synced from `inventory/hosts.yml` by an
SCM inventory source, and that sync runs `ansible-inventory`, which parses every
`group_vars` file next to the inventory. Three things follow, all verified
against a live AAP 2.6 (#4):

- With the vaulted file under `inventory/group_vars/`, the sync dies with
  `ERROR! Attempting to decrypt but no vault secrets found`.
- It cannot be given the password: AAP rejects Vault credentials on SCM
  inventory sources outright — *"Credentials of type insights and vault are
  disallowed for scm inventory sources."*
- Smuggling the password in via a custom credential type **would** work and is
  the wrong thing to do: the sync would then write `env_secrets` and the SSH
  private key into AAP's inventory variables in plaintext, visible in the UI.

Keeping secrets out of the inventory tree is what lets the sync parse
`connection.yml` freely while the credentials stay encrypted and arrive at run
time through the job template's Vault credential.

!!! warning
    Do not move `secrets.yml` back to `inventory/group_vars/`. The consequences
    above were verified against a live AAP instance and will recur.

---

## The `local.yml` overlay and what it replaced

*Issues:
[#131](https://github.com/ericcames/sales.demos/issues/131),
[#166](https://github.com/ericcames/sales.demos/issues/166),
[#499](https://github.com/ericcames/sales.demos/issues/499),
[#554](https://github.com/ericcames/sales.demos/issues/554)*

`inventory/group_vars/<env>/local.yml` is the per-SE repoint overlay — and that
IS the COP practice being taught. `local.yml.example` beside each
`connection.yml` shows the keys to override; copy it to `local.yml` and fill in
your cluster's values. Ansible loads a `group_vars/<group>/` directory in sorted
order and the last file wins, so it overrides `connection.yml` with no code
change. Each SE creates their own, points at their own cluster, and can
`git pull` without conflicting on the identity lines. This is the same pattern
the Red Hat Automation COP uses to manage many AAPs from one codebase.

### How `local.yml` reaches AAP

`local.yml` IS the answer to the AAP job-template question, and the mechanism is
`config.yml`. Gitignored files are invisible to AAP's SCM checkout — that part
is still true. But `config.yml` runs locally with `local.yml`, resolves the
effective values (including the override), and populates the AAP inventory host
variables via the API. AAP job templates read those host vars, not
`connection.yml` from the SCM checkout. So `local.yml` reaches AAP, through
`config.yml`, without ever being committed.

This replaced the earlier design where `connection.yml` had to be committed for
AAP to see the new cluster (#166). That design required every repoint to go
through a PR, and a stale `connection.yml` was a real defect. The current design
treats `connection.yml` as the upstream reference for fresh clones and
`local.yml` as the operational input — the distinction SEs need to learn.

### Why the name matters

`connection.local.yml` sorts *before* `connection.yml` and loses; it would be
read, silently overridden, and leave the user on the committed cluster believing
otherwise. Measured, not assumed.

---

## Why `check-no-secrets.sh` has three ordered checks

The script makes three checks that cannot silently pass:

1. nothing named `secrets.yml` is tracked — catches `git add -f`
2. the `.gitignore` rule actually matches, tested with `git check-ignore`
3. a tracked `secrets.yml`, if one exists anyway, still begins with
   `$ANSIBLE_VAULT`

!!! note "Check 2 is a verification, not a replacement"
    The rule here used to say an ignore rule hides the file instead of verifying
    it, and that was correct: gitignoring the file and keeping the old loop would
    have been *silent*. `git ls-files` returns nothing, the loop never iterates,
    `fail` stays `0`, and the script prints "passed" — and because every other
    pattern in it also pipes from `git ls-files`, a plaintext untracked
    `secrets.yml` full of live tokens would be invisible to all of them too. So
    the ignore rule is not trusted; it is *verified*. Deleting it fails the build.

### Why ordering is load-bearing

Check 1 must run **before** check 2: git reports a tracked file as "not ignored"
whatever `.gitignore` says, so testing check-ignore first blames `.gitignore`
for a rule that is present and correct.

---

## Token cleanup exceptions

*Issues:
[#102](https://github.com/ericcames/sales.demos/issues/102),
[#515](https://github.com/ericcames/sales.demos/issues/515),
[#69](https://github.com/ericcames/sales.demos/issues/69)*

The rule is: any playbook creating a token must delete it in an `always:` block
so stale tokens do not accumulate. The exception is a token that IS the
deliverable, and there are two. A credential created so that something else can
keep using it cannot be deleted in an `always:` block without destroying the
thing it was created for. The rule still holds without exception for every token
created *incidentally*, to get a playbook's own work done.

### 1. The AAP MCP client token

Created by `utilities/make-aap-mcp.sh` on a laptop (#102, #515). It is never
committed — the token is written to a gitignored file in `.aap/` and read at
launch by the stdio bridge in `.mcp.json`. It is retired by hand; the script
prints cleanup instructions, and you should say so out loud when handing this to
anyone.

### 2. The PAH Galaxy token

Created by `playbooks/link_hub.yml` (#69). This one **is** created by a
playbook — the rule's earlier wording said no playbook creates such a token, and
that stopped being true here rather than being wrong before. Three things keep it
from being a hole:

- **It is minted, never stored.** It comes from `aap_username` / `aap_password`,
  which already rotate with the environment, so a rebuilt cluster reconstructs it
  with nothing to go stale. That is the whole answer to #69's gate 3: ask how
  long the *environment* lives before designing anything that stores a credential
  from it.
- **The playbook retires its own.** Gateway tokens *accumulate* (unlike the
  galaxy_ng endpoint, which resets), so `link_hub.yml` deletes the tokens it
  minted on earlier runs before minting a fresh one, matched on description.
  Exactly one should ever exist.
- **There is a real cleanup path, and it is proven.**
  `-e hub_galaxy_link_state=absent` unassigns the credential, deletes it, and
  deletes the token. This is the half that makes the exception narrow, and it
  ships in the same PR as the link.

### Permission inheritance

Both tokens **inherit the creating user's permissions** — Red Hat's words, not a
paraphrase — so making one as `admin` gives the holder admin. For MCP the
environment's `aap_mcp_allow_write_operations` is a second gate, not the only
one. For the Galaxy token the mitigation is scope: `read`, verified sufficient
against the hub index before it was chosen, because a project sync only ever
downloads.

---

## Windows golden image: identity, not readiness

*Issue: [#358](https://github.com/ericcames/sales.demos/issues/358)*

The Windows image repoint steps were correct and did not work, for two days. The
playbook decided whether to import from whether the `win2k22` DataSource was
*Ready* — never from *which image* it served. After the first successful import
every environment is Ready for ever, so a changed `quay_windows_image` patched
the HCO cron template (which imports nothing on a private registry, #224),
skipped the DataVolume, skipped the repoint, passed a verification that only
asked "Ready?" and "Bound?", and printed success.

Sandbox advertised `win2k22-cis-l1-golden:20260907-0516` while every clone
booted `win2k22-golden:20260906-0300` — the repo the producer publishes its
**unhardened** build to, imported 26 hours before the hardened image was built.
The demo guest scored 9 of 27 CIS controls and the talk track was inviting
customers to read that report.

!!! warning "The lesson"
    The import decision is now identity, not readiness, and the identity is
    re-read from the cluster and asserted on every run, including runs that
    import nothing. Ready and Bound are both true of the wrong image; that is the
    whole lesson, and it is the same one as check 2 in
    `utilities/check-no-secrets.sh` — desired state is tested, not trusted.
    A DataVolume's source is immutable, so a changed tag deletes and re-imports
    rather than editing in place.

---

## Why there is no CHANGELOG.md

*Issue: [#432](https://github.com/ericcames/sales.demos/issues/432)*

The changelog never had a release to anchor it — 5,386 of its 5,394 lines sat
under a single `[Unreleased]` heading in a file that also claimed to follow
Semantic Versioning, 60 of the last 60 commits touched it, and nothing was ever
deleted from it. The same prose was written three times: issue, commit message,
entry. A one-line-per-PR version would have transcribed `git log --oneline`,
because the commit subjects here already read that way.

| Question | Where the answer lives |
|---|---|
| What changed, and when | `git log`, plus the closed issue and merged PR |
| Why a convention exists | [sales.demos/CLAUDE.md](https://github.com/ericcames/sales.demos/blob/main/CLAUDE.md) |
| What is planned | [ROADMAP.md](https://github.com/ericcames/sales.demos/blob/main/ROADMAP.md) |
| What happened before 2026-09-10 | the [archive](../reference/history/README.md) in this repo |

No per-PR artifact replaced it. Writing a decision record every merge would
rename the work rather than retire it. Durable conventions come to `CLAUDE.md`,
deliberately and rarely, which is what that file already is.

---

## Branch cleanup under squash merge

*Issues:
[#177](https://github.com/ericcames/sales.demos/issues/177),
[#197](https://github.com/ericcames/sales.demos/issues/197),
[#571](https://github.com/ericcames/sales.demos/issues/571)*

`delete_branch_on_merge` is enabled on the repository, so a merged PR cleans up
`origin/<branch>`. That is a repository setting, not a tracked file, so it is
recorded in `CLAUDE.md` — it cannot be seen by reading the tree (#97).

### The local branch survives

This note used to say it did not (#177). It read "no manual pruning is needed",
which is true of the remote and false of the clone you are standing in, so
leftovers accumulated silently — the note told you not to look. Delete the local
copy when you merge:

```bash
git checkout main && git pull && git branch -d <branch>
```

### `git branch --merged main` misses squash-merged branches

A finder that works under both merge strategies (#197):

```bash
gh pr list --state merged --limit 30 --json headRefName -q '.[].headRefName' \
  | while read -r b; do git show-ref -q --verify "refs/heads/$b" && echo "$b"; done
```

### When to use `-d` versus `-D`

Use `-d` by default. With an upstream set (every branch here has one via
`git push -u`), `-d` checks "pushed to upstream", not "merged into HEAD". After
a squash merge it prints a warning about "not yet merged to HEAD" — that is
expected and means nothing. `-d` still catches unpushed work, which is the loss
that actually matters.

Once the upstream is gone, `-D` is correct (#571). After
`delete_branch_on_merge` and a `fetch --prune`, `-d` falls back to HEAD and
refuses *every* squash-merged branch. Confirm `gh pr view <n>` says MERGED and
`git status` is clean in any worktree on it, then `-D`.

---

## Branch protection and CI check registration

*Issues:
[#435](https://github.com/ericcames/sales.demos/issues/435),
[#647](https://github.com/ericcames/sales.demos/issues/647)*

### Why zero required approvals is deliberate

A pull request is required, with 0 required approvals. Zero is deliberate, not
laziness: a PR should not block on a second person being around. Zero still
forces the branch-and-PR flow, which is the part that matters.

This used to be justified by "there is one collaborator", and that stopped being
true (#435). @mlowcher61 has `write` on all three repos and now co-owns every
path in `.github/CODEOWNERS`, so requiring an approval is possible where it once
would have deadlocked. It is still not wanted, for the reason above — the
decision outlived its original argument, which is exactly the kind of thing
worth re-reading rather than inheriting.

CODEOWNERS here requests review; it does not gate. `require_code_owner_reviews`
is `false`, so a listed owner is auto-requested and nothing waits on them. Do
not read co-ownership as enforcement.

### Adding a CI job is not the same as requiring it

All 9 lint checks are required — `yamllint`, `ansible-lint`, `secret-guard`,
`secrets-example-sync`, `generated-files`, `skills-frontmatter`,
`docs-artifacts-current`, `renderer-matches-role`, `fact-normalisation-agrees`.

!!! warning "#647 spent a day in this gap"
    `fact-normalisation-agrees` shipped in that PR, ran green on every push, and
    could not have blocked anything: required checks are a branch-protection
    setting, not a tracked file — the same invisibility that put the whole list
    in `CLAUDE.md`. Two steps, every time:

    1. Add the job to `.github/workflows/lint.yml` and to the list in `CLAUDE.md`.
    2. `gh api -X PATCH repos/ericcames/sales.demos/branches/main/protection/required_status_checks`
       with `-F strict=false` and the **full** `contexts[]` set — the full set,
       because the endpoint replaces rather than appends.

    The context name must match the job id exactly. A typo does not error; the PR
    simply waits for ever on a check that never reports. Confirm on the next PR
    with `gh pr checks`.

### Why admin enforcement exists

It applies to admins. Anything less would not have prevented what prompted it: a
commit went straight to `main` because a `git checkout -b` failed on an existing
branch and `|| true` swallowed the error. Admin bypass would have let that
through, since the push already carried admin rights. Turning enforcement off for
a genuine emergency is two clicks — doing that deliberately is a different thing
from doing it by accident.

---

## The worktree mandate

### The 2026-09-04 incident

This working tree is shared by more than one Claude session at a time, and the
branch can change under you. This is invisible from reading the tree, and every
session otherwise assumes it is alone in the checkout.

On 2026-09-04, between a `git checkout -b` and the commit at the end of that
same task, another session had merged two PRs, advanced `main`, and checked out
its own branch. The commit landed on **theirs**.

### What that breaks, in order of nastiness

1. The commit goes on someone else's branch, so their PR carries your change and
   **one concern per PR is violated without either session noticing**.
2. `git add -A` can stage their uncommitted work in flight.
3. `git push -u origin <your-branch>` pushes the *stale* ref you created
   earlier, not your commit — it looks successful and publishes nothing.
4. `gh pr create` uses the current branch, which is theirs.

### Recovery without damage

`git branch -f <your-branch> <sha>` claims your commit onto the right branch
and touches nothing else. Do **not** force-push or rewrite a branch another
session has already pushed — that is theirs to fix; say so and let the user
decide.

### Why the conditional rule failed

The unconditional rule ("always use a worktree for code changes") replaced the
earlier conditional rule ("use a worktree when multiple sessions are running").
The conditional rule failed in practice — every session assumes it is alone until
another one switches the branch underneath it. The unconditional rule eliminates
the assumption entirely. The main checkout never moves off `main`, so there is
nothing to collide with.

A worktree is a second checkout of the same repo in a sibling directory, sharing
one `.git` object store. Each session gets its own branch, index, and working
tree — the cross-session failures above become impossible, and Git enforces that
no two worktrees can be on the same branch.

```bash
# Create -- sibling directory, descriptive suffix
git worktree add ../sales.demos-<slug> <branch-name>

# List all worktrees
git worktree list

# Work in it
cd ../sales.demos-<slug>

# Clean up after merge
git worktree remove ../sales.demos-<slug>
```

Claude Code's Agent tool accepts `isolation: "worktree"` and automates this —
the worktree auto-cleans if the agent makes no changes; otherwise the path and
branch come back in the result.

!!! note "What worktrees do not solve"
    Cluster conflicts. Two sessions modifying the same OpenShift namespace, AAP
    objects, or Grafana resources can still collide. Coordinate by giving each
    session a different scope — different playbooks, different namespaces, or
    different environments via `--limit`.

The defensive habits (re-check branch, explicit `git add`, `--head` on PR
create) stay as a safety net — they protect against races within a single
worktree and are still correct even with worktrees.

---

## Overrides of global CLAUDE.md

Two rules in the project-level `CLAUDE.md` deliberately override the global
`~/.claude/CLAUDE.md`. The project-level file takes precedence for this repo.

### No CHANGELOG.md

The global file said "maintain a CHANGELOG.md for all repos." This repo retired
its changelog in
[#432](https://github.com/ericcames/sales.demos/issues/432) and the rule is now
deprecated across all repos. See
[Why there is no CHANGELOG.md](#why-there-is-no-changelogmd) above for the full
reasoning.

### Images go in the docs repo, not `docs/images/`

The global file said "images go in `docs/images/`." This repo does not have a
`docs/` directory — documentation lives in `sales.demos-docs`. The global rule
has been updated to reflect the consolidated docs hosting model.
