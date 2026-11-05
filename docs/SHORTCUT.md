# The iPhone Shortcut that sends the text

One shortcut with a Time of Day automation on the sender's iPhone. It
fetches the morning's text from the site and sends it to the group from
the phone's own number. Nothing else holds anyone's number.

Written for **iOS 27** (rewritten 2026-11-05 from Apple's Shortcuts User
Guide and the iOS 27 release notes). iOS 27 moved automations into the
shortcut itself: the Time of Day trigger is an action at the top of the
shortcut, and there is no separate Automation tab to build in any more.
The **Automation** list in the app shows every shortcut that has one.

## Build it

1. In Shortcuts, tap **+**. A new shortcut opens on **Describe a
   Shortcut**; tap **Edit** for the actions view and build this one by
   hand, so every step below is there exactly. (Settings can make the
   classic editor the default.)
2. From the action list's **Automation** category, add **Time of Day**. It
   goes to the top of the shortcut. Set **6:30 AM**, **Daily**.
3. Add **Format Date**. Tap its faded **Date** and pick **Current Date**: it
   must turn solid and read "Format Current Date". Left faded, it formats
   nothing, the link ends in `/text/.txt`, and every run says "No Topsail
   Reporter today". Then open the action's options: Date Format
   **Custom**, Format String `yyyy-MM-dd` (lowercase y and d, capital M),
   Time Format **None**.
4. Add **Text**. Type
   `https://payne2225.github.io/topsail-reporter/text/`
   then insert the **Formatted Date** variable, then type `.txt`
   (no spaces anywhere).
5. Add **Get Contents of URL** (it takes the Text above).
6. Add **Get Text from Input** (input: **Contents of URL**). This is the
   step that turns the downloaded file into words. Without it the group
   gets a `.txt` attachment.
7. Add **If**: input **Text** (from step 6), condition **begins with**,
   value `Topsail Reporter`.
8. Inside the If, add **Send Message**.
   - Message: tap the message field, tap **Select Variable**, then tap the
     blue **Text** token under Get Text from Input. The field must show
     **Text**, never **Contents of URL**.
   - Recipients: the group. Since iOS 27, Send Message can send to a group
     conversation.
   - If the action shows a **Show When Run** switch in its options, turn it
     off.
9. In **Otherwise**, add **Show Notification**: `No Topsail Reporter today`.
10. Let it run without asking: **Edit**, then the **Info** button, then
    **Privacy**, and turn on **Allow Running When Locked**. Apple notes the
    automation then "will not notify you when it's triggered", and that you
    "may need to set individual actions to run automatically": if Send
    Message still asks on the first run, allow it to run without asking.
11. Name it (`Topsail Reporter`) and tap **Done**.

The "begins with" check is the safety: if the site has no text for today,
GitHub answers with an error page, the check fails, and nothing is sent.

**Finding it later:** in Shortcuts, tap **Automation** (on iPhone you may
have to tap **Back** first). It lists every shortcut that has an
automation, with a filter for Turned On and Turned Off. Open it and tap
**Edit** to change it.

## The group gets a file instead of the words

Found 2026-11-05: the 6:30 texts arrived as "2026-11-05.txt, Text
Document" and "2026-11-05-island.txt". The site was fine, and so was the
shortcut's wiring (Get Text from Input after Get Contents of URL, Send
Message sending its Text). The cause is iOS 27: a `.txt` download
already counts as text, so Get Text from Input can hand the same file on,
and Send Message attaches it. The fix, confirmed on the fishing shortcut
2026-11-05: make a fresh string.

1. Right after **Get Text from Input**, add a **Text** action. In it, tap
   **Select Variable** and tap the blue **Text** token under Get Text from
   Input, so the Text action holds only that token.
2. Right after it, add **Set Variable**: name it `Message` (its input is
   the Text action above).
3. In the **If**, replace the input with **Message** (tap the token, then
   Clear, then Select Variable). **Changing the If's input resets its
   condition to "is"**: tap it and pick **begins with** again, with the
   value `Topsail Reporter`. Left on "is", every run says "No Topsail
   Reporter today".
4. In **Send Message**, replace the message with **Message** the same way.

If it was ever built without Get Text from Input, or Send Message shows
**Contents of URL**, fix that first: tap the token, **Clear**, then
**Select Variable** and pick the right one.

Test on a copy, never on the group's shortcut: duplicate it (touch and
hold it in the library, **Duplicate**), remove the copy's Time of Day
trigger, TYPE only your own number as its recipient, and tap play.

## Test it before the group sees anything

Put only your own number in Send Message and tap the play button. On a day
with an edition, your phone texts you that day's text. When it reads
right, swap in the group's recipients.

To get your own copy once others are on it, TYPE your number into the
recipients rather than picking your own contact card. Messages treats your
card as the sender and drops it, so the others get the text and you only
see it as a sent message (found 2026-10-20).

Every tap of play that passes the check sends a real text to everyone in
the recipients, so test with yourself alone, or warn whoever is on it.

## The Island Edition: a second shortcut

The non-fishing edition has its own text, so it gets its own shortcut and
its own group. The quickest way is to duplicate the working fishing one
(touch and hold it in the library, **Duplicate**) and change four things
in the copy:

- The **Time of Day** trigger at the top (a duplicate keeps it): the time
  you want the island group to get it. The text is ready by 6:30 AM, so
  any time after that works (8:00 AM lets people sleep).
- The **Text** with the link: change the end from `.txt` to
  `-island.txt`, so it reads
  `https://payne2225.github.io/topsail-reporter/text/`, then **Formatted
  Date**, then `-island.txt` (no spaces).
- **Send Message** recipients: the island group.
- The name: `Topsail Reporter Island`.

Then delete the old island shortcut (or turn its automation off), or the
group gets it twice. Building it from scratch instead is the steps above
plus the fresh-string fix, with the same three changes.

The If check stays "begins with `Topsail Reporter`": the Island Edition's
text opens "Topsail Reporter, Island Edition, ...". Test it the same way,
with only your own number first.

## When the run ends

Turn both automations off after the last edition: in **Automation**, turn
each one off (or open it and remove its Time of Day trigger). Otherwise
they fire every morning and show "No Topsail Reporter today".

## Not in Apple's guide (left as it was)

Apple's iOS 27 guide does not document Send Message's options, Get Text
from Input, or Format Date. The steps for those are the iOS 26 build,
which the Nov 5 run shows still works up to the Send Message step.
