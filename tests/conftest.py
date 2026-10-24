from __future__ import annotations

import copy
import datetime as dt
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Nothing a test calls may run a live check or send an alert: the local jobs
# run these tests from their own clone, where a live check would run the
# tests again (2026-10-23: a loop of "tests failed" alerts).
os.environ["TOPSAIL_IN_TESTS"] = "1"

import fetch  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures", "2026-10-14")
FIXTURE_NOW = dt.datetime(2026, 10, 14, 18, 30, tzinfo=dt.timezone.utc)

_DATA = None


@pytest.fixture
def data() -> dict:
    """The morning of 2026-10-14, every feed replayed from tests/fixtures."""
    global _DATA
    if _DATA is None:
        _DATA = fetch.build("2026-10-14", now_utc=FIXTURE_NOW, replay_dir=FIXTURES)
    return copy.deepcopy(_DATA)


GOOD_REPORT = """---
date: 2026-10-14
kind: sample
headline: Flat water, falling tide, and the drum know it
island_headline: Warm sun, small surf, and a museum worth the walk
---

## Text
Sound is the play this morning: fish the moving water around the 11:28 AM high. The surf is small and friendly. Bring a jacket for the evening, it cools off fast once the sun drops at 6:37.

## Lead
A light southwest breeze and a 1 to 2 foot surf make for an easy morning on the water.

## The Bite
Red drum have been working the oyster bars on the falling tide after the 11:28 AM high.

## Beach & Weather
Sunny and warm. Low rip risk.

## Around the Island
Trunk or treat at 5:30 PM at the town hall, per the town's events page.

## Island Text
Sunny and warm with a light breeze, an easy beach day. The museum opens at 11:00 AM, and the 4:51 PM low tide uncovers the most sand for a shell walk.

## Island Lead
An easy, warm day on the island with a light southwest breeze.

## Things To Do
- The Missiles and More Museum opens at 11:00 AM, per its site.

## Sources
- [NCDMF limits](https://www.deq.nc.gov/about/divisions/marine-fisheries)
- [Town of Topsail Beach](https://topsailbeachnc.gov/)
"""


def git(repo: str, *args: str) -> str:
    done = subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True)
    return done.stdout.decode().strip()


@pytest.fixture
def repo_pair(tmp_path):
    """(clone, origin): a bare origin with one commit on main, and a clone of it."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "clone", "-q", str(origin), str(seed)], check=True,
                   capture_output=True)
    for repo in (seed,):
        git(str(repo), "config", "user.email", "test@example.com")
        git(str(repo), "config", "user.name", "Test")
    (seed / "README.md").write_text("seed\n", encoding="utf-8")
    git(str(seed), "add", "README.md")
    git(str(seed), "commit", "-q", "-m", "seed")
    git(str(seed), "push", "-q", "origin", "HEAD:refs/heads/main")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(origin), str(clone)], check=True,
                   capture_output=True)
    git(str(clone), "config", "user.email", "test@example.com")
    git(str(clone), "config", "user.name", "Test")
    return str(clone), str(origin), str(seed)
