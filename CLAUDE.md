# Topsail Reporter: start here

A public repo. Any machine, any session:

1. `git pull --rebase origin main`.
2. Read `docs/HANDOFF.md`: §0 (the resume point) first, then whatever the
   task touches. Then the newest entries in `docs/PATCH_NOTES.md`.

Every change:

- `python -m pytest -q` before pushing anything that touches a `.py` (the
  tests are offline and never run a live job).
- A page change: `python render.py`, look at it, and commit `site/` with it.
- In the same commit: a dated bullet in `docs/PATCH_NOTES.md`, and
  `docs/HANDOFF.md` if how the Reporter works changed.
- A detailed commit message. Pull with rebase, then push straight to `main`;
  CI runs the tests and Pages deploys `site/`.

At the end of a session, rewrite `docs/HANDOFF.md` §0 (where it stands, what
is next, what is open) and push it.

Never: reader names, phones or addresses on a page (HANDOFF §2); the
`local/` Facebook jobs anywhere but the home PC; a cookie, the Facebook
post archive or the alert webhook in the repo; `fetch.py` or `publish.py`
for today's date by hand (that is the morning routine's job).
