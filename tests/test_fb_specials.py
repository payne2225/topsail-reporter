from __future__ import annotations

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local"))

import fb_specials as fb  # noqa: E402

NOW = dt.datetime(2026, 11, 3, 10, 30, tzinfo=fb.ET)        # a Tuesday morning


def _hm(when):
    return when.strftime("%Y-%m-%d %H:%M")


def test_facebook_timestamps_read_as_eastern_times():
    assert _hm(fb.posted_at("Just now", NOW)) == "2026-11-03 10:30"
    assert _hm(fb.posted_at("25m", NOW)) == "2026-11-03 10:05"
    assert _hm(fb.posted_at("3 hrs", NOW)) == "2026-11-03 07:30"
    assert _hm(fb.posted_at("Yesterday at 4:12 PM", NOW)) == "2026-11-02 16:12"
    assert _hm(fb.posted_at("Sunday at 11:00 AM", NOW)) == "2026-11-01 11:00"
    assert _hm(fb.posted_at("November 3 at 9:05 AM", NOW)) == "2026-11-03 09:05"
    assert _hm(fb.posted_at("October 31", NOW)) == "2026-10-31 00:00"
    assert _hm(fb.posted_at("Tuesday, November 3, 2026 at 9:41 AM", NOW)) == "2026-11-03 09:41"
    assert _hm(fb.posted_at("December 30", NOW)) == "2025-12-30 00:00"   # never a future day
    assert fb.posted_at("Shared with Public", NOW) is None
    assert fb.posted_at("", NOW) is None


def test_only_food_and_hours_news_is_kept():
    assert fb.is_food_news("Tonight's special: blackened grouper with rice, $18")
    assert fb.is_food_news("Closed today for a private event, back tomorrow at 11!")
    assert not fb.is_food_news("We're hiring line cooks! Apply in person.")
    assert not fb.is_food_news("Happy birthday to our favorite regular")


def test_a_photo_of_the_specials_board_comes_through_its_alt_text():
    alts = ["May be an image of text that says 'FRIDAY SPECIALS FISH TACOS $12'",
            "May be an image of 2 people"]
    assert fb.alt_text(alts) == "FRIDAY SPECIALS FISH TACOS $12"


def test_permalinks_lose_their_tracking():
    assert (fb.clean_url("https://www.facebook.com/x/posts/pfbid0abc?__cft__[0]=Az&__tn__=%2CO")
            == "https://www.facebook.com/x/posts/pfbid0abc")
    assert (fb.clean_url("https://www.facebook.com/permalink.php?story_fbid=12&id=34&__tn__=K")
            == "https://www.facebook.com/permalink.php?story_fbid=12&id=34")


def test_checks_merge_through_the_day_and_only_new_posts_alert():
    a = {"id": "surfdog", "posted_et": "10:05 AM", "sort": "10:05", "text": "Spaghetti", "url": "u1"}
    b = {"id": "riverview", "posted_et": "2:40 PM", "sort": "14:40", "text": "Flounder plate", "url": "u2"}
    first, new = fb.merge(None, "2026-11-03", [a], "10:31 AM", [])
    assert new == [a] and first["checked_et"] == ["10:31 AM"]
    second, new = fb.merge(first, "2026-11-03", [dict(a, text="Spaghetti, sold out"), b], "3:32 PM", ["coras"])
    assert new == [b]
    assert [p["text"] for p in second["posts"]] == ["Spaghetti, sold out", "Flounder plate"]
    assert second["checked_et"] == ["10:31 AM", "3:32 PM"] and second["failed"] == ["coras"]
    # Yesterday's file never carries into today.
    third, new = fb.merge(second, "2026-11-04", [], "10:30 AM", [])
    assert third["posts"] == [] and third["checked_et"] == ["10:30 AM"]


def test_the_alert_names_each_new_post_and_links_the_page():
    post = {"id": "surfdog", "text": "Spaghetti with meat sauce", "url": "u1"}
    text = fb.alert_text([post], {"surfdog": "SurfDog Bites & Brews"}, "10:31 AM", "2026-11-03", ["coras"])
    assert text.splitlines() == [
        "Topsail specials, 10:31 AM ET check:",
        "- SurfDog Bites & Brews: Spaghetti with meat sauce",
        "Could not read: coras.",
        "https://payne2225.github.io/topsail-reporter/2026-11-03/island/"]


def test_the_check_refuses_to_push_from_a_working_copy(capsys):
    assert fb.main(["--ids", "none"]) == 2
    assert "use --no-push or --dry-run here" in capsys.readouterr().out


def test_a_board_photo_is_read_only_when_it_looks_like_one():
    assert fb.wants_reading("", ["No photo description available."])            # says nothing else
    assert fb.wants_reading("Today's lineup!", ["May be an image of text"])
    assert fb.wants_reading("Thursday Lunch Specials. Specials are available til 3, call us!",
                            ["No photo description available."])
    assert not fb.wants_reading("Our new patio heaters are in, come warm up by the water tonight",
                                ["May be an image of 2 people and outdoors"])


def test_post_text_drops_see_more_and_hashtags():
    assert (fb.tidy("TODAY: 50% off domestics & $5 craft! #thirstythursday #beer See less")
            == "TODAY: 50% off domestics & $5 craft!")
    assert fb.tidy("Three #1 wins") == "Three #1 wins"


def _post(i, text):
    return {"id": f"p{i}", "posted_et": "10:00 AM", "text": text}


def test_claude_keeps_or_drops_and_the_keywords_stand_in_when_it_cannot():
    posts = [_post(0, "Tacos and taps tonight, $4 tacos"), _post(1, "Plan your next party with us!"),
             _post(2, "Closed today for a private event")]
    seen = []

    def ask(prompt):
        seen.append(prompt)
        return "[0, 2]"
    assert fb.keep_posts(posts, {}, ask) == [posts[0], posts[2]]
    assert '"text": "Plan your next party with us!"' in seen[0]
    # No answer, or a garbled one: the keyword filter decides.
    assert fb.keep_posts(posts, {}, lambda _: None) == [posts[0], posts[2]]
    assert fb.keep_posts(posts, {}, lambda _: "Sure! Here you go") == [posts[0], posts[2]]
    assert fb.keep_posts([], {}, ask) == []


def test_long_alerts_split_at_line_breaks():
    text = "\n".join(["head"] + ["x" * 900] * 3 + ["link"])
    parts = fb.chunks(text, 1900)
    assert all(len(c) <= 1900 for c in parts) and "\n".join(parts) == text
    assert fb.chunks("y" * 4000, 1900) == ["y" * 1900, "y" * 1900, "y" * 200]
