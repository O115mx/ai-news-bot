import feedparser, sqlite3, datetime, pathlib, json, snscrape.modules.twitter as s

# ========= 設定 =========
FEEDS = [
    "https://export.arxiv.org/rss/cs.LG",
    "https://news.mynavi.jp/techplus/rss",     # ← 見つからなければ後で削除
    "https://ledge.ai/feed",
]
TW_HANDLES = [
    "taiyo_ai_gakuse", "ytiskw", "Aoi_genai",
]
MAX_PER_DAY = 5        # Slack に出す件数
DB = "seen.db"
OUT = "items.json"
# =======================

def seen(url, cur):
    return cur.execute("SELECT 1 FROM seen WHERE url=?", (url,)).fetchone()

conn = sqlite3.connect(DB)
cur = conn.cursor(); cur.execute("CREATE TABLE IF NOT EXISTS seen(url TEXT PRIMARY KEY)")

new_items = []

# RSS
for url in FEEDS:
    for e in feedparser.parse(url).entries:
        if seen(e.link, cur): continue
        new_items.append(dict(title=e.title, text=e.summary, link=e.link))
        cur.execute("INSERT INTO seen VALUES(?)", (e.link,))

# X (昨日分だけ)
yesterday = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).date()
for handle in TW_HANDLES:
    for tw in s.TwitterUserScraper(handle).get_items():
        if tw.date.date() < yesterday: break
        if seen(tw.url, cur): continue
        new_items.append(dict(title=f"{handle}: {tw.content[:60]}", text=tw.content, link=tw.url))
        cur.execute("INSERT INTO seen VALUES(?)", (tw.url,))

conn.commit(); conn.close()

# 後工程用に保存
pathlib.Path(OUT).write_text(json.dumps(new_items[:MAX_PER_DAY], ensure_ascii=False))
print(f"Fetched {len(new_items)} new items")
