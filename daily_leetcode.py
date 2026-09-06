"""
Daily LeetCode Question Bot
----------------------------
Picks today's topic from a rotating list, fetches Medium-difficulty
questions for that topic from LeetCode's public GraphQL endpoint,
skips questions already sent before, picks 3 at random, and sends
them via Telegram. Updates the "already sent" log so questions never
repeat.

Runs via GitHub Actions on a daily cron schedule (see
.github/workflows/daily.yml).
"""

import os
import json
import random
import datetime
import requests

# ---------------------------------------------------------------------
# CONFIG — edit this list to change/add/remove topics in the rotation.
# "name" is just for display; "slug" must match LeetCode's tag slug.
# ---------------------------------------------------------------------
TOPICS = [
    {"name": "Arrays",               "slug": "array"},
    {"name": "Strings",              "slug": "string"},
    {"name": "Linked List",          "slug": "linked-list"},
    {"name": "Trees",                "slug": "binary-tree"},
    {"name": "Graphs",               "slug": "graph"},
    {"name": "Dynamic Programming",  "slug": "dynamic-programming"},
    {"name": "Backtracking",         "slug": "backtracking"},
    {"name": "Greedy",               "slug": "greedy"},
    {"name": "Binary Search",        "slug": "binary-search"},
    {"name": "Heaps",                "slug": "heap-priority-queue"},
    {"name": "Stack",                "slug": "stack"},
    {"name": "Sliding Window",       "slug": "sliding-window"},
]

DIFFICULTY = "MEDIUM"          # fixed per your requirement
QUESTIONS_PER_DAY = 3
SENT_LOG_PATH = "sent_questions.json"
EPOCH = datetime.date(2026, 1, 1)   # arbitrary fixed reference point for rotation

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}

QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList: questionList(
    categorySlug: $categorySlug
    limit: $limit
    skip: $skip
    filters: $filters
  ) {
    total: totalNum
    questions: data {
      difficulty
      title
      titleSlug
      frontendQuestionId: questionFrontendId
      paidOnly: isPaidOnly
      topicTags { name slug }
    }
  }
}
"""


def get_today_topic():
    days_since_epoch = (datetime.date.today() - EPOCH).days
    idx = days_since_epoch % len(TOPICS)
    return TOPICS[idx]


def fetch_questions(topic_slug, difficulty, limit=100):
    payload = {
        "query": QUERY,
        "variables": {
            "categorySlug": "",
            "skip": 0,
            "limit": limit,
            "filters": {
                "difficulty": difficulty,
                "tags": [topic_slug],
            },
        },
    }
    resp = requests.post(LEETCODE_GRAPHQL_URL, json=payload, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"LeetCode GraphQL error: {data['errors']}")
    questions = data["data"]["problemsetQuestionList"]["questions"]
    # Drop premium-only questions since they can't be opened for free
    return [q for q in questions if not q.get("paidOnly")]


def load_sent_ids():
    if os.path.exists(SENT_LOG_PATH):
        with open(SENT_LOG_PATH, "r") as f:
            return set(json.load(f))
    return set()


def save_sent_ids(sent_ids):
    with open(SENT_LOG_PATH, "w") as f:
        json.dump(sorted(sent_ids, key=int), f, indent=2)


def send_telegram_message(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=15)
    resp.raise_for_status()


def main():
    topic = get_today_topic()
    print(f"Today's topic: {topic['name']} ({topic['slug']}), difficulty: {DIFFICULTY}")

    questions = fetch_questions(topic["slug"], DIFFICULTY)
    sent_ids = load_sent_ids()

    unsent = [q for q in questions if q["questionFrontendId"] not in sent_ids]

    # If we've exhausted the pool for this topic, reset just for this topic
    # so the rotation never dries up.
    pool = unsent if len(unsent) >= QUESTIONS_PER_DAY else questions

    if not pool:
        send_telegram_message(
            f"⚠️ No {DIFFICULTY.title()} questions found for topic '{topic['name']}' today."
        )
        return

    picks = random.sample(pool, min(QUESTIONS_PER_DAY, len(pool)))

    lines = [f"📅 Today's topic: {topic['name']} | {DIFFICULTY.title()}"]
    for q in picks:
        lines.append(f"#{q['questionFrontendId']} - https://leetcode.com/problems/{q['titleSlug']}/")

    message = "\n".join(lines)
    print(message)
    send_telegram_message(message)

    sent_ids.update(q["questionFrontendId"] for q in picks)
    save_sent_ids(sent_ids)


if __name__ == "__main__":
    main()