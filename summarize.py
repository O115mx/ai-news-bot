import json, pathlib, torch
from transformers import pipeline

model_name = "facebook/bart-large-cnn"   # CPU OK
summarizer = pipeline("summarization", model=model_name, device=-1)

items = json.loads(pathlib.Path("items.json").read_text())
briefs = []
for it in items:
    try:
        s = summarizer(it["text"], max_length=60, min_length=25, do_sample=False)[0]["summary_text"]
    except Exception:
        s = it["text"][:120]  # 要約失敗時は冒頭だけ
    briefs.append({**it, "summary": s})

pathlib.Path("briefs.json").write_text(json.dumps(briefs, ensure_ascii=False))
