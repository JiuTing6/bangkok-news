# Thailand10 Ingest Cron 任务提示词
# 每天 08:30 BKK 触发，负责抓取原料并入库 news_pool.json

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

Brave 定位：**补漏+惊喜发现**，主力新闻由 RSS 覆盖。
当前4组搜索：AI/Cloud/Crypto、国际学校/医疗、高端房产、X.com扫描。
每组最多8条，freshness=pd（过去24小时）。

抓取完成后，`data/issues/YYYY-MM-DD-raw.json` 包含：
- `items`：RSS 条目（字段：id, source, title, url, date, desc, tags）
- `brave_results`：每组搜索的 results（字段：title, url, snippet, age）
- `brave_total`：Brave 条目总数

### 第5步：轻量处理与入库

读取 raw.json，对每条原料（RSS items + Brave results 全部）执行：

#### 5a. 硬性排除

**排除以下，其余全收：**

1. **无标题或无URL** → 跳过
2. **与泰国无直接关联** → 跳过
3. **非新闻页面** → 跳过（Wikipedia、YouTube、网站首页/聚合页、学术论文）

**"泰国直接关联"判断标准（必须满足其一）：**
- 事件发生在泰国境内
- 泰国政府/机构/企业是行动主体或声明方
- 直接影响在泰外国人的生活、签证、安全、物价
- 泰国经济指标、政策、市场直接受影响
- 涉及泰国人或在泰外国人

**反例（不满足→不入库，即使RSS抓到了也排除）：**
- 特朗普/美国政策本身（如油轮护航令、对西班牙制裁），除非文章明确提到对泰国的影响
- 中东/伊朗战争进展本身（如空袭、领袖更替、各国撤侨），除非文章主体是泰国撤侨或泰国受影响
- 全球股市、外国经济数据（未提及泰国）
- 全球AI/crypto新闻（未涉及泰国）
- 他国内政、国际外交（无泰国角色）

**关键判断原则：文章主体必须是泰国。仅仅因为"可能间接影响泰国"不够——文章本身必须讨论泰国。**

**正例（满足→入库）：**
- "泰国政府宣布从中东撤侨"（主体是泰国政府行动）✅
- "PTT宣布冻结油价应对中东局势"（主体是泰国企业政策）✅
- "泰国出口商面临美国关税冲击"（主体是泰国经济）✅
- "谷歌宣布在泰国建AI数据中心"（主体涉及泰国）✅
- "特朗普下令海军护航油轮"（主体是美国，泰国未提及）❌
- "各国紧急撤离中东滞留旅客"（主体是全球各国，非泰国专题）❌

**软文、PR稿、旅游促销、社会新闻——只要与泰国有关，全收，用 tags 标注。**

#### 5b. 去重（纯机械判断）
对比 pool 中现有 `url` + `title_cn`，以及 history 中的 `title`：
- **相同 URL** → 直接跳过
- **标题内容高度相似**（同一事件同一来源）→ 跳过
- **同一篇文章多站转载**（syndication）→ 只留原始来源，跳过转载
- **同一事件有明确新进展** → 入库，tags 加 `#追踪`

#### 5c. 轻量标注（每条填写以下字段）

```json
{
  "id": "<RSS用id字段，Brave用 md5(title+url)[:12]>",
  "title_cn": "<中文标题，英文原文则翻译，专有名词附英文对照>",
  "importance": "<P1 / P2 / P3>",
  "section_hint": "<thailand / property / bangkok / pattaya / cn_thai>",
  "tags": ["#政策", "#签证"],
  "source": "<媒体名>",
  "url": "<原文链接>",
  "origin": "<rss 或 brave>",
  "added_date": "YYYY-MM-DD",
  "expires_date": "<时效性: added_date+15天；非时效性: added_date+30天>",
  "time_sensitive": true/false,
  "status": "pending"
}
```

**注意：不写 summary_cn，Publish 阶段再补。**

**Tags（只用以下列表，不得自创tag）：**
`#政策` `#签证` `#安全` `#政治` `#经济数据` `#楼市大盘` `#新楼盘` `#房产` `#开发商` `#AI基建` `#AI应用` `#科技` `#crypto` `#教育` `#医疗` `#本地奇闻` `#治安犯罪` `#旅游` `#PR软文` `#品牌` `#活动促销` `#追踪` `#中泰` `#能源` `#外交` `#交通` `#金融` `#文化`

**重要性（P级）：**
- P1：影响外国人的政策/签证/安全、重大突发、追踪议题重要进展
- P2：政治重大变化、AI/科技基建落地、具体楼盘、本地有料奇闻
- P3：常规经济数据、楼市趋势报告、组阁例行进展、旅游促销、社会犯罪

**降频：** `#经济数据` `#楼市大盘` `#政治`例行 → 每天最多各2条
**优先：** `#新楼盘` `#本地奇闻` `#AI基建` `#AI应用` → 同级别优先入库

**板块 hint：**
- `bangkok`：明确发生在曼谷市内的本地新闻
- `pattaya`：North Pattaya / Na Kluea / Wong Amat / Phra Tamnak
- `cn_thai`：中泰双边关系、中国投资/游客/移民
- `property`：房产市场动态、政策、项目
- `thailand`：以上都不是 → 兜底

**有效期：**
- `time_sensitive: true` → expires = added_date + 15天
- `time_sensitive: false` → expires = added_date + 30天

#### 5d. 每日入库上限50条
超出按 P1→P2→P3、时效优先、RSS优先于Brave 截取。

#### 5e. 写入 news_pool.json

1. 归档过期条目（`expires_date < 今日`）到 `data/archive/YYYY-MM.json`
2. 追加新条目，按 `added_date` 降序排序写回

### 第6步：打印入库统计
```
[INGEST YYYY-MM-DD] RSS: X条原料，Brave: X条原料，新入库: X条，过滤/去重: X条，pool总量: X条
重要性：P1=X | P2=X | P3=X
板块：thailand=X | property=X | bangkok=X | pattaya=X
今日主题：（2-3行概述）
```

---

## 注意事项
- **不生成 HTML，不 git push，不通知 Ade。**
- `title_cn` 专有名词首次出现附英文对照
- 如果 fetch 脚本报错，继续处理已有数据，不中断
