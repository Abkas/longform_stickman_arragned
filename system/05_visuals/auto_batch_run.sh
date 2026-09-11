#!/usr/bin/env bash
# Wrapper for the flow-batch-video003 systemd timer/service -- reads the
# --accounts string live from accounts.local.md's "## Ready-to-use
# --accounts string" section on every invocation, rather than a hardcoded
# copy baked into the .service unit (added 2026-09-11: the hardcoded
# version already started going stale the same day it was written, since
# accounts get added/renamed constantly during setup -- editing a systemd
# unit file every time is easy to forget; editing accounts.local.md is
# already the normal workflow).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACCOUNTS_FILE="$DIR/accounts.local.md"

if [ ! -f "$ACCOUNTS_FILE" ]; then
    echo "auto_batch_run.sh: $ACCOUNTS_FILE not found -- nothing to do." >&2
    exit 1
fi

# Pull the fenced code block right after the "Ready-to-use --accounts
# string" heading: the one non-blank, non-fence line in that section.
ACCOUNTS=$(awk '/^## Ready-to-use/{found=1; next} found && /^```/{if(in_block){exit} in_block=1; next} found && in_block {print; exit}' "$ACCOUNTS_FILE")

if [ -z "$ACCOUNTS" ]; then
    echo "auto_batch_run.sh: couldn't find a --accounts string in $ACCOUNTS_FILE -- nothing to do." >&2
    exit 1
fi

echo "$(date -Iseconds) -- auto_batch_run.sh: using accounts string: $ACCOUNTS"
exec "$DIR/run.sh" run_full_batch.py "$DIR/../../videos/003-stoned-ape" --accounts "$ACCOUNTS"
