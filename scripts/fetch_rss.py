#!/usr/bin/env python3
"""
Thailand10 RSS 抓取工具
用法：python3 fetch_rss.py [days]
输出：JSON格式的原始新闻条目
"""

import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
import hashlib
import re
from datetime import datetime, timezone, timedelta

DAYS_BACK = int(sys.argv[1]) if len(sys.argv) > 1 else 4

RSS_SOURCES = [
    {
        "id": "bangkokpost_top",
        "name": "Bangkok Post",
        "url": "https://www.bangkokpost.com/rss/data/topstories.xml",
        "weight": 5
    },
    {
        "id": "bangkokpost_property",
        "name": "Bangkok Post Property",
        "url": "https://www.bangkokpost.com/rss/data/property.xml",
        "weight": 5
    },
    {
        "id": "thaiger",
        "name": "The Thaiger",
        "url": "https://thethaiger.com/feed",
        "weight": 4
    },
    {
        "id": "thaiger_bangkok",
        "name": "The Thaiger Bangkok",
        "url": "https://thethaiger.com/news/bangkok/feed",
        "weight": 5
    },
    {
        "id": "khaosod",
        "name": "Khaosod English",
        "url": "https://www.khaosodenglish.com/feed/",
        "weight": 4
    },
    {
        "id": "nation",
        "name": "The Nation",
        "url": "https://www.nationthailand.com/rss.xml",
        "weight": 4
    },
    {
        "id": "pattaya_mail",
        "name": "Pattaya Mail",
        "url": "https://www.pattayamail.com/feed",
        "weight": 4
    }
]

def make_hash(title, url):
    s = f"{title.strip().lower()}|{url.strip()}"
    return hashlib.md5(s.encode()).hexdigest()[:12]

def parse_rss_date(date_str):
    """解析 RSS pubDate 格式"""
    if not date_str:
        return None
    date_str = date_str.strip()
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%d %b %Y %H:%M:%S %z",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return None

def strip_html(text):
    """简单去除HTML标签"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()[:600]

def fetch_rss(source):
    items = []
    try:
        req = urllib.request.Request(
            source["url"],
            headers={"User-Agent": "Bangkok-News-Bot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
        root = ET.fromstring(content)
        ns = {"content": "http://purl.org/rss/1.0/modules/content/"}

        cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)

        for item in root.findall(".//item"):
            title_el  = item.find("title")
            link_el   = item.find("link")
            date_el   = item.find("pubDate")
            desc_el   = item.find("description")
            cats      = [c.text for c in item.findall("category") if c.text]

            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            link  = link_el.text.strip()  if link_el  is not None and link_el.text  else ""
            if not title or not link:
                continue

            # 跳过德文内容（Pattaya Blatt）
            if "Pattaya Blatt" in str(cats) or "Deutsch" in str(cats):
                continue

            pub_date = parse_rss_date(date_el.text if date_el is not None else "")
            if pub_date and pub_date < cutoff:
                continue

            desc = ""
            if desc_el is not None and desc_el.text:
                desc = strip_html(desc_el.text)
            content_el = item.find("content:encoded", ns)
            if content_el is not None and content_el.text:
                desc = strip_html(content_el.text)[:600]

            items.append({
                "id":      make_hash(title, link),
                "source":  source["name"],
                "source_id": source["id"],
                "weight":  source["weight"],
                "title":   title,
                "url":     link,
                "date":    pub_date.isoformat() if pub_date else "",
                "desc":    desc,
                "tags":    cats[:5]
            })

    except Exception as e:
        print(f"[WARN] {source['name']}: {e}", file=sys.stderr)

    return items

def main():
    all_items = []
    seen_ids = set()

    for source in RSS_SOURCES:
        items = fetch_rss(source)
        for item in items:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                all_items.append(item)

    # 按日期排序（新→旧）
    all_items.sort(key=lambda x: x["date"], reverse=True)

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "days_back": DAYS_BACK,
        "total": len(all_items),
        "items": all_items
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
