#!/usr/bin/env python3
"""
Quick fix: Restore summary_cn from translated.json to news_pool.json
"""
import json

# Load translated data (source of truth)
with open('data/issues/2026-03-11-translated.json', 'r', encoding='utf-8') as f:
    translated = json.load(f)

# Build a lookup by URL
trans_by_url = {item['url']: item for item in translated}

# Load and fix pool
with open('data/news_pool.json', 'r', encoding='utf-8') as f:
    pool = json.load(f)

fixed_count = 0
for item in pool:
    if item['url'] in trans_by_url:
        trans_item = trans_by_url[item['url']]
        if trans_item.get('summary_cn') and trans_item['summary_cn'] != item.get('summary_cn'):
            item['summary_cn'] = trans_item['summary_cn']
            fixed_count += 1

# Backup and write
import shutil
shutil.copy('data/news_pool.json', 'data/news_pool.json.backup-2026-03-11-before-fix')
with open('data/news_pool.json', 'w', encoding='utf-8') as f:
    json.dump(pool, f, ensure_ascii=False, indent=2)

print(f"✅ Fixed {fixed_count} items with correct summary_cn from translated.json")
print(f"📂 Backup saved: data/news_pool.json.backup-2026-03-11-before-fix")
