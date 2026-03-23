#!/usr/bin/env python3
"""
dedup.py — Thailand10 Layer 2: 语义去重
Calls OpenRouter (Gemini Flash) with JSON mode.
Python handles all file I/O. No LLM tool-calling required.

Usage:
  python3 dedup.py --input <filtered.json> --pool <pool-excerpt.json> --output <deduped.json>

All non-duplicate items pass through. Topic quota control is handled at publish time.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import socket
import time
from pathlib import Path


# ── Config ──────────────────────────────────────────────────────────────────

MODEL = "google/gemini-3-flash-preview"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
BATCH_SIZE = 10          # items per API call (dedup needs pool context, batch smaller)
MAX_TOKENS = 4096
MAX_RETRIES = 2


SYSTEM_PROMPT = """你是新闻去重过滤器。给定一批候选新闻条目和现有 pool（最近10天），判断候选条目是否与 pool 重复，返回不重复的条目。

## 去重规则（按优先级）
1. URL 完全相同 → skip（直接跳过）
2. 标题语义高度重合（同一事件，同一角度，无新增信息）→ skip
3. 同一事件但有新进展/新数据/新角度 → keep（正常保留）
4. 不确定 → 偏向 keep（宁可放进来，不要漏掉）

## 注意
- Pool 摘录已限定最近10天，因此比对范围有限，不要过于保守
- 目标是去掉明显重复，不是精细语义过滤

## 输出要求
只输出纯 JSON（字段名: items），只包含 keep 的候选条目，原样保留所有原始字段。
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


def call_api(key: str, candidates: list, pool_excerpt: list, attempt: int = 1) -> list:
    """Send a batch of candidates + pool context to flash, return kept items."""
    payload = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"## 现有 Pool（最近10天，共 {len(pool_excerpt)} 条）\n"
                    + json.dumps(pool_excerpt, ensure_ascii=False)
                    + f"\n\n## 候选条目（共 {len(candidates)} 条，请判断是否与 pool 重复）\n"
                    + json.dumps(candidates, ensure_ascii=False)
                    + "\n\n返回不重复的候选条目（JSON格式，字段名 items）："
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        sys.exit(f"❌ API error {e.code}: {body}")
    except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
        if attempt <= MAX_RETRIES:
            print(f"⚠️  Network timeout/error (attempt {attempt}), retrying in 5s... {e}")
            time.sleep(5)
            return call_api(key, candidates, pool_excerpt, attempt + 1)
        sys.exit(f"❌ Network error after {attempt} attempts: {e}")

    content = result["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        if attempt <= MAX_RETRIES:
            print(f"⚠️  JSON parse error (attempt {attempt}), retrying in 5s... {e}")
            time.sleep(5)
            return call_api(key, candidates, pool_excerpt, attempt + 1)
        sys.exit(f"❌ JSON parse error after {attempt} attempts: {e}\nRaw: {content[:500]}")

    # Extract list from response
    if isinstance(parsed, list):
        return parsed
    elif "items" in parsed:
        return parsed["items"]
    else:
        for v in parsed.values():
            if isinstance(v, list):
                return v
        sys.exit(f"❌ Unexpected response shape: {list(parsed.keys())}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to filtered JSON (candidates)")
    parser.add_argument("--pool", required=True, help="Path to pool excerpt JSON")
    parser.add_argument("--output", required=True, help="Path to write deduped JSON")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE, help="Candidates per API call")
    args = parser.parse_args()

    key = load_key()

    with open(args.input) as f:
        candidates = json.load(f)

    with open(args.pool) as f:
        pool_excerpt = json.load(f)

    # Use only id, title, url from pool to save tokens
    pool_slim = [
        {"id": x.get("id", ""), "title": x.get("title_cn") or x.get("title", ""), "url": x.get("url", "")}
        for x in pool_excerpt
    ]

    total_input = len(candidates)
    print(f"📥 Loaded {total_input} candidates, {len(pool_slim)} pool items")

    results = []
    batches = [candidates[i:i+args.batch] for i in range(0, len(candidates), args.batch)]

    for i, batch in enumerate(batches, 1):
        print(f"🔄 Batch {i}/{len(batches)} ({len(batch)} candidates)...", end=" ", flush=True)
        kept = call_api(key, batch, pool_slim)
        print(f"✅ kept {len(kept)}/{len(batch)}")
        results.extend(kept)

    # Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    dedup_skip = total_input - len(results)

    # Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    kept_count = len(results)
    print(f"✅ Written {kept_count} items to {args.output}")
    print(f"DEDUP_RESULT: input={total_input} keep={kept_count} skip={dedup_skip}")


if __name__ == "__main__":
    main()
