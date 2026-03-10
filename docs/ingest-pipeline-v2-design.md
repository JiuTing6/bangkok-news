# Ingest Pipeline v2 设计文档

**版本：** v2.0-draft  
**更新：** 2026-03-09  
**状态：** 设计验证阶段（已完成关键实验）

---

## 背景

当前 Ingest（v1）是单一 Sonnet 4.6 session 从头跑到尾，存在以下问题：

- 成本偏高（~$0.29-0.47/次，月度 ~$9-12）
- 曾出现连续 timeout（2026-03-05 两次超时）
- 过滤/去重/翻译混在一个 session，出错难定位

---

## v2 目标架构：Orchestrator + 子Agent 流水线

```
Cron（minimax/scanner）→ Orchestrator session
  ├── exec: fetch_rss.py + fetch_brave.py → raw.json       [Python]
  ├── sessions_spawn(model=scanner) → Filter Agent          [LLM-F]
  ├── sessions_spawn(model=scanner) → Dedup Agent           [LLM-D]
  └── sessions_spawn(model=sonnet) → Translation Agent      [LLM-T]
       └── exec: pool_merge.py → news_pool.json             [Python]
```

数据传递：通过文件（子agent自己 read，不内联到 prompt）

---

## 各步骤执行方与成本

| # | 步骤 | 执行方 | 模型 | 估算 tokens（in/out） | 估算成本/次 |
|---|---|---|---|---|---|
| 0 | Orchestrator 调度 | LLM-O | minimax-m2.5 | 3k / 0.5k | ~$0.0004 |
| 1 | RSS + Brave 抓取 | Python | — | — | $0 |
| 2 | Layer 1：过滤（泰国相关性） | LLM-F | scanner（Gemini Flash） | 15k / 0.5k | ~$0.003 |
| 3 | Layer 2：去重 | LLM-D | scanner | ~15k / 1k | ~$0.002 |
| 4 | Layer 3：翻译 + 标注 | LLM-T | Sonnet 4.6 | 15k / 12k | ~$0.18 |
| 5 | pool_merge 入库收尾 | Python | — | — | $0 |

**每次运行合计：~$0.19 → 月度 ~$5.70（节省约 40-50%）**

---

## 关键设计决策（2026-03-09 确认）

### 1. Cron → 子Agent spawn 可行性 ✅ 已验证

- 实验：建立一次性 isolated cron job，内部调用 `sessions_spawn`
- 结果：成功，childSessionKey 正常返回
- 结论：isolated cron session（`cron:<jobId>`）与 sub-agent（`subagent:<uuid>`）是不同 session 类型，cron 不受"sub-agent 不能再 spawn"的限制

### 2. Scanner JSON 输出能力 ✅ 已验证

- **过滤测试**（10条假数据）：10/10 正确，纯 JSON，无杂质，7秒
- **过滤测试**（29条真实 3/3 数据）：判断质量优秀，15秒，tokens 13.2k/5.2k
- **去重测试**（25条候选 vs 116条 pool）：URL精确匹配100%正确，语义去重90%准确，10秒，tokens 32.2k/1.8k
- 注意：去重测试输出带了 ``` 代码框，需在 prompt 加强"纯JSON"指令

### 3. Gemini 关于 maxSpawnDepth 的说法 ❌ 错误

- Gemini 声称有 `maxSpawnDepth` 配置和"嵌套子代理"功能，版本号 v2026.2.17
- 实际 OpenClaw 文档无此配置，为 LLM 编造内容
- 教训：LLM 输出的技术细节必须查官方文档验证

---

## Layer 2 去重简化方案（2026-03-09 确认）

### 原始设计痛点
- 需要比对整个 pool（可能 200+ 条）
- 需要区分"重复" vs "追踪进展"两种情况

### 简化决策
1. **10天窗口**：只比对最近10天内的 pool 条目，更早的不参与去重
   - 理由：10天前的事情若再出现，要么有新进展（值得入库），要么无所谓重复
   - 效果：参与比对的条目从 100+ 降至 ~50条

2. **100条上限**：pool 输入硬上限 100条（取最新的100条）
   - 与10天窗口结合，实际传入 token 大幅减少

3. **取消追踪标签（#追踪）**：
   - 6期实测观察：RSS 内容频率本身即反映话题重要性
   - 追踪标签在 Publish 阶段使用率低
   - 取消后：Layer 2 只做去重（keep/skip），Layer 3 Sonnet 不需处理追踪逻辑

### 去重简化后的规则
- **URL 完全相同** → 直接 skip
- **标题语义高度重合（同一事件，10天内）** → skip
- **同一事件有新角度/新进展** → keep（不打特殊标签，正常入库）
- **超过10天的同类话题** → keep（无论是否重复）

---

## 地理名称识别能力确认 ✅

Scanner 对泰国地名识别无需依赖"Thailand"字样：
- 已确认识别：Bangkok、Pattaya、Phuket、Koh Samui、Krabi、Mae Sai、Kamphaeng Phet、Chon Buri、Udon Thani、Rawai（普吉）、Nong Prue（芭提雅）等
- 依据：3/3 过滤测试，无"Thailand"字样的 Phuket / Kamphaeng Phet 条目均正确判断

---

## 待完成

### 实验阶段（不动生产环境）
- [ ] 建立 `experiment/` 独立目录
- [ ] 编写 orchestrator prompt（minimax/scanner 驱动）
- [ ] 编写 filter_agent_prompt（Layer 1）
- [ ] 编写 dedup_agent_prompt（Layer 2，含10天窗口逻辑）
- [ ] 编写 translation_agent_prompt（Layer 3，去掉追踪标签）
- [ ] 编写 `scripts/pool_merge.py`（Python 收尾：归档过期+合并写入）
- [ ] 端到端联调测试

### 上线阶段
- [ ] 切换 cron `c9fbffa7` model 为 minimax/scanner
- [ ] 替换 `cron_prompt_ingest.md` 为新 orchestrator prompt
- [ ] 监控首次生产跑结果

### 生产环境约束（绝对不动）
- ❌ 不改动现有 cron jobs（`c9fbffa7` / `a3aa4070` / `de8116d8`）
- ❌ 不动 `cron_prompt_ingest.md`（现有版本）
- ❌ 不动 `data/news_pool.json` 生产数据

---

## 参考

- OpenClaw 文档：`sessions_spawn` 限制说明 → `/opt/homebrew/lib/node_modules/openclaw/docs/concepts/session-tool.md`
- OpenClaw 文档：Cron isolated session → `/opt/homebrew/lib/node_modules/openclaw/docs/automation/cron-jobs.md`
- 实验日志：`memory/2026-03-09.md`
