import os, json, requests
briefs = json.loads(open("briefs.json").read())

blocks = []
for b in briefs:
    blocks += [
        {"type": "section",
         "text": {"type": "mrkdwn",
                  "text": f"*<{b['link']}|{b['title']}>*\n{b['summary']}"}},
        {"type": "divider"}
    ]

resp = requests.post(
    os.getenv("SLACK_WEBHOOK"),
    json={"blocks": blocks or [{"type":"section","text":{"type":"mrkdwn","text":"(本日新着なし)"}}]}
)
print("Slack status", resp.status_code)
