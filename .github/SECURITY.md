# Security Policy

## Scope

This repository holds **demo documentation** — talk tracks, run sheets,
architecture guides, objections, and design plans, published as a
[GitHub Pages site](https://ericcames.github.io/sales.demos-docs). It is
markdown and images. There is no application, no service, and **no credential of
any kind** — not encrypted, not in a vault, not in an environment file. Nothing
here needs one.

This repository is **public**.

## What should never be committed

- **Customer or company names** — never, in any form: not in a talk track, not
  in an example, not in a screenshot, and not in a commit message, PR title or
  body, or issue
- Credentials of any kind — bearer tokens, private keys, AWS access keys,
  GitHub tokens, passwords
- Kubeconfigs
- Screenshots that show any of the above in a terminal, a browser tab, or a
  window title

Screenshots are the one that actually catches people. A credential in a file is
grep-able; a credential in a PNG is not, and neither the CI guard below nor a
diff review will see it. **Look at the image, not just the diff.**

## RHDP URLs are the documented exception

`*.dyn.redhatworkshops.io` hostnames and cluster IDs **are committed in
plaintext, on purpose**. They are ephemeral demo-platform addresses that expire
in days, not customer-identifying, and run sheets quote real commands against
them because a run sheet with placeholders in it cannot be followed live.

**Do not "fix" them into placeholders**, and note that `check-no-secrets.sh`
deliberately does not flag them — so nothing mechanical would catch the mistake.

Customer data remains forbidden. The exception is narrow: RHDP addresses only.

## Automated enforcement

[`utilities/check-no-secrets.sh`](../utilities/check-no-secrets.sh) runs as the
`secret-guard` check on every pull request and push to `main` via
[`.github/workflows/lint.yml`](workflows/lint.yml). It scans every tracked file
for four shapes:

| | Pattern |
|---|---|
| OpenShift bearer token | `sha256~…` |
| Private key block | `-----BEGIN … PRIVATE KEY-----` |
| AWS access key id | `AKIA…` |
| GitHub token | `ghp_` / `gho_` / `ghu_` / `ghs_` / `ghr_…` |

It matches the *shape* of a real credential, so prose discussing tokens passes
while a genuine value fails the build.

**It is a safety net, not a substitute for reading your own diff.** It cannot
see inside an image, it does not know a customer's name when it reads one, and
it only inspects files that are already tracked — an untracked file is invisible
to it.

## Supported versions

Only the latest commit on `main` is maintained. The published site always
reflects `main`.

## Reporting

There is no private exposure here to disclose responsibly, so **open a public
GitHub issue**.

If you are reporting a committed credential or a customer identifier, **open the
issue without quoting the value**. Say which file and which line; that is enough
to act on. Anything that was committed will be rotated where applicable and
purged from history.
