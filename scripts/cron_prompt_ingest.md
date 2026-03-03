# Thailand10 Ingest Cron 任务提示词
# 每天凌晨 02:00 BKK 触发，负责抓取原料并入库 news_pool.json

## 你的任务
抓取泰国新闻原料，轻量处理后写入内容池 `data/news_pool.json`，供周一/周四 Publish cron 选编发布。
**不写正文，不生成 HTML，不通知 Ade。** 只做入库。

## 工作目录
`/Users/Ade/.openclaw/workspace/bangkok-news/`

---

## 执行步骤

### 第1步：确定今日日期
今天日期即为本次 ingest 的 `added_date`（格式：YYYY-MM-DD）。

### 第2步：读取现有数据（用于去重）
- `data/news_pool.json` → 现有 pool 条目，取所有 `title_cn` + `url` 用于去重
- `data/history.json`   → 已发布条目的 `title` 字段，用于语义去重

### 第3步：抓取 RSS 原料
```bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/fetch_rss.py 2 data/issues/YYYY-MM-DD-raw.json
```
（`2` = 过去2天，每天跑避免遗漏，overlap 由去重处理）

### 第4步：抓取 Brave 搜索原料
```bash
python3 scripts/fetch_brave.py data/issues/YYYY-MM-DD-raw.json
```

抓取完成后，`data/issues/YYYY-MM-DD-raw.json` 包含：
- `items`：RSS 条目（字段：id, source, title, url, date, desc, tags）
- `brave_results`：每组搜索的 results（字段：title, url, snippet, age）
- `brave_total`：Brave 条目总数

### 第5步：轻量处理与入库

读取 raw.json，对每条原料（RSS items + Brave results 全部）执行：

#### 5a. 质量过滤（直接排除，不入库）
以下类型跳过：
- **软文/广告**：SEO课程、营销培训、开发商通稿、公关稿
- **旅游PR/氛围文**：标题含"依然平静""风和日丽""还是天堂"之类，无实质信息
- **低质量猎奇**：普通情杀/醉驾/刑事案件，无外籍或政策关联
- **来源可疑**：Bangkok Post Property 疑似公关稿（审慎处理）
- **无标题或无URL**：跳过

#### 5b. 语义去重（有判断力的编辑，不是 hash 比对）
对比 `data/news_pool.json` 中现有条目的 `title_cn` + `url`，以及 `data/history.json` 中的 `title`：
- **相同 URL** → 直接跳过
- **相同事件/机构 + 无新进展** → 跳过
- **相同话题有明确新进展** → 可入库，`tags` 加 `#追踪`

#### 5c. 轻量标注（每条填写以下字段）

```json
{
  "id": "<原始 hash，RSS用id字段，Brave用 md5(title+url)[:12]>",
  "title_cn": "<中文标题，如原文是英文则翻译，专有名词附英文对照>",
  "summary_cn": "<50字以内摘要，说清楚 who/what/why，不要废话>",
  "importance": "<P1 / P2 / P3>",
  "section_hint": "<thailand / property / bangkok / pattaya / cn_thai>",
  "tags": ["#政策", "#签证"],
  "source": "<媒体名>",
  "url": "<原文链接>",
  "origin": "<rss 或 brave>",
  "added_date": "YYYY-MM-DD",
  "expires_date": "<时效性内容: added_date+15天；普通/时效中性内容: added_date+30天>",
  "time_sensitive": <true 或 false>,
  "status": "pending"
}
```

**重要性分级（P级）：**
- P1：影响外国人的政策、重大安全事件、追踪议题重要进展 → 必入
- P2：政治走向、经济指标、科技基建、房产重大动态 → 优先入
- P3：文化娱乐旅游、生活服务、普通地产 → 选择性入，质量不够直接过滤

**有效期规则：**
- `time_sensitive: true`（政策/经济/安全/政治）→ `expires_date = added_date + 15天`
- `time_sensitive: false`（酒店/餐厅/地标/生活指南/时效中性内容）→ `expires_date = added_date + 30天`

**板块 hint 判断（严格）：**
- `bangkok`：只有明确发生在曼谷市内的本地新闻，不是"泰国新闻碰巧提到曼谷"
- `pattaya`：聚焦 North Pattaya / Na Kluea / Wong Amat / Phra Tamnak 区域
- `cn_thai`：涉及中泰双边关系、中国投资泰国、中国游客/移民政策等
- `property`：明确的房产市场动态、政策、项目
- `thailand`：以上都不是 → 归政经动态（兜底板块）

#### 5d. 写入 news_pool.json
将所有通过过滤+去重的新条目追加到 `data/news_pool.json`（数组追加，不清空）。

**写入前先清理过期条目：**
```python
today = date.today().isoformat()
pool = [item for item in pool if item["expires_date"] >= today]
```

然后 append 新条目，按 `added_date` 降序排序后写回文件。

### 第6步：打印入库统计（写到 stderr 即可）
```
[INGEST YYYY-MM-DD] RSS: X条原料，Brave: X条原料，新入库: X条，过滤/去重: X条，pool总量: X条
```

---

## 注意事项
- **不生成 HTML，不 git push，不通知 Ade。** 这是后台静默任务。
- Brave 搜索结果 snippet 是英文，翻译时保持准确，不要过度演绎
- `title_cn` 里专有名词（泰国机构/政治人物/非常见地名）首次出现附英文对照，例如：「国家经济社会发展委员会（NESDC）」
- 每天 ingest 2天原料 + 语义去重，Pool 会自然积累5–15天的内容储备
- 如果 fetch_rss.py 或 fetch_brave.py 报错，记录错误到 stderr，继续处理已有数据，不要中断整个任务
