# Environments

Three, and they are not the same kind of thing.

| Environment | What it is | Posture |
|---|---|---|
| `sandbox` | The RHDP environment you build against and break | Read-write |
| `demo` | The RHDP environment you show customers | Read-only over MCP ([below](#mcp-servers-per-environment)) |
| `edge` | A persistent bare-metal Single Node OpenShift cluster on a NUC | Read-write |

`edge` differs from the RHDP pair by construction: it does not expire, DNS is
local (dnsmasq) rather than a public domain, and its installer ISO comes from
[image.builder.pipeline](https://github.com/ericcames/image.builder.pipeline)
Phase 5. The same playbooks target it with `--limit edge`.

There is deliberately **no `golden` environment.** "This config is proven good"
is a state of the config, not a connection target — git already models that with
`main` plus a release tag.

---

## Telling them apart at the sign-in page

Environments look identical at the AAP login page, and the moment you are most
likely to act on the wrong one is the moment before you have touched anything.
Each gets a badged sign-in logo, following the same severity convention as
`aap_config`:

| Environment | Color | | |
|---|---|---|---|
| `sandbox` | green | the one you break | ![sandbox sign-in](../images/logo-sandbox.png){ width="400" style="background:#1a1a1a;padding:8px;border-radius:4px" } |
| `demo` | red | the one customers watch | ![demo sign-in](../images/logo-demo.png){ width="400" style="background:#1a1a1a;padding:8px;border-radius:4px" } |
| `edge` | purple | the one you own | ![edge sign-in](../images/logo-edge.png){ width="400" style="background:#1a1a1a;padding:8px;border-radius:4px" } |

```bash
python3 utilities/make-env-logo.py --env sandbox
```

This writes `assets/aap-branding/logo-<env>.png` and its `.png.b64` sidecar,
both committed. `config.yml` applies the sidecar as the gateway's `custom_logo`
through `inventory/group_vars/<env>/gateway_settings.yml`, which changes the
**sign-in page only**. The post-login masthead is a bundled UI asset, not a
setting — measured in [#54](https://github.com/ericcames/sales.demos/issues/54) with `custom_logo` applied and re-checked on
AAP 2.7 in [#101](https://github.com/ericcames/sales.demos/issues/101): none of the gateway settings marks the environment
after login.

The colors come from `utilities/env_colors.py`, which the browser extension's
`colors.json` is generated from — so the sign-in page and the post-login pill
cannot disagree about what an environment is.

!!! note "This page said `edge` had no logo until 2026-09-10"
    True when written, and false four commits later:
    [#426](https://github.com/ericcames/sales.demos/issues/426) added the purple
    one along with `inventory/group_vars/edge/gateway_settings.yml`. Adding a
    fourth environment means moving three things together — a color in
    `env_colors.py`, a generated pair in `assets/aap-branding/`, and a
    `gateway_settings.yml`. `check-env-logos.py` catches the last two; nothing
    catches a missing color.

The generated files live in
[`assets/aap-branding/`](https://github.com/ericcames/sales.demos/tree/main/assets/aap-branding),
**not** under `docs/`. They are AAP configuration inputs read at playbook run
time, not documentation; that directory's README says so, because they look like
screenshots and deleting them breaks `config.yml`.

---

## Telling them apart after login

The sign-in badge is gone the moment you are logged in, which is when you are
actually clicking things. No gateway setting fixes that, so the post-login half
is a browser extension:

```bash
# chrome://extensions -> Developer mode -> Load unpacked
utilities/aap-env-badge/
```

It paints a `SANDBOX` / `DEMO` / `EDGE` pill in the middle of the masthead in
the same colors. It covers five UIs in one load and changes nothing on any
cluster:

| UI | Route prefix | How it resolves |
|---|---|---|
| AAP | `aap-*` | Asks AAP directly (`target_env` on job templates) |
| Automation Orchestrator | `ao-automation-orchestrator` | Cache, then AO's proxy API ([#477](https://github.com/ericcames/sales.demos/issues/477)) |
| Self-service portal | `rhaap-portal-*` | Cache only ([#536](https://github.com/ericcames/sales.demos/issues/536)) |
| OCP console | `console-openshift-console` | Cache only ([#539](https://github.com/ericcames/sales.demos/issues/539)) |
| OCP OAuth login | `oauth-openshift` | Cache only ([#539](https://github.com/ericcames/sales.demos/issues/539)) |

"Cache" means `chrome.storage.local` — written by AAP when it resolves, keyed
by cluster domain (everything after `.apps.`). All five UIs share the same
cluster, so the key is identical. Opening AAP in another tab turns a grey pill
colored on every other tab without a reload.

The manifest matches `*.dyn.redhatworkshops.io` (sandbox, demo) and
`*.internal.ames.net` (edge), so the extension works on all three environments.

**It asks AAP which environment it is** rather than recognizing the hostname, so
there is nothing to regenerate when RHDP hands you a new cluster. It reads
`target_env`, which this repo already sets on its job templates. A cluster that
answers but declares no environment gets a neutral `UNRECOGNIZED ENV` pill —
deliberately, since that is when you are most likely to act on the wrong one.

This replaced a generated hostname map that went stale on every rotation and
failed silently ([#87](https://github.com/ericcames/sales.demos/issues/87)).

---

## MCP servers per environment

The environment is in every server's name, so choosing a server is choosing its
posture — one server whose target changed underneath you is exactly the
[#16](https://github.com/ericcames/sales.demos/issues/16) failure, with write tools attached.

| Server | `sandbox` | `demo` | `edge` |
|---|---|---|---|
| OpenShift — `openshift-<env>` | read-write | **read-only** | read-write |
| AAP — `aap-<env>` | writes allowed | **writes refused** | none |
| Self-service portal — `portal-<env>` | read-only | read-only | none |
| Automation Orchestrator — `ao-<env>` | read-only | read-only | none |

**`demo`'s read-only posture is two separate guards, and they must move
together.** Relaxing one and not the other gives a false sense of what the
environment allows:

- **OpenShift** — the `--read-only` flag on `openshift-demo` in
  [`.mcp.json`](https://github.com/ericcames/sales.demos/blob/main/.mcp.json), enforced by the client.
- **AAP** — `aap_mcp_allow_write_operations: false` in
  [`inventory/group_vars/demo/mcp.yml`](https://github.com/ericcames/sales.demos/blob/main/inventory/group_vars/demo/mcp.yml)
  (`true` for sandbox), enforced by the server. `mcp_server.yml` refuses to run
  if it is undefined, and a change deletes and recreates the MCP server, because
  a plain re-apply would keep enforcing the old permission.

The portal and AO servers are read-only by what their tools can do, on every
environment. `edge` has only `openshift-edge`: an `aap-edge` is a posture
decision nobody has made yet, and AO is not installed there. The Grafana server
is not per-environment — Grafana Cloud outlives the clusters.
[`/sales-demos-mcp`](https://github.com/ericcames/sales.demos/blob/main/.claude/skills/sales-demos-mcp/SKILL.md)
sets all of them up.

---

## One host per environment, and why

Each environment has its own host in `inventory/hosts.yml` — `sandbox-local`,
`demo-local`, `edge-local`. That matters: when both groups shared one host, `--limit` filtered
hosts but not `group_vars`, so both environments' variables merged and
`--limit demo` silently used sandbox's hostname and token
([#16](https://github.com/ericcames/sales.demos/issues/16)).

**Never point two environment groups at the same host.**

Everything else that differs per environment sits beside it in
`inventory/group_vars/<env>/`: `connection.yml` (committed), `local.yml` (your
gitignored repoint — see [New environment](new-environment.md#quick-start)),
`gateway_settings.yml` (the sign-in logo), and `mcp.yml` for `sandbox` and
`demo`. Credentials are the exception: they are keyed under `env_secrets.<env>`
in the vault, never in `group_vars/<env>/`.
