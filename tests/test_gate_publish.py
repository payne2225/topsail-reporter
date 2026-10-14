from __future__ import annotations

import datetime as dt
import json
import os

import config
import gate
import publish
from conftest import git

UTC = dt.timezone.utc
NOV2_430_EST = dt.datetime(2026, 11, 2, 9, 30, tzinfo=UTC)


def data_json(made: dt.datetime) -> str:
    return json.dumps({"generated_utc": made.strftime("%Y-%m-%dT%H:%M:%SZ")})


def test_off_outside_the_run():
    assert gate.decide("2026-10-20", NOV2_430_EST, None, None)[0] == gate.OFF
    assert gate.decide("2026-11-08", NOV2_430_EST, None, None)[0] == gate.OFF


def test_go_on_a_fresh_morning():
    assert gate.decide("2026-11-02", NOV2_430_EST, None, None) == (gate.GO, "daily")


def test_done_once_the_report_is_published():
    assert gate.decide("2026-11-02", NOV2_430_EST, "---", data_json(NOV2_430_EST))[0] == gate.DONE


def test_busy_while_an_earlier_fire_is_writing():
    made = NOV2_430_EST - dt.timedelta(minutes=58)
    assert gate.decide("2026-11-02", NOV2_430_EST, None, data_json(made))[0] == gate.BUSY


def test_go_when_the_numbers_edition_is_old_and_no_report_came():
    made = NOV2_430_EST - dt.timedelta(minutes=80)
    assert gate.decide("2026-11-02", NOV2_430_EST, None, data_json(made)) == (gate.GO, "daily")
    assert gate.decide("2026-11-02", NOV2_430_EST, None, "not json")[0] == gate.GO


def test_the_first_winter_fire_is_still_the_right_day():
    # 08:30 UTC on Nov 1 is 3:30 AM EST, after the clock change at 2 AM.
    first = config.eastern(dt.datetime(2026, 11, 1, 8, 30, tzinfo=UTC))
    assert (first.date().isoformat(), first.hour, first.minute) == ("2026-11-01", 3, 30)
    # The day after the run, the gate stops before it ever touches git.
    status, date, _ = gate.gate("/nonexistent", dt.datetime(2026, 11, 8, 8, 30, tzinfo=UTC))
    assert (status, date) == (gate.OFF, "2026-11-08")


def test_gate_reads_origin_not_the_checkout(repo_pair):
    clone, origin, seed = repo_pair
    now = dt.datetime(2026, 10, 29, 8, 40, tzinfo=UTC)
    assert gate.gate(clone, now)[0] == gate.GO
    os.makedirs(os.path.join(seed, "reports"))
    with open(os.path.join(seed, "reports", "2026-10-29.md"), "w") as f:
        f.write("---\n")
    git(seed, "add", "reports")
    git(seed, "commit", "-q", "-m", "report")
    git(seed, "push", "-q", "origin", "HEAD:refs/heads/main")
    assert gate.gate(clone, now)[:2] == (gate.DONE, "2026-10-29")


def _edition(repo: str, date: str, body: str = "x") -> None:
    for rel, text in ((f"data/{date}.json", "{}"), (f"site/text/{date}.txt", body),
                      (f"site/{date}/index.html", "<p>" + body)):
        path = os.path.join(repo, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)


def test_publish_pushes_and_lands_the_checkout(repo_pair):
    clone, origin, seed = repo_pair
    _edition(clone, "2026-10-29")
    status, detail = publish.publish(clone, "2026-10-29", "numbers", sleep=lambda s: None)
    assert status == "PUSHED" and "left as it was" not in detail
    assert git(origin, "show", "main:site/text/2026-10-29.txt") == "x"
    assert git(clone, "rev-parse", "HEAD") == git(origin, "rev-parse", "main")
    assert git(clone, "status", "--porcelain") == ""
    assert publish.publish(clone, "2026-10-29", "numbers", sleep=lambda s: None)[0] == "NOTHING NEW"


def test_publish_keeps_what_someone_else_pushed_meanwhile(repo_pair):
    clone, origin, seed = repo_pair
    with open(os.path.join(seed, "NOTES.md"), "w") as f:
        f.write("pushed by someone else\n")
    git(seed, "add", "NOTES.md")
    git(seed, "commit", "-q", "-m", "notes")
    git(seed, "push", "-q", "origin", "HEAD:refs/heads/main")
    _edition(clone, "2026-10-29", "full")
    os.makedirs(os.path.join(clone, "reports"))
    with open(os.path.join(clone, "reports", "2026-10-29.md"), "w") as f:
        f.write("---\ndate: 2026-10-29\n---\n")
    assert publish.publish(clone, "2026-10-29", "full", sleep=lambda s: None)[0] == "PUSHED"
    assert git(origin, "show", "main:NOTES.md") == "pushed by someone else"
    assert git(origin, "show", "main:reports/2026-10-29.md").startswith("---")


def test_publish_leaves_a_checkout_with_other_edits_alone(repo_pair):
    clone, origin, seed = repo_pair
    with open(os.path.join(clone, "README.md"), "w") as f:
        f.write("edited by hand\n")
    _edition(clone, "2026-10-29")
    status, detail = publish.publish(clone, "2026-10-29", "numbers", sleep=lambda s: None)
    assert status == "PUSHED" and "left as it was" in detail
    with open(os.path.join(clone, "README.md")) as f:
        assert f.read() == "edited by hand\n"
