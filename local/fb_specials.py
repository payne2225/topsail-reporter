"""The day's restaurant specials from Facebook, for the Island Edition.

Runs on the home PC only, never in the cloud routine, signed in to Facebook
in a browser profile outside the repo (see fb_session.py; sign in once with
`python local/fb_login.py`). A check:

    python local/fb_specials.py            # read, write, render, test, push, alert
    python local/fb_specials.py --dry-run  # read and print; write nothing
    python local/fb_specials.py --debug --ids surfdog,riverview

reads each restaurant's own Facebook page (`facebook` in
reference/restaurants.json), keeps that page's posts from today (Eastern)
that read like food or hours news, and merges them into
specials/<date>.json, which render.py shows on the day's Island Edition.
Only a restaurant's own post text is kept: never a comment, never a name
from one, never a cookie. The alert goes to the one person set up in
%LOCALAPPDATA%\\topsail-reporter\\alert.json (outside the repo).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ET = ZoneInfo("America/New_York")
SITE_BASE = "https://payne2225.github.io/topsail-reporter"

# ---- reading a post (pure: tested in tests/test_fb_specials.py) -------------

MONTHS = {m: i for i, m in enumerate(
    ("january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"), 1)}
DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_CLOCK = r"(\d{1,2}):(\d{2})\s*([AP]M)"


def _at(day: dt.date, h: str, m: str, ampm: str) -> dt.datetime:
    hour = int(h) % 12 + (12 if ampm.upper() == "PM" else 0)
    return dt.datetime(day.year, day.month, day.day, hour, int(m), tzinfo=ET)


def posted_at(label: str, now: dt.datetime) -> dt.datetime | None:
    """When a post went up, from Facebook's timestamp text, or None.

    Handles "Just now", "5m", "3 hrs", "Yesterday at 4:12 PM", "Thursday at
    3:05 PM", "October 22 at 3:05 PM", "October 22" and the hover tooltip's
    "Thursday, October 22, 2026 at 3:05 PM". `now` is Eastern."""
    s = " ".join((label or "").replace(" ", " ").replace("\xa0", " ").split()).strip()
    low = s.lower()
    if not low:
        return None
    if low in ("just now", "now"):
        return now
    m = re.fullmatch(r"(\d+)\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days|w|wk|wks|week|weeks)(?: ago)?", low)
    if m:
        n, unit = int(m.group(1)), m.group(2)[0]
        delta = {"m": dt.timedelta(minutes=n), "h": dt.timedelta(hours=n),
                 "d": dt.timedelta(days=n), "w": dt.timedelta(weeks=n)}[unit]
        return now - delta
    m = re.fullmatch(r"(today|yesterday) at " + _CLOCK, s, re.I)
    if m:
        day = now.date() - dt.timedelta(days=1 if m.group(1).lower() == "yesterday" else 0)
        return _at(day, *m.groups()[1:])
    m = re.fullmatch(r"(?:(?:%s),? )?(%s) (\d{1,2})(?:, (\d{4}))?(?: at %s)?"
                     % ("|".join(DAYS), "|".join(MONTHS), _CLOCK), s, re.I)
    if m:
        month, mday, year = MONTHS[m.group(1).lower()], int(m.group(2)), m.group(3)
        day = dt.date(int(year) if year else now.year, month, mday)
        if not year and day > now.date():         # "December 30" read in January
            day = dt.date(day.year - 1, month, mday)
        if m.group(4):
            return _at(day, *m.groups()[3:])
        return dt.datetime(day.year, day.month, day.day, tzinfo=ET)
    m = re.fullmatch(r"(%s) at %s" % ("|".join(DAYS), _CLOCK), s, re.I)
    if m:
        back = (now.weekday() - DAYS.index(m.group(1).lower())) % 7 or 7
        return _at(now.date() - dt.timedelta(days=back), *m.groups()[1:])
    return None


FOOD = re.compile(
    r"special|today|tonight|lunch|dinner|brunch|breakfast|menu|soup|chowder|catch|fresh|"
    r"feature|happy hour|\$\s?\d|plate|platter|basket|steam|oyster|shrimp|fish|flounder|"
    r"grouper|tuna|crab|lobster|scallop|taco|burger|pizza|wing|bbq|barbecue|brisket|"
    r"prime rib|ribs|steak|pasta|sandwich|dessert|cake|pie|beer|on tap|cocktail|margarita|"
    r"open|closed|closing|hours|kitchen",
    re.I)
NOT_FOOD = re.compile(r"\b(?:now hiring|we(?:'| a)re hiring|hiring|apply (?:now|today|in person)|job)\b", re.I)


def is_food_news(text: str) -> bool:
    """A post worth putting under Specials today: food, a deal or an hours
    change, and not a hiring notice."""
    return bool(FOOD.search(text)) and not NOT_FOOD.search(text)


def alt_text(alts: list[str]) -> str:
    """Facebook's own description of a posted photo, when it read words off
    it ("May be an image of text that says 'FRIDAY SPECIAL ...'"): a
    whiteboard of specials posted as a photo still comes through."""
    said = []
    for a in alts:
        m = re.search(r"that says ['‘“\"](.+?)['’”\"]?$", a or "", re.S)
        if m:
            said.append(" ".join(m.group(1).split()))
    return " ".join(said)


def clean_url(href: str) -> str:
    """A post permalink without Facebook's tracking parameters."""
    href = href.split("#")[0]
    base, _, query = href.partition("?")
    keep = [q for q in query.split("&") if q.split("=")[0] in ("story_fbid", "id", "fbid", "set", "v")]
    return base + ("?" + "&".join(keep) if keep else "")


