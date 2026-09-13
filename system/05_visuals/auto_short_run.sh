#!/usr/bin/env bash
# Wrapper for the flow-shorts-video004 systemd timer/service -- same
# live-accounts-string pattern as auto_batch_run.sh (video 003's long-form
# timer), but calls flow_batch_driver.py directly instead of
# run_full_batch.py: a 5-shot Short needs no chunking/verify-promote
# machinery, just idempotent skip-if-exists retries of whichever shots
# are still missing, with the vertical 9:16 aspect ratio set explicitly
# (this Short's whole reason for existing as a separate timer instead of
# reusing video 003's -- different aspect ratio, different tiny shot
# count, would be wasted complexity going through run_full_batch.py).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACCOUNTS_FILE="$DIR/accounts.local.md"

if [ ! -f "$ACCOUNTS_FILE" ]; then
    echo "auto_short_run.sh: $ACCOUNTS_FILE not found -- nothing to do." >&2
    exit 1
fi

ACCOUNTS=$(awk '/^## Ready-to-use/{found=1; next} found && /^```/{if(in_block){exit} in_block=1; next} found && in_block {print; exit}' "$ACCOUNTS_FILE")

if [ -z "$ACCOUNTS" ]; then
    echo "auto_short_run.sh: couldn't find a --accounts string in $ACCOUNTS_FILE -- nothing to do." >&2
    exit 1
fi

echo "$(date -Iseconds) -- auto_short_run.sh: using accounts string: $ACCOUNTS"
exec "$DIR/run.sh" flow_batch_driver.py "$DIR/../../videos/004-psychopath-problem/short_v1" \
    --accounts "$ACCOUNTS" --range 1-5 --aspect-ratio "9:16"
