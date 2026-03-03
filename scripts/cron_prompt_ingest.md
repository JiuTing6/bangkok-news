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

#### 5a. 硬性排除

**排除以下两类，其余全收：**

1. **无标题或无URL** → 跳过

2. **与泰国无直接关联** → 跳过

   **"泰国直接关联"判断标准（必须满足其一）：**
   - 事件发生在泰国境内
   - 泰国政府/机构/企业是行动主体或声明方
   - 直接影响在泰外国人的生活、签证、安全、物价
   - 泰国经济指标、政策、市场直接受影响
   - 涉及泰国人或在泰外国人

   **反例（不满足→不入库）：**
   - 中东战争本身（无泰国角色）
   - 美国政治新闻（无泰国关联）
   - 全球股市、外国经济数据（未提及泰国）

   **正例（满足→入库）：**
   - 中东战争 → 泰国撤侨行动（主体是泰国政府）
   - 中东战争 → 油价上涨 → 泰国燃油补贴政策（泰国政策直接响应）
   - 中东航线关闭 → 泰国入境旅客下滑（泰国旅游业直接受影响）
   - 美国关税 → 泰国出口商/泰国GDP预测（泰国经济直接受影响）

**软文、PR稿、旅游促销、社会新闻——只要与泰国有关，全收，用 tags 标注，交给 publish 阶段精选。**

#### 5b. 去重（纯机械判断，不带主观）
对比 `data/news_pool.json` 中现有条目的 `url` + `title_cn`，以及 `data/history.json` 中的 `title`：
- **相同 URL** → 直接跳过
- **标题内容高度相似**（同一事件、同一机构、同一政策，不要求字符100%一致）→ 跳过
- **同一事件有明确新进展**（如续报、结果公布）→ 入库，tags 加 `#追踪`

**去重只判断"是不是重复"，不判断"值不值得收"。**

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

**内容类型 tags（按实际内容打，可多选）：**
- `#政策` `#签证` `#经济` `#政治` `#安全` `#科技` — 正规新闻
- `#房产` `#开发商` — 房地产
- `#PR软文` — 明显的公关稿/开发商通稿
- `#品牌` — 品牌活动、企业公告
- `#活动促销` — 旅游促销、节日活动、优惠信息
- `#治安犯罪` — 刑事案件、社会治安
- `#旅游` — 旅游景点、观光信息
- `#追踪` — 已有事件的新进展

**重要性分级（P级）：**
- P1：影响外国人的政策、重大安全事件、追踪议题重要进展
- P2：政治走向、经济指标、科技基建、房产重大动态
- P3：文化娱乐旅游、生活服务、促销活动、社会新闻

**有效期规则：**
- `time_sensitive: true`（政策/经济/安全/政治）→ `expires_date = added_date + 15天`
- `time_sensitive: false`（酒店/餐厅/地标/生活指南/促销/时效中性内容）→ `expires_date = added_date + 30天`

**板块 hint 判断（严格）：**
- `bangkok`：只有明确发生在曼谷市内的本地新闻，不是"泰国新闻碰巧提到曼谷"
- `pattaya`：聚焦 North Pattaya / Na Kluea / Wong Amat / Phra Tamnak 区域
- `cn_thai`：涉及中泰双边关系、中国投资泰国、中国游客/移民政策等
- `property`：明确的房产市场动态、政策、项目
- `thailand`：以上都不是 → 归政经动态（兜底板块）

#### 5d. 每日入库上限

通过排除+去重后，如候选条目超过 **50条**，按以下优先级取前50：
1. P1 优先于 P2 优先于 P3
2. 同级别内，时效性内容（`time_sensitive: true`）优先
3. 同级别同类型内，RSS 来源优先于 Brave（RSS 来源更可靠）

**每天最多新增50条入库。**

#### 5e. 写入 news_pool.json

**第一步：归档过期条目**

读取 `data/news_pool.json`，将 `expires_date < 今日` 的条目移入归档文件：
```
data/archive/YYYY-MM.json  （按月归档，文件名为过期条目的 added_date 所在月份）
```

归档文件格式：数组，每月一个文件，只追加不覆盖（读取现有内容后 append 再写回）。
若文件不存在则新建。

**第二步：追加新条目**

将本次新条目 append 到清理后的 pool，按 `added_date` 降序排序后写回 `data/news_pool.json`。

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
