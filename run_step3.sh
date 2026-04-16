#!/bin/bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/fetch_rss.py --start 2026-04-10 --end 2026-04-11 -o data/issues/2026-04-11-raw.json
