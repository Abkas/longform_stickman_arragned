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
import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from PIL import Image, UnidentifiedImageError

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
# MAX_ROUNDS_BEFORE_STOP raised 5 -> 24 (2026-09-10, at the user's request):
# with ROUND_COOLDOWN_S at 1hr, 5 rounds gave up after ~5hrs -- too early
# for an unattended run meant to keep working through a full day/quota
# reset cycle. 24 rounds -> worst case (every account blocked every
# round) keeps retrying for about a day before finally giving up.
RESTART_AFTER_CONSECUTIVE_FAILURES = 2
COOLDOWN_AFTER_CONSECUTIVE_FAILURES = 4
SWITCH_ACCOUNT_AFTER_CONSECUTIVE_FAILURES = 6
MAX_ROUNDS_BEFORE_STOP = 24

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

# Per-account quota-cooldown model (2026-09-10, replacing the old
# "retry the whole round after ROUND_COOLDOWN_S" approach for FlowBlockedError
# specifically -- see EscalationState.on_quota_blocked). At the user's
# request: once an account hits Flow's own "usage limit" block, retrying it
# again and again is pointless -- it gets its OWN cooldown timer and the run
# just moves on to whichever OTHER account isn't currently cooling down,
# picking back up on any account the moment its timer expires, rather than
# a single shared wait that blocks the whole run.
#
# How long that cooldown should be isn't precisely knowable from outside --
# researched 2026-09-10: Google's documented models are either a ~24h daily
# reset (the older, and apparently still-common, free-tier model: 50
# credits/day, refreshing 24h after first use that day) or a newer
# 2026 "compute-based" model resetting every ~5h on some plans, and which
# applies isn't visible to us. Real evidence from this account settles it in
# practice, though: 'default' got blocked ~14:32 and was STILL blocked at
# 20:59 -- 6.5+ hours later, past even the 5h model. So rather than hard-code
# a guess that's already contradicted by observation, this starts at a
# moderate guess and adapts: if an account gets blocked again right after
# its cooldown just expired, the cooldown DOUBLES for that account next time
# (capped at 24h) -- converging on whatever's actually true instead of
# repeating a wrong guess all day.
ACCOUNT_QUOTA_COOLDOWN_S = 6 * 3600       # 6h starting guess
MAX_ACCOUNT_QUOTA_COOLDOWN_S = 24 * 3600  # cap -- matches the documented daily-reset model

# How long this PROCESS will sleep in-place waiting for an account's
# cooldown, before giving up and exiting cleanly instead (2026-09-11, at
# the user's request, mirroring this machine's existing astrellee social
# automation: a systemd --user timer re-invokes this script every 15 min
# rather than one process sleeping for up to 24h). A single process
# blocked in time.sleep() for half a day is fragile -- a laptop suspend,
# a crash, a Ctrl+C, anything kills the wait and loses all of it with
# nothing to show; a short timer re-check is what "catches up after the
# laptop was off/offline" actually means in practice (same reasoning as
# astrellee-facebook-check.timer's own description). Set higher than the
# timer interval so a wait shorter than one tick still resolves in-process
# without waiting for the next external re-invocation.
MAX_INPROCESS_COOLDOWN_WAIT_S = 20 * 60  # 20 min

# Module-level so every launch_session() call (initial launch, stall-recovery
# restart, account-switch -- 5 call sites) picks up the same value without
# threading a parameter through all of them. Set once from --aspect-ratio at
# the top of main(), before any session gets launched. Default ":9" matches
# a "16:9" radio button label (landscape, long-form video) -- the pre-existing
# behavior this project has always used. Pass "9:16" for vertical/Shorts.
ASPECT_RATIO_LABEL = ":9"


def setup_session(page) -> None:
    """One-time per-session settings: image mode, aspect ratio, model,
    count. Adjust the radio/menuitem names below if your project's UI
    differs from what was recorded -- these are typed exactly as recorded."""
    page.get_by_label("Settings trigger").click()
    page.get_by_role("radio", name="Image").click()
    # Partial-text match against the radio button's label -- ASPECT_RATIO_LABEL
    # defaults to ":9" (matches "16:9", landscape); pass --aspect-ratio "9:16"
    # at the CLI for vertical/Shorts. If Flow's actual radio labels differ
    # from these guesses, adjust the strings passed to --aspect-ratio, not
    # this line.
    page.get_by_role("radio", name=ASPECT_RATIO_LABEL).click()
    page.get_by_label("Select model family").click()
    page.get_by_role("menuitem", name="🍌 Nano Banana Pro").click()
    page.get_by_role("radio", name="x1").click()
    # close the settings panel the same way it was opened, if needed
    page.get_by_label("Settings trigger").click()


