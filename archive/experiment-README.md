# Ingest Pipeline v2 — 实验目录

**状态：** 开发/测试阶段  
**生产环境：绝对不动 data/news_pool.json 和现有 cron jobs**

## 目录结构

```
experiment/
  prompts/
    orchestrator.md       # 总控（minimax），驱动整个流程
    filter_agent.md       # Layer 1 过滤（scanner）
    dedup_agent.md        # Layer 2 去重（scanner）
    translation_agent.md  # Layer 3 翻译标注（Sonnet）
  scripts/
    pool_merge.py         # Python 收尾：归档过期+合并写入
  data/
    YYYY-MM-DD-flat.json        # 展平后的原始条目
    YYYY-MM-DD-filtered.json    # Layer 1 输出
    YYYY-MM-DD-deduped.json     # Layer 2 输出
    YYYY-MM-DD-translated.json  # Layer 3 输出
    YYYY-MM-DD-pool-excerpt.json # Pool摘录（去重比对用）
    YYYY-MM-DD-pool-result.json  # 实验merge结果（不是生产pool）
  README.md
```

## 测试流程

### 单步测试（推荐先做）

1. 用现有 `data/issues/2026-03-09-raw.json` 手动测试 filter_agent
2. 用 filter 输出测试 dedup_agent
3. 用 dedup 输出测试 translation_agent
4. 用 translation 输出测试 pool_merge.py

### 端到端测试

直接运行 orchestrator prompt（作为 Sonnet session 手动执行，或 cron 测试）

## 上线步骤（验证通过后）

1. 更新 cron `c9fbffa7` 的 model 为 `minimax/minimax-m2.5`
2. 替换 `scripts/cron_prompt_ingest.md` 为 `experiment/prompts/orchestrator.md` 的内容
3. 监控首次生产跑结果
