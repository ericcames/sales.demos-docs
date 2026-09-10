# Contributing

This repo holds the **words** for the demos — talk tracks, run sheets,
architecture guides, objections. The automation they describe lives in
[sales.demos](https://github.com/ericcames/sales.demos). Read
[`docs/demos/README.md`](docs/demos/README.md) before writing: it has the rules
these documents follow and why there are two layers rather than one.

## Three-tier documentation split

| Tier | Home | Content |
|------|------|---------|
| Automation | [sales.demos](https://github.com/ericcames/sales.demos) | Playbooks, inventory, skills, terraform |
| Demo docs | **This repo** | Talk tracks, run sheets, architecture, objections |
| Marketing | [Google Drive](https://drive.google.com/drive/folders/1Me_blEFV-xHUyZeL48F0GjCyWl3_KSxG) | Key messages, Gemini prompts, product links |

New documentation goes here or to Google Drive, **not** to `sales.demos`.

## Never commit

- Customer or company names — in any file, commit message, PR title or body, or
  issue. Not in a talk track, not in an example, not in a screenshot.
- Credentials of any kind: bearer tokens, private keys, AWS keys, GitHub tokens.

**RHDP URLs are the documented exception.** `*.dyn.redhatworkshops.io`
hostnames and cluster IDs are ephemeral demo-platform addresses, not
customer-identifying, and appear in run sheets on purpose. Do not "fix" them
into placeholders. See [`.github/SECURITY.md`](.github/SECURITY.md).

## Preview before you push

```bash
pip install mkdocs-material
mkdocs serve
```

Serves at <http://127.0.0.1:8000/sales.demos-docs/> and reloads on save.

## Adding a demo

1. `cp -r docs/demos/_template docs/demos/<slug>`
2. **Write `run-sheet.md` first.** It forces the arc into a shape that fits the
   slot; everything else is easier afterwards.
3. Fill in the other four standard files — `README.md`, `talk-track.md`,
   `architecture.md`, `objections.md`.
4. Add the nav entry in [`mkdocs.yml`](mkdocs.yml) **and** a row to the table in
   [`docs/demos/README.md`](docs/demos/README.md). A page with neither is built
   and unreachable.
5. End the talk track with the source table mapping each claim to the file in
   `sales.demos` that backs it. **If you cannot source a sentence, cut it.**

A sixth file needs a reason — `docs/demos/README.md` explains the one that has
earned it so far.

## Workflow

1. **Open an issue before writing.** Label it — run
   `gh label list --repo ericcames/sales.demos-docs` and apply every label that
   fits. This repo has an `accessibility` label the sibling repos lack; use it
   when a change is about a barrier rather than a bug.
2. **Branch from `main`; never commit to it directly.** Name the branch
   `<type>-<issue>-<slug>` — `docs-2-edge-sno-guide`. Carrying the issue number
   links the branch back to the decision without anyone reading `git log`.
3. **One concern per PR.** Group by shared root cause, not item count. The test:
   would you revert these together? Then ship them together.
4. Update [`CHANGELOG.md`](CHANGELOG.md) under `[Unreleased]`.
5. Run `mkdocs build` — it must be clean.
6. **Check every link you added.** CI does not. Relative paths must resolve in
   the tree; external URLs must return 200. This has bitten before.
7. Open a PR with `Closes #N` in the body, so the issue closes on merge.

**`main` is protected**, and it applies to admins. A pull request is always
required, with **0 required approvals** — zero is deliberate, not laziness:
there is one collaborator and GitHub does not let you approve your own PR, so
requiring one would deadlock every PR. Zero still forces the branch-and-PR flow,
which is the part that matters. Both CI checks below must pass, and PR
conversations must be resolved.

## CI checks

Two required checks on every PR ([`.github/workflows/lint.yml`](.github/workflows/lint.yml)):

| Check | What it does |
|---|---|
| `mkdocs-build` | Runs `mkdocs build`. Catches a broken nav entry, bad YAML, or a missing page. |
| `secret-guard` | [`utilities/check-no-secrets.sh`](utilities/check-no-secrets.sh) — scans tracked files for bearer tokens, private keys, AWS access keys and GitHub tokens. |

The site deploys to GitHub Pages on push to `main`
([`.github/workflows/pages.yml`](.github/workflows/pages.yml)). **Nothing else
deploys from CI**, and neither check reads prose — a green run means the site
compiled and no credential is tracked. It says nothing about whether a claim is
true. That is what the source table at the end of each talk track is for.

## Worktrees

**This working tree may be shared by more than one Claude Code session at a
time**, and the branch can change under you. Always use an isolated worktree for
changes; treat the main checkout as read-only.

```bash
git worktree add ../sales.demos-docs-<slug> -b <branch-name>
cd ../sales.demos-docs-<slug>
# ... work ...
git worktree remove ../sales.demos-docs-<slug>
```

Re-check `git branch --show-current` immediately **before** `git add` and
`git commit`, not once at the start of the task.

## After merge

Merged branches delete themselves on the remote — `delete_branch_on_merge` is
enabled. The local copy survives:

```bash
git checkout main && git pull && git branch -d <branch>
```

Use `-d`, never `-D`. After a **squash** merge `-d` prints a warning that the
branch is "not yet merged to HEAD" — that is expected and means nothing, because
a squash puts a new commit on `main` and the branch tip never becomes an
ancestor of it. Confirm with `gh pr view <n>` if unsure.