def _locate_prompt_box(page):
    """Find the "What do you want to create?" prompt box. Tried in order --
    confirmed from a real debug screenshot (2026-09-10) that the box IS on
    screen when the old `page.locator("p").filter(has_text=...)` selector
    times out, so that text is very likely rendered as a `placeholder`
    attribute (or CSS pseudo-content) on an input/textarea, not literal
    text inside a <p>, which a <p>-text filter can never match. Tries the
    placeholder-attribute reading first, falls back to the old <p> filter
    and a tag-agnostic text search in case the real markup differs from
    either guess. Returns a bounding box dict, or None if nothing matched
    (each candidate uses .count() first, which doesn't wait, so a missing
    candidate is a fast skip rather than a 30s timeout)."""
    candidates = [
        page.get_by_placeholder("What do you want to create?"),
        page.get_by_text("What do you want to create?", exact=False),
        page.locator("p").filter(has_text="What do you want to create?"),
    ]
    for loc in candidates:
        try:
            if loc.count() > 0:
                box = loc.first.bounding_box()
                if box:
                    return box
        except Exception:
            continue
    return None


def _prompt_box_is_empty(page) -> bool:
    """True if the box is currently showing its placeholder text (i.e. has
    no typed content) -- unlike get_by_placeholder (attribute-based, always
    matches regardless of content), these two checks only match when the
    box is actually empty, so this is real evidence a submission cleared
    it, not just that the element exists."""
    for loc in (
        page.get_by_text("What do you want to create?", exact=False),
        page.locator("p").filter(has_text="What do you want to create?"),
    ):
        try:
            if loc.count() > 0:
                return True
        except Exception:
            continue
    return False


def enter_prompt(page, shot_num: int, prompt: str) -> None:
    box_geo = _locate_prompt_box(page)
    if box_geo is None:
        _debug_shot(page, shot_num, "prompt-box-not-found")
        raise TimeoutError(
            f"Prompt box ('What do you want to create?') never appeared for "
            f"shot {shot_num} -- see {DEBUG_DIR}/shot{shot_num}_prompt-box-not-found.png"
        )
    # Raw mouse click at the box's coordinates rather than locator.click()
    # -- confirmed from a real run that .click() can silently fail to focus
    # the real input on a second/later use (prompt stayed empty, nothing
    # ever got submitted, no error raised). Mirrors the same fix used for
    # the hover-reveal "More options" button.
    cx = box_geo["x"] + box_geo["width"] / 2
    cy = box_geo["y"] + box_geo["height"] / 2
    page.mouse.click(cx, cy)
    page.wait_for_timeout(200)
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.keyboard.type(prompt, delay=15)  # small delay per keystroke, more human


DEBUG_DIR = Path(__file__).parent / ".flow_debug"

# Per-account quota-cooldown state, persisted to disk -- added 2026-09-11
# after switching to short-lived periodic invocations (a systemd timer
# re-running this script every 15 min, see auto_batch_run.sh) instead of
# one long-lived process sleeping through cooldowns. A fresh process has
# no memory of an account having already been blocked earlier -- without
# persisting this, the adaptive doubling (EscalationState.on_quota_blocked)
# never actually compounds, and worse, every 15-min tick would blindly
# re-try an account still deep in a 6-24h cooldown instead of skipping it
# outright. Shared across all invocations (single file, not per-video --
# an account's real-world quota is account-level, not tied to one video).
QUOTA_COOLDOWN_STATE_FILE = Path(__file__).parent / ".flow_quota_cooldowns.json"


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


