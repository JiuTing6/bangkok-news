#!/usr/bin/env python3
"""
One-shot ingest script for 2026-03-08
"""
import json, hashlib, shutil, os
from datetime import date, timedelta

TODAY = date(2026, 3, 8)
TODAY_STR = "2026-03-08"
RAW_FILE = "data/issues/2026-03-08-raw.json"
POOL_FILE = "data/news_pool.json"
HISTORY_FILE = "data/published_history.json"
ARCHIVE_DIR = "data/archive"

with open(RAW_FILE) as f:
    raw = json.load(f)

with open(POOL_FILE) as f:
    pool = json.load(f)

with open(HISTORY_FILE) as f:
    hist = json.load(f)

# Build dedup sets
pool_urls = {x.get("url", "") for x in pool}
pool_titles = {x.get("title_cn", "") for x in pool}
hist_titles = set()
if isinstance(hist, dict):
    for k, v in hist.items():
        if k.startswith("_") or k == "entries":
            continue
        if isinstance(v, dict):
            t = v.get("title", "") or v.get("title_cn", "")
            if t:
                hist_titles.add(t)
    for e in hist.get("entries", []):
        if isinstance(e, dict):
            t = e.get("title", "") or e.get("title_cn", "")
            if t:
                hist_titles.add(t)

def expires(ts):
    days = 15 if ts else 30
    return (TODAY + timedelta(days=days)).strftime("%Y-%m-%d")

