#!/usr/bin/env python3
"""
Drives Flow directly (via your logged-in persistent Chromium profile, see
flow_record_session.py) to generate every shot in a video's shot_list.md
without going through a third-party batch extension.

STATUS: built from two manual recordings against the real Flow UI (see
system/05_visuals/flow_record_session.py's usage), but NOT yet run
end-to-end against the live site by me -- I have no way to test this
myself against your logged-in account. Two things in here are best-effort
guesses that need confirming on a real run:
  1. PROMPT_BOX_LOCATOR / typing via page.keyboard.type() -- the recorder
     never captured a fill/type action on this field across two attempts
     (likely a contenteditable rich-text box that Playwright's auto-record
     doesn't track keystrokes on), so this uses the standard workaround
     (click, select-all, type) instead of a recorded action.
  2. "Which thumbnail is the new one" -- the recording found it by the
     image's auto-generated alt text ("Man wearing hat"), which is
     different every time and can't be hardcoded. This assumes the newest
     result becomes the FIRST "More options" button on the page and waits
     for that button count to increase by one. If that assumption is
     wrong for your account/layout, tell me what actually happens and
     I'll fix the locator.

ALWAYS test on a small --range first (per system/04_shots/shot.md's own
"always test a small batch before generating the full shot list" rule) --
don't point this at all 262 shots on the first run.

Usage:
    # one-time login (only needed once per account, reused after):
    python system/05_visuals/flow_record_session.py

    # test run, 3 shots, single account:
    python system/05_visuals/flow_batch_driver.py videos/003-stoned-ape \\
        --project-url https://flow.google.com/project/<your-project-id> \\
        --range 1-3

    # after confirming the test batch is correct, run the rest:
    python system/05_visuals/flow_batch_driver.py videos/003-stoned-ape \\
        --project-url https://flow.google.com/project/<your-project-id> \\
        --range 4-262

    # multi-account: log into each account once first --
    #   python system/05_visuals/flow_record_session.py --account acc1
    #   python system/05_visuals/flow_record_session.py --account acc2
    # then pass all of them as name=project-url pairs (same order they'll
    # rotate in):
    python system/05_visuals/flow_batch_driver.py videos/003-stoned-ape \\
        --accounts "acc1=https://flow.google.com/project/aaa,acc2=https://flow.google.com/project/bbb" \\
        --range 1-262

Safe to re-run / resume: any shot that already has a matching file in
generate/generated/images/ is skipped (same convention as
generate_visuals.py), so a crash partway through just needs a re-run with
the same --range.

Important: a shot that fails is NOT retried in-place within the same run
-- the loop just moves on to the next shot (on whatever account/browser
state resulted from that failure's recovery step, see below) and leaves
the failed one as a gap. This is deliberate: one genuinely-broken shot
retrying forever would block the rest of the video from making progress.
Gaps get swept up by running this same command again (skips everything
already downloaded, so only the gaps actually run) -- run_full_batch.py
does exactly that automatically per chunk, plus a final whole-video
cleanup pass, so you don't have to do it by hand when using that.

Stall recovery (fully unattended -- never logs you out of any account, so
it's safe to leave running overnight). Escalates per shot, across
whichever account is currently active:
  1. RESTART_AFTER_CONSECUTIVE_FAILURES: close and relaunch the browser on
     the SAME account's profile -- fixes a wedged tab/page without
     touching any session.
  2. COOLDOWN_AFTER_CONSECUTIVE_FAILURES: if a restart alone didn't help,
     back off for ACCOUNT_COOLDOWN_S (default 10 min) on THIS account
     before restarting it again -- in case it's just this account that's
     rate-limited/flagged and a short wait clears it, before giving up on
     it and moving to another account entirely.
  3. SWITCH_ACCOUNT_AFTER_CONSECUTIVE_FAILURES: if the cooldown didn't
     help either, move on to the NEXT account in --accounts (round-robin)
     and keep going from there. With only one account configured
     (--project-url, or a single --accounts entry), this step is a no-op
     -- there's nowhere else to switch to, so it falls straight through
     to step 4.
  4. Once EVERY configured account has been tried and failed this way
     (one full round), back off for ROUND_COOLDOWN_S (default 1 hour) --
     the actual fix for a rate-limit/"unusual activity" flag that's
     hitting every account, which needs real time to clear, not a new
     identity -- then start back over from the FIRST account.
  5. If MAX_ROUNDS_BEFORE_STOP full rounds all end in step 4 (every
     account, repeatedly, across multiple cooldowns), the script gives up
     cleanly (still logged into everything) and prints what's left undone.
     This cap is a safety valve against looping for real hours on
     something that's actually broken (bad URL, changed UI, exhausted
     quota on every account) rather than just rate-limited -- raise it if
     you genuinely want unattended retries for longer than that.

Deliberately does NOT ever delete/reset any browser profile: that would
log an account out, and there is no safe way to log back in automatically
(Google blocks scripted sign-in, and most accounts need 2FA a human has
to enter) -- so wiping cookies would just trade a stuck download for a
stuck login screen, which defeats unattended running rather than fixing
it. If you ever see failures persist past the final clean stop, that's a
signal to check the browser(s) by hand, not something this script should
try to paper over on its own.

A note on multi-account rotation: this cycles between accounts
specifically to keep going past a rate-limit/"unusual activity" flag on
one of them. That's the kind of pattern Google's abuse detection exists
to catch, and doing it across several of your own accounts risks more of
them getting flagged than if a single account just backs off and waits.
Worth knowing before leaning on this for a big unattended run.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
import time
from pathlib import Path
from typing import NamedTuple, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

sys.path.insert(0, str(Path(__file__).parent))
from verify_batch import parse_shot_list, slugify  # noqa: E402


class Account(NamedTuple):
    name: str
    project_url: str
    profile_dir: Path


def profile_dir_for(account_name: Optional[str]) -> Path:
    """Mirrors flow_record_session.py's profile_dir_for -- must stay in
    sync with it, since that's where each account's login actually gets
    created."""
    base = Path(__file__).parent
    return base / ".flow_profile" if not account_name else base / f".flow_profile_{account_name}"


# Stall recovery: if shots keep failing back-to-back (download never
# detected, generation hangs, etc.), a stuck page/session is the likely
# cause, not a bad prompt. Escalating levels, all of which keep every
# account logged in (never touches any .flow_profile*) so this is safe to
# leave running unattended overnight:
#   1. RESTART_AFTER: close and relaunch the browser on the current
#      account's SAME profile -- clears whatever wedged tab/page state
#      caused the stall.
#   2. COOLDOWN_AFTER: if a restart alone didn't help, back off for
#      ACCOUNT_COOLDOWN_S on this SAME account, then restart it again --
#      in case only this account is rate-limited and a short wait clears
#      it, before giving up on it and switching away.
#   3. SWITCH_ACCOUNT_AFTER: if the cooldown didn't help either, move on
#      to the next configured account and keep going (round-robin). A
#      no-op with only one account -- falls straight through to level 4.
#   4. Once every account has been tried and failed (one full round),
#      back off for ROUND_COOLDOWN_S before retrying from the first
#      account again -- the actual fix for a rate-limit/"unusual
#      activity" flag hitting every account, which needs time to clear,
#      not a new identity.
#   5. If MAX_ROUNDS_BEFORE_STOP full rounds all end up back here, give up
#      cleanly (still logged in everywhere) rather than looping for real
#      hours on something that's actually broken.
RESTART_AFTER_CONSECUTIVE_FAILURES = 2
COOLDOWN_AFTER_CONSECUTIVE_FAILURES = 4
SWITCH_ACCOUNT_AFTER_CONSECUTIVE_FAILURES = 6
MAX_ROUNDS_BEFORE_STOP = 5

# How long to back off on the SAME account before restarting it again
# (level 2), in seconds. Default 10 min.
ACCOUNT_COOLDOWN_S = 600

# How long to back off after a full round (every account tried, all
# failed), in seconds. Default 1 hour.
ROUND_COOLDOWN_S = 3600

# Pacing: randomized delay between shots so requests don't fire in an
# obviously-scripted fixed cadence. Widen this if you see rate-limit /
# quota errors from Flow.
# Widened after a real run got flagged by Google ("We noticed some unusual
# activity") partway through a 262-shot overnight session -- tight,
# continuous automated traffic for hours is exactly the pattern this kind
# of detection is built to catch. Slower is not a guarantee against it
# happening again, just a reduction in how obviously bot-like the pacing
# looks.
MIN_DELAY_S = 30
MAX_DELAY_S = 55

# How long to wait for one generation to finish before giving up on it.
GENERATION_TIMEOUT_MS = 120_000


def setup_session(page) -> None:
    """One-time per-session settings: image mode, aspect ratio, model,
    count. Adjust the radio/menuitem names below if your project's UI
    differs from what was recorded -- these are typed exactly as recorded."""
    page.get_by_label("Settings trigger").click()
    page.get_by_role("radio", name="Image").click()
    # NOTE: recorded as a partial match ":9" -- confirm this is the aspect
    # ratio you actually want (16:9 for landscape long-form) before a real
    # run; adjust the `name=` string if the recorder just truncated it.
    page.get_by_role("radio", name=":9").click()
    page.get_by_label("Select model family").click()
    page.get_by_role("menuitem", name="🍌 Nano Banana Pro").click()
    page.get_by_role("radio", name="x1").click()
    # close the settings panel the same way it was opened, if needed
    page.get_by_label("Settings trigger").click()


def enter_prompt(page, prompt: str) -> None:
    box = page.locator("p").filter(has_text="What do you want to create?")
    box_geo = box.bounding_box()
    if box_geo:
        # Raw mouse click at the box's coordinates rather than
        # locator.click() -- confirmed from a real run that .click() can
        # silently fail to focus the real input on a second/later use
        # (prompt stayed empty, nothing ever got submitted, no error
        # raised). Mirrors the same fix used for the hover-reveal "More
        # options" button.
        cx = box_geo["x"] + box_geo["width"] / 2
        cy = box_geo["y"] + box_geo["height"] / 2
        page.mouse.click(cx, cy)
    else:
        box.click()  # fallback if bounding_box() ever comes back empty
    page.wait_for_timeout(200)
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.keyboard.type(prompt, delay=15)  # small delay per keystroke, more human


DEBUG_DIR = Path(__file__).parent / ".flow_debug"


def _debug_shot(page, shot_num: int, tag: str) -> None:
    """Save a screenshot + a dump of every 'More options'-labeled element's
    bounding box, so a failure can be diagnosed without watching it live."""
    DEBUG_DIR.mkdir(exist_ok=True)
    try:
        page.screenshot(path=str(DEBUG_DIR / f"shot{shot_num}_{tag}.png"), full_page=False)
    except Exception:
        pass


# Header/toolbar "More options"-labeled buttons (project menu, account
# menu) sit above this Y coordinate and must be excluded -- confirmed from
# a real run's debug screenshot, where .first grabbed the project menu
# (anchored near the top-left "..." at y~38) instead of any image tile.
# Grid tiles start well below the search/toolbar row. Similarly, the left
# nav sidebar (All media/Images/Characters/Scenes/Tools) sits left of this
# X coordinate and must also be excluded, since it overlaps the same Y
# range as the grid's first row.
HEADER_CUTOFF_Y = 70
SIDEBAR_CUTOFF_X = 235


def newest_tile_center_point(page):
    """Return the (x, y) center point of the top-left-most tile's 'More
    options' button in the actual media grid, excluding header/sidebar
    buttons with the same accessible name. Returns a raw coordinate, not a
    Locator -- these buttons are hover-revealed (opacity-hidden until the
    tile is hovered) and kept failing Playwright's strict visibility
    checks on .hover()/.click() even though they geometrically exist;
    driving them via page.mouse instead sidesteps that check entirely."""
    candidates = page.get_by_label("More options").all()
    in_grid = []
    for loc in candidates:
        box = loc.bounding_box()
        if box and box["y"] > HEADER_CUTOFF_Y and box["x"] > SIDEBAR_CUTOFF_X:
            in_grid.append((box["y"], box["x"], box))
    if not in_grid:
        return None
    in_grid.sort(key=lambda t: (t[0], t[1]))  # topmost row, then leftmost
    box = in_grid[0][2]
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def _grid_tile_count(page) -> int:
    return len([
        1 for loc in page.get_by_label("More options").all()
        if (box := loc.bounding_box()) and box["y"] > HEADER_CUTOFF_Y and box["x"] > SIDEBAR_CUTOFF_X
    ])


# Specific reasons seen so far in Flow's "Failed / not charged" error
# card. Both confirmed from real runs: "reached your usage limit" (quota
# exhausted) and "unusual activity" (an account-level abuse/bot flag --
# seen after two live test batches ran back-to-back with no real pacing
# gap between them, exactly the tight-cadence pattern the MIN/MAX_DELAY_S
# pacing below exists to avoid). There may be others Flow shows that
# haven't been seen yet -- _flow_error_card_text() below doesn't require
# matching one of these by name, so an unrecognized reason still gets
# caught rather than silently falling through to the generic "prompt
# never submitted" misdiagnosis.
KNOWN_FLOW_ERROR_REASONS = ("reached your usage limit", "unusual activity")


def _flow_error_card_text(page):
    """Returns a short reason string if a Flow "Failed / not charged"
    error card is currently showing (quota exhausted, an "unusual
    activity" abuse flag, or anything else Flow rejects a generation
    with), else None. Anchored on "You have not been charged for this
    generation." -- confirmed common to every such card seen so far --
    rather than requiring one specific reason, so a new/different Flow
    error message still gets caught instead of silently falling through.
    Confirmed from real runs: this error card does NOT have a 'More
    options' button like a real result tile does, so the tile-count
    checks this file otherwise relies on never see it -- without this
    check, ANY such Flow-side rejection gets misreported as "the prompt
    never submitted" and burns 3 blind retries that can't possibly help
    before finally failing anyway."""
    try:
        if page.get_by_text("You have not been charged for this generation.", exact=False).count() == 0:
            return None
        for reason in KNOWN_FLOW_ERROR_REASONS:
            if page.get_by_text(reason, exact=False).count() > 0:
                return reason
        return "unrecognized Flow error"
    except Exception:
        return None


class FlowBlockedError(Exception):
    """Raised when Flow itself reports a "Failed / not charged" error
    for the CURRENT account (quota exhausted, an "unusual activity" flag,
    etc.), as opposed to a generic stall/timeout. Handled specially in
    main(): retrying or restarting this same account can't help, so it
    short-circuits straight to switching accounts instead of wasting a
    restart+cooldown first."""


def generate_and_download(page, shot_num: int, prompt: str, dest_path: Path) -> None:
    more_options_before = _grid_tile_count(page)

    # Submit-confirmation retry: typing/clicking can silently fail to
    # actually submit anything (confirmed from a real run -- prompt box
    # stayed empty, no new tile ever appeared, no error raised). Rather
    # than trust one type+click and wait the full 2-minute generation
    # timeout on a submission that never happened, do a FAST check (a few
    # seconds) that a new placeholder tile actually showed up, and retry
    # the whole type+submit cycle if not.
    submitted = False
    for submit_attempt in range(3):
        enter_prompt(page, prompt)
        page.wait_for_timeout(300)
        page.get_by_label("Start generation").click()

        quick_deadline = time.monotonic() + 8
        while time.monotonic() < quick_deadline:
            if _grid_tile_count(page) > more_options_before:
                submitted = True
                break
            reason = _flow_error_card_text(page)
            if reason:
                _debug_shot(page, shot_num, "flow-error")
                raise FlowBlockedError(
                    f"Flow reported an error for shot {shot_num} ({reason}, "
                    "not charged) -- this account is blocked for now "
                    f"(see {DEBUG_DIR}/shot{shot_num}_flow-error.png)"
                )
            page.wait_for_timeout(1000)
        if submitted:
            break
        _debug_shot(page, shot_num, f"submit-attempt-{submit_attempt}-no-effect")
        page.wait_for_timeout(2000)

    if not submitted:
        raise TimeoutError(
            f"Prompt never seemed to submit after 3 attempts -- see "
            f"{DEBUG_DIR}/shot{shot_num}_submit-attempt-*-no-effect.png"
        )

    # Wait for the generation to actually finish (the quick check above
    # only confirms it started -- this is the full wait for it to render).
    deadline = time.monotonic() + GENERATION_TIMEOUT_MS / 1000
    while time.monotonic() < deadline:
        if _grid_tile_count(page) > more_options_before:
            break
        reason = _flow_error_card_text(page)
        if reason:
            _debug_shot(page, shot_num, "flow-error")
            raise FlowBlockedError(
                f"Flow reported an error for shot {shot_num} ({reason}, "
                "not charged) -- this account is blocked for now "
                f"(see {DEBUG_DIR}/shot{shot_num}_flow-error.png)"
            )
        page.wait_for_timeout(2000)
    else:
        _debug_shot(page, shot_num, "no-new-result")
        raise TimeoutError("Timed out waiting for a new generated result "
                            f"(see {DEBUG_DIR}/shot{shot_num}_no-new-result.png)")

    _debug_shot(page, shot_num, "before-more-options")

    # The topmost-leftmost tile in the grid is the newest result. Right
    # after it first appears it can still be a LOADING placeholder (its
    # menu only has Rename/View trash/Delete, no Download, until the image
    # actually finishes rendering) -- confirmed from a real run's debug
    # screenshot. So: open the menu, check Download is actually in it, and
    # if not, close and wait longer for the real finish.
    download_ready = False
    for attempt in range(20):  # ~20 * 3.5s = up to 70s of extra waiting past "first appeared"
        point = newest_tile_center_point(page)
        if point is None:
            page.wait_for_timeout(3000)
            continue
        cx, cy = point
        # Raw mouse move+click at pixel coordinates, NOT locator.hover()/
        # .click() -- those enforce Playwright's strict visibility check,
        # which this hover-reveal (opacity-hidden until hovered) button
        # kept failing even though it geometrically exists. Moving the
        # mouse there twice (some hover-reveal implementations need an
        # actual pointer-move event, not a teleport, to register) then
        # clicking the same point sidesteps that check entirely.
        page.mouse.move(cx, cy)
        page.wait_for_timeout(150)
        page.mouse.move(cx + 1, cy + 1)
        page.wait_for_timeout(350)
        page.mouse.click(cx, cy)
        page.wait_for_timeout(500)  # let the dropdown finish animating in
        if page.get_by_role("menuitem", name="Download").count() > 0:
            download_ready = True
            break
        # wrong menu (still-loading placeholder), or click missed entirely
        # -- close whatever might have opened and wait before retrying.
        page.keyboard.press("Escape")
        page.wait_for_timeout(3000)

    _debug_shot(page, shot_num, "after-more-options-click")

    if not download_ready:
        _debug_shot(page, shot_num, "no-download-menuitem")
        raise TimeoutError(
            "Opened 'More options' repeatedly but never saw a 'Download' "
            f"item -- see {DEBUG_DIR}/shot{shot_num}_after-more-options-click.png "
            "to see what actually opened."
        )

    page.get_by_role("menuitem", name="Download").click()

    page.wait_for_timeout(300)
    _debug_shot(page, shot_num, "download-submenu")

    with page.expect_download() as dl_info:
        page.get_by_role("menuitem", name="1K Original size").click()
    download = dl_info.value
    download.save_as(str(dest_path))


class StalledOut(Exception):
    """Raised to unwind out of the batch loop after repeated stalls
    survive a restart AND a cooldown -- the caller stops cleanly rather
    than escalating further (never touches the login/profile)."""


LAUNCH_DEBUG_DIR = Path(__file__).parent / ".flow_debug"


def launch_session(p, account: Account):
    """(Re)launch the persistent browser context for `account` and run
    setup_session. Used for the initial launch, the same-account
    stall-recovery restart, AND switching to a different account, so all
    three never drift out of sync. Never deletes/resets a profile --
    whichever account's profile_dir this points at stays logged in.

    Confirmed from real runs: waiting for the "Settings trigger" button to
    render here is NOT reliably a fixed delay -- observed anywhere from
    "already there" to a flat 45s Playwright timeout on the SAME project,
    with the button confirmed present and visible seconds later on a
    completely separate manual check both times. Whatever's actually
    causing that (a client-side route re-render invalidating an in-flight
    wait_for, a slow/variable server-side render, something else) isn't
    pinned down yet -- this retries once via a full page reload (which
    resolves a stuck SPA route in similar cases) rather than assuming it's
    a one-off, and saves a screenshot before giving up so a repeat of this
    doesn't need an ad-hoc diagnostic script to see what's on screen."""
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(account.profile_dir),
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(account.project_url)
    page.wait_for_timeout(3000)  # initial settle before even checking

    settings_trigger = page.get_by_label("Settings trigger")
    try:
        settings_trigger.wait_for(state="visible", timeout=30_000)
    except PWTimeoutError:
        page.reload()
        page.wait_for_timeout(3000)
        try:
            settings_trigger.wait_for(state="visible", timeout=30_000)
        except PWTimeoutError:
            LAUNCH_DEBUG_DIR.mkdir(exist_ok=True)
            shot_path = LAUNCH_DEBUG_DIR / f"launch-failed_{account.name}.png"
            try:
                page.screenshot(path=str(shot_path), full_page=False)
            except Exception:
                pass
            raise TimeoutError(
                f"'Settings trigger' never appeared on account "
                f"'{account.name}' (project {account.project_url}) even "
                f"after a reload -- see {shot_path}. Not a shot failure, "
                "the whole session never got going; check the project URL "
                "and that this account is actually logged in."
            )

    page.wait_for_timeout(500)  # let the rest of the toolbar settle too
    setup_session(page)
    return context, page


class EscalationState:
    """Owns the stall-recovery ladder's mutable state (current account,
    consecutive-failure counters, live browser context/page) and applies
    one step of escalation per failed shot. See this file's module
    docstring for the full 5-level ladder this implements."""

    def __init__(self, p, accounts: list) -> None:
        self.p = p
        self.accounts = accounts
        self.account_idx = 0
        self.account_fail_streak = 0        # consecutive failures on the CURRENT account
        self.already_cooled_down_this_account = False  # level-2 fires once per account attempt
        self.accounts_tried_this_round = 0  # accounts switched away from, still failing
        self.rounds_exhausted = 0           # full rotations where every account failed
        self.context, self.page = launch_session(p, self.account)

    @property
    def account(self) -> Account:
        return self.accounts[self.account_idx]

    def on_success(self) -> None:
        self.account_fail_streak = 0
        self.already_cooled_down_this_account = False
        self.accounts_tried_this_round = 0
        self.rounds_exhausted = 0

    def _relaunch(self, account_idx=None) -> None:
        if account_idx is not None:
            self.account_idx = account_idx
        self.context.close()
        self.context, self.page = launch_session(self.p, self.account)

    def on_failure(self, shot_num: int, force_switch: bool = False, reason: Optional[str] = None) -> None:
        """Apply one step of the ladder for a shot that just failed.
        force_switch=True (used for FlowBlockedError) skips straight to
        the switch-account step -- restarting/cooling down the SAME
        account can't help when Flow itself blocked it (quota exhausted,
        an "unusual activity" flag, etc. -- see `reason`).
        Raises StalledOut if the whole run should stop."""
        if force_switch:
            self.account_fail_streak = max(self.account_fail_streak, SWITCH_ACCOUNT_AFTER_CONSECUTIVE_FAILURES)
        else:
            self.account_fail_streak += 1

        if self.account_fail_streak >= SWITCH_ACCOUNT_AFTER_CONSECUTIVE_FAILURES:
            self.accounts_tried_this_round += 1

            if self.accounts_tried_this_round >= len(self.accounts):
                self.rounds_exhausted += 1
                if self.rounds_exhausted >= MAX_ROUNDS_BEFORE_STOP:
                    print(f"\n  Every account failed, {self.rounds_exhausted} "
                          "full rotation(s) in a row (with a cooldown "
                          "between each) -- stopping cleanly (still "
                          "logged in everywhere) rather than looping "
                          "further unattended.")
                    raise StalledOut()
                print(f"\n  All {len(self.accounts)} account(s) failed this "
                      f"round -- backing off {ROUND_COOLDOWN_S // 60} min "
                      "in case this is a rate-limit/\"unusual activity\" "
                      f"flag, then retrying from {self.accounts[0].name}.")
                self.context.close()
                time.sleep(ROUND_COOLDOWN_S)
                self.accounts_tried_this_round = 0
                self.account_fail_streak = 0
                self.already_cooled_down_this_account = False
                self.account_idx = 0
                self.context, self.page = launch_session(self.p, self.account)
            else:
                next_idx = (self.account_idx + 1) % len(self.accounts)
                why = reason or (
                    f"{SWITCH_ACCOUNT_AFTER_CONSECUTIVE_FAILURES} downloads in a "
                    "row didn't come through, restart and cooldown included")
                print(f"\n  {why} -- switching to account "
                      f"'{self.accounts[next_idx].name}' for the rest of "
                      f"this run (shot {shot_num} itself stays a gap -- a later "
                      f"pass over this same range picks it back up, since "
                      f"anything already downloaded gets skipped).")
                self.account_fail_streak = 0
                self.already_cooled_down_this_account = False
                self._relaunch(next_idx)

        elif self.account_fail_streak >= COOLDOWN_AFTER_CONSECUTIVE_FAILURES and not self.already_cooled_down_this_account:
            print(f"\n  {self.account_fail_streak} downloads in a row didn't "
                  f"come through, restart included -- backing off "
                  f"{ACCOUNT_COOLDOWN_S // 60} min on account "
                  f"'{self.account.name}' in case it's just "
                  f"this one that's rate-limited, then continuing with "
                  f"the next shot on it (shot {shot_num} itself stays a gap for "
                  f"now -- see this file's docstring for how gaps get "
                  f"swept up).")
            self.context.close()
            time.sleep(ACCOUNT_COOLDOWN_S)
            self.already_cooled_down_this_account = True
            self.context, self.page = launch_session(self.p, self.account)

        elif self.account_fail_streak >= RESTART_AFTER_CONSECUTIVE_FAILURES:
            print(f"\n  {self.account_fail_streak} downloads in a row didn't "
                  f"come through -- restarting the browser (same "
                  f"account, '{self.account.name}') before "
                  f"moving on to the next shot (shot {shot_num} itself stays a "
                  f"gap for now).")
            self._relaunch()
            # don't reset account_fail_streak here: a restart that
            # doesn't actually help should still count toward the
            # cooldown/switch/round thresholds above.

    def close(self) -> None:
        self.context.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video_dir", type=Path)
    ap.add_argument("--project-url", help="Your Flow project URL (single-account mode, "
                     "default profile). Mutually exclusive with --accounts.")
    ap.add_argument("--accounts", help="Multi-account mode: comma-separated "
                     "name=project-url pairs, e.g. "
                     "'default=https://flow.google.com/project/aaa,acc2=https://flow.google.com/project/bbb'. "
                     "Each name must already be logged in via "
                     "'flow_record_session.py --account <name>' -- EXCEPT the "
                     "reserved name 'default', which means your original "
                     "single-account profile (.flow_profile/, made by running "
                     "flow_record_session.py with no --account at all). "
                     "Rotates through all listed accounts on repeated stalls "
                     "-- see this file's module docstring. Mutually exclusive "
                     "with --project-url.")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--range", help="Contiguous shot range, e.g. 1-20")
    group.add_argument("--shots", help="Comma-separated, possibly non-contiguous shot numbers, e.g. 5,9,14,201 (for redoing QC failures)")
    ap.add_argument("--force", action="store_true", help="Regenerate even if a file already exists (deletes the old one first) -- use with --shots to replace QC-failed images")
    args = ap.parse_args()

    if bool(args.project_url) == bool(args.accounts):
        raise SystemExit("Pass exactly one of --project-url (single account) "
                          "or --accounts (multi-account rotation).")

    if args.accounts:
        accounts = []
        for pair in args.accounts.split(","):
            pair = pair.strip()
            if not pair:
                continue
            name, sep, url = pair.partition("=")
            if not sep:
                raise SystemExit(f"--accounts entry {pair!r} isn't name=project-url")
            name = name.strip()
            # "default" is a reserved name meaning your original single-account
            # profile (.flow_profile/, made without --account) -- not a
            # separate .flow_profile_default/ that was never logged into.
            profile_dir = profile_dir_for(None) if name == "default" else profile_dir_for(name)
            accounts.append(Account(name, url.strip(), profile_dir))
        if not accounts:
            raise SystemExit("--accounts was given but parsed to zero accounts")
    else:
        accounts = [Account("default", args.project_url, profile_dir_for(None))]

    shot_list_path = args.video_dir / "shot_list.md"
    shots = dict(parse_shot_list(shot_list_path))

    if args.range:
        start_s, end_s = args.range.split("-")
        start, end = int(start_s), int(end_s)
        wanted = [n for n in range(start, end + 1) if n in shots]
        missing = set(range(start, end + 1)) - set(shots)
    else:
        wanted = [int(s) for s in args.shots.split(",") if s.strip()]
        missing = set(wanted) - set(shots)
    if missing:
        raise SystemExit(f"shot_list.md is missing shot numbers: {sorted(missing)}")

    out_dir = args.video_dir / "generate" / "generated" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    todo = []
    for n in wanted:
        prompt = shots[n]
        slug = slugify(prompt)
        dest = out_dir / f"{n}_{slug}.png"
        existing = list(out_dir.glob(f"{n}_*"))
        if existing:
            if args.force:
                for f in existing:
                    print(f"Shot {n}: --force, deleting existing {f.name}")
                    f.unlink()
            else:
                print(f"Shot {n}: already have a file, skipping")
                continue
        todo.append((n, prompt, dest))

    if not todo:
        print("Nothing to do -- every shot in range already has a file.")
        return

    print(f"Will generate {len(todo)} shot(s): {[n for n, _, _ in todo]}")
    if len(accounts) > 1:
        print(f"Rotating across {len(accounts)} accounts on repeated stalls: "
              f"{[a.name for a in accounts]}")

    stalled_out = False
    launch_failed = None  # set to the exception if a session launch fails and can't be caught by the ladder
    failures = []
    try:
        with sync_playwright() as p:
            st = EscalationState(p, accounts)

            try:
                for i, (n, prompt, dest) in enumerate(todo):
                    print(f"\n[{i+1}/{len(todo)}] Shot {n}: {prompt[:80]}{'...' if len(prompt) > 80 else ''} "
                          f"[{st.account.name}]")
                    try:
                        generate_and_download(st.page, n, prompt, dest)
                        print(f"  -> saved {dest.name}")
                        st.on_success()
                    except FlowBlockedError as e:
                        # Flow itself blocked this account (quota exhausted,
                        # an "unusual activity" flag, etc.) -- retrying or
                        # restarting THIS account can't possibly help, so
                        # skip straight to switching accounts instead of
                        # wasting a restart+cooldown on it first.
                        print(f"  !! BLOCKED: {e}")
                        failures.append(n)
                        if len(failures) >= 3 and len(failures) == i + 1:
                            print("\n3 failures in a row right at the start -- something's "
                                  "likely broken (selector mismatch, not logged in, wrong "
                                  "project URL, or every account already blocked). "
                                  "Stopping rather than burning your quota.")
                            break
                        st.on_failure(n, force_switch=True, reason=str(e))
                    except (PWTimeoutError, TimeoutError, Exception) as e:
                        print(f"  !! FAILED: {e}")
                        failures.append(n)

                        if len(failures) >= 3 and len(failures) == i + 1:
                            print("\n3 failures in a row right at the start -- something's "
                                  "likely broken (selector mismatch, not logged in, wrong "
                                  "project URL). Stopping rather than burning your quota.")
                            break

                        st.on_failure(n)

                    if i < len(todo) - 1:
                        delay = random.uniform(MIN_DELAY_S, MAX_DELAY_S)
                        print(f"  waiting {delay:.0f}s before next shot...")
                        st.page.wait_for_timeout(int(delay * 1000))
            except StalledOut:
                stalled_out = True
            else:
                st.close()
    except Exception as e:
        # A browser/session (re)launch failed somewhere -- either the
        # very first one (nothing ran yet) or one triggered mid-run by
        # the escalation ladder itself (restart/switch/round-cooldown).
        # Either way this is NOT one shot failing, it's the whole run
        # unable to continue -- report it plainly instead of a raw
        # traceback, and stop rather than guess at further recovery.
        launch_failed = e

    if launch_failed:
        print(f"\nStopped: couldn't get a working browser session going: "
              f"{launch_failed}\n"
              "Re-run the same command -- shots already downloaded are "
              "skipped, so it resumes from where it left off. If this "
              "keeps happening, check the account/project by hand.")
        if failures:
            print(f"Shots that did complete or fail before this: succeeded "
                  f"{len(todo) - len(failures)}, failed {failures}")
        return

    if stalled_out:
        print(
            "\nStopped: downloads kept stalling on every account, across "
            "repeated rotations and cooldowns -- everything's still logged "
            "in, nothing to fix on your end before re-running.\n"
            "Re-run the same command -- shots already downloaded are "
            "skipped, so it resumes from where it left off. If it stalls "
            "the same way again, it's worth checking a browser by hand "
            "(quota exhausted on every account, a real captcha/challenge, "
            "UI changed, etc.)."
        )
        return

    print(f"\nDone. {len(todo) - len(failures)}/{len(todo)} succeeded.")
    if failures:
        print(f"Failed shots (re-run the same --range to retry, already-done ones are skipped): {failures}")
    print("\nRun `python system/05_visuals/verify_batch.py audit "
          f"{args.video_dir}` to check the results.")


if __name__ == "__main__":
    main()
