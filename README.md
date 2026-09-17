# sales.demos-docs

The words for the demos, kept under version control next to the automation that
runs them. Talk tracks, run sheets, architecture guides and honest answers to
the objections a customer actually raises — written for the pre-sales engineer
who is presenting, not for the person who built the automation. Every claim in
a talk track is sourced back to a file in
[sales.demos](https://github.com/ericcames/sales.demos), so when the code
changes the story is a `git diff` away from changing with it.

| | |
|---|---|
| **For** | Red Hat pre-sales engineers preparing and presenting a demo |
| **Produces** | A searchable site — run sheets, talk tracks, architecture, objections |
| **Read it** | **[ericcames.github.io/sales.demos-docs](https://ericcames.github.io/sales.demos-docs)** |
| **Status** | Per-demo status lives in the [use-case table](docs/demos/README.md) — the one place that tracks it |

The site is mkdocs-material, built and deployed from `main` by GitHub Actions.
The markdown in `docs/` is the only source; there is nothing to build by hand.

## 🚀 Getting started

🎤 **Presenting a demo?** You do not need this repo. Go to
[the site](https://ericcames.github.io/sales.demos-docs), pick your demo, and
read the **run sheet** — it is the page to hold while you present. Read the
**talk track** once, the week before.

✍️ **Editing the docs?** Preview locally before you open a PR:

```bash
git clone https://github.com/ericcames/sales.demos-docs.git
cd sales.demos-docs
mkdocs serve
```

Leave it running, and it reloads on save. Ctrl-C stops it.

> [!NOTE]
> `mkdocs serve` prints the URL it is serving on —
> `Serving on http://127.0.0.1:8000/sales.demos-docs/` — and that is the one to
> click. It answers **only while the server is running**, so it is not a link
> to follow from GitHub: on its own it goes nowhere, which is the expected
> behaviour and not a broken link.
>
> The `/sales.demos-docs/` suffix is not decoration — mkdocs takes the dev
> server's mount point from the path component of `site_url` in
> [`mkdocs.yml`](mkdocs.yml). Measured: `http://127.0.0.1:8000/` **302s** to
> that path rather than failing, so either address works in a browser; any
> other path 404s.

One-time, if you do not already have it: `pip install --user mkdocs-material`.

CI runs two required checks on every PR — `mkdocs-build` and `secret-guard` —
and both must be clean before a PR merges. Neither one reads prose.

🤝 **Changing the automation and the words together?** Every claim in a talk
track is sourced back to a file in
[sales.demos](https://github.com/ericcames/sales.demos), so the two often move
in one sitting. Start the agent session over there — its `.mcp.json` is
project-scoped, so the cluster servers load only in a session started in that
directory, and this repo has none. Then keep `mkdocs serve` running here
alongside it.

### Adding a demo

```bash
cp -r docs/demos/_template docs/demos/<slug>
```

Fill in the five standard files — `README.md`, `run-sheet.md`, `talk-track.md`,
`architecture.md`, `objections.md`. **Write the run sheet first**: it forces the
arc into a shape that fits the slot, and everything else gets easier afterwards.
Then add the nav entry in [`mkdocs.yml`](mkdocs.yml) and a row to the table in
[`docs/demos/README.md`](docs/demos/README.md) — a page with no nav entry is
built but unreachable.

**End the talk track with the source table** mapping each claim to the file in
`sales.demos` that backs it. If you cannot source a sentence, cut it.

[`docs/demos/README.md`](docs/demos/README.md) has the rules these documents
follow and why there are two layers rather than one. Read it before writing.

[`CONTRIBUTING.md`](CONTRIBUTING.md) covers branching, PRs and the CI checks.

## 🧰 Claude skills

| Skill | Does |
|---|---|
| [`/docs-check`](.claude/skills/docs-check/SKILL.md) | The four site checks CI does not run — strict build, broken relative links, dead external URLs, and the `- #N` heading trap |

About 30 seconds for a full run. CI builds the site and scans for secrets;
it does not check a single link, which is why this exists. Run it before you
open a PR.

## 📁 What's here

| Directory | Content |
|---|---|
| `docs/demos/` | Talk tracks, run sheets, architecture, objections — one folder per demo |
| `docs/image-factory/` | Where the hardened RHEL and Windows images come from, and the compliance evidence behind them |
| `docs/plan/` | Design plans for each use case — the research and the decisions |
| `docs/reference/` | Operator reference for the automation — environments, running playbooks, AAP, the EE, reusing the repo |
| `docs/images/` | Screenshots and diagrams |

## 📚 Where everything else lives

| You want | Go to |
|---|---|
| The rules these documents follow | [`docs/demos/README.md`](docs/demos/README.md) |
| Branching, PRs, CI checks, worktrees | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Why a convention exists | [`CLAUDE.md`](CLAUDE.md) |
| What may and may not be committed | [`.github/SECURITY.md`](.github/SECURITY.md) |
| What changed and when | `git log`, plus the [closed issues](https://github.com/ericcames/sales.demos-docs/issues?q=is%3Aissue+is%3Aclosed) |
| What happened before 2026-09-10 | the [history archive](https://ericcames.github.io/sales.demos-docs/reference/history/) |

## 🔗 Related repositories

| Repo | What it is | Which way the dependency runs |
|---|---|---|
| [sales.demos](https://github.com/ericcames/sales.demos) | Playbooks, inventory, skills, terraform | This repo **documents** it |
| [image.builder.pipeline](https://github.com/ericcames/image.builder.pipeline) | The image factory — CIS-hardened RHEL and Windows golden images | Documented here, in [`docs/image-factory/`](docs/image-factory/README.md) |
| [Sales Demos (Google Drive)](https://drive.google.com/drive/folders/1Me_blEFV-xHUyZeL48F0GjCyWl3_KSxG) | Marketing content, key messages, Gemini prompts | Neither — the third tier |

New documentation goes here or to Google Drive, not to `sales.demos`.

**This repo is the canonical copy.** `docs/plan/` and `docs/demos/` used to exist
in both repos with nothing keeping them in step, and 20 of the 35 shared files
had drifted apart — including a run sheet still telling presenters that Windows
"cannot be logged into yet", days after that was proven working end to end.
`sales.demos` now links here rather than carrying its own copy.

A few documents stay with the code deliberately, because moving them would break
something rather than tidy it: `CONTRIBUTING.md` (GitHub surfaces it during PR
creation), `terraform/ocpvirt/README.md` (module docs belong with the module),
`utilities/aap-env-badge/README.md`, and `assets/aap-branding/README.md` — those
files are AAP *configuration inputs* read at playbook run time, not
documentation, however much they look like screenshots.

## 🔒 This repo is public

No customer names, ever. Demo-platform hostnames (`*.dyn.redhatworkshops.io`)
are the documented exception — see [`.github/SECURITY.md`](.github/SECURITY.md).

## ⚖️ License

[MIT](LICENSE)
