#!/usr/bin/env python3
"""
migrate_tags_v2_topics.py — Topic tag 合并：10→9
  #旅游 → #旅居
  #生活 → #旅居
  #文化 → #旅居
  #教育 → #旅居
  #健康 → #健康（保持，现在是独立 topic）
"""

import json
from collections import Counter
from pathlib import Path

POOL_PATH = Path("/Users/Ade/.openclaw/workspace/bangkok-news/data/news_pool.json")

MERGE_MAP = {
    "#旅游": "#旅居",
    "#生活": "#旅居",
    "#文化": "#旅居",
    "#教育": "#旅居",
}

def main():
    print("📂 读取 news_pool.json ...")
    with open(POOL_PATH) as f:
        pool = json.load(f)
    print(f"   共 {len(pool)} 条")

    before = Counter(item.get("topic_tag", "?") for item in pool)
    print("\n=== 迁移前 topic_tag 分布 ===")
    for k, v in before.most_common():
        print(f"  {k}: {v}")

    changed = 0
    for item in pool:
        old = item.get("topic_tag", "")
        new = MERGE_MAP.get(old)
        if new:
            item["topic_tag"] = new
            changed += 1

    after = Counter(item.get("topic_tag", "?") for item in pool)
    print(f"\n✅ 迁移条目: {changed} 条")
    print("\n=== 迁移后 topic_tag 分布 ===")
    for k, v in after.most_common():
        print(f"  {k}: {v}")

    print(f"\n💾 写回 news_pool.json ...")
    with open(POOL_PATH, "w") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)
    print("✅ 完成！")

if __name__ == "__main__":
    main()
