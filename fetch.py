import feedparser, sqlite3, datetime, pathlib, json, traceback, requests

# ========= 設定 =========
MAX_PER_DAY = 10   # 例えば10件に増やす
DB  = "seen.db"
OUT = "items.json"

FEEDS = [
    # ── 論文 ─────────────────────
    "https://export.arxiv.org/rss/cs.LG",

    # ── 国内ニュース ─────────────
    "https://news.mynavi.jp/techplus/rss",
    "https://atmarkit.itmedia.co.jp/rss/all.rdf",
    "https://metaversesouken.com/ai/feed",
    "https://ledge.ai/feed/",
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

    # ── Qiita タグ ────────────────
    "https://qiita.com/tags/GenerativeAI/feed",
]

# --- Twitter は RSSHub 経由で ---
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
FEEDS += [RSSHUB.format(u) for u in TW_HANDLES]
# =========================



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
