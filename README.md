# Daily LeetCode Question Bot

Sends you 3 Medium-difficulty LeetCode question numbers/links every day,
rotating automatically through a list of topics. 100% free — runs on
GitHub Actions + Telegram.

## One-time setup (~10 minutes)

### 1. Create a Telegram bot
1. Open Telegram, search for **@BotFather**, start a chat.
2. Send `/newbot`, follow the prompts (pick any name/username).
3. BotFather gives you a **bot token** — copy it. Looks like `123456789:ABC-def...`.

### 2. Get your chat ID
1. Search for your new bot in Telegram and send it any message (e.g. "hi").
2. In a browser, visit:
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. In the JSON response, find `"chat":{"id": 123456789, ...}` — that number is your **chat ID**.

### 3. Create a GitHub repo
1. Create a new (can be private) GitHub repo.
2. Upload these 3 files, keeping the folder structure:
   - `daily_leetcode.py`
   - `.github/workflows/daily.yml`
   - `README.md` (optional)

### 4. Add your secrets
In the repo: **Settings → Secrets and variables → Actions → New repository secret**
- `TELEGRAM_BOT_TOKEN` → paste your bot token
- `TELEGRAM_CHAT_ID` → paste your chat ID

### 5. Test it
Go to the **Actions** tab → "Daily LeetCode Questions" workflow → **Run workflow**
(this is the `workflow_dispatch` trigger). You should get a Telegram message
within a few seconds.

### 6. Set up the reliable daily trigger (cron-job.org)
GitHub's built-in `schedule` trigger can be delayed or skipped, so use
[cron-job.org](https://cron-job.org) (free) to call GitHub's API directly instead:

1. Create a GitHub **fine-grained personal access token**: Settings → Developer
   settings → Personal access tokens → Fine-grained tokens → select this repo →
   set **Actions** permission to **Read and write**.
2. Sign up at cron-job.org → **Create cronjob**:
   - URL: `https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/workflows/daily.yml/dispatches`
   - Method: `POST`
   - Headers: `Authorization: Bearer YOUR_TOKEN`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`
   - Body (JSON): `{"ref": "main"}` (use your actual default branch name)
   - Schedule: daily, timezone IST, time 08:00
3. Save, then run cron-job.org's "Test run" — confirm a new run appears in your repo's Actions tab.

Keep GitHub's own `schedule` trigger in `daily.yml` too — it's harmless to have
both, and acts as a backup if cron-job.org ever has an outage.

## Customizing

- **Change the time:** edit the `cron` line in `.github/workflows/daily.yml`
  (cron times are in UTC — IST is UTC+5:30).
- **Change topics:** edit the `TOPICS` list at the top of `daily_leetcode.py`.
  Each entry needs the LeetCode tag `slug` — you can find these in the URL
  when you filter by tag on leetcode.com/problemset.
- **Change difficulty:** edit `DIFFICULTY = "MEDIUM"` to `"EASY"` or `"HARD"`.
- **Never repeats:** `sent_questions.json` is auto-created and committed back
  to your repo after each run, tracking every question number you've
  already received so you won't see duplicates. If a topic's pool runs out,
  it resets just for that topic instead of going silent.

## Cost
Entirely free:
- GitHub Actions: public repos get unlimited free minutes; private repos get
  2,000 free minutes/month (this job takes a few seconds/day).
- Telegram Bot API: free, no limits at this scale.
- LeetCode GraphQL endpoint: public, no key needed.