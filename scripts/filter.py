#!/usr/bin/env python3
"""
filter.py — Thailand10 Layer 1: 泰国相关性过滤 + topic 分类
Calls OpenRouter (Gemini Flash) with JSON mode.
Python handles all file I/O. No LLM tool-calling required.

Usage:
  python3 filter.py --input <flat.json> --output <filtered.json>

Output: filtered items with topic_tag + relevance_score added.
Items with relevance_score < 0.4 are dropped.
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
BATCH_SIZE = 10          # items per API call
MAX_TOKENS = 8192
MAX_RETRIES = 2
RELEVANCE_THRESHOLD = 0.4  # 低于此分数直接淘汰

VALID_TOPICS = {
    "#时政", "#经济", "#治安", "#旅居", "#社会",
    "#房产", "#科技", "#中泰", "#健康"
}

SYSTEM_PROMPT = """你是泰国新闻分类过滤器。输入是一批新闻条目（JSON数组），你的任务是：
1. 判断每条新闻是否与泰国本地相关
2. 对相关新闻归入topic分类，并给出相关度评分

## 9个Topic定义
- #时政：泰国政治/外交/地缘/政府决策
- #经济：宏观经济/金融/贸易/能源价格/BOI/投资
- #治安：犯罪/交通事故/灾害/骗局预警/污染/环境安全
- #旅居：旅游/生活/美食/文化/教育/签证移民/健康日常/旅游活动
- #社会：社会事件/奇闻/人情味故事/争议/普通社会新闻
- #房产：房地产/基建/开发商/买房政策/商业地产
- #科技：AI/新能源技术/数据中心/智慧城市/科技产业
- #中泰：中泰双边关系/中国在泰投资/华人社区/中国游客
- #健康：医疗/食品安全/公共卫生/药品/流行病

## 丢弃标准（直接设 relevance_score=0.0）
- 纯全球新闻，无泰国具体行动/数据/提及（美联储加息、中东战争、AI模型发布等）
- Wikipedia 页面、YouTube 视频、学术论文、纯广告页
- 来源极不可靠或非新闻性质

## relevance_score 评分标准
- 1.0：核心泰国新闻，标题即泰国本地事件
- 0.7-0.9：明确涉及泰国的重要新闻
- 0.4-0.6：泰国相关但较边缘或间接
- 0.1-0.3：极弱相关（不会入库，但打分参考）
- 0.0：完全不相关

## 特定来源偏向
- source_id == "thaiheadlines"（泰国头条新闻，中文媒体）：内容多为中泰关系、华人社区、中国在泰投资/旅游。**优先归入 #中泰**，除非内容明确与中国/华人无关（如纯泰国政治、自然灾害等）。

## 判断示例
- 泰国政府从中东撤侨 → #时政, 0.9
- 谷歌宣布在曼谷投资数据中心 → #科技, 0.85
- 泰央行回应美联储加息对泰铢影响 → #经济, 0.75
- 普吉岛著名餐厅获得米其林星 → #旅居, 0.8
- 曼谷一外籍男子因毒品被捕 → #治安, 0.85
- 美国海军在红海护航（无泰国内容）→ 不相关, 0.0
- OpenAI 发布新模型（无泰国内容）→ 不相关, 0.0
- [thaiheadlines] 千人沉浸式观影《镖人》把中国武侠带火到泰国 → #中泰, 0.8
- [thaiheadlines] 泰国免签政策调整 → #旅居, 0.85（与中国无关，不强制#中泰）

## 输出格式
对每条输入，输出包含以下字段（在原始字段基础上新增）：
- topic_tag: 9个topic之一，不相关则填 null
- relevance_score: 0.0-1.0

只输出纯 JSON，格式：{"items": [...]}，无代码块标记，无说明文字。
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
    """Send a batch of items to flash, return all items with topic_tag + relevance_score added."""
    payload = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"请对以下 {len(items)} 条新闻进行分类评分，返回JSON（字段名 items）：\n\n"
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        sys.exit(f"❌ API error {e.code}: {body}")
    except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
        if attempt <= MAX_RETRIES:
            print(f"⚠️  Network timeout/error (attempt {attempt}), retrying in 5s... {e}")
            time.sleep(5)
            return call_api(key, items, attempt + 1)
        sys.exit(f"❌ Network error after {attempt} attempts: {e}")

    content = result["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        if attempt <= MAX_RETRIES:
            print(f"⚠️  JSON parse error (attempt {attempt}), retrying in 5s... {e}")
            time.sleep(5)
            return call_api(key, items, attempt + 1)
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
    parser.add_argument("--input", required=True, help="Path to flat JSON")
    parser.add_argument("--output", required=True, help="Path to write filtered JSON")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE, help="Items per API call")
    args = parser.parse_args()

    key = load_key()

    with open(args.input) as f:
        items = json.load(f)

    total_input = len(items)
    print(f"📥 Loaded {total_input} items from {args.input}")

    all_scored = []
    batches = [items[i:i+args.batch] for i in range(0, len(items), args.batch)]

    for i, batch in enumerate(batches, 1):
        print(f"🔄 Batch {i}/{len(batches)} ({len(batch)} items)...", end=" ", flush=True)
        scored = call_api(key, batch)
        print(f"✅ scored {len(scored)}/{len(batch)}")
        all_scored.extend(scored)

    # Apply relevance threshold filter
    kept = []
    low_relevance = 0
    no_topic = 0
    for item in all_scored:
        score = item.get("relevance_score", 0.0)
        topic = item.get("topic_tag")

        # Validate topic
        if topic and topic not in VALID_TOPICS:
            topic = None
            item["topic_tag"] = None

        if score < RELEVANCE_THRESHOLD or not topic:
            if score < RELEVANCE_THRESHOLD:
                low_relevance += 1
            else:
                no_topic += 1
            continue

        kept.append(item)

    # Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    kept_count = len(kept)
    skip_count = total_input - kept_count
    print(f"✅ Written {kept_count} items to {args.output}")
    print(f"FILTER_RESULT: input={total_input} keep={kept_count} skip={skip_count} "
          f"(low_relevance={low_relevance} no_topic={no_topic})")


if __name__ == "__main__":
    main()
