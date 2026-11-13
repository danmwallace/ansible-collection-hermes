#!/usr/bin/bash
# bash roles/mcp_servers/tests/check-verbose-log.sh (from the collection root)
# Runs the molecule scenario at -v and fails if a secret or the planted account
# details from ~/.claude.json appear anywhere in Ansible's output.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
log=$(mktemp)
trap 'rm -f "$log"' EXIT
ANSIBLE_VERBOSITY=1 molecule test -s default >"$log" 2>&1; rc=$?
fail=0
if [ "$rc" -ne 0 ]; then echo "FAIL  molecule itself failed (rc $rc)"; fail=1; else echo "ok    molecule passed"; fi
# slurp shows a file base64-encoded: also look for prepare.yml's ~/.claude.json that way
pii_b64=$(printf '%s' '{"oauthAccount": {"emailAddress": "pii-sentinel@example.invalid"}}' | base64 -w0)
for s in s3cr3t-value trap-secret pii-sentinel@example.invalid "${pii_b64:0:40}"; do
    # Only the role's own runs count: verify's tests print the secret on purpose.
    n=$(sed 's/\x1b\[[0-9;]*m//g' "$log" | sed '/verify: Executing/,$d' | grep -c -- "$s")
    if [ "$n" -gt 0 ]; then echo "FAIL  '$s' appears $n time(s) in the -v output"; fail=1; else echo "ok    '$s' not in the -v output"; fi
done
exit "$fail"
