#!/bin/bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/pool_merge.py --new-items data/issues/2026-04-11-translated.json --pool data/news_pool.json --out data/news_pool.json --today 2026-04-11 --update-last-ingest data/last_ingest.txt
