"""Hours, season and menu news from every restaurant's Facebook page, daily.

Off-season hours and menus get posted on Facebook weeks before anyone
updates a website. Once a day this reads each place's own page (`facebook`
in reference/restaurants.json), keeps every post it finds in a local
archive beside the job's clone (%LOCALAPPDATA%\\topsail-reporter\\posts,
never committed: post text can name customers), and has Opus 5.5 pick the
posts that are news about the place itself: hours or days changing,
closing for the season, reopening, a new or off-season menu. Each kept post
becomes one plain sentence (no names) in reference/fb_news.json, which the
Island Edition shows in that place's details. New items go to the one
person in alert.json.

    python local/fb_news.py                    # read, keep, write, render, test, push, alert
    python local/fb_news.py --days 14          # look further back (the first run)
    python local/fb_news.py --dry-run --debug  # read and print; write nothing

Same rules as the specials check: home PC only, the Page's own posts only,
never a comment or a name from one, never a cookie. If Claude cannot be
reached nothing is published and the posts are tried again next time.
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

NEWS = os.path.join(fb.HERE, "reference", "fb_news.json")
KEEP_DAYS = 30                      # news older than this leaves the file
KINDS = ("hours", "menu")

# ---- deciding (pure: tested in tests/test_fb_news.py) -------------------------------

NEWS_PROMPT = (
    "Below, as JSON, are recent Facebook posts by restaurants near Topsail Island, NC. Keep a "
    "post only if it is news about the restaurant itself that someone choosing where to eat in "
    "the next few weeks would want: hours or days changing, off-season or winter hours, "
    "closing for the season, a last day open, a temporary closure, reopening, or a new, "
    "seasonal or changed menu (an off-season menu, a new fall menu). Drop the day's specials, "
    "single dishes, events and music, giveaways, hiring, holidays, history, thank-yous and "
    "photos of guests. For each kept post write one plain sentence of at most 25 words saying "
    "only what the post says, naming no person. Turn relative days into dates from the posted "
    "date (posted 2026-10-22, 'this Saturday' is 'Saturday, Oct 24'). Also give until: the last "
    "date (YYYY-MM-DD) the news matters, for a one-time closure or a dated event, or null for "
    "a change that lasts (new hours, a new menu, closing for the season). Reply with ONLY a "
    "JSON list like [{\"i\": 0, \"kind\": \"hours\", \"line\": \"...\", \"until\": null}], "
    "kind being hours or menu, or [] if none.\n\n")


def parse_news(said: str | None, count: int) -> list[dict] | None:
    """Claude's answer as [{i, kind, line}], or None when it gave none we
    can trust (then nothing is published and the posts are tried again)."""
    m = re.search(r"\[.*\]", said or "", re.S)
    if not m:
        return None
    try:
        items = json.loads(m.group(0))
    except ValueError:
        return None
    out = []
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            return None
        i, kind, line = it.get("i"), it.get("kind"), " ".join(str(it.get("line") or "").split())
        if not isinstance(i, int) or not 0 <= i < count or kind not in KINDS or not line:
            continue
        until = it.get("until")
        try:
            until = dt.date.fromisoformat(until).isoformat() if until else None
        except (TypeError, ValueError):
            until = None
        out.append({"i": i, "kind": kind, "line": line[:240], "until": until})
    return out


def classify(posts: list[dict], names: dict[str, str], ask=None) -> list[dict] | None:
    """The posts worth a line, each with kind and line; None if Claude
    could not be reached."""
    if not posts:
        return []
    ask = ask or (lambda prompt: fb._claude([{"type": "text", "text": prompt}], timeout=300))
    kept = []
    for start in range(0, len(posts), 25):                     # one call per 25 posts
        batch = posts[start:start + 25]
        listing = [{"i": i, "restaurant": names.get(p["id"], p["id"]), "posted": p["date"],
                    "text": p["text"][:1200]} for i, p in enumerate(batch)]
        said = parse_news(ask(NEWS_PROMPT + json.dumps(listing, ensure_ascii=False)), len(batch))
        if said is None:
            return None
        kept += [dict(batch[it["i"]], kind=it["kind"], line=it["line"], until=it["until"])
                 for it in said]
    return kept


def merge_news(old: dict | None, kept: list[dict], today: dt.date, checked: str) -> tuple[dict, list[dict]]:
    """fb_news.json with the new items in, duplicates out and anything older
    than KEEP_DAYS dropped. Returns (data, the items that are new)."""
    items = {n["key"]: n for n in (old or {}).get("news", [])}
    new = []
    for k in kept:
        if k["key"] in items:
            continue
        items[k["key"]] = {"key": k["key"], "id": k["id"], "date": k["date"], "kind": k["kind"],
                           "line": k["line"], "until": k.get("until"), "url": k["url"]}
        new.append(items[k["key"]])
    cutoff = (today - dt.timedelta(days=KEEP_DAYS)).isoformat()
    news = sorted((n for n in items.values() if n["date"] >= cutoff),
                  key=lambda n: (n["date"], n["key"]), reverse=True)
    return {"_about": ABOUT, "checked": checked, "news": news}, new


ABOUT = ("Hours, season and menu news from each restaurant's own Facebook page, one plain "
         "sentence per post (written by local/fb_news.py on the home PC; Opus 5.5 picks and "
         "words them, naming no one). The Island Edition shows a place's items from the 21 "
         "days before the edition's date, never past an item's until date (a one-time "
         "closure). Items older than 30 days drop off.")


def news_alert(new: list[dict], names: dict[str, str], checked: str, failed: list[str],
               waiting: int = 0) -> str:
    lines = [f"Topsail restaurant news, {checked} check:"]
    for n in new:
        d = dt.date.fromisoformat(n["date"])
        lines.append(f"- {names.get(n['id'], n['id'])} ({n['kind']}, {d:%b} {d.day}): {n['line']} {n['url']}")
    if waiting:
        lines.append(f"Claude could not be reached, so {waiting} posts wait for the next check.")
    if failed:
        lines.append("Could not read: " + ", ".join(names.get(i, i) for i in failed) + ".")
    return "\n".join(lines)


NEWS_PHOTO_PROMPT = (
    "This is a photo a restaurant posted on Facebook. If it is a menu, reply with ONLY 'Menu: ' "
    "and the menu's title or season as written (like 'Menu: Off-season lunch'), or just 'Menu' "
    "if it shows none. If it "
    "announces hours, days open, closing or reopening, reply with ONLY that announcement's "
    "words as one plain line. Otherwise reply with exactly NONE.")


def wants_photo(text: str, alts: list[str]) -> bool:
    """A photo worth a look: the post says little, or Facebook saw text or a
    menu in it."""
    return len(text or "") < 40 or any(re.search(r"\b(text|menu)\b", a or "", re.I) for a in alts)


def read_news_photo(image: bytes) -> str | None:
    import base64
    kind = "image/png" if image[:4] == b"\x89PNG" else "image/jpeg"
    said = fb._claude([{"type": "image", "source": {"type": "base64", "media_type": kind,
                                                    "data": base64.b64encode(image).decode()}},
                       {"type": "text", "text": NEWS_PHOTO_PROMPT}])
    return None if not said or said.upper().startswith("NONE") else said


# ---- the local archive (outside the repo) -------------------------------------------

def _state(*parts: str) -> str:
    from fb_session import STATE
    return os.path.join(STATE, *parts)


def _load(path: str, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


# ---- the check ---------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, default=2, help="how many days back to look (default 2)")
    ap.add_argument("--ids", help="only these places, comma-separated")
    ap.add_argument("--dry-run", action="store_true", help="read and print; write nothing")
    ap.add_argument("--debug", action="store_true", help="print every post read")
    ap.add_argument("--no-push", action="store_true", help="write and render, but do not push or alert")
    ap.add_argument("--log", help="append everything printed to this file (the scheduled task)")
    args = ap.parse_args(argv)
    if args.log:
        sys.stdout = sys.stderr = open(args.log, "a", encoding="utf-8", buffering=1)
        print(f"==== {dt.datetime.now(fb.ET):%Y-%m-%d %I:%M %p} ET restaurant news")

    now = dt.datetime.now(fb.ET)
    today = now.date()
    seen_path = _state("news_seen.json")
    days = args.days
    if not os.path.exists(seen_path) and days < 14:
        days = 14                                   # the first run looks two weeks back
    since = today - dt.timedelta(days=days)
    checked = f"{now:%b} {now.day}, {now:%I:%M %p}".replace(" 0", " ") + " ET"
    live = not (args.dry_run or args.no_push)
    from fb_session import STATE
    if live and os.path.normcase(fb.HERE) != os.path.normcase(os.path.join(STATE, "repo")):
        print(f"A live check runs from {os.path.join(STATE, 'repo')}; use --no-push or --dry-run here.")
        return 2
    if live and fb.in_tests():
        print("No live check under the tests.")
        return 2
    if live:
        fb._run("git", "fetch", "-q")
        fb._run("git", "reset", "-q", "--hard", "origin/main")
    with open(os.path.join(fb.HERE, "reference", "restaurants.json"), encoding="utf-8") as f:
        places = [p for p in json.load(f)["places"] if p.get("facebook") and p["status"] != "closed"]
    if args.ids:
        wanted = set(args.ids.split(","))
        places = [p for p in places if p["id"] in wanted]
    names = {p["id"]: p["name"] for p in places}
    seen = set(_load(seen_path, []))
    deep = days > 3
    from playwright.sync_api import sync_playwright
    from fb_session import open_context, signed_in

    fresh, failed, archived = [], [], 0
    with sync_playwright() as pw:
        ctx = open_context(pw, headless=True)
        if not signed_in(ctx):
            ctx.close()
            msg = "Topsail restaurant news: the Facebook sign-in has lapsed. Run local/fb_login.py on the home PC."
            print(msg)
            if live:
                print(fb.send_alert(msg))
            return 2
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for p in places:
            print(f"{p['id']}: {p['facebook']}")
            try:
                read = fb.read_page(page, p["facebook"], now, args.debug,
                                    want=60 if deep else 10, scrolls=45 if deep else 14,
                                    stop_before=dt.datetime.combine(since, dt.time(), fb.ET))
            except fb.NotSignedIn:
                failed.append(p["id"])
                print("  signed out")
                break
            except Exception as e:  # noqa: BLE001 - one page failing never stops the check
                failed.append(p["id"])
                print(f"  failed: {type(e).__name__}: {str(e)[:120]}")
                continue
            arch_path = _state("posts", f"{p['id']}.json")
            arch = _load(arch_path, {})
            recent = [x for x in read if x["when"].date() >= since]
            for x in recent:
                key = f"{p['id']}@{x['when']:%Y-%m-%dT%H:%M}"
                text = x["text"]
                if key not in arch:
                    alts = [alt for _, alt in x["images"]]
                    photo = None
                    if x["images"] and wants_photo(text, alts):
                        try:
                            photo = read_news_photo(page.request.get(x["images"][0][0]).body())
                        except Exception:  # noqa: BLE001 - the post keeps its own words
                            photo = None
                        if photo:
                            print(f"  read a photo: {photo[:80]!r}")
                    arch[key] = {"when": x["when"].isoformat(), "text": text, "photo": photo,
                                 "url": x["url"]}
                    archived += 1
                entry = arch[key]
                if key not in seen:
                    words = " ".join(w for w in (entry["text"], entry.get("photo")) if w)
                    if words:
                        fresh.append({"key": key, "id": p["id"], "date": x["when"].date().isoformat(),
                                      "text": words, "url": entry["url"]})
            if not args.dry_run:
                _save(arch_path, arch)
            print(f"  {len(read)} posts read, {len(recent)} since {since}")
            time.sleep(random.uniform(4, 9))
        ctx.close()

    kept = classify(fresh, names)
    waiting = len(fresh) if kept is None else 0
    for x in fresh:
        hit = next((k for k in kept or [] if k["key"] == x["key"]), None)
        print(f"  {'KEEP ' + hit['kind'] + ': ' + hit['line'] if hit else 'drop'} | {x['id']}: {x['text'][:90]!r}")
    print(f"{archived} posts added to the archive; {len(fresh)} new to Claude; "
          f"{len(kept or [])} kept{'; Claude unreachable' if kept is None else ''}")
    if args.dry_run:
        return 0
    if kept is not None:
        seen |= {x["key"] for x in fresh}

    for attempt in range(2):
        if live:
            fb._run("git", "fetch", "-q")
            fb._run("git", "reset", "-q", "--hard", "origin/main")
        data, new = merge_news(_load(NEWS, None), kept or [], today, checked)
        if attempt == 0:
            text = news_alert(new, names, checked, failed, waiting)
            print(text if new or failed or waiting else "No new restaurant news.")
        if not new:
            break                                   # nothing for the page
        _save(NEWS, data)
        fb._run(sys.executable, "render.py")
        tests = fb._run(sys.executable, "-m", "pytest", "-q", check=False)
        if tests.returncode:
            print(tests.stdout[-2000:])
            if live:
                print(fb.send_alert("Topsail restaurant news: the tests failed after this check, so "
                                    "nothing was pushed. See specials.log on the home PC."))
            return 1
        if not live:
            break
        fb._run("git", "add", NEWS, "site")
        fb._run("git", "commit", "-q", "-m",
                f"Restaurant news: {checked} check ({len(new)} new)\n\n"
                "Written by local/fb_news.py on the home PC.")
        if not fb._run("git", "push", "-q", check=False).returncode:
            break
    else:
        print(fb.send_alert("Topsail restaurant news: the push failed twice. See specials.log on the home PC."))
        return 1
    if live:                                        # a trial run never uses up a post
        _save(seen_path, sorted(seen))
    if live and (new or failed or waiting):
        print(fb.send_alert(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