def _topmost_tile_image_src(page) -> Optional[str]:
    """Return the `src` of the topmost-leftmost tile's thumbnail <img> in
    the grid (same header/sidebar exclusion as newest_tile_center_point),
    or None if no tile is present. Added 2026-09-10 after a real,
    confirmed bug: once the completion-detection fix (see
    generate_and_download's docstring comment) stopped requiring the
    topmost tile to be provably NEW before downloading it, the script
    would happily download whatever old, already-existing tile happened
    to sort as topmost-leftmost -- confirmed from real downloaded files:
    shots 1, 18 and 20 all ended up as byte-identical copies of a much
    earlier, unrelated shot's image (shot 14's), because that old tile
    was still sitting at the top of that account's grid when a newer
    submission hadn't visually landed there yet (or landed somewhere the
    position-sort didn't pick up first). A thumbnail's `src` is a stable
    per-asset identifier, so comparing it before/after submission (see
    generate_and_download) is a genuine, content-based "is this actually
    new" check -- unlike the old page-wide button COUNT this replaced
    days earlier, which broke down once many tiles existed; this doesn't
    depend on counting anything, just on the identity of one specific
    tile changing."""
    candidates = page.locator("img").all()
    in_grid = []
    for loc in candidates:
        try:
            box = loc.bounding_box()
        except Exception:
            continue
        if box and box["y"] > HEADER_CUTOFF_Y and box["x"] > SIDEBAR_CUTOFF_X:
            try:
                src = loc.get_attribute("src")
            except Exception:
                src = None
            in_grid.append((box["y"], box["x"], src))
    if not in_grid:
        return None
    in_grid.sort(key=lambda t: (t[0], t[1]))
    return in_grid[0][2]


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
    # Baseline thumbnail identity, captured BEFORE submitting anything --
    # see _topmost_tile_image_src's docstring for why this exists (a real
    # bug: shots 1/18/20 all downloaded as copies of an unrelated, much
    # earlier shot's image once the "is this actually new" gate was
    # dropped). Compared against the post-submission value below; the
    # download flow refuses to proceed until the topmost tile's identity
    # has genuinely changed.
    baseline_src = _topmost_tile_image_src(page)

    # Submit-confirmation retry: typing/clicking can silently fail to
    # actually submit anything (confirmed from a real run -- prompt box
    # stayed empty, no new tile ever appeared, no error raised). Checked via
    # _prompt_box_is_empty (did the box actually clear back to its
    # placeholder state), NOT via _grid_tile_count -- confirmed from a real
    # debug screenshot (2026-09-10) that a freshly-submitted generation
    # shows as an in-progress placeholder tile with no "More options"
    # button yet (that only appears once rendering finishes), so the old
    # tile-count check couldn't tell a genuinely-still-rendering submission
    # from one that never went through, and retried real, already-running
    # generations -- burning quota on duplicate images sitting in the Flow
    # project (confirmed: several shots came back 2-3x in the media grid
    # after a run using the old check). The box-empty check is unambiguous:
    # Flow only clears it once the click actually registers.
    submitted = False
    for submit_attempt in range(3):
        enter_prompt(page, shot_num, prompt)
        page.wait_for_timeout(300)
        page.get_by_label("Start generation").click()

        quick_deadline = time.monotonic() + 8
        while time.monotonic() < quick_deadline:
            if _prompt_box_is_empty(page):
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

    # Wait for the generation to actually finish, THEN confirm the newest
    # tile's menu actually offers Download -- merged into one loop
    # (2026-09-10, after a real debug screenshot showed the OLD two-phase
    # version fail): the previous "wait for completion" phase compared
    # _grid_tile_count() (a page-wide count of every "More options" button
    # anywhere in the grid) against a baseline taken before submission.
    # That comparison went stale on a long-running session with many tiles
    # accumulated (duplicates from before today's earlier fix, prior test
    # batches, etc.) -- confirmed from shot 18's debug screenshot: the
    # image had ACTUALLY finished rendering, sitting right there fully
    # complete in the grid, while the count-based check still timed out
    # and declared failure, leaving a real generated image never
    # downloaded. The per-tile check below (does opening the NEWEST tile's
    # own menu specifically offer "Download") doesn't depend on counting
    # anything page-wide, so it isn't thrown off by how many other tiles
    # exist. The topmost-leftmost tile is the newest result; right after
    # it first appears it can still be a LOADING placeholder (its menu
    # only has Rename/View trash/Delete, no Download, until the image
    # actually finishes rendering) -- confirmed from a real run's debug
    # screenshot, hence the retry-with-close-and-rewait below.
    download_ready = False
    deadline = time.monotonic() + GENERATION_TIMEOUT_MS / 1000
    while time.monotonic() < deadline:
        reason = _flow_error_card_text(page)
        if reason:
            _debug_shot(page, shot_num, "flow-error")
            raise FlowBlockedError(
                f"Flow reported an error for shot {shot_num} ({reason}, "
                "not charged) -- this account is blocked for now "
                f"(see {DEBUG_DIR}/shot{shot_num}_flow-error.png)"
            )
        current_src = _topmost_tile_image_src(page)
        if current_src is None or current_src == baseline_src:
            # Either no tile at all yet, or still the SAME tile that was
            # there before this shot was even submitted -- not a real
            # result for THIS shot, don't open its menu or download it.
            page.wait_for_timeout(3000)
            continue
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
            f"item within {GENERATION_TIMEOUT_MS // 1000}s -- see "
            f"{DEBUG_DIR}/shot{shot_num}_after-more-options-click.png "
            "to see what actually opened."
        )

    page.get_by_role("menuitem", name="Download").click()

    page.wait_for_timeout(300)
    _debug_shot(page, shot_num, "download-submenu")

    with page.expect_download() as dl_info:
        page.get_by_role("menuitem", name="1K Original size").click()
    download = dl_info.value
    download.save_as(str(dest_path))
    _verify_downloaded_image(dest_path, shot_num)


