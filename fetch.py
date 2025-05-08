import feedparser, sqlite3, datetime, pathlib, json, traceback, requests

# ========= 設定 =========
MAX_PER_DAY = 5            # Slack に出す件数
DB           = "seen.db"
OUT          = "items.json"

# --- RSS / Atom フィード ---
FEEDS = [
    "https://export.arxiv.org/rss/cs.LG",
    "https://news.mynavi.jp/techplus/rss",
    "https://ledge.ai/feed",
]

# --- Twitter を RSSHub 経由で取得 ---
TW_HANDLES = [
    "taiyo_ai_gakuse",
    "ytiskw",
    "Aoi_genai",
]
RSSHUB = "https://rsshub.app/twitter/user/{}"   # 公開ノード
FEEDS += [RSSHUB.format(u) for u in TW_HANDLES]
# ===========================


def seen(cur, url: str) -> bool:
    return cur.execute("SELECT 1 FROM seen WHERE url=?", (url,)).fetchone() is not None


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS seen(url TEXT PRIMARY KEY)")

    new_items = []

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            if feed.bozo:   # RSS 解析エラー
                print("⚠️  feed parse error:", url)
                continue
            for e in feed.entries:
                link = getattr(e, "link", None)
                if not link or seen(cur, link):
                    continue
                title   = getattr(e, "title", "No title")
                summary = getattr(e, "summary", getattr(e, "description", ""))[:1000]
                new_items.append({"title": title, "text": summary, "link": link})
                cur.execute("INSERT INTO seen VALUES(?)", (link,))
        except Exception as err:
            # RSSHub が 429/502 の時など、エラー内容を出力してスキップ
            print("⚠️  error fetching", url, "->", err.__class__.__name__)
            traceback.print_exc()

    conn.commit()
    conn.close()

    # 最新 MAX_PER_DAY 件だけ保存
    pathlib.Path(OUT).write_text(
        json.dumps(new_items[:MAX_PER_DAY], ensure_ascii=False, indent=2)
    )
    print(f"Fetched {len(new_items)} new items")


if __name__ == "__main__":
    main()
