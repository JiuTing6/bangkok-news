#!/usr/bin/env python3
"""
translate.py — Thailand10 Translation Step
Calls OpenRouter (scanner/Gemini Flash) with JSON mode.
Python handles all file I/O. No LLM tool-calling required.

Usage:
  python3 translate.py --input <deduped.json> --output <translated.json> --date <YYYY-MM-DD>
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import date, timedelta
from pathlib import Path


# ── Config ──────────────────────────────────────────────────────────────────

MODEL = "google/gemini-3-flash-preview"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
BATCH_SIZE = 5           # items per API call (conservative; tune up if stable)
MAX_TOKENS = 8192
MAX_RETRIES = 2


SYSTEM_PROMPT = """你是泰国华文新闻翻译专员。输入是一批英文/泰文新闻条目（JSON数组），你的任务是补全每条条目的中文字段，并返回完整的 JSON 数组。

## 字段规则

### desc_original
- 直接取输入的 `desc` 字段原文，截断至500字符，原样保留不翻译
- `desc` 为空则填 ""

### title_cn
- 信达雅，不要机翻腔
- 专有名词首次出现附英文（如：披集县 Phichit、素坤逸路 Sukhumvit）

### summary_cn
- 基于 desc 提炼翻译成中文，100-150字
- 抓核心事实，结合泰国背景解读，保持客观中立
- 专有名词同 title_cn 规则
- 禁止 Markdown，纯文字
- 若 desc 为空填 ""

### importance
- P1：直接影响在泰外国人日常（政策/签证/安全/法律/物价）
- P2：基建大项目、重大楼盘、重要经济数据、奇闻要案
- P3：常规经济、促销活动、一般旅游资讯

### section_hint
- bangkok：明确发生在曼谷市内
- pattaya：明确属于芭提雅地区
- property：房产政策、大型开发商动态、外国人买房规则
- cn_thai：中泰双边关系、中国投资/游客/移民/企业在泰
- thailand：全国性政治/经济/社会新闻

### location_detail
- 最具体的地名（街区/县府/区名），无法确定则留空 ""

### tags
- 从以下选1-3个：#签证 #移民 #房产 #基建 #交通 #旅游 #中泰 #经济 #安全 #政策 #环境 #美食 #夜生活
- 无合适的留空 []

### time_sensitive / expires_date
- time_sensitive: true = 有明确时效（政策生效日、活动截止日）；false = 时效中性
- expires_date: time_sensitive=true → added_date+15天；false → added_date+30天

### 固定字段（不变）
- id, source, url, origin: 保持原值
- event_id: 生成简洁英文事件ID，如 thailand_visa_overstay_2026_03
- status: 固定 "pending"
- added_date: 由调用方注入

## 输出要求
只输出纯 JSON 数组，与输入条目一一对应，顺序不变。
"""


def load_key() -> str:
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    with open(config_path) as f:
        cfg = json.load(f)
    key = cfg.get("env", {}).get("OPENROUTER_API_KEY", "")
    if not key:
        sys.exit("❌ OPENROUTER_API_KEY not found in ~/.openclaw/openclaw.json")
    return key


def call_api(key: str, items: list, added_date: str, attempt: int = 1) -> list:
    """Send a batch of items to scanner, return translated items."""
    # Inject added_date into each item for the model's reference
    items_with_date = [{**item, "added_date": added_date} for item in items]

    payload = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"今日日期: {added_date}\n\n"
                    f"请翻译以下 {len(items)} 条新闻，返回完整 JSON 数组（字段名: items）：\n\n"
                    + json.dumps(items_with_date, ensure_ascii=False)
                ),
            },
        ],
    }

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        sys.exit(f"❌ API error {e.code}: {body}")

    content = result["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        if attempt <= MAX_RETRIES:
            print(f"⚠️  JSON parse error (attempt {attempt}), retrying... {e}")
            return call_api(key, items, added_date, attempt + 1)
        sys.exit(f"❌ JSON parse error after {attempt} attempts: {e}\nRaw: {content[:500]}")

    # Model returns {"items": [...]} or bare array
    if isinstance(parsed, list):
        return parsed
    elif "items" in parsed:
        return parsed["items"]
    else:
        # Try to find any list value
        for v in parsed.values():
            if isinstance(v, list):
                return v
        sys.exit(f"❌ Unexpected response shape: {list(parsed.keys())}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to deduped JSON")
    parser.add_argument("--output", required=True, help="Path to write translated JSON")
    parser.add_argument("--date", default=str(date.today()), help="YYYY-MM-DD (default: today)")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE, help="Items per API call")
    args = parser.parse_args()

    key = load_key()

    with open(args.input) as f:
        items = json.load(f)

    print(f"📥 Loaded {len(items)} items from {args.input}")

    results = []
    batches = [items[i:i+args.batch] for i in range(0, len(items), args.batch)]

    for i, batch in enumerate(batches, 1):
        print(f"🔄 Batch {i}/{len(batches)} ({len(batch)} items)...", end=" ", flush=True)
        translated = call_api(key, batch, args.date)

        # Sanity check count
        if len(translated) != len(batch):
            print(f"⚠️  count mismatch: sent {len(batch)}, got {len(translated)}")
        else:
            print("✅")

        results.extend(translated)

    # Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Stats
    p1 = sum(1 for x in results if x.get("importance") == "P1")
    p2 = sum(1 for x in results if x.get("importance") == "P2")
    p3 = sum(1 for x in results if x.get("importance") == "P3")
    print(f"✅ Written {len(results)} items to {args.output}")
    print(f"TRANSLATION_RESULT: total={len(results)} P1={p1} P2={p2} P3={p3}")


if __name__ == "__main__":
    main()
