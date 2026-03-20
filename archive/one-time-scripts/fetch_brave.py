#!/usr/bin/env python3
"""
Thailand10 Brave Search 抓取工具
用法：python3 fetch_brave.py <raw.json路径>
功能：运行所有预设搜索组，将结果追加写入 raw.json 的 brave_results 字段

Brave Search API: https://api.search.brave.com/res/v1/web/search
"""

import json
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ── API 配置 ──────────────────────────────────────────────────────────────────
BRAVE_API_KEY = "BSA2h45NgEAJZRtc7IjJJOO-L1FBgOs"
BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
RESULTS_PER_QUERY = 8        # 每组最多抓几条
DELAY_BETWEEN_QUERIES = 1.2  # 秒，避免触发限速

# ── 搜索组配置 ────────────────────────────────────────────────────────────────
# 定位：补娱乐活动料 —— 音乐节、烟花秀、节日庆典、艺术展、购物节
# 主力新闻由RSS覆盖，Brave专注活动资讯（RSS很少报）
# 每组：(query, freshness)
# freshness: "pd"=过去1天, "pw"=过去1周, "pm"=过去1月, None=不限
# 2026-03-08 v3: 专注娱乐活动，每期至少选1条
SEARCH_GROUPS = [
    # 音乐节 + 演唱会
    ("Thailand music festival concert Bangkok Pattaya 2026 -site:wikipedia.org -site:youtube.com", "pw"),
    # 烟花秀 + 节日庆典（泼水节/跨年/国王生日）
    ("Thailand fireworks Songkran New Year celebration Bangkok Pattaya 2026 -site:wikipedia.org -site:youtube.com", "pw"),
    # 艺术展 + 博物馆 + 文化活动
    ("Bangkok Pattaya art exhibition museum cultural event 2026 -site:wikipedia.org -site:youtube.com", "pw"),
    # 购物节 + 促销 + 展会
    ("Thailand shopping festival fair expo Bangkok 2026 -site:wikipedia.org -site:youtube.com", "pw"),
]

# 触发式搜索组（仅在相关话题出现时才跑）
# 特定节日或大型活动前后启用
TRIGGERED_GROUPS = [
    # ("Songkran 2026 Thailand festival event -site:wikipedia.org", "pw"),
    # ("Bangkok Art Biennale 2026 -site:wikipedia.org", "pw"),
]


def brave_search(query: str, freshness: str = None, count: int = RESULTS_PER_QUERY) -> list:
    """调用 Brave Search API，返回结果列表"""
    params = {
        "q": query,
        "count": count,
        "text_decorations": "false",
        "search_lang": "en",
        "spellcheck": "false",
    }
    if freshness:
        params["freshness"] = freshness

    url = BRAVE_API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_bytes = resp.read()
            # 处理 gzip 压缩（服务器可能自动压缩）
            if raw_bytes[:2] == b'\x1f\x8b':
                import gzip
                raw_bytes = gzip.decompress(raw_bytes)
            data = json.loads(raw_bytes.decode("utf-8"))

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title":   item.get("title", ""),
                "url":     item.get("url", ""),
                "snippet": item.get("description", ""),
                "age":     item.get("age", ""),
            })
        return results

    except Exception as e:
        print(f"[WARN] Brave search failed: {query[:50]} → {e}", file=sys.stderr)
        return []


def main():
    if len(sys.argv) < 2:
        print("用法: python3 fetch_brave.py <raw.json路径>", file=sys.stderr)
        sys.exit(1)

    raw_path = sys.argv[1]

    # 读取现有 raw.json
    try:
        with open(raw_path, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        print(f"[ERROR] 无法读取 {raw_path}: {e}", file=sys.stderr)
        sys.exit(1)

    all_groups = SEARCH_GROUPS + TRIGGERED_GROUPS
    brave_results = []
    total_results = 0

    for i, (query, freshness) in enumerate(all_groups, 1):
        print(f"[{i}/{len(all_groups)}] {query[:60]}", file=sys.stderr)
        results = brave_search(query, freshness)
        brave_results.append({
            "query":     query,
            "freshness": freshness,
            "count":     len(results),
            "results":   results,
        })
        total_results += len(results)
        if i < len(all_groups):
            time.sleep(DELAY_BETWEEN_QUERIES)

    # 追加写入 raw.json
    raw["brave_results"] = brave_results
    raw["brave_fetched_at"] = datetime.now(timezone.utc).isoformat()
    raw["brave_total"] = total_results

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    print(f"[OK] Brave搜索完成：{len(all_groups)}组，{total_results}条结果 → {raw_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
