# Environments

Three, and they are not the same kind of thing.

| Environment | What it is | Posture |
|---|---|---|
| `sandbox` | The RHDP environment you build against and break | Read-write |
| `demo` | The RHDP environment you show customers | Read-only over MCP |
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

Both RHDP environments look identical at the AAP login page, and the moment you
are most likely to act on the wrong one is the moment before you have touched
anything. Each gets a badged sign-in logo — green for the environment you break,
red for the one you show customers, the same severity convention as `aap_config`.

```bash
python3 utilities/make-env-logo.py --env sandbox
```

This sets the gateway's `custom_logo`, which changes the **sign-in page only**.
The post-login masthead is a bundled UI asset, not a setting — re-measured in
[#54](https://github.com/ericcames/sales.demos/issues/54) with `custom_logo`
applied, and none of the 44 gateway settings marks the environment after login.

!!! note "`edge` has no badged logo"
    `inventory/group_vars/edge/` has only `connection.yml` — no
    `gateway_settings.yml` — so nothing sets `custom_logo` there.

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

It paints a `SANDBOX` / `DEMO` pill in the middle of the masthead in the same
colours and matches both environments in one load. It changes nothing on the
cluster.

**It asks AAP which environment it is** rather than recognising the hostname, so
there is nothing to regenerate when RHDP hands you a new cluster. It reads
`target_env`, which this repo already sets on its job templates. A cluster that
answers but declares no environment gets a neutral `UNRECOGNIZED ENV` pill —
deliberately, since that is when you are most likely to act on the wrong one.

This replaced a generated hostname map that went stale on every rotation and
failed silently ([#87](https://github.com/ericcames/sales.demos/issues/87)).

---

## One host per environment, and why

Each environment has its own host in `inventory/hosts.yml` — `sandbox-local`,
`demo-local`. That matters: when both groups shared one host, `--limit` filtered
hosts but not `group_vars`, so both environments' variables merged and
`--limit demo` silently used sandbox's hostname and token
([#16](https://github.com/ericcames/sales.demos/issues/16)).

**Never point two environment groups at the same host.**
