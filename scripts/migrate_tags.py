#!/usr/bin/env python3
"""
migrate_tags.py — 存量 news_pool.json tag 迁移
- 为每条条目生成 city_tag（从 section_hint 派生）
- 为每条条目生成 topic_tag（从旧 tags 规则映射，特殊条目用 Flash 判断）
- 写回 news_pool.json
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

POOL_PATH = Path("/Users/Ade/.openclaw/workspace/bangkok-news/data/news_pool.json")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-3-flash-preview"

# ── 已知城市（5大 + 其余归 #更多地区）──
KNOWN_CITIES = {"#曼谷", "#芭提雅", "#普吉岛", "#清迈", "#泰国"}

# ── section_hint → city_tag 映射 ──
SECTION_TO_CITY = {
    "bangkok":  "#曼谷",
    "pattaya":  "#芭提雅",
    "phuket":   "#普吉岛",
    "chiangmai":"#清迈",
    "thailand": "#泰国",
    "property": "#泰国",
    "cn_thai":  "#泰国",
    "politics": "#泰国",
    "energy":   "#泰国",
    "finance":  "#泰国",
    "expat":    "#泰国",
    "other":    "#泰国",
}

# ── 旧 tag → topic_tag 规则映射 ──
TAG_MAP = {
    # 时政
    "#政策": "#时政", "#政治": "#时政", "#外交": "#时政",
    "#中东": "#时政", "#中东局势": "#时政", "#地缘政治": "#时政",
    "#地缘": "#时政", "#人民党": "#时政", "#议会": "#时政",
    "#修宪": "#时政", "#组阁": "#时政", "#国际会议": "#时政",
    "#反腐": "#时政", "#腐败": "#时政", "#辟谣": "#时政",
    "#贸易": "#时政",  # 贸易政策
    # 经济
    "#经济": "#经济", "#经济数据": "#经济", "#金融": "#经济",
    "#关税": "#经济", "#投资": "#经济", "#外资": "#经济",
    "#BOI": "#经济", "#劳工": "#经济", "#商业": "#经济",
    "#股市": "#经济", "#泰国股市": "#经济", "#SET": "#经济",
    "#银行": "#经济", "#不良贷款": "#经济", "#货币": "#经济",
    "#货币政策": "#经济", "#通胀": "#经济", "#通货膨胀": "#经济",
    "#油价": "#经济", "#燃油价格": "#经济", "#宏观经济": "#经济",
    "#营销": "#经济", "#投资趋势": "#经济", "#外籍买家": "#经济",
    "#边境贸易": "#经济",
    # 生活
    "#移民": "#生活", "#签证": "#生活", "#涉外": "#生活",
    "#外籍": "#生活", "#外国人": "#生活", "#健康": "#生活",
    "#医疗": "#生活", "#整形手术": "#生活", "#大麻": "#生活",
    "#天气": "#生活", "#养老目的地": "#生活", "#泰国移居": "#生活",
    # 社会
    "#治安犯罪": "#社会", "#犯罪": "#社会", "#谋杀": "#社会",
    "#盗窃": "#社会", "#毒品": "#社会", "#禁毒": "#社会",
    "#火灾": "#社会", "#安全事故": "#社会", "#社会治安": "#社会",
    "#社会": "#社会", "#边境": "#社会", "#人道主义": "#社会",
    "#撤离": "#社会", "#撤侨": "#社会", "#涉外犯罪": "#社会",
    "#本地奇闻": "#社会", "#警察": "#社会", "#意外": "#社会",
    "#名表盗窃": "#社会", "#豪宅安全": "#社会", "#野生动物走私": "#社会",
    "#博彩": "#社会", "#争议": "#社会",
    # 旅游
    "#旅游": "#旅游", "#旅游活动": "#旅游", "#旅游安全": "#旅游",
    "#旅游岛屿": "#旅游", "#泰国旅游": "#旅游", "#夜生活": "#旅游",
    "#美食": "#旅游", "#餐饮": "#旅游", "#活动促销": "#旅游",
    "#活动": "#旅游", "#音乐节": "#旅游", "#城市导览": "#旅游",
    "#步行城市": "#旅游", "#芭提雅音乐节": "#旅游", "#娱乐资讯": "#旅游",
    # 教育
    "#教育": "#教育", "#神童": "#教育", "#花滑": "#教育",
    "#体育": "#教育",
    # 科技
    "#科技": "#科技", "#AI应用": "#科技", "#数据中心": "#科技",
    "#智慧城市": "#科技", "#创意经济": "#科技", "#充电宝": "#科技",
    # 房产
    "#房产": "#房产", "#基建": "#房产", "#商业地产": "#房产",
    "#房产市场": "#房产", "#泰国房产": "#房产", "#开发商": "#房产",
    "#豪宅": "#房产", "#SCAsset": "#房产", "#城市建设": "#房产",
    # 文化
    "#文化": "#文化", "#美术馆": "#文化", "#艺术": "#文化",
    "#艺术博物馆": "#文化", "#展览": "#文化",
    # 安全
    "#安全": "#安全", "#交通": "#安全", "#航空": "#安全",
    "#污染": "#安全", "#环境": "#安全", "#社会安全": "#安全",
    "#英国游客": "#安全",
}

# 需要 LLM 判断的旧 tag
LLM_NEEDED_TAGS = {"#中泰", "#能源"}

# 丢弃的 tag（不参与映射）
DISCARD_TAGS = {"#追踪", "#新闻", "#PR软文", "#观点", "#生活",
                "#曼谷", "#芭提雅", "#普吉", "#清莱",
                "#北革府", "#达府", "#武里南", "#伊朗", "#土耳其",
                "#中东影响", "#地缘", "#资产避风港", "#避风港",
                "#外资", "#泰国房产", "#人民党",
                "#国际会议"}


def load_key() -> str:
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    with open(config_path) as f:
        cfg = json.load(f)
    key = cfg.get("env", {}).get("OPENROUTER_API_KEY", "")
    if not key:
        sys.exit("❌ OPENROUTER_API_KEY not found")
    return key


def call_flash(key: str, items: list) -> list:
    """Ask Flash to classify #中泰 / #能源 items into topic_tag."""
    batch_input = [
        {"idx": i, "title": it.get("title", ""), "title_cn": it.get("title_cn", ""),
         "summary_cn": it.get("summary_cn", ""), "tags": it.get("tags", [])}
        for i, it in enumerate(items)
    ]
    prompt = """你是新闻分类专员。对每条新闻，根据内容判断 topic_tag，从以下10个中选1个：
#时政 #经济 #生活 #社会 #旅游 #教育 #科技 #房产 #文化 #安全

规则：
- #中泰 标签：投资/贸易/商业 → #经济；外交/政治/移民 → #时政
- #能源 标签：能源技术/新能源/数据中心 → #科技；能源政策/油价/电价/补贴 → #经济

输入是 JSON 数组，输出也是 JSON 数组，字段：idx + topic_tag。
只输出纯 JSON 数组，无其他文字。"""

    payload = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "max_tokens": 2048,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请分类以下 {len(batch_input)} 条：\n\n" +
             json.dumps(batch_input, ensure_ascii=False)}
        ]
    }
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    content = result["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    # 可能包在 {"items": [...]} 或直接是列表
    if isinstance(parsed, dict):
        for v in parsed.values():
            if isinstance(v, list):
                return v
    return parsed


def derive_city_tag(item: dict) -> str:
    section = item.get("section_hint", "thailand")
    return SECTION_TO_CITY.get(section, "#泰国")


def derive_topic_tag_rule(item: dict) -> str | None:
    """Pure-rule mapping. Returns None if needs LLM."""
    tags = item.get("tags", [])
    # Check if any tag needs LLM
    for t in tags:
        if t in LLM_NEEDED_TAGS:
            return None  # needs LLM

    # Try rule mapping
    topic_votes: dict[str, int] = {}
    for t in tags:
        if t in DISCARD_TAGS:
            continue
        mapped = TAG_MAP.get(t)
        if mapped:
            topic_votes[mapped] = topic_votes.get(mapped, 0) + 1

    if topic_votes:
        return max(topic_votes, key=lambda k: topic_votes[k])
    return "#社会"  # fallback


def main():
    print("📂 读取 news_pool.json ...")
    with open(POOL_PATH) as f:
        pool = json.load(f)
    print(f"   共 {len(pool)} 条")

    key = load_key()

    # 分组：规则映射 vs 需要 LLM
    rule_items = []
    llm_items = []
    llm_indices = []

    for i, item in enumerate(pool):
        city_tag = derive_city_tag(item)
        item["city_tag"] = city_tag

        topic = derive_topic_tag_rule(item)
        if topic is None:
            llm_items.append(item)
            llm_indices.append(i)
        else:
            item["topic_tag"] = topic
            rule_items.append(item)

    print(f"✅ 规则映射: {len(rule_items)} 条")
    print(f"🤖 需要 LLM: {len(llm_items)} 条（#中泰 / #能源）")

    # LLM 批量处理
    if llm_items:
        print(f"🚀 调用 Flash API 处理 {len(llm_items)} 条...")
        try:
            results = call_flash(key, llm_items)
            result_map = {r["idx"]: r["topic_tag"] for r in results}
            for local_idx, pool_idx in enumerate(llm_indices):
                topic = result_map.get(local_idx, "#时政")
                pool[pool_idx]["topic_tag"] = topic
            print(f"✅ LLM 分类完成")
        except Exception as e:
            print(f"⚠️  LLM 调用失败: {e}，用规则兜底（#时政）")
            for pool_idx in llm_indices:
                pool[pool_idx]["topic_tag"] = "#时政"

    # 统计
    from collections import Counter
    city_counts = Counter(item.get("city_tag", "?") for item in pool)
    topic_counts = Counter(item.get("topic_tag", "?") for item in pool)

    print("\n=== city_tag 分布 ===")
    for k, v in city_counts.most_common():
        print(f"  {k}: {v}")

    print("\n=== topic_tag 分布 ===")
    for k, v in topic_counts.most_common():
        print(f"  {k}: {v}")

    # 写回
    print(f"\n💾 写回 news_pool.json ...")
    with open(POOL_PATH, "w") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)
    print("✅ 迁移完成！")


if __name__ == "__main__":
    main()