# Manually curated entries after filtering, dedup, and annotation
new_entries = [
    {
        "id": "9be737db28e1",
        "title_cn": "战火冲击波：中东局势下泰国能源与供应链的多重压力与应对",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#能源", "#经济数据"],
        "source": "Bangkok Post",
        "url": "https://www.bangkokpost.com/thailand/special-reports/3212173/easing-the-shock-of-war",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "a7e44728508c",
        "title_cn": "🔄 泰国启动从伊朗撤离行动，首批公民已开始离境（3月8日更新）",
        "importance": "P1",
        "section_hint": "thailand",
        "tags": ["#安全", "#外交", "#追踪"],
        "source": "Bangkok Post",
        "url": "https://www.bangkokpost.com/thailand/general/3212158/thais-begin-evacuations-from-iran",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "c8e451017729",
        "title_cn": "大选后续：最高行政法院仍在审查18起选举及公投相关案件",
        "importance": "P3",
        "section_hint": "thailand",
        "tags": ["#政治"],
        "source": "Bangkok Post",
        "url": "https://www.bangkokpost.com/thailand/politics/3212058/18-poll-cases-still-under-review",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "403b1415340f",
        "title_cn": "中东紧张局势推高泰国化肥价格，孔敬（Khon Kaen）调查显示尿素（Urea）零售价大幅上涨",
        "importance": "P3",
        "section_hint": "thailand",
        "tags": ["#经济数据", "#能源"],
        "source": "Bangkok Post",
        "url": "https://www.bangkokpost.com/thailand/general/3212193/fertiliser-prices-rise-amid-middle-east-tensions",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "971f4bfdca49",
        "title_cn": "入学考现金扔垃圾桶事件：玛希隆附属学校（Matthayom）入学考严苛规定引发全国争议",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#教育", "#本地奇闻"],
        "source": "Bangkok Post",
        "url": "https://www.bangkokpost.com/thailand/general/3211960/cashinthetrash-chaos-at-entrance-exam",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "f97d7da3607e",
        "title_cn": "改革授权遭遇政治现实：泰国选后联合政府组建进程与政策改革承诺之间的张力",
        "importance": "P3",
        "section_hint": "thailand",
        "tags": ["#政治"],
        "source": "Bangkok Post",
        "url": "https://www.bangkokpost.com/thailand/politics/3211775/reform-mandate-meets-political-reality",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "4f89758c1941",
        "title_cn": "专家呼吁尽速组建新'危机政府'，以应对中东冲击、油价飙升和经济多重压力",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#政治"],
        "source": "Bangkok Post",
        "url": "https://www.bangkokpost.com/thailand/politics/3211470/experts-urge-swift-new-crisis-government",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "fe85c8e5daa0",
        "title_cn": "普吉府着力解决13万外籍劳工工作许可证（Work Permit）积压问题，省级办公室加快审批",
        "importance": "P1",
        "section_hint": "thailand",
        "tags": ["#签证", "#政策"],
        "source": "The Thaiger",
        "url": "https://thethaiger.com/news/phuket/phuket-tackles-work-permit-delays-for-130000-foreign-workers",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "db27a6e8dc98",
        "title_cn": "🔄 泰国将战略石油储备提升至可用95天，应对中东局势持续紧张的能源安全威胁",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#能源", "#政策", "#追踪"],
        "source": "The Thaiger",
        "url": "https://thethaiger.com/news/national/thailand-boosts-oil-reserves-to-last-95-days-amid-middle-east-tensions",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "beca37e73ca3",
        "title_cn": "芭提雅市长巡视流浪狗收容所，计划建设30莱（Rai）新设施应对收容量增长",
        "importance": "P3",
        "section_hint": "pattaya",
        "tags": ["#本地奇闻"],
        "source": "Pattaya Mail",
        "url": "https://www.pattayamail.com/news/pattaya-mayor-checks-on-stray-dogs-at-city-shelter-plans-new-30-rai-facility-for-growing-numbers",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(False),
        "time_sensitive": False,
        "status": "pending"
    },
    {
        "id": "5ec934a5e720",
        "title_cn": "泰国特别调查局（DSI）破获与政界人士有关联的百亿铢网络赌博（Online Gambling）网络",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#治安犯罪", "#政治"],
        "source": "The Thaiger",
        "url": "https://thethaiger.com/news/national/dsi-uncovers-billion-baht-online-gambling-network-linked-to-politician",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "d378383d986d",
        "title_cn": "2026芭提雅音乐节（Pattaya Music Festival）首周末正式开幕，多部门联动保障安保",
        "importance": "P3",
        "section_hint": "pattaya",
        "tags": ["#活动促销", "#旅游"],
        "source": "Pattaya Mail",
        "url": "https://www.pattayamail.com/news/security-in-place-as-pattaya-music-festival-2026-kicks-off-its-first-weekend",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "caa63b8d4295",
        "title_cn": "泰国是否计划'向游客发钱'？旅游补贴方案传言引发社交媒体热议与官方澄清",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#旅游", "#政策"],
        "source": "Pattaya Mail",
        "url": "https://www.pattayamail.com/latestnews/news/is-thailand-planning-to-give-money-to-tourists",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "9272b9e3e4cf",
        "title_cn": "芭提雅将学生及教师安全列为首要任务，市政当局对校车（School Bus）车队开展安全检查",
        "importance": "P3",
        "section_hint": "pattaya",
        "tags": ["#教育", "#安全"],
        "source": "Pattaya Mail",
        "url": "https://www.pattayamail.com/news/pattaya-says-safety-of-students-and-teachers-is-a-top-priority-as-school-bus-fleet-inspected",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(False),
        "time_sensitive": False,
        "status": "pending"
    },
    {
        "id": "5347ed72e343",
        "title_cn": "俄罗斯男子在芭提雅Jomtien区因涉嫌非法大麻（Cannabis）加工被捕",
        "importance": "P2",
        "section_hint": "pattaya",
        "tags": ["#治安犯罪"],
        "source": "Pattaya Mail",
        "url": "https://www.pattayamail.com/news/russian-man-arrested-in-pattaya-for-alleged-illegal-cannabis-processing-operation",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "d58ab3029ae9",
        "title_cn": "气象局发布旱季强对流天气预警：雷暴大风即将袭击全泰国，请注意防范",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#安全"],
        "source": "The Thaiger",
        "url": "https://thethaiger.com/news/national/thailand-braces-for-summer-storm-with-thunderstorms-and-strong-winds",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "e6de0c1e034d",
        "title_cn": "开战六天后：泰国为何应拒绝美国主导的'丛林法则'外交逻辑（考索英文评论）",
        "importance": "P3",
        "section_hint": "thailand",
        "tags": ["#外交", "#政治"],
        "source": "Khaosod English",
        "url": "https://www.khaosodenglish.com/featured/2026/03/06/why-it-matters-for-thais-and-thailand-to-say-no-to-the-us-led-rule-of-the-jungle",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "a206d8adf666",
        "title_cn": "北柳府（Chachoengsao）Ban Pho区稀释剂（Thinner）化工厂发生大火并伴随爆炸",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#安全"],
        "source": "Khaosod English",
        "url": "https://www.khaosodenglish.com/featured/2026/03/06/factory-fire-with-explosions-erupts-at-thinner-plant-in-chachoengsao",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "fe2f6f015ca0",
        "title_cn": "泰国移民局（Immigration）反驳柬埔寨媒体关于游客在泰遭受不当对待的报道",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#签证", "#外交"],
        "source": "Khaosod English",
        "url": "https://www.khaosodenglish.com/news/2026/03/06/thai-immigration-slams-cambodian-media-over-tourist-mistreatment-claims",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "66607defd286",
        "title_cn": "两名泰国女性在台湾因走私海洛因（Heroin）被判处监禁",
        "importance": "P3",
        "section_hint": "thailand",
        "tags": ["#治安犯罪"],
        "source": "The Thaiger",
        "url": "https://thethaiger.com/news/national/2-thai-women-jailed-in-taiwan-for-heroin-smuggling",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(False),
        "time_sensitive": False,
        "status": "pending"
    },
    {
        "id": "a5167fc4a6a0",
        "title_cn": "巴西籍毒品配送嫌疑人在帕岸岛（Koh Pha Ngan）被移民警察逮捕",
        "importance": "P2",
        "section_hint": "thailand",
        "tags": ["#治安犯罪"],
        "source": "The Thaiger",
        "url": "https://thethaiger.com/news/national/brazilian-drug-delivery-suspect-arrested-koh-pha-ngan",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "522b4ef2a25f",
        "title_cn": "泰中投资论坛吸引逾800名投资者参与，泰国投资促进委员会（BOI）联合中国大使馆主办",
        "importance": "P2",
        "section_hint": "cn_thai",
        "tags": ["#中泰", "#经济数据"],
        "source": "Khaosod English",
        "url": "https://www.khaosodenglish.com/news/business/2026/03/06/thailand-china-investment-forum-draws-over-800-investors",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(False),
        "time_sensitive": False,
        "status": "pending"
    },
    {
        "id": "50d7d27f01ac",
        "title_cn": "本周末曼谷精选：3月7至8日五大活动推荐",
        "importance": "P3",
        "section_hint": "bangkok",
        "tags": ["#活动促销", "#旅游"],
        "source": "The Thaiger",
        "url": "https://thethaiger.com/guides/best-of/things-to-do/things-to-do-bangkok-march-7-to-8",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "192ba498c562",
        "title_cn": "曼谷都市电力局（MEA）叫停内部通讯系统，起因遥控摩托车（Remote Key Motorbike）大规模异常失控",
        "importance": "P3",
        "section_hint": "bangkok",
        "tags": ["#本地奇闻", "#科技"],
        "source": "The Thaiger",
        "url": "https://thethaiger.com/news/national/mea-shuts-down-device-bangkok-remote-key-motorbikes-issues",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "4fbae4a37c6f",
        "title_cn": "甲米（Krabi）蔻兰塔岛（Koh Lanta）两名外国男子逃单加油费后失联，车主报警追查",
        "importance": "P3",
        "section_hint": "thailand",
        "tags": ["#治安犯罪"],
        "source": "The Thaiger",
        "url": "https://thethaiger.com/news/krabi/2-foreign-men-refuel-at-koh-lanta-fuel-dispenser-and-leave-without-paying",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "f3dc8439ab76",
        "title_cn": "曼谷一名跨性别女性因抢劫韩国游客被捕，警方追查后续同伙",
        "importance": "P2",
        "section_hint": "bangkok",
        "tags": ["#治安犯罪"],
        "source": "The Thaiger Bangkok",
        "url": "https://thethaiger.com/news/national/transwoman-nabbed-bangkok-south-korean-tourist-robbery",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(True),
        "time_sensitive": True,
        "status": "pending"
    },
    {
        "id": "92f88b530df1",
        "title_cn": "曼谷唐人街（Chinatown）奇事：女子约会App相遇对象却被派去完成Line Man外卖配送任务",
        "importance": "P3",
        "section_hint": "bangkok",
        "tags": ["#本地奇闻"],
        "source": "The Thaiger Bangkok",
        "url": "https://thethaiger.com/news/national/bangkok-dating-app-meetup-line-man-delivery-run",
        "origin": "rss",
        "added_date": TODAY_STR,
        "expires_date": expires(False),
        "time_sensitive": False,
        "status": "pending"
    },
]