def merge(old: dict | None, day: str, found: list[dict], checked: str,
          failed: list[str]) -> tuple[dict, list[dict]]:
    """Fold one check's posts into the day's file. Returns the file and the
    posts that are new since the last check (what the alert names)."""
    data = old if old and old.get("date") == day else {"date": day, "checked_et": [], "posts": []}
    have = {p["url"]: p for p in data["posts"]}
    new = []
    for post in found:
        if post["url"] not in have:
            new.append(post)
        have[post["url"]] = post            # an edited post keeps its newest text
    data["posts"] = sorted(have.values(), key=lambda p: (p.get("sort", ""), p["id"]))
    data["checked_et"] = data.get("checked_et", []) + [checked]
    data["failed"] = failed
    return data, new


def alert_text(new: list[dict], names: dict[str, str], checked: str, day: str,
               failed: list[str]) -> str:
    lines = [f"Topsail specials, {checked} ET check:"]
    for p in new:
        text = p["text"] if len(p["text"]) <= 280 else p["text"][:277].rsplit(" ", 1)[0] + "..."
        lines.append(f"- {names.get(p['id'], p['id'])}: {text}")
    if failed:
        lines.append("Could not read: " + ", ".join(names.get(i, i) for i in failed) + ".")
    lines.append(f"{SITE_BASE}/{day}/island/")
    return "\n".join(lines)


# ---- reading Facebook ------------------------------------------------------------

class NotSignedIn(RuntimeError):
    pass


POST_LINKS = ("a[href*='/posts/'], a[href*='/photos/'], a[href*='story_fbid'], "
              "a[href*='/videos/'], a[href*='/reel/'], a[href*='/permalink/'], a[href*='/photo/']")


def read_page(page, url: str, now: dt.datetime, debug: bool = False) -> list[dict]:
    """The newest posts on one Page: [{text, when, url}] (when may be None)."""
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(4000)
    if "/login" in page.url or page.locator("input[name=pass]").count():
        raise NotSignedIn(url)
    for _ in range(3):
        page.mouse.wheel(0, 1800)
        page.wait_for_timeout(1500 + random.randint(0, 800))
    units = page.locator("div[aria-posinset]")
    if not units.count():
        units = page.locator("div[role=article]:not([role=article] [role=article])")
    out = []
    for i in range(min(units.count(), 6)):
        unit = units.nth(i)
        try:
            for more in unit.get_by_role("button", name="See more").all()[:2]:
                more.click(timeout=2000)
                page.wait_for_timeout(300)
        except Exception:  # noqa: BLE001 - a post that will not expand keeps its short text
            pass
        msg = unit.locator("[data-ad-preview=message], [data-ad-comet-preview=message]").first
        text = msg.inner_text(timeout=2000) if msg.count() else ""
        alts = unit.locator("img[alt]").evaluate_all("els => els.map(e => e.alt)")
        photo = alt_text(alts)
        text = " ".join((text + (" " + photo if photo and photo not in text else "")).split())
        when, link = None, None
        for a in unit.locator(POST_LINKS).all()[:5]:
            href = a.get_attribute("href") or ""
            label = (a.get_attribute("aria-label") or a.inner_text(timeout=1000) or "").strip()
            when = posted_at(label, now)
            if not when:
                try:
                    a.hover(timeout=2000)
                    tip = page.locator("[role=tooltip]").last
                    tip.wait_for(timeout=2500)
                    when = posted_at(tip.inner_text(), now)
                except Exception:  # noqa: BLE001
                    pass
            if when:
                link = clean_url(href if href.startswith("http") else "https://www.facebook.com" + href)
                break
        if debug:
            print(f"    [{i}] when={when} link={link} text={text[:90]!r}")
        if text and when and link:
            out.append({"text": text, "when": when, "url": link})
    return out


# ---- the check ---------------------------------------------------------------------

def _run(*cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, check=check)


