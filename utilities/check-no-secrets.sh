#!/usr/bin/env bash
# check-no-secrets.sh — CI enforcement of the credential audit.
#
# This repo is public. The same patterns from sales.demos apply here.
set -uo pipefail

fail=0

check() {
  local label="$1" pattern="$2"
  local hits
  hits=$(git ls-files -z | xargs -0 grep -nEI -e "$pattern" 2>/dev/null || true)
  if [ -n "$hits" ]; then
    echo "::error::$label"
    printf '%s\n' "$hits" | sed 's/^/    /'
    fail=1
  fi
}

check "OpenShift bearer token" \
      'sha256~[A-Za-z0-9_-]{20,}'

check "Private key block" \
      '-----BEGIN [A-Z ]*PRIVATE KEY-----'

check "AWS access key id" \
      'AKIA[0-9A-Z]{16}'

check "GitHub token" \
      'gh[pousr]_[A-Za-z0-9]{36}'

if [ "$fail" -ne 0 ]; then
  echo
  echo "Secret-hygiene check failed."
  echo "This repo is public — no credentials in tracked files, ever."
  exit 1
fi

echo "Secret-hygiene check passed."
