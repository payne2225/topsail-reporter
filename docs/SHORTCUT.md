# The iPhone Shortcut that sends the text

One personal automation on the sender's iPhone. It fetches the morning's
text from the site and sends it to the group from the phone's own number.
Nothing else holds anyone's number.

## Build it (Shortcuts app, iOS 17 or later)

1. **Automation** tab, **+**, **Time of Day**. Set **6:30 AM**, **Daily**,
   and choose **Run Immediately**. Tap **Next**, then **New Blank Automation**.
2. Add **Format Date**. Tap its Date and pick **Current Date**. Set Date
   Format to **Custom** and type `yyyy-MM-dd`. Set Time Format to **None**.
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

## When the run ends

Turn the automation off after the last edition. Otherwise it fires every
morning and shows "No Topsail Reporter today".