def send_alert(text: str) -> str:
    """Send to the one channel in alert.json; until one is set, only log."""
    from fb_session import STATE
    path = os.path.join(STATE, "alert.json")
    if not os.path.exists(path):
        return "no alert channel set (alert.json); logged only"
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if cfg.get("ntfy"):
        req = urllib.request.Request(f"https://ntfy.sh/{cfg['ntfy']}", data=text.encode("utf-8"),
                                     headers={"Title": "Topsail specials"})
    elif cfg.get("discord_webhook"):
        req = urllib.request.Request(cfg["discord_webhook"],
                                     data=json.dumps({"content": text[:1900]}).encode("utf-8"),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "topsail-reporter"})
    else:
        return "alert.json names no channel; logged only"
    urllib.request.urlopen(req, timeout=20).read()
    return "alert sent"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", help="the day to check (default: today, Eastern)")
    ap.add_argument("--ids", help="only these places, comma-separated")
    ap.add_argument("--dry-run", action="store_true", help="read and print; write nothing")
    ap.add_argument("--debug", action="store_true", help="print every post read")
    ap.add_argument("--no-push", action="store_true", help="write and render, but do not push or alert")
    args = ap.parse_args(argv)

    now = dt.datetime.now(ET)
    day = args.date or now.date().isoformat()
    checked = now.strftime("%I:%M %p").lstrip("0")
    with open(os.path.join(HERE, "reference", "restaurants.json"), encoding="utf-8") as f:
        places = [p for p in json.load(f)["places"] if p.get("facebook") and p["status"] != "closed"]
    if args.ids:
        wanted = set(args.ids.split(","))
        places = [p for p in places if p["id"] in wanted]
    names = {p["id"]: p["name"] for p in places}
    live = not (args.dry_run or args.no_push)
    from fb_session import STATE
    if live and os.path.normcase(HERE) != os.path.normcase(os.path.join(STATE, "repo")):
        # A live check resets its checkout to GitHub's main, so it only ever
        # runs in the job's own clone, never in a working copy.
        print(f"A live check runs from {os.path.join(STATE, 'repo')}; use --no-push or --dry-run here.")
        return 2
    from playwright.sync_api import sync_playwright
    from fb_session import open_context, signed_in

    found, failed = [], []
    with sync_playwright() as pw:
        ctx = open_context(pw, headless=True)
        if not signed_in(ctx):
            ctx.close()
            msg = "Topsail specials: the Facebook sign-in has lapsed. Run local/fb_login.py on the home PC."
            print(msg)
            if live:
                print(send_alert(msg))
            return 2
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for p in places:
            print(f"{p['id']}: {p['facebook']}")
            try:
                posts = read_page(page, p["facebook"], now, args.debug)
            except NotSignedIn:
                failed.append(p["id"])
                print("  signed out")
                break
            except Exception as e:  # noqa: BLE001 - one page failing never stops the check
                failed.append(p["id"])
                print(f"  failed: {type(e).__name__}: {str(e)[:120]}")
                continue
            for post in posts:
                if post["when"].date().isoformat() == day and is_food_news(post["text"]):
                    found.append({"id": p["id"], "posted_et": post["when"].strftime("%I:%M %p").lstrip("0"),
                                  "sort": post["when"].strftime("%H:%M"),
                                  "text": post["text"], "url": post["url"]})
            print(f"  {len(posts)} posts read, {sum(1 for x in found if x['id'] == p['id'])} kept")
            time.sleep(random.uniform(4, 9))
        ctx.close()

    path = os.path.join(HERE, "specials", f"{day}.json")
    for attempt in range(2):
        if live:
            # The job's own clone: start from what is on GitHub right now, so
            # the push never meets a conflict (the morning routine pushes too).
            _run("git", "fetch", "-q")
            _run("git", "reset", "-q", "--hard", "origin/main")
        old = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old = json.load(f)
        data, new = merge(old, day, found, checked, failed)
        text = alert_text(new, names, checked, day, failed)
        if attempt == 0:
            print(text if new or failed else f"Nothing new at {checked}.")
        if args.dry_run:
            return 0
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")
        _run(sys.executable, "render.py")
        tests = _run(sys.executable, "-m", "pytest", "-q", check=False)
        if tests.returncode:
            print(tests.stdout[-2000:])
            if live:
                print(send_alert("Topsail specials: the tests failed after this check, so nothing "
                                 "was pushed. See specials.log on the home PC."))
            return 1
        if not live:
            return 0
        _run("git", "add", path, "site")
        if not _run("git", "diff", "--cached", "--quiet", check=False).returncode:
            break                                   # nothing changed on the page
        _run("git", "commit", "-q", "-m",
             f"Specials: {day}, {checked} ET check ({len(new)} new, {len(data['posts'])} today)\n\n"
             "Written by local/fb_specials.py on the home PC.")
        if not _run("git", "push", "-q", check=False).returncode:
            break
    else:
        print(send_alert("Topsail specials: the push failed twice. See specials.log on the home PC."))
        return 1
    if new or failed:
        print(send_alert(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
