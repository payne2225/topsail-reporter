from __future__ import annotations

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local"))

import fb_news as fn  # noqa: E402

NAMES = {"daddy-macs": "Daddy Mac's Beach Grille", "breezeway": "Breezeway Restaurant"}


def _post(key, pid="daddy-macs", date="2026-10-23", text="Our off-season menu is here!"):
    return {"key": key, "id": pid, "date": date, "text": text, "url": f"https://www.facebook.com/{key}"}


def test_claudes_answer_is_read_strictly():
    said = 'Here you go: [{"i": 0, "kind": "menu", "line": "Off-season menu is out."}, ' \
           '{"i": 7, "kind": "hours", "line": "x"}, {"i": 1, "kind": "music", "line": "y"}]'
    assert fn.parse_news(said, 2) == [{"i": 0, "kind": "menu", "line": "Off-season menu is out.",
                                       "until": None}]
    once = '[{"i": 0, "kind": "hours", "line": "Closed Saturday, Oct 24 evening.", "until": "2026-10-24"},' \
           ' {"i": 1, "kind": "hours", "line": "Closed Monday.", "until": "next week"}]'
    assert [x["until"] for x in fn.parse_news(once, 2)] == ["2026-10-24", None]
    assert fn.parse_news("[]", 3) == []
    assert fn.parse_news(None, 3) is None and fn.parse_news("no list here", 3) is None
    assert fn.parse_news("[1, 2]", 3) is None                 # not the shape asked for


def test_classify_batches_and_gives_none_when_claude_is_away():
    posts = [_post(f"k{i}") for i in range(30)]
    calls = []

    def ask(prompt):
        calls.append(prompt)
        return '[{"i": 0, "kind": "menu", "line": "Off-season menu is out."}]'
    kept = fn.classify(posts, NAMES, ask=ask)
    assert len(calls) == 2                                    # 25 + 5
    assert [k["key"] for k in kept] == ["k0", "k25"] and kept[0]["kind"] == "menu"
    assert fn.classify(posts, NAMES, ask=lambda _: None) is None
    assert fn.classify([], NAMES, ask=lambda _: 1 / 0) == []


def test_merge_keeps_one_of_each_post_and_drops_old_news():
    today = dt.date(2026, 10, 23)
    old = {"news": [dict(key="a", id="breezeway", date="2026-09-01", kind="hours", line="Old.", url="u"),
                    dict(key="b", id="breezeway", date="2026-10-20", kind="hours", line="Thu-Sat now.", url="u")]}
    kept = [dict(_post("b"), kind="hours", line="Thu-Sat now."),
            dict(_post("c"), kind="menu", line="Off-season menu is out.")]
    data, new = fn.merge_news(old, kept, today, "Oct 23, 8:30 PM ET")
    assert [n["key"] for n in new] == ["c"]
    assert [n["key"] for n in data["news"]] == ["c", "b"]     # newest first; Sept 1 aged out
    assert data["checked"] == "Oct 23, 8:30 PM ET" and "text" not in data["news"][0]


def test_the_alert_lists_new_items_and_what_went_wrong():
    new = [dict(key="c", id="daddy-macs", date="2026-10-23", kind="menu",
                line="Off-season menu is out.", url="https://www.facebook.com/c")]
    text = fn.news_alert(new, NAMES, "Oct 23, 8:30 PM ET", ["breezeway"], waiting=3)
    assert text.splitlines() == [
        "Topsail restaurant news, Oct 23, 8:30 PM ET check:",
        "- Daddy Mac's Beach Grille (menu, Oct 23): Off-season menu is out. https://www.facebook.com/c",
        "Claude could not be reached, so 3 posts wait for the next check.",
        "Could not read: Breezeway Restaurant.",
    ]


def test_a_photo_is_looked_at_when_the_post_says_little_or_shows_a_menu():
    assert fn.wants_photo("", [])
    assert fn.wants_photo("A long caption about our wonderful fall season here", ["May be an image of menu"])
    assert not fn.wants_photo("A long caption about our wonderful fall season here", ["May be an image of 2 people"])
