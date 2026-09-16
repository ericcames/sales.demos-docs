# Reference

Operator reference for
[sales.demos](https://github.com/ericcames/sales.demos) — how to run the
automation, point it at your own cluster, and understand what AAP is actually
executing. New here? The repo's
[🚀 Getting started](https://github.com/ericcames/sales.demos#-getting-started)
is the front door; these pages are the detail behind it.

**Presenting a demo? You do not need any of this.** Go to
[Demos](../demos/README.md), pick yours, and read the run sheet.

| Page | Read it when |
|---|---|
| [First-time setup](first-time-setup.md) | You are setting up a new machine to use this repo, or a prerequisite check is failing |
| [Environments](environments.md) | You need to know which cluster you are on, or why the sign-in logo is badged |
| [New environment](new-environment.md) | Your RHDP cluster expired and you need to point at a fresh one |
| [Running playbooks](running-playbooks.md) | You are running a phase from a laptop, or about to merge a playbook change |
| [Running from AAP](running-from-aap.md) | You want the workflows and job templates AAP actually has |
| [Facts and drift](facts-and-drift.md) | You want to show what AAP knows about a guest, or what changed since last time |
| [Execution environment](execution-environment.md) | A job template fails in a way a laptop run does not reproduce |
| [Reusing this repo](reusing-this-repo.md) | You cloned or forked it and want it pointed at your own cluster |
| [Repo layout](repo-layout.md) | You are looking for a file, or wondering why `secrets.yml` or `local.yml` is not where you would guess |
| [Project history](history/README.md) | You followed a reference to a `CHANGELOG.md` that no longer exists, or want the reasoning behind a past decision |

---

## Where things live

The automation and its words are split across two repos on purpose.

| Content | Home |
|---|---|
| Playbooks, inventory, skills, terraform, execution environment | [sales.demos](https://github.com/ericcames/sales.demos) |
| Talk tracks, run sheets, architecture, objections, design plans, images | **this repo** |
| CIS-hardened image factory | [image.builder.pipeline](https://github.com/ericcames/image.builder.pipeline) |
| What changed and when | `git log` and closed issues in the repo concerned — the per-PR changelogs were retired on 2026-09-10 and are [archived here](history/README.md) |

A few documents stay with the code deliberately, because separating them would
break something rather than tidy it:

- **`CONTRIBUTING.md`** — GitHub surfaces it during pull-request creation.
- **`terraform/ocpvirt/README.md`** — module documentation belongs with the
  module.
- **`utilities/aap-env-badge/README.md`** — it documents the extension beside
  it.
- **`assets/aap-branding/README.md`** — those files are AAP *configuration
  inputs* read at playbook run time, not documentation. They only look like
  screenshots.
