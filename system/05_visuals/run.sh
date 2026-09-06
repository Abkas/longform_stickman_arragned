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
exec "$DIR/.venv/bin/python3" "$DIR/$1" "${@:2}"
