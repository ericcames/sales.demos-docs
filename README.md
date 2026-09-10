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
| **Status** | Four demos published — OpenShift Virtualization, Private Automation Hub, MCP Servers, Edge / SNO |

The site is mkdocs-material, built and deployed from `main` by GitHub Actions.
The markdown in `docs/` is the only source; there is nothing to build by hand.

## Getting started

**Presenting a demo?** You do not need this repo. Go to
[the site](https://ericcames.github.io/sales.demos-docs), pick your demo, and
read the **run sheet** — it is the page to hold while you present. Read the
**talk track** once, the week before.

**Editing the docs?** Preview locally before you open a PR:

```bash
git clone https://github.com/ericcames/sales.demos-docs.git
cd sales.demos-docs
pip install mkdocs-material
mkdocs serve
```

That serves at **<http://127.0.0.1:8000/sales.demos-docs/>** and reloads on
save. `mkdocs build` is what CI runs, and it must be clean before a PR merges.

**Changing the automation and the words together?** Every claim in a talk track
is sourced back to a file in
[sales.demos](https://github.com/ericcames/sales.demos), so the two often move
in one sitting. Start the agent session over there — its `.mcp.json` is
project-scoped, so the cluster servers load only in a session started in that
directory, and this repo has none. Then keep `mkdocs serve` running here
alongside it; nothing in this repo needs an agent.

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

[`docs/demos/README.md`](docs/demos/README.md) has the rules these documents
follow and why there are two layers rather than one. Read it before writing.

[`CONTRIBUTING.md`](CONTRIBUTING.md) covers branching, PRs and the CI checks.

## What's here

| Directory | Content |
|---|---|
| `docs/demos/` | Talk tracks, run sheets, architecture, objections — one folder per demo |
| `docs/plan/` | Design plans for each use case — the research and the decisions |
| `docs/images/` | Screenshots and logos |

## What's elsewhere

| Resource | Home |
|---|---|
| Playbooks, inventory, skills, terraform | [sales.demos](https://github.com/ericcames/sales.demos) |
| CIS-hardened image factory | [image.builder.pipeline](https://github.com/ericcames/image.builder.pipeline) |
| Marketing content, key messages, Gemini prompts | [Sales Demos (Google Drive)](https://drive.google.com/drive/folders/1Me_blEFV-xHUyZeL48F0GjCyWl3_KSxG) |

New documentation goes here or to Google Drive, not to `sales.demos`.

## This repo is public

No customer names, ever. Demo-platform hostnames (`*.dyn.redhatworkshops.io`)
are the documented exception — see [`.github/SECURITY.md`](.github/SECURITY.md).

## License

[MIT](LICENSE)
