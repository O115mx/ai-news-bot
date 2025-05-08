import feedparser
import sqlite3
import datetime
import pathlib
import json
import traceback

# =========  設定  =========
MAX_PER_DAY = 10            # Slack に送る最大件数
DB_FILE     = "seen.db"
OUT_FILE    = "items.json"

# --- 収集したい RSS フィード ---
FEEDS = [
    # arXiv
    "https://export.arxiv.org/rss/cs.LG",

    # 国内ニュース・ブログ
    "https://news.mynavi.jp/techplus/rss",
    "https://atmarkit.itmedia.co.jp/rss/all.rdf",
    "https://ledge.ai/feed/",
    "https://metaversesouken.com/ai/feed",
    "https://www.sbbit.jp/rss/all",
    "https://xtech.nikkei.com/rss/pickup.rdf",
    "https://www.itmedia.co.jp/rss/2.0/itmedia_all.xml",
    "https://japan.cnet.com/rss/index.rdf",
    "https://japan.zdnet.com/rss/index.rdf",
    "https://thebridge.jp/feed",
    "https://it.impress.co.jp/rss/atom.xml",
    "https://ainow.ai/feed",
    "https://aismiley.co.jp/feed",
    "https://chatgpt-lab.com/feed",

    # Qiita タグ例
    "https://qiita.com/tags/GenerativeAI/feed",
]

# --- Twitter を RSSHub 経由で追加 ---
TW_HANDLES = [
    "taiyo_ai_gakuse",
    "ytiskw",
    "Aoi_genai",
    "usutaku_channel",
    "SuguruKun_ai",
    "shota7180",
    "MacopeninSUTABA",
]
RSSHUB = "https://rsshub.app/twitter/user/{}"
FEEDS.extend([RSSHUB.format(u) for u in TW_HANDLES])
# ===============================


def seen(cur, url: str) -> bool:
    """URL が既に DB にあれば True"""
    return cur.execute("SELECT 1 FROM seen WHERE url=?", (url,)).fetchone() is not None


def main():
    # --- DB 準備 ---
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS seen(url TEXT PRIMARY KEY)")

    new_items = []

    # --- フィード巡回 ---
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)

            # entries が 0 のフィードはスキップ
            if not feed.entries:
                print("⚠️  empty feed:", url)
                continue

            for e in feed.entries:
                link = getattr(e, "link", None)
                if not link or seen(cur, link):
                    continue

                title   = getattr(e, "title", "No title")
                summary = (
                    getattr(e, "summary", getattr(e, "description", ""))[:1000]
                )

                new_items.append(
                    {"title": title, "text": summary, "link": link}
                )
                cur.execute("INSERT INTO seen VALUES(?)", (link,))

        except Exception as err:
            # フィード取得エラーは警告表示だけで継続
            print("⚠️  error fetching", url, "->", err.__class__.__name__)
            traceback.print_exc()

    conn.commit()
    conn.close()

    # --- 後工程用に保存 ---
    pathlib.Path(OUT_FILE).write_text(
        json.dumps(new_items[:MAX_PER_DAY], ensure_ascii=False, indent=2)
    )
    print(f"Fetched {len(new_items)} new items")


if __name__ == "__main__":
    main()
