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
RESULTS_PER_QUERY = 10       # 每组最多抓几条
DELAY_BETWEEN_QUERIES = 1.2  # 秒，避免触发限速

# ── 搜索组配置 ────────────────────────────────────────────────────────────────
# 每组：(query, freshness)
# freshness: "pd"=过去1天, "pw"=过去1周, "pm"=过去1月, None=不限
SEARCH_GROUPS = [
    # 政治
    ("Thailand politics coalition government 2026",              "pw"),
    ("Thailand People's Party OR Pheu Thai OR Bhumjaithai 2026", "pw"),
    ("ข่าวการเมืองไทย รัฐบาล ล่าสุด",                           "pw"),
    # 经济
    ("Thailand economy GDP inflation central bank 2026",         "pw"),
    ("เศรษฐกิจไทย ล่าสุด 2569",                                 "pw"),
    # 科技基建
    ("Thailand data center cloud AI investment 2026",            "pw"),
    # 签证外籍
    ("Thailand visa expat foreigner policy 2026",               "pw"),
    # 芭提雅房产
    ('Pattaya luxury condo "Wong Amat" OR "Na Kluea" OR "North Pattaya" 2026', "pm"),
    ("พัทยาเหนือ คอนโด หรู ต่างชาติ 2569",                     "pm"),
    # 泰国房产
    ("Thailand property market luxury foreign buyer 2026",      "pw"),
    ("อสังหาริมทรัพย์ ไทย ต่างชาติ ซื้อ 2569",                 "pw"),
    # 曼谷本地
    ("Bangkok city news latest 2026",                           "pw"),
    ("Bangkok city news crime safety development 2026",         "pw"),
    # AI 泰国
    ("Thailand AI data center investment infrastructure 2026",  "pw"),
    ("Thailand artificial intelligence government education healthcare 2026", "pw"),
    # 新楼盘
    ("Bangkok new condo launch presale opening 2026",           "pw"),
]

# 触发式搜索组（仅在相关话题出现时才跑，在代码里手动添加到TRIGGERED_GROUPS）
# 目前默认不跑，如有需要在此追加
TRIGGERED_GROUPS = [
    # ("China Thailand investment railway 2026", "pw"),  # 中泰重磅时启用
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
