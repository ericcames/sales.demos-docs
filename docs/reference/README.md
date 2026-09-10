# Reference

Operator reference for
[sales.demos](https://github.com/ericcames/sales.demos) — how to run the
automation, point it at your own cluster, and understand what AAP is actually
executing.

**Presenting a demo? You do not need any of this.** Go to
[Demos](../demos/README.md), pick yours, and read the run sheet.

| Page | Read it when |
|---|---|
| [Environments](environments.md) | You need to know which cluster you are on, or why the sign-in logo is badged |
| [Running playbooks](running-playbooks.md) | You are running a phase from a laptop, or about to merge a playbook change |
| [Running from AAP](running-from-aap.md) | You want the workflows and job templates AAP actually has |
| [Execution environment](execution-environment.md) | A job template fails in a way a laptop run does not reproduce |
| [Reusing this repo](reusing-this-repo.md) | You cloned or forked it and want it pointed at your own cluster |

---

## Where things live

The automation and its words are split across two repos on purpose.

| Content | Home |
|---|---|
| Playbooks, inventory, skills, terraform, execution environment | [sales.demos](https://github.com/ericcames/sales.demos) |
| Talk tracks, run sheets, architecture, objections, design plans, images | **this repo** |
| CIS-hardened image factory | [image.builder.pipeline](https://github.com/ericcames/image.builder.pipeline) |

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
