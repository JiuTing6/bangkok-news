#!/usr/bin/env python3
"""
filter.py — Thailand10 Layer 1: 泰国相关性过滤
Calls OpenRouter (Gemini Flash) with JSON mode.
Python handles all file I/O. No LLM tool-calling required.

Usage:
  python3 filter.py --input <flat.json> --output <filtered.json>
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path


# ── Config ──────────────────────────────────────────────────────────────────

MODEL = "google/gemini-3-flash-preview"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
BATCH_SIZE = 10          # items per API call
MAX_TOKENS = 8192
MAX_RETRIES = 2


SYSTEM_PROMPT = """你是泰国相关性过滤器。输入是一批新闻条目（JSON数组），你的任务是判断每条新闻是否与泰国相关，返回过滤后的 JSON 数组。

## 保留（keep）标准
- 文章主体是泰国、发生在泰国、直接涉及泰国的政策/人/事件
- 泰国地名出现在标题或摘要中（Bangkok, Pattaya, Phuket, Chiang Mai, Koh Samui, Krabi, Hua Hin, Udon Thani, Korat, Hat Yai, Rayong, Chon Buri, Nonthaburi 等）
- 国际事件但明确涉及泰国政府/企业/民众的具体行动

## 丢弃（skip）标准
- 纯全球新闻，无泰国具体行动/数据/提及（美联储加息、中东战争、AI模型发布等）
- Wikipedia 页面、YouTube 视频、学术论文、纯广告页
- 来源极不可靠或非新闻性质

## 判断示例
- 泰国政府从中东撤侨 ✅ keep
- 泰国央行回应美联储加息对泰铢影响 ✅ keep
- 谷歌宣布在曼谷投资数据中心 ✅ keep
- 美国海军在红海护航 ❌ skip
- OpenAI 发布新模型 ❌ skip

## 输出要求
只输出纯 JSON 数组（字段名: items），只包含 keep=true 的条目，原样保留所有原始字段。
不含任何说明文字、不含代码块标记。
格式：{"items": [...]}
"""


def load_key() -> str:
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    with open(config_path) as f:
        cfg = json.load(f)
    key = cfg.get("env", {}).get("OPENROUTER_API_KEY", "")
    if not key:
        sys.exit("❌ OPENROUTER_API_KEY not found in ~/.openclaw/openclaw.json")
    return key


def call_api(key: str, items: list, attempt: int = 1) -> list:
    """Send a batch of items to flash, return kept items."""
    payload = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"请过滤以下 {len(items)} 条新闻，返回与泰国相关的条目（JSON格式，字段名 items）：\n\n"
                    + json.dumps(items, ensure_ascii=False)
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
            return call_api(key, items, attempt + 1)
        sys.exit(f"❌ JSON parse error after {attempt} attempts: {e}\nRaw: {content[:500]}")

    # Extract list from response
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
    parser.add_argument("--input", required=True, help="Path to flat JSON")
    parser.add_argument("--output", required=True, help="Path to write filtered JSON")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE, help="Items per API call")
    args = parser.parse_args()

    key = load_key()

    with open(args.input) as f:
        items = json.load(f)

    total_input = len(items)
    print(f"📥 Loaded {total_input} items from {args.input}")

    results = []
    batches = [items[i:i+args.batch] for i in range(0, len(items), args.batch)]

    for i, batch in enumerate(batches, 1):
        print(f"🔄 Batch {i}/{len(batches)} ({len(batch)} items)...", end=" ", flush=True)
        kept = call_api(key, batch)
        print(f"✅ kept {len(kept)}/{len(batch)}")
        results.extend(kept)

    # Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    kept_count = len(results)
    skip_count = total_input - kept_count
    print(f"✅ Written {kept_count} items to {args.output}")
    print(f"FILTER_RESULT: input={total_input} keep={kept_count} skip={skip_count}")


if __name__ == "__main__":
    main()
