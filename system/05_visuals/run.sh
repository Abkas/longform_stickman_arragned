#!/usr/bin/env bash
# Always runs a system/05_visuals/*.py script with the dedicated project
# venv's interpreter -- fixes "ModuleNotFoundError" caused by different
# shells resolving a bare `python3` to different interpreters (some with
# playwright/Pillow installed, some without). This removes that ambiguity
# for good: always the same known-good interpreter, full path, no PATH
# lookup involved.
#
# Usage (from the repo root, or anywhere -- path is resolved from this
# script's own location):
#   ./system/05_visuals/run.sh flow_batch_driver.py videos/003-stoned-ape --project-url <url> --range 1-20
#   ./system/05_visuals/run.sh run_full_batch.py videos/003-stoned-ape --project-url <url>
#   ./system/05_visuals/run.sh build_contact_sheets.py videos/003-stoned-ape
#   ./system/05_visuals/run.sh verify_batch.py audit videos/003-stoned-ape
#   ./system/05_visuals/run.sh flow_record_session.py

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Unbuffered stdout -- without this, print() output sits in Python's
# default block buffer (several KB) whenever stdout is redirected to a
# file/pipe instead of a live terminal, so a log file redirected from a
# long run looks empty/stale for minutes at a time even while the script
# is actively working, only catching up in one big dump at exit. Exported
# (not just -u on this process) so it also reaches run_full_batch.py's
# own subprocess.run() calls to flow_batch_driver.py, which inherit the
# environment by default.
export PYTHONUNBUFFERED=1
exec "$DIR/.venv/bin/python3" "$DIR/$1" "${@:2}"
