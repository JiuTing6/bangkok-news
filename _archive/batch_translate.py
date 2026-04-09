import json
import os
import re

# 路径配置
PROMPT_FILE = "/Users/Ade/.openclaw/workspace/bangkok-news/experiment/prompts/translation_agent.md"
INPUT_FILE = "/Users/Ade/.openclaw/workspace/bangkok-news/data/issues/2026-03-11-deduped.json"
OUTPUT_FILE = "/Users/Ade/.openclaw/workspace/bangkok-news/data/issues/2026-03-11-translated-test2.json"
TODAY = "2026-03-11"

def load_data():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_prompt():
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def process():
    raw_data = load_data()
    system_prompt = get_prompt()
    
    # 模拟处理逻辑：由于 subagent 无法一次性处理 40+ 条数据且保持高质量翻译（上下文限制），
    # 我们采取分批调用的策略。但在这个脚本中，我主要作为编排者。
    # 实际上，我应该直接把任务交给模型处理。
    
    print(f"Total items to process: {len(raw_data)}")
    
    # 为了演示和确保准确，我将构建一个包含所有数据的完整请求
    # 但由于 JSON 很大，我直接在后续对话中逐条或分块处理，最后合并。
    
process()
