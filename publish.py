"""Commit this morning's edition on top of origin/main and push it.

    python publish.py --date 2026-11-05 --what numbers   # the quick edition
    python publish.py --date 2026-11-05 --what full      # the written report

Publishes data/<date>.json, reports/<date>.md when it exists, and all of
site/. The commit is built on a fresh fetch of origin/main with this
checkout's copies of exactly those files, so a push can never conflict with
anything else on main and nothing outside them is touched. Retries a
rejected push up to five times. Then lands this checkout on the pushed
commit when nothing else in it is modified.

Prints PUSHED <sha>, NOTHING NEW, or FAILED <why> (exit 1).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))


class GitError(RuntimeError):
    pass


def _git(repo: str, *args: str, data: bytes | None = None, env: dict | None = None,
         check: bool = True) -> subprocess.CompletedProcess:
    done = subprocess.run(["git", "-C", repo, *args], input=data, capture_output=True,
                          env=env, timeout=120)
    if check and done.returncode != 0:
        raise GitError(f"git {args[0]}: " +
                       (done.stderr or done.stdout).decode("utf-8", "replace").strip()[:300])
    return done


def _out(done: subprocess.CompletedProcess) -> str:
    return done.stdout.decode("utf-8", "replace").strip()


def _identity(repo: str) -> dict:
    env = dict(os.environ)
    if not _out(_git(repo, "config", "user.email", check=False)):
        for key, value in (("GIT_AUTHOR_NAME", "Claude"), ("GIT_COMMITTER_NAME", "Claude"),
                           ("GIT_AUTHOR_EMAIL", "noreply@anthropic.com"),
                           ("GIT_COMMITTER_EMAIL", "noreply@anthropic.com")):
            env.setdefault(key, value)
    return env


def edition_paths(repo: str, date_iso: str) -> list[str]:
    paths = [f"data/{date_iso}.json"]
    if os.path.exists(os.path.join(repo, "reports", f"{date_iso}.md")):
        paths.append(f"reports/{date_iso}.md")
    for folder, _dirs, files in os.walk(os.path.join(repo, "site")):
        for name in files:
            rel = os.path.relpath(os.path.join(folder, name), repo).replace(os.sep, "/")
            paths.append(rel)
    return sorted(paths)


def build_commit(repo: str, base: str, paths: list[str], message: str) -> str | None:
    """A commit on `base` with this checkout's copies of `paths`; None if unchanged."""
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "index"))
        _git(repo, "read-tree", base, env=env)
        for rel in paths:
            with open(os.path.join(repo, *rel.split("/")), "rb") as f:
                blob = _out(_git(repo, "hash-object", "-w", "--stdin", data=f.read()))
            _git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},{rel}", env=env)
        tree = _out(_git(repo, "write-tree", env=env))
    if tree == _out(_git(repo, "rev-parse", f"{base}^{{tree}}")):
        return None
    return _out(_git(repo, "commit-tree", tree, "-p", base, "-m", message, env=_identity(repo)))


def land(repo: str, commit: str, paths: list[str]) -> bool:
    """Move this checkout onto `commit` when only edition files are modified."""
    status = _git(repo, "status", "--porcelain", "--untracked-files=no",
                  check=False).stdout.decode("utf-8", "replace")
    # Not stripped as a whole: that eats the first line's leading status column.
    dirty = [line[3:].strip() for line in status.splitlines() if line.strip()]
    if any(p not in paths for p in dirty):
        return False
    return _git(repo, "reset", "-q", "--hard", commit, check=False).returncode == 0


def publish(repo: str, date_iso: str, what: str, attempts: int = 5,
            sleep=time.sleep) -> tuple[str, str]:
    paths = edition_paths(repo, date_iso)
    message = (f"Topsail Reporter {date_iso}: the {what} edition\n\n"
               f"Published by the morning routine: {', '.join(p for p in paths if not p.startswith('site/'))}"
               f" and the rendered site ({sum(p.startswith('site/') for p in paths)} files).")
    last = ""
    for attempt in range(attempts):
        try:
            _git(repo, "fetch", "-q", "origin", "main")
            base = _out(_git(repo, "rev-parse", "FETCH_HEAD"))
            commit = build_commit(repo, base, paths, message)
            if commit is None:
                land(repo, base, paths)
                return "NOTHING NEW", base[:7]
            push = _git(repo, "push", "-q", "origin", f"{commit}:refs/heads/main", check=False)
            if push.returncode == 0:
                landed = land(repo, commit, paths)
                return "PUSHED", commit[:7] + ("" if landed else
                                               " (checkout left as it was: other files modified)")
            last = push.stderr.decode("utf-8", "replace").strip()[:200]
        except (GitError, subprocess.TimeoutExpired) as exc:
            last = str(exc)
        sleep(min(5 * (attempt + 1), 20))
    return "FAILED", last


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--date", required=True)
    parser.add_argument("--what", choices=("numbers", "full"), required=True)
    parser.add_argument("--root", default=HERE, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    status, detail = publish(args.root, args.date, args.what)
    print(f"{status} {detail}")
    return 1 if status == "FAILED" else 0


if __name__ == "__main__":
    sys.exit(main())
