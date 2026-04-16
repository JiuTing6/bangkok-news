#!/bin/bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/dedup.py --input data/issues/2026-04-11-filtered.json --pool data/issues/2026-04-11-pool-excerpt.json --output data/issues/2026-04-11-deduped.json
