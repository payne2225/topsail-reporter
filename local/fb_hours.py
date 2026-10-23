"""Season and hours notices from the favorite places' Facebook pages, once,
before the run starts.

The specials check (fb_specials.py) keeps only the day's posts, so a
"closed for the season" or "new hours" post made in the days before the run
would never reach anyone. This reads the pages of the places marked
`pick: true` in reference/restaurants.json, back to --since (default two
weeks), and sends one alert through alert.json either way: the posts that
announce closing, reduced days or hours, or a reopening date, or that there
were none, with each page's newest post date. It writes nothing to the repo.

    python local/fb_hours.py                    # read and alert
    python local/fb_hours.py --dry-run --debug  # read and print only

Same rules as the specials check: home PC only, the Page's own posts only,
never a comment or a name from one, never a cookie.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fb_specials as fb  # noqa: E402

# ---- deciding (pure: tested in tests/test_fb_hours.py) -----------------------------

HOURS_WORDS = re.compile(
    r"\bclos(?:e|ed|es|ing)\b|\bseason\b|\bwinter\b|\bre-?open|\blast (?:day|night|weekend)\b|"
    r"\bnew hours\b|\bhours\b|\bopen (?:only )?(?:on )?(?:mon|tue|wed|thu|fri|sat|sun)", re.I)


def is_hours_news(text: str) -> bool:
    """The keyword stand-in for Claude: a post that may be about being open."""
    return bool(HOURS_WORDS.search(text or ""))


HOURS_PROMPT = (
    "Below, as JSON, are recent Facebook posts by restaurants near Topsail Island, NC. Keep a "
    "post only if it tells someone planning to eat there in the coming weeks whether or when "
    "it is open: closing for the season or the winter, a last day, night or weekend open, "
    "days or hours cut back or changed (like 'open Thursday and Saturday this week' or "
    "'closed Mondays starting...'), a temporary closure, or a reopening date. Drop specials, "
    "menus, events and music, party booking, hiring, history and photos with no such news. "
    "Reply with ONLY a JSON list of the i values to keep, like [0, 2], or [] if none.\n\n")


def hours_posts(posts: list[dict], names: dict[str, str], ask=None) -> list[dict]:
    """The posts about being open or closed. Claude decides; when it cannot
    be reached, the keyword filter does."""
    if not posts:
        return []
    ask = ask or (lambda prompt: fb._claude([{"type": "text", "text": prompt}]))
    listing = [{"i": i, "restaurant": names.get(p["id"], p["id"]), "posted": p["posted"],
                "text": p["text"][:1200]} for i, p in enumerate(posts)]
    said = ask(HOURS_PROMPT + json.dumps(listing, ensure_ascii=False))
    m = re.search(r"\[[\d,\s]*\]", said or "")
    if m:
        try:
            keep = {int(i) for i in json.loads(m.group(0))}
            return [p for i, p in enumerate(posts) if i in keep]
        except ValueError:
            pass
    return [p for p in posts if is_hours_news(p["text"])]


def _list(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def hours_alert(found: list[dict], names: dict[str, str], newest: dict[str, dt.datetime],
                since: dt.date, today: dt.date, failed: list[str]) -> str:
    """One message: what the pages said about being open, or that they said
    nothing, and when each last posted."""
    read = [i for i in names if i not in failed]
    head = f"Topsail hours check, {today:%a %b} {today.day}"
    lines = []
    if found:
        lines.append(f"{head}: posts about closing or hours since {since:%b} {since.day}:")
        for p in found:
            text = p["text"] if len(p["text"]) <= 1500 else p["text"][:1497].rsplit(" ", 1)[0] + "..."
            lines.append(f"- {names.get(p['id'], p['id'])}, {p['posted']}: {text} {p['url']}")
    elif read:
        lines.append(f"{head}: nothing about closing or hours from "
                     f"{_list([names[i] for i in read])} since {since:%b} {since.day}.")
    else:
        lines.append(f"{head}: no page could be read.")
    last = [f"{names[i]} {newest[i]:%b} {newest[i].day}" for i in read if i in newest]
    if last:
        lines.append("Newest posts: " + ", ".join(last) + ".")
    if failed:
        lines.append("Could not read: " + ", ".join(names.get(i, i) for i in failed) + ".")
    return "\n".join(lines)


NOTICE_PROMPT = (
    "This is a photo a restaurant posted on Facebook. If it announces the restaurant's hours, "
    "days open, closing (for the season or otherwise) or reopening, reply with ONLY that "
    "announcement's words as one plain line. Copy the words as written. If it announces none "
    "of that, reply with exactly NONE.")


def wants_notice_reading(text: str, alts: list[str]) -> bool:
    """A photo that may be a notice: Facebook saw text in it, or the post says
    little else and is not a specials or menu post."""
    if re.search(r"special|menu|feature|lunch|dinner", text or "", re.I):
        return False
    return any(fb.BOARD_ALT.search(a or "") for a in alts) or len(text or "") < 40


def read_notice(image: bytes) -> str | None:
    import base64
    kind = "image/png" if image[:4] == b"\x89PNG" else "image/jpeg"
    said = fb._claude([{"type": "image", "source": {"type": "base64", "media_type": kind,
                                                    "data": base64.b64encode(image).decode()}},
                       {"type": "text", "text": NOTICE_PROMPT}])
    return None if not said or said.upper().startswith("NONE") else said


# ---- the check ---------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", help="oldest day to look at (default: two weeks back)")
    ap.add_argument("--ids", help="these places instead of the picks, comma-separated")
    ap.add_argument("--dry-run", action="store_true", help="read and print; send nothing")
    ap.add_argument("--debug", action="store_true", help="print every post read")
    ap.add_argument("--log", help="append everything printed to this file (the scheduled task)")
    args = ap.parse_args(argv)
    if args.log:
        sys.stdout = sys.stderr = open(args.log, "a", encoding="utf-8", buffering=1)
        print(f"==== {dt.datetime.now(fb.ET):%Y-%m-%d %I:%M %p} ET hours check")

    now = dt.datetime.now(fb.ET)
    since = dt.date.fromisoformat(args.since) if args.since else now.date() - dt.timedelta(days=14)
    from fb_session import STATE
    if os.path.normcase(fb.HERE) == os.path.normcase(os.path.join(STATE, "repo")):
        # The job's own clone: read today's list of picks from GitHub's main.
        fb._run("git", "fetch", "-q")
        fb._run("git", "reset", "-q", "--hard", "origin/main")
    with open(os.path.join(fb.HERE, "reference", "restaurants.json"), encoding="utf-8") as f:
        places = [p for p in json.load(f)["places"] if p.get("facebook") and p["status"] != "closed"]
    if args.ids:
        wanted = set(args.ids.split(","))
        places = [p for p in places if p["id"] in wanted]
    else:
        places = [p for p in places if p.get("pick")]
    names = {p["id"]: p["name"] for p in places}
    if not places:
        print("No places to check.")
        return 0
    from playwright.sync_api import sync_playwright
    from fb_session import open_context, signed_in

    posts, newest, failed = [], {}, []
    with sync_playwright() as pw:
        ctx = open_context(pw, headless=True)
        if not signed_in(ctx):
            ctx.close()
            msg = "Topsail hours check: the Facebook sign-in has lapsed. Run local/fb_login.py on the home PC."
            print(msg)
            if not args.dry_run:
                print(fb.send_alert(msg))
            return 2
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for p in places:
            print(f"{p['id']}: {p['facebook']}")
            try:
                # Riverview posts about three times a day: 60 posts is two weeks.
                read = fb.read_page(page, p["facebook"], now, args.debug, want=60, scrolls=45)
            except fb.NotSignedIn:
                failed.append(p["id"])
                print("  signed out")
                break
            except Exception as e:  # noqa: BLE001 - one page failing never stops the check
                failed.append(p["id"])
                print(f"  failed: {type(e).__name__}: {str(e)[:120]}")
                continue
            if read:
                newest[p["id"]] = max(x["when"] for x in read)
            recent = [x for x in read if x["when"].date() >= since]
            for x in recent:
                text = x["text"]
                alts = [alt for _, alt in x["images"]]
                if x["images"] and wants_notice_reading(text, alts):
                    try:
                        notice = read_notice(page.request.get(x["images"][0][0]).body())
                    except Exception:  # noqa: BLE001 - the post keeps its own words
                        notice = None
                    if notice:
                        text = f"{text} {notice}" if text else notice
                        print(f"  read a photo: {notice[:80]!r}")
                if text:
                    posts.append({"id": p["id"], "text": text, "url": x["url"],
                                  "posted": f"{x['when']:%a %b} {x['when'].day}"})
            print(f"  {len(read)} posts read, {len(recent)} since {since}")
            time.sleep(random.uniform(4, 9))
        ctx.close()
    found = hours_posts(posts, names)
    for x in posts:
        print(f"  {'KEEP' if x in found else 'drop'} {x['id']}: {x['text'][:100]!r}")
    text = hours_alert(found, names, newest, since, now.date(), failed)
    print(text)
    if not args.dry_run:
        print(fb.send_alert(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
