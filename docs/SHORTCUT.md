# The iPhone Shortcut that sends the text

One personal automation on the sender's iPhone. It fetches the morning's
text from the site and sends it to the group from the phone's own number.
Nothing else holds anyone's number.

## Build it (Shortcuts app, iOS 17 or later)

1. **Automation** tab, **+**, **Time of Day**. Set **6:30 AM**, **Daily**,
   and choose **Run Immediately**. Tap **Next**, then **New Blank Automation**.
2. Add **Format Date**. Tap its faded **Date** and pick **Current Date**: it
   must turn solid and read "Format Current Date". Left faded, it formats
   nothing, the link ends in `/text/.txt`, and every run says "No Topsail
   Reporter today". Then tap the **>** on the action: Date Format
   **Custom**, Format String `yyyy-MM-dd` (lowercase y and d, capital M),
   Time Format **None**.
3. Add **Text**. Type
   `https://payne2225.github.io/topsail-reporter/text/`
   then insert the **Formatted Date** variable, then type `.txt`
   (no spaces anywhere).
4. Add **Get Contents of URL** (it takes the Text above).
5. Add **Get Text from Input** (input: Contents of URL).
6. Add **If**: input **Text** (from step 5), condition **begins with**,
   value `Topsail Reporter`.
7. Inside the If, add **Send Message**: message = the **Text** from step 5,
   recipients = the group. Expand the action and turn **Show When Run** off,
   so it sends without asking.
8. In **Otherwise**, add **Show Notification**: `No Topsail Reporter today`.

The "begins with" check is the safety: if the site has no text for today,
GitHub answers with an error page, the check fails, and nothing is sent.

## Test it before the group sees anything

Put only your own number in Send Message and tap the play button. On a day
with a sample edition, your phone texts you that sample. When it reads
right, swap in the group's recipients.

## The Island Edition: a second automation

The non-fishing edition has its own text, so it gets its own automation and
its own group. Build a second one exactly like the first, with three
changes:

- Step 1: pick the time you want the island group to get it. The text is
  ready by 6:30 AM, so any time after that works (8:00 AM lets people sleep).
- Step 3: the link ends in `-island.txt` instead of `.txt`:
  `https://payne2225.github.io/topsail-reporter/text/`, then **Formatted
  Date**, then `-island.txt` (no spaces).
- Step 7: recipients = the island group.

The If check stays "begins with `Topsail Reporter`": the Island Edition's
text opens "Topsail Reporter, Island Edition, ...". Test it the same way,
with only your own number first.

## When the run ends

Turn both automations off after the last edition. Otherwise they fire every
morning and show "No Topsail Reporter today".
