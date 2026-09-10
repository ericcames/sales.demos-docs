# sales.demos-docs — repo conventions

Demo documentation, talk tracks, and architecture guides. Published as a
GitHub Pages site at
[ericcames.github.io/sales.demos-docs](https://ericcames.github.io/sales.demos-docs).

**[`CONTRIBUTING.md`](CONTRIBUTING.md) is the human-facing version of the
conventions below** (#7). It is deliberately a second copy rather than a link:
this file is loaded into an agent's context automatically and `CONTRIBUTING.md`
is not, so moving the rules out of here would quietly degrade every session.
**Change one, change the other** — and prefer `CONTRIBUTING.md` as the place a
new rule is written first, since a person can find it.

## This repo is public

No customer information, ever. No customer name, password, or API token in any
tracked file, commit message, PR title or body, or issue.

**RHDP URLs are the documented exception.** `*.dyn.redhatworkshops.io`
hostnames are ephemeral demo-platform addresses, not customer-identifying.

## Three-tier documentation split

| Tier | Home | Content |
|------|------|---------|
| Automation | [sales.demos](https://github.com/ericcames/sales.demos) | Playbooks, inventory, skills, terraform |
| Demo docs | **This repo** | Talk tracks, run sheets, architecture, objections |
| Marketing | [Google Drive](https://drive.google.com/drive/folders/1Me_blEFV-xHUyZeL48F0GjCyWl3_KSxG) | Key messages, Gemini prompts, product links |

New documentation goes here or to Google Drive, not to `sales.demos`.

## Adding a demo

Copy `docs/demos/_template/` to `docs/demos/<slug>/` and fill in the five
standard files. Add the nav entry in `mkdocs.yml`. See
`docs/demos/README.md` for the philosophy and rules.

## Branching and PRs

- **Branch from `main`; never commit to it directly.** Name the branch
  `<type>-<issue>-<slug>` — `docs-2-edge-sno-guide`.
- **One concern per PR.**
- **`main` is protected.** A pull request is required, with 0 required
  approvals — a PR should not block on a second person being around. All CI
  checks are required. Enforced on admins. The "one collaborator" reason this
  used to give stopped being true (#20); @mlowcher61 co-owns every path in
  `.github/CODEOWNERS`, which requests review and does **not** gate the merge.
- **Merged branches delete themselves** on the remote
  (`delete_branch_on_merge` is enabled). Delete the local copy after merge:
  ```bash
  git checkout main && git pull && git branch -d <branch>
  ```

## Worktrees

**This working tree is shared by more than one Claude session at a time.**
Always use an isolated worktree for code changes — treat the main checkout as
read-only.

```bash
git worktree add ../sales.demos-docs-<slug> -b <branch-name>
cd ../sales.demos-docs-<slug>
# ... work ...
git worktree remove ../sales.demos-docs-<slug>
```

Re-check `git branch --show-current` immediately before `git add` and
`git commit`.

## CI checks

Two required checks on every PR (`.github/workflows/lint.yml`):

1. **`mkdocs-build`** — builds the site with `mkdocs build`, verifying the
   site compiles without errors.
2. **`secret-guard`** — scans tracked files for bearer tokens, private keys,
   AWS keys, and GitHub tokens.

The site deploys to GitHub Pages on push to `main`
(`.github/workflows/pages.yml`).

## Running locally

```bash
pip install mkdocs-material
mkdocs serve
```

Opens at `http://127.0.0.1:8000/sales.demos-docs/`.