# Filter out entries already in pool by URL
existing_urls = {x.get("url", "") for x in pool}
filtered_entries = []
skipped_urls = []
for e in new_entries:
    if e["url"] in existing_urls:
        skipped_urls.append(e["title_cn"][:50])
    else:
        filtered_entries.append(e)

print(f"Skipped (already in pool): {len(skipped_urls)}")
for s in skipped_urls:
    print(f"  - {s}")

print(f"New entries to add: {len(filtered_entries)}")

# Archive expired entries
os.makedirs(ARCHIVE_DIR, exist_ok=True)
today_obj = TODAY
active_pool = []
archived = []
for item in pool:
    exp = item.get("expires_date", "")
    if exp and exp < TODAY_STR:
        archived.append(item)
    else:
        active_pool.append(item)

if archived:
    archive_key = TODAY_STR[:7]  # YYYY-MM
    archive_file = f"{ARCHIVE_DIR}/{archive_key}.json"
    existing_archive = []
    if os.path.exists(archive_file):
        with open(archive_file) as f:
            existing_archive = json.load(f)
    existing_archive.extend(archived)
    with open(archive_file, "w") as f:
        json.dump(existing_archive, f, ensure_ascii=False, indent=2)
    print(f"Archived {len(archived)} expired entries to {archive_file}")

# Add new entries
active_pool.extend(filtered_entries)

# Sort by added_date descending
active_pool.sort(key=lambda x: x.get("added_date", ""), reverse=True)

# Write back
with open(POOL_FILE, "w") as f:
    json.dump(active_pool, f, ensure_ascii=False, indent=2)

# Stats
p1 = sum(1 for x in filtered_entries if x["importance"] == "P1")
p2 = sum(1 for x in filtered_entries if x["importance"] == "P2")
p3 = sum(1 for x in filtered_entries if x["importance"] == "P3")
sections = {}
for x in filtered_entries:
    s = x["section_hint"]
    sections[s] = sections.get(s, 0) + 1

print(f"\n[INGEST 2026-03-08] RSS: 32条原料，Brave: 1条原料，新入库: {len(filtered_entries)}条，过滤/去重: {32 + 1 - len(filtered_entries)}条，pool总量: {len(active_pool)}条")
print(f"重要性：P1={p1} | P2={p2} | P3={p3}")
print(f"板块：" + " | ".join(f"{k}={v}" for k, v in sorted(sections.items())))
