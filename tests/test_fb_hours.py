from __future__ import annotations

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local"))

import fb_hours as fh  # noqa: E402
import fb_specials as fb  # noqa: E402

NAMES = {"breezeway": "Breezeway Restaurant", "riverview": "Riverview Cafe",
         "sears-landing": "Sears Landing"}
SINCE = dt.date(2026, 10, 22)
TODAY = dt.date(2026, 11, 5)


def _post(i, text, posted="Mon Nov 2"):
    return {"id": i, "text": text, "posted": posted, "url": f"https://www.facebook.com/{i}"}


def test_hours_words_catch_closing_and_cut_back_days_not_specials():
    assert fh.is_hours_news("We'll be closed for the season after Sunday. See you in April!")
    assert fh.is_hours_news("Heads up, friends! We'll be open Thursday and Saturday this week")
    assert fh.is_hours_news("We reopen April 2nd")
    assert fh.is_hours_news("New hours starting Nov 1: Thu-Sun 5-9")
    assert not fh.is_hours_news("Tonight's special: crab-stuffed flounder, $24")
    assert not fh.is_hours_news("Live music on the deck with Mike Rooney 6-9!")


def test_claude_picks_the_hours_posts_and_the_keywords_stand_in_when_it_cannot():
    posts = [_post("breezeway", "Last weekend of the season! Closed after Sunday."),
             _post("riverview", "Friday lunch specials: shrimp burger $12")]
    assert fh.hours_posts(posts, NAMES, ask=lambda _: "[0]") == posts[:1]
    assert fh.hours_posts(posts, NAMES, ask=lambda _: "[]") == []
    assert fh.hours_posts(posts, NAMES, ask=lambda _: None) == posts[:1]
    assert fh.hours_posts([], NAMES, ask=lambda _: 1 / 0) == []


def test_the_alert_names_what_was_found_with_links():
    found = [_post("breezeway", "Closed for the season after Sunday, Nov 8.", "Sun Nov 1")]
    newest = {"breezeway": dt.datetime(2026, 11, 1, 12, tzinfo=fb.ET),
              "riverview": dt.datetime(2026, 11, 4, 15, tzinfo=fb.ET)}
    text = fh.hours_alert(found, NAMES, newest, SINCE, TODAY, [])
    assert text.startswith("Topsail hours check, Thu Nov 5: posts about closing or hours since Oct 22:")
    assert "- Breezeway Restaurant, Sun Nov 1: Closed for the season after Sunday, Nov 8. " \
           "https://www.facebook.com/breezeway" in text
    assert "Newest posts: Breezeway Restaurant Nov 1, Riverview Cafe Nov 4." in text


def test_the_alert_says_so_when_nothing_was_posted_and_who_could_not_be_read():
    newest = {"breezeway": dt.datetime(2026, 10, 19, 13, tzinfo=fb.ET),
              "sears-landing": dt.datetime(2026, 11, 4, 9, tzinfo=fb.ET)}
    text = fh.hours_alert([], NAMES, newest, SINCE, TODAY, ["riverview"])
    assert text.splitlines() == [
        "Topsail hours check, Thu Nov 5: nothing about closing or hours from "
        "Breezeway Restaurant or Sears Landing since Oct 22.",
        "Newest posts: Breezeway Restaurant Oct 19, Sears Landing Nov 4.",
        "Could not read: Riverview Cafe.",
    ]
    assert fh.hours_alert([], NAMES, {}, SINCE, TODAY, list(NAMES)).splitlines()[0] == \
        "Topsail hours check, Thu Nov 5: no page could be read."


def test_a_notice_photo_is_read_but_a_specials_board_is_left_to_the_specials_check():
    assert fh.wants_notice_reading("", [])
    assert fh.wants_notice_reading("Big news!", [])
    assert fh.wants_notice_reading("A few words about this fall from all of us here at the restaurant",
                                   ["May be an image of text that says 'CLOSED'"])
    assert not fh.wants_notice_reading("Thursday Lunch Specials", [])
    assert not fh.wants_notice_reading("Dinner menu tonight", ["May be an image of text"])
