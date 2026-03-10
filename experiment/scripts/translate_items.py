#!/usr/bin/env python3
"""
Translation script using OpenRouter API
Translates English news items to Chinese with summaries
"""
import json
import os
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
import ssl

API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o"  # Using GPT-4o for translation

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def translate_item(item, today):
    """Translate a single item to Chinese"""
    
    title = item.get('title', '')
    desc = item.get('desc', '')[:500]  # Limit desc to 500 chars
    
    # Build prompt for translation
    prompt = f"""请将以下英文新闻条目翻译成中文，并提供中文摘要。

标题: {title}
摘要: {desc}

请按以下JSON格式输出（只输出JSON，不要其他内容）:
{{
    "title_cn": "中文标题",
    "summary_cn": "100-200字的中文摘要",
    "importance": "P1或P2或P3",
    "section_hint": "bangkok/pattaya/property/cn_thai/thailand",
    "location_detail": "具体地名或空字符串",
    "tags": ["#标签1", "#标签2"],
    "time_sensitive": true或false
}}

规则:
- importance: P1=直接影响外国人日常生活, P2=重大基建/经济数据, P3=一般新闻
- section_hint: 曼谷=bangkok, 芭提雅=pattaya, 房产=property, 中泰关系=cn_thai, 其他=thailand
- location_detail: 最具体的地名
- tags: 从 [#签证,#移民,#房产,#基建,#交通,#旅游,#中泰,#经济,#安全,#政策,#环境,#美食,#夜生活] 选择1-3个
- time_sensitive: 有明确时效=true，否则=false
"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://openclaw.local",
        "X-Title": "Thailand10 Ingest"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500
    }
    
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60, context=ssl_context) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
        
        # Parse JSON from response
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        translated = json.loads(content)
        
        # Build full item
        is_time_sensitive = translated.get('time_sensitive', False)
        expires_days = 15 if is_time_sensitive else 30
        expires_date = (datetime.strptime(today, '%Y-%m-%d') + timedelta(days=expires_days)).strftime('%Y-%m-%d')
        
        return {
            "id": item.get('id', ''),
            "event_id": f"thailand_{title[:20].lower().replace(' ', '_')}_{today[2:7]}",
            "title_cn": translated.get('title_cn', title),
            "desc_original": desc,
            "summary_cn": translated.get('summary_cn', ''),
            "importance": translated.get('importance', 'P3'),
            "section_hint": translated.get('section_hint', 'thailand'),
            "location_detail": translated.get('location_detail', ''),
            "tags": translated.get('tags', []),
            "source": item.get('source', ''),
            "url": item.get('url', ''),
            "origin": item.get('origin', 'rss'),
            "added_date": today,
            "expires_date": expires_date,
            "time_sensitive": is_time_sensitive,
            "status": "pending"
        }
        
    except Exception as e:
        print(f"Error translating: {e}")
        # Return a fallback item
        return {
            "id": item.get('id', ''),
            "event_id": f"thailand_fallback_{today[2:7]}",
            "title_cn": title,
            "desc_original": desc,
            "summary_cn": desc[:200],
            "importance": "P3",
            "section_hint": "thailand",
            "location_detail": "",
            "tags": [],
            "source": item.get('source', ''),
            "url": item.get('url', ''),
            "origin": item.get('origin', 'rss'),
            "added_date": today,
            "expires_date": (datetime.strptime(today, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d'),
            "time_sensitive": False,
            "status": "pending"
        }

def main():
    today = "2026-03-09"
    
    # Load deduped items
    with open('data/issues/2026-03-09-deduped.json') as f:
        items = json.load(f)
    
    print(f"Translating {len(items)} items...")
    
    translated_items = []
    p1_count = p2_count = p3_count = 0
    
    for i, item in enumerate(items):
        print(f"  [{i+1}/{len(items)}] Translating: {item.get('title', '')[:50]}...")
        translated = translate_item(item, today)
        translated_items.append(translated)
        
        # Count importance levels
        imp = translated.get('importance', 'P3')
        if imp == 'P1':
            p1_count += 1
        elif imp == 'P2':
            p2_count += 1
        else:
            p3_count += 1
    
    # Write output
    with open('data/issues/2026-03-09-translated.json', 'w') as f:
        json.dump(translated_items, f, ensure_ascii=False, indent=2)
    
    print(f"\nTRANSLATION_RESULT: total={len(translated_items)} P1={p1_count} P2={p2_count} P3={p3_count}")
    print(f"Translation completed: {len(translated_items)} items")

if __name__ == '__main__':
    main()