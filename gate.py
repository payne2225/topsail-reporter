"""Should this fire write today's Topsail Reporter? The routine's FIRST command.

    python gate.py

The routine's cron fires twice a morning, at 08:30 and 09:30 UTC (4:30 and
5:30 AM EDT; 3:30 and 4:30 AM EST, from Nov 1), and only on the days the
run covers. This prints ONE line and exits with its code:

    GO <date> <kind>   0   write today's edition
    OFF <date>        10   no edition today: stop now
    DONE <date>       10   today's full report is already on origin: stop now
    BUSY <date>       10   an earlier fire published the numbers edition less
                           than 75 minutes ago and is still writing: stop now
    GIT ERROR <date>   1   origin could not be read: carry on as GO and say
                           so in the report (a fire that cannot reach GitHub
                           cannot publish either, so there is nothing to
                           collide with)

There is no lock to take: two fires writing the same morning would only
overwrite the same files, and the Shortcut reads one file at 6:30.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time

import config

HERE = os.path.dirname(os.path.abspath(__file__))
GO, OFF, DONE, BUSY, GIT_ERROR = "GO", "OFF", "DONE", "BUSY", "GIT ERROR"
EXIT_CODES = {GO: 0, OFF: 10, DONE: 10, BUSY: 10, GIT_ERROR: 1}


class GitError(RuntimeError):
    pass


def _git(repo: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    done = subprocess.run(["git", "-C", repo, *args], capture_output=True, timeout=120)
    if check and done.returncode != 0:
        raise GitError((done.stderr or done.stdout).decode("utf-8", "replace").strip()[:300])
    return done


def fetch_origin(repo: str, attempts: int = 3, sleep=time.sleep) -> str:
    for attempt in range(attempts):
        try:
            _git(repo, "fetch", "-q", "origin", "main")
            break
        except (GitError, subprocess.TimeoutExpired):
            if attempt == attempts - 1:
                raise
            sleep(5 * (attempt + 1))
    return _git(repo, "rev-parse", "FETCH_HEAD").stdout.decode().strip()


def show(repo: str, rev: str, rel: str) -> str | None:
    if _git(repo, "cat-file", "-e", f"{rev}:{rel}", check=False).returncode != 0:
        return None
    return _git(repo, "cat-file", "blob", f"{rev}:{rel}").stdout.decode("utf-8")


def decide(date_iso: str, now_utc: dt.datetime, report: str | None,
           data: str | None) -> tuple[str, str]:
    kind = config.kind_for(date_iso)
    if kind is None:
        return OFF, "no edition today. Stop now."
    if report is not None:
        return DONE, "today's full report is already published. Stop now."
    if data is not None:
        try:
            made = dt.datetime.strptime(json.loads(data)["generated_utc"],
                                        "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
            age = (now_utc - made).total_seconds() / 60
        except (ValueError, KeyError, TypeError):
            age = None
        if age is not None and age < config.BUSY_MINUTES:
            return BUSY, (f"an earlier fire published the numbers {age:.0f} minutes ago "
                          "and is still writing. Stop now.")
    return GO, kind


def gate(repo: str, now_utc: dt.datetime, sleep=time.sleep) -> tuple[str, str, str]:
    date_iso = config.eastern(now_utc).strftime("%Y-%m-%d")
    if config.kind_for(date_iso) is None:
        return OFF, date_iso, "no edition today. Stop now."
    base = fetch_origin(repo, sleep=sleep)
    status, detail = decide(date_iso, now_utc, show(repo, base, f"reports/{date_iso}.md"),
                            show(repo, base, f"data/{date_iso}.json"))
    return status, date_iso, detail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=HERE, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    now_utc = dt.datetime.now(dt.timezone.utc)
    try:
        status, date_iso, detail = gate(args.root, now_utc)
    except (GitError, subprocess.TimeoutExpired) as exc:
        date_iso = config.eastern(now_utc).strftime("%Y-%m-%d")
        print(f"{GIT_ERROR} {date_iso}: {exc}. Carry on as GO "
              f"({config.kind_for(date_iso)}) and say so in your report.")
        return EXIT_CODES[GIT_ERROR]
    print(f"{status} {date_iso} {detail}" if status == GO else f"{status} {date_iso}: {detail}")
    return EXIT_CODES[status]


if __name__ == "__main__":
    sys.exit(main())
