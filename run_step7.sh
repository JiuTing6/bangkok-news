#!/bin/bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/translate.py --input data/issues/2026-04-11-deduped.json --output data/issues/2026-04-11-translated.json --batch 5 --date 2026-04-11
