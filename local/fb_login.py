"""Sign in to Facebook once, in the profile the specials check uses.

    python local/fb_login.py

A Chromium window opens on Facebook's sign-in page. Sign in yourself (and
approve the new-device check if Facebook asks), then close the window. The
script only reports whether the profile now holds a session; it never
prints or saves anything else.
"""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

from fb_session import PROFILE, open_context, signed_in


def main() -> int:
    with sync_playwright() as pw:
        ctx = open_context(pw, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.facebook.com/login")
        print("Sign in in the browser window, then close the window.")
        ctx.wait_for_event("close", timeout=0)
        ctx = open_context(pw, headless=True)
        ok = signed_in(ctx)
        ctx.close()
    print(f"Signed in: {'yes' if ok else 'no'} (profile: {PROFILE})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