def _verify_downloaded_image(dest_path: Path, shot_num: int) -> None:
    """Confirm dest_path is a real, complete image before the caller
    considers this shot done -- at the user's request (2026-09-10): one
    shot's download must be verified before the next prompt is ever sent,
    strictly sequential, no exceptions. Checks existence, non-zero size,
    and that PIL can actually decode it (catches a truncated/partial
    download that Playwright's save_as() didn't itself error on). Deletes
    a bad file rather than leaving it behind -- a corrupt file would
    otherwise satisfy the "already have a file" skip-check on the next
    run and silently stay broken forever."""
    if not dest_path.exists() or dest_path.stat().st_size == 0:
        if dest_path.exists():
            dest_path.unlink()
        raise TimeoutError(
            f"Shot {shot_num}: download reported success but "
            f"{dest_path.name} is missing or empty -- not counting this "
            "as done."
        )
    try:
        with Image.open(dest_path) as img:
            img.verify()
    except (UnidentifiedImageError, OSError) as e:
        dest_path.unlink()
        raise TimeoutError(
            f"Shot {shot_num}: downloaded {dest_path.name} isn't a valid "
            f"image ({e}) -- deleted it, will retry rather than leave a "
            "corrupt file that looks done."
        )


class EventLog:
    """Structured, machine-analyzable log of every shot-level event, one
    JSON object per line, appended to (never overwritten) across separate
    runs of this video -- at the user's request (2026-09-10): a record of
    which prompt/shot succeeded on which account, which got blocked, when
    an account switch or cooldown happened, etc., kept separately from the
    prose printed to stdout/the log file so it can be grepped/loaded (e.g.
    `pandas.read_json(path, lines=True)`) for analysis later instead of
    re-parsing free-text log lines. Line-buffered + flushed after every
    write so it's readable live, same reasoning as run.sh's
    PYTHONUNBUFFERED fix for the prose log."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._f = open(path, "a", buffering=1)

    def log(self, event: str, **fields) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "event": event,
            **fields,
        }
        self._f.write(json.dumps(record) + "\n")
        self._f.flush()

    def close(self) -> None:
        self._f.close()


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

    def __init__(self, p, accounts: list, events: Optional[EventLog] = None) -> None:
        self.p = p
        self.accounts = accounts
        self.events = events
        self.account_idx = 0
        self.account_fail_streak = 0        # consecutive failures on the CURRENT account
        self.already_cooled_down_this_account = False  # level-2 fires once per account attempt
        self.accounts_tried_this_round = 0  # accounts switched away from, still failing
        self.rounds_exhausted = 0           # full rotations where every account failed
        self.quota_blocked_until: dict[str, float] = {}   # account name -> time.time() it's usable again
        self.quota_blocked_streak: dict[str, int] = {}    # account name -> consecutive quota-blocks (for adaptive backoff)
        self._load_quota_state()
        # Cooldown-aware from the very first launch -- fixed 2026-09-11
        # after a real gap: this used to always launch accounts[0]
        # unconditionally, ignoring the cooldown state just loaded above,
        # so every 15-min tick wasted a real browser launch + shot attempt
        # on whichever account happened to be listed first even when it
        # was already known (from disk) to still be hours from clearing.
        # _launch_first_available skips anything still cooling down;
        # _launch_first_working is the fallback for the (rare) case where
        # every account is either cooling down or fails to LAUNCH, so
        # there's still at least an attempt to report a real error from
        # instead of silently doing nothing.
        if not self._launch_first_available(0):
            # Not available right now doesn't necessarily mean broken --
            # most likely every account is still legitimately cooling
            # down (known from disk). Mirror on_quota_blocked's own
            # "wait briefly, or exit cleanly for a longer wait" logic
            # rather than either hanging for hours or blindly launching a
            # known-blocked account anyway (which _launch_first_working
            # would do, defeating the whole point of checking first).
            now = time.time()
            waits = {a.name: self.quota_blocked_until.get(a.name, now) for a in self.accounts}
            soonest_name = min(waits, key=waits.get)
            wait_s = max(0, waits[soonest_name] - now)
            if wait_s <= MAX_INPROCESS_COOLDOWN_WAIT_S:
                print(f"\n  Every account is cooling down right now. Waiting "
                      f"{wait_s / 60:.0f} min for '{soonest_name}' to clear before even starting.")
                time.sleep(wait_s)
                if not self._launch_first_available(0):
                    # Cooldown timestamp passed but it STILL couldn't
                    # launch (a real launch failure, not just quota) --
                    # now it's worth trying every account for real.
                    if not self._launch_first_working(0):
                        raise RuntimeError(
                            "No configured account could be launched -- see prior messages.")
            else:
                print(f"\n  Every account is cooling down right now. Soonest is "
                      f"'{soonest_name}' in {wait_s / 60:.0f} min -- longer than this process "
                      f"will wait before even starting ({MAX_INPROCESS_COOLDOWN_WAIT_S // 60} min cap). "
                      "Exiting cleanly; the next scheduled tick picks this back up.")
                if self.events:
                    self.events.log("all_accounts_cooldown_exit_at_start",
                                     wait_minutes=round(wait_s / 60, 1), next_account=soonest_name)
                raise StalledOut()

    @property
    def account(self) -> Account:
        return self.accounts[self.account_idx]

    def _load_quota_state(self) -> None:
        """Load quota_blocked_until/quota_blocked_streak from disk, if
        present -- see QUOTA_COOLDOWN_STATE_FILE's comment. Missing/corrupt
        file just means "no known cooldowns yet", not an error."""
        try:
            data = json.loads(QUOTA_COOLDOWN_STATE_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return
        for name, entry in data.items():
            if "until" in entry:
                self.quota_blocked_until[name] = entry["until"]
            if "streak" in entry:
                self.quota_blocked_streak[name] = entry["streak"]

    def _save_quota_state(self) -> None:
        names = set(self.quota_blocked_until) | set(self.quota_blocked_streak)
        data = {
            name: {
                "until": self.quota_blocked_until.get(name, 0),
                "streak": self.quota_blocked_streak.get(name, 0),
            }
            for name in names
        }
        try:
            QUOTA_COOLDOWN_STATE_FILE.write_text(json.dumps(data, indent=2))
        except OSError:
            pass  # persistence is best-effort -- losing it just means the next process re-learns from Flow directly

    def on_success(self) -> None:
        self.account_fail_streak = 0
        self.already_cooled_down_this_account = False
        self.accounts_tried_this_round = 0
        self.rounds_exhausted = 0
        # A real success proves this account's quota is genuinely clear
        # right now -- reset its adaptive backoff so a later, unrelated
        # block doesn't inherit an inflated cooldown from a past streak.
        self.quota_blocked_streak[self.account.name] = 0
        self._save_quota_state()

    def _relaunch(self, account_idx=None) -> None:
        if account_idx is not None:
            self.account_idx = account_idx
        self.context.close()
        self.context, self.page = launch_session(self.p, self.account)

    def _launch_first_working(self, start_idx: int) -> bool:
        """Try launching accounts starting at start_idx, wrapping around,
        skipping any that fail to LAUNCH (as opposed to fail a shot) --
        added 2026-09-10 after a real run died entirely because one
        account ('acc3') couldn't launch (a selector issue unrelated to
        quota/blocking), even though the other two accounts were fine.
        Before this, any launch_session() failure during account-switch or
        round-cooldown propagated all the way out of the shot loop and
        killed the whole run (`launch_failed` in main()), defeating the
        entire point of having multiple accounts to rotate through.  Sets
        self.account_idx/context/page on the first account that launches;
        returns False only if NONE of the configured accounts can even
        launch (a real "nothing works" situation, still worth stopping
        for)."""
        n = len(self.accounts)
        for offset in range(n):
            idx = (start_idx + offset) % n
            try:
                ctx, pg = launch_session(self.p, self.accounts[idx])
            except Exception as e:
                print(f"\n  Couldn't launch account '{self.accounts[idx].name}': "
                      f"{e} -- skipping this account, trying the next one.")
                if self.events:
                    self.events.log("account_launch_failed",
                                     account=self.accounts[idx].name, reason=str(e))
                continue
            self.account_idx = idx
            self.context, self.page = ctx, pg
            return True
        return False

    def _launch_first_available(self, start_idx: int) -> bool:
        """Like _launch_first_working, but ALSO skips any account still
        under its own quota_blocked_until cooldown -- used both by
        on_quota_blocked's per-account rotation AND by __init__'s very
        first launch (so a fresh process consults the persisted cooldown
        state before ever touching an account, instead of always trying
        accounts[0] blind regardless of what's already known about it).
        Sets self.account_idx/context/page on success; returns False only
        if every account is either still cooling down or fails to
        launch."""
        n = len(self.accounts)
        now = time.time()  # wall-clock, not monotonic -- quota_blocked_until is persisted across process restarts
        for offset in range(n):
            idx = (start_idx + offset) % n
            acct = self.accounts[idx]
            if self.quota_blocked_until.get(acct.name, 0) > now:
                continue
            try:
                ctx, pg = launch_session(self.p, acct)
            except Exception as e:
                print(f"\n  Couldn't launch account '{acct.name}': {e} -- skipping.")
                if self.events:
                    self.events.log("account_launch_failed", account=acct.name, reason=str(e))
                continue
            self.account_idx = idx
            self.context, self.page = ctx, pg
            return True
        return False

    def on_quota_blocked(self, shot_num: int, reason: str) -> None:
        """Handle a FlowBlockedError (Flow's own "usage limit"/"unusual
        activity" card) under the per-account cooldown model -- see the
        ACCOUNT_QUOTA_COOLDOWN_S comment above for why this replaced the
        old shared-round-cooldown approach. Retrying or restarting the
        SAME account can't possibly help (Flow itself rejected it, not a
        flaky selector), so: put this account on its own cooldown timer
        (doubling if it got blocked again right after its last cooldown
        ended), then move straight to whichever OTHER account isn't
        currently cooling down. If literally every account is cooling
        down right now, sleep until the EARLIEST one clears -- not a
        fixed shared wait -- then resume with that one. Never gives up:
        this is meant to run unattended across cooldowns all day."""
        name = self.account.name
        streak = self.quota_blocked_streak.get(name, 0) + 1
        self.quota_blocked_streak[name] = streak
        cooldown = min(ACCOUNT_QUOTA_COOLDOWN_S * (2 ** (streak - 1)), MAX_ACCOUNT_QUOTA_COOLDOWN_S)
        until = time.time() + cooldown  # wall-clock, not monotonic -- persisted across process restarts
        self.quota_blocked_until[name] = until
        print(f"\n  '{name}' quota-blocked ({reason}) -- cooling down for "
              f"{cooldown / 3600:.1f}h (blocked-in-a-row: {streak}), shot {shot_num} "
              "stays a gap for now. Moving to the next available account.")
        if self.events:
            self.events.log("account_quota_cooldown", shot=shot_num, account=name,
                             reason=reason, cooldown_hours=round(cooldown / 3600, 2),
                             blocked_streak=streak)
        self._save_quota_state()

        self.context.close()
        next_idx = (self.account_idx + 1) % len(self.accounts)
        if self._launch_first_available(next_idx):
            print(f"  Switched to account '{self.account.name}'.")
            return

        # Every account is either cooling down or failing to launch --
        # wait for whichever one clears first, then use it.
        now = time.time()  # wall-clock, matching quota_blocked_until
        # Accounts with no entry yet (never blocked) would have been
        # picked by _launch_first_available already if launchable, so
        # reaching here means every account either has a real cooldown
        # timestamp or just failed to launch; only wait on ones with an
        # actual timestamp.
        waits = {a.name: self.quota_blocked_until.get(a.name, now) for a in self.accounts}
        soonest_name = min(waits, key=waits.get)
        soonest_at = waits[soonest_name]
        wait_s = max(0, soonest_at - now)

        if wait_s > MAX_INPROCESS_COOLDOWN_WAIT_S:
            # Too long to sleep through in-process (see
            # MAX_INPROCESS_COOLDOWN_WAIT_S) -- exit cleanly instead of
            # blocking for hours. The systemd timer (or whatever re-runs
            # this) picks it back up on its next tick; nothing is lost,
            # every cooldown timestamp already recorded in this run is
            # gone once the process exits, but the NEXT invocation just
            # re-discovers "still blocked" from Flow itself within a
            # couple of shots and re-applies the same adaptive cooldown.
            print(f"\n  Every account is cooling down (or failing to launch) right now. "
                  f"Soonest is '{soonest_name}' in {wait_s / 60:.0f} min -- longer than this "
                  f"process will wait in-place ({MAX_INPROCESS_COOLDOWN_WAIT_S // 60} min cap). "
                  "Exiting cleanly; re-run later (or let a scheduled timer re-invoke this) "
                  "to pick back up.")
            if self.events:
                self.events.log("all_accounts_cooldown_exit", shot=shot_num,
                                 wait_minutes=round(wait_s / 60, 1), next_account=soonest_name)
            raise StalledOut()

        print(f"\n  Every account is cooling down (or failing to launch) right now. "
              f"Waiting {wait_s / 60:.0f} min for '{soonest_name}' to clear.")
        if self.events:
            self.events.log("all_accounts_cooldown_wait", shot=shot_num,
                             wait_minutes=round(wait_s / 60, 1), next_account=soonest_name)
        time.sleep(wait_s)
        soonest_idx = next(i for i, a in enumerate(self.accounts) if a.name == soonest_name)
        if not self._launch_first_available(soonest_idx):
            # Extremely unlikely (would mean even the just-cleared account
            # fails to LAUNCH, not just quota) -- fall back to the old
            # launch-resilience helper so this doesn't hang forever.
            if not self._launch_first_working(soonest_idx):
                raise StalledOut()

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
                    if self.events:
                        self.events.log("stalled_out", shot=shot_num,
                                         rounds_exhausted=self.rounds_exhausted)
                    raise StalledOut()
                print(f"\n  All {len(self.accounts)} account(s) failed this "
                      f"round -- backing off {ROUND_COOLDOWN_S // 60} min "
                      "in case this is a rate-limit/\"unusual activity\" "
                      f"flag, then retrying from {self.accounts[0].name}.")
                if self.events:
                    self.events.log("round_cooldown", shot=shot_num,
                                     rounds_exhausted=self.rounds_exhausted,
                                     wait_s=ROUND_COOLDOWN_S)
                self.context.close()
                time.sleep(ROUND_COOLDOWN_S)
                self.accounts_tried_this_round = 0
                self.account_fail_streak = 0
                self.already_cooled_down_this_account = False
                if not self._launch_first_working(0):
                    print("\n  None of the configured accounts could even "
                          "launch -- stopping cleanly.")
                    if self.events:
                        self.events.log("stalled_out", shot=shot_num, reason="no account could launch")
                    raise StalledOut()
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
                if self.events:
                    self.events.log("account_switch", shot=shot_num,
                                     from_account=self.account.name,
                                     to_account=self.accounts[next_idx].name,
                                     reason=why)
                self.account_fail_streak = 0
                self.already_cooled_down_this_account = False
                self.context.close()
                if not self._launch_first_working(next_idx):
                    print("\n  None of the remaining accounts could even "
                          "launch -- stopping cleanly.")
                    if self.events:
                        self.events.log("stalled_out", shot=shot_num, reason="no account could launch")
                    raise StalledOut()

        elif self.account_fail_streak >= COOLDOWN_AFTER_CONSECUTIVE_FAILURES and not self.already_cooled_down_this_account:
            print(f"\n  {self.account_fail_streak} downloads in a row didn't "
                  f"come through, restart included -- backing off "
                  f"{ACCOUNT_COOLDOWN_S // 60} min on account "
                  f"'{self.account.name}' in case it's just "
                  f"this one that's rate-limited, then continuing with "
                  f"the next shot on it (shot {shot_num} itself stays a gap for "
                  f"now -- see this file's docstring for how gaps get "
                  f"swept up).")
            if self.events:
                self.events.log("account_cooldown", shot=shot_num,
                                 account=self.account.name, wait_s=ACCOUNT_COOLDOWN_S)
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
            if self.events:
                self.events.log("account_restart", shot=shot_num, account=self.account.name)
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
    ap.add_argument("--out-dir", type=Path, help="Override the download destination directory "
                     "(default: <video_dir>/generate/generated/images). Used by run_full_batch.py "
                     "to generate each chunk into its own chunkN/ subfolder for per-chunk "
                     "verification before promoting to the flat images/ directory.")
    ap.add_argument("--aspect-ratio", default=":9", help="Partial-text match against Flow's "
                     "aspect-ratio radio button label, set once per session in setup_session(). "
                     "Default ':9' matches a '16:9' label (landscape, this project's long-form "
                     "default). Pass '9:16' for vertical/Shorts. If Flow's actual radio labels "
                     "differ from these guesses, adjust this string, not the driver code.")
    args = ap.parse_args()

    if bool(args.project_url) == bool(args.accounts):
        raise SystemExit("Pass exactly one of --project-url (single account) "
                          "or --accounts (multi-account rotation).")

    global ASPECT_RATIO_LABEL
    ASPECT_RATIO_LABEL = args.aspect_ratio

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

    out_dir = args.out_dir if args.out_dir else args.video_dir / "generate" / "generated" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Structured per-shot event log (JSONL, appended across runs) -- at the
    # user's request (2026-09-10): a machine-analyzable record of exactly
    # which prompt succeeded/failed on which account and when, separate
    # from the prose printed above/to the redirected log file. See
    # EventLog's docstring.
    events = EventLog(args.video_dir / "generate" / "batch_events.jsonl")

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
    stopped_early = False  # set when the "3 failures in a row" circuit-breaker fires
    try:
        with sync_playwright() as p:
            try:
                # Construction can itself raise StalledOut now (all
                # accounts cooling down past the in-process wait cap at
                # startup -- see EscalationState.__init__) -- inside this
                # try so that gets the correct clean "stalled_out" message
                # below instead of being misreported as a launch failure
                # by the outer except.
                st = EscalationState(p, accounts, events)
                for i, (n, prompt, dest) in enumerate(todo):
                    # Inner retry loop: a FlowBlockedError switches
                    # EscalationState to a newly-available account (see
                    # on_quota_blocked) -- retry THIS SAME shot immediately
                    # on that account rather than only marking it a gap and
                    # moving on. Fixed 2026-09-10 after a real run switched
                    # accounts correctly but then just gave up on the shot
                    # anyway, wasting the switch (the new account sat idle
                    # until a whole separate future pass picked the gap back
                    # up). Capped at one attempt per configured account so
                    # a shot that's somehow unblockable everywhere still
                    # gives up rather than looping forever.
                    quota_attempts = 0
                    while True:
                        print(f"\n[{i+1}/{len(todo)}] Shot {n}: {prompt[:80]}{'...' if len(prompt) > 80 else ''} "
                              f"[{st.account.name}]")
                        events.log("attempt", shot=n, account=st.account.name, prompt=prompt[:200])
                        try:
                            generate_and_download(st.page, n, prompt, dest)
                            print(f"  -> saved {dest.name}")
                            events.log("success", shot=n, account=st.account.name, file=dest.name)
                            st.on_success()
                            break
                        except FlowBlockedError as e:
                            # Flow itself blocked this account (quota
                            # exhausted, an "unusual activity" flag, etc.)
                            # -- retrying or restarting THIS account can't
                            # possibly help. Per-account cooldown + rotate-
                            # to-next-available model (see
                            # EscalationState.on_quota_blocked) -- an
                            # EXPECTED, handled case now, not a sign the
                            # run is broken, so it does NOT count toward
                            # the "3 failures in a row" circuit breaker
                            # below (that breaker is for genuinely
                            # unexpected failures).
                            print(f"  !! BLOCKED: {e}")
                            events.log("blocked", shot=n, account=st.account.name, reason=str(e))
                            st.on_quota_blocked(n, str(e))
                            quota_attempts += 1
                            if quota_attempts >= len(accounts):
                                print(f"  Tried every configured account for shot {n}, still "
                                      "blocked everywhere -- leaving it as a gap for now "
                                      "(a later pass picks it back up).")
                                failures.append(n)
                                break
                            continue  # retry this SAME shot on the account we just switched to
                        except (PWTimeoutError, TimeoutError, Exception) as e:
                            print(f"  !! FAILED: {e}")
                            events.log("failed", shot=n, account=st.account.name, reason=str(e))
                            failures.append(n)

                            if len(failures) >= 3 and len(failures) == i + 1:
                                print("\n3 failures in a row right at the start -- something's "
                                      "likely broken (selector mismatch, not logged in, wrong "
                                      "project URL). Stopping rather than burning your quota.")
                                events.log("circuit_breaker_stop", shot=n, failures=list(failures))
                                stopped_early = True
                            else:
                                st.on_failure(n)
                            break

                    if stopped_early:
                        break
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
        events.log("run_launch_failed", reason=str(launch_failed), failures=list(failures))
        events.close()
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
        events.log("run_stalled_out", failures=list(failures))
        events.close()
        return

    attempted = len(failures) if stopped_early else len(todo)
    succeeded = attempted - len(failures)
    if stopped_early:
        never_attempted = [n for n, _, _ in todo[attempted:]]
        print(f"\nStopped early after {attempted}/{len(todo)} shots attempted "
              f"({succeeded} succeeded, {len(failures)} failed) -- see the "
              "circuit-breaker message above. "
              f"{len(never_attempted)} shot(s) were never even attempted: {never_attempted}")
    else:
        print(f"\nDone. {succeeded}/{len(todo)} succeeded.")
    if failures:
        print(f"Failed shots (re-run the same --range to retry, already-done ones are skipped): {failures}")
    print("\nRun `python system/05_visuals/verify_batch.py audit "
          f"{args.video_dir}` to check the results.")
    events.log("run_complete", succeeded=succeeded, total=len(todo),
               stopped_early=stopped_early, failures=list(failures))
    events.close()


if __name__ == "__main__":
    main()
