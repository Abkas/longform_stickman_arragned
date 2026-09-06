#!/usr/bin/env python3
"""
One-time recording session: launches a real, persistent Chromium profile
(cookies/login survive between runs, same as a normal browser), opens
Flow, and opens the Playwright Inspector so you can record yourself
generating ONE image by hand. The Inspector emits the Python code for each
action live -- copy the whole thing out when you're done and send it back;
that becomes the basis for flow_batch_driver.py's real selectors.

Why persistent + a visible window: Google's sign-in flow actively blocks
freshly-spun-up automated browsers ("this browser may not be secure"). A
persistent profile you log into once, by hand, in a real visible window,
looks like an ordinary browser session on every later run -- no different
from just using Chrome normally, just launched by a script instead of
clicking an icon.

Usage:
    # single-account setup (default profile):
    python system/05_visuals/flow_record_session.py

    # multi-account setup (one profile per Flow account, for
    # flow_batch_driver.py's --accounts rotation) -- run once per account:
    python system/05_visuals/flow_record_session.py --account acc1
    python system/05_visuals/flow_record_session.py --account acc2

First run: log into your Google account in the window that opens, same as
any browser. Then navigate to Flow, start a new project, and in the
Inspector window that pops up, click "Record" and walk through generating
ONE image (paste a prompt, submit, wait for it, click download). Stop
recording, copy the generated code out of the Inspector, paste it into a
reply here.

The profile persists in system/05_visuals/.flow_profile/ (or
.flow_profile_<account>/ when --account is given; both gitignored -- add
to .gitignore if not already there) so you only log in once per account;
every later run of this script or flow_batch_driver.py reuses that same
session. IMPORTANT for multi-account: log into a DIFFERENT Google account
in each --account run -- reusing the same Google login across two
--account profiles defeats the point (flow_batch_driver.py's account
rotation assumes each profile is a genuinely separate account).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright


def profile_dir_for(account: str | None) -> Path:
    base = Path(__file__).parent
    return base / ".flow_profile" if not account else base / f".flow_profile_{account}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", help="Name for a second/third/etc. Flow account's "
                     "profile (used with flow_batch_driver.py's --accounts). "
                     "Omit for the single default profile.")
    args = ap.parse_args()

    profile_dir = profile_dir_for(args.account)
    profile_dir.mkdir(exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://flow.google.com")
        who = f"account '{args.account}'" if args.account else "the default account"
        print(
            f"\nWindow open for {who} (profile: {profile_dir}).\n"
            "Log into Google if prompted -- USE A DIFFERENT GOOGLE ACCOUNT "
            "than any other profile you've already set up this way -- then "
            "navigate to a project and Flow's image-generation screen.\n"
            "Then call page.pause() equivalent: press the Playwright "
            "Inspector's Record button (should already be open) and walk "
            "through ONE full generation (paste prompt -> submit -> wait "
            "-> download). Copy the code it generates and send it back.\n"
        )
        page.pause()  # opens the Inspector with a Record toggle
        context.close()


if __name__ == "__main__":
    main()
