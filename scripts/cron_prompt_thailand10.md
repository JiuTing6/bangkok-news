# Thailand10 Cron 任务提示词
# 每次 Cron 触发时，sub-agent 读取此文件并执行

## 你的任务
生成一期《泰兰德10:00 / Thailand 10:00》新闻简报，写入 HTML 文件，推送到 GitHub Pages，通知 Ade。

## 工作目录
`/Users/Ade/.openclaw/workspace/bangkok-news/`

## 执行步骤

### 第1步：确定期数和日期
- 读取 `thailand10/index.html`，数一下现有归档条目数，+1 即为本期期号
- 今天日期即为本期日期

### 第2步：读取记忆文件
- `data/history.json`    → 已发布条目（含标题），用于语义去重，见下方去重规则
- `data/tracking.json`   → 持续追踪议题，本期如有进展需标注 🔄
- `data/rotation.json`   → 长期内容轮播记录
- `data/buffer.json`     → 内容储备库，本期新鲜内容不足10条时从此处补充
- `data/editorial_feedback.md` → **主编反馈日志，必读**，将历史教训内化为编辑判断

### 第3步：抓取新闻原料
运行 RSS 抓取（过去4天，周四刊；过去4天含周末，周一刊）：
```bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/fetch_rss.py 4 data/issues/YYYY-MM-DD-raw.json
```
（YYYY-MM-DD 替换为本期日期，永久保留原始素材，用于事后分析抓取量 vs 选取量）

然后运行 Brave 搜索脚本，结果自动追加写入同一 raw.json：
```bash
python3 scripts/fetch_brave.py data/issues/YYYY-MM-DD-raw.json
```
脚本会跑13组预设关键词，将全部结果写入 `brave_results` 字段（126条左右）。

**完成后 raw.json 包含：**
- `items`：RSS抓取条目
- `brave_results`：每组搜索的标题、URL、snippet
- `brave_total`：Brave条目总数

**⚠️ AI 不得在此步骤之外自行调用 web_search。所有选编原料必须且只能来自 raw.json。**

### 第4步：编辑选题（核心工作）

**选题三原则（按优先级顺序严格执行）：**
1. **原料优先：** 以本期实际扫描到的新闻为第一基础，有什么选什么，不虚构不补填
2. **重要性优先：** 以新闻本身的重要性、时效性和影响力为核心筛选标准，编辑判断永远第一
3. **板块关联度：** 在重要性相近的情况下，以与板块的相关性决定归属，不为填充板块而降标

**版块配额（全部动态，无硬性下限）：**
- 📡 政经动态：无上限（政治/经济/科技基建/社会/外国人签证，兜底板块，永远有料）
- 🏠 房地产：有则收，无则0
- 🛺 曼谷：**严格只收曼谷本地新闻**，不相关宁可0条并入政经动态
- 🌅 芭提雅：有则收，聚焦北芭/Na Kluea/Wong Amat/Phra Tamnak
- 🚅 中泰：触发式，无重磅直接省略

**每期发布量：**
- **下限：** 10条（硬性，低于此需加大搜索力度或启用内容储备库）
- **上限：** 25条为软性参考值，**新闻密集期可突破**
- **溢出处理：** 超出25条的优质稿件不丢弃，存入 `data/buffer.json`（内容储备库），供新闻淡季调取发布，标注原始日期和来源

**内容储备库调用规则：**
- 每期新鲜内容不足10条时，从 `data/buffer.json` 补充存稿
- 存稿按时效性分两类：
  - **时效性内容**（政策/经济/安全）：有效期14天，过期归档不再调用
  - **时效中性内容**（新开酒店/餐厅/寺庙/地标/生活指南等）：有效期90天，随时可调用，读者不会感知时间差
- 调取优先级：P1/P2 > P3；时效性内容优先于时效中性内容；与本期已有内容不重复

**新闻重要性分级：**
- P1：影响外国人的政策、重大安全事件、追踪议题重要进展 → 必收
- P2：政治走向、经济指标、科技基建落地、房产重大动态 → 优先
- P3：全国文化娱乐旅游 → 仅在版面宽裕时收录

**受欢迎度权重（popularity bonus）：**
- 来源：读者 👍/👎 反馈累计（存储于新闻库）
- 作用范围：**仅在重要性相近（同级P）的候选稿件之间作为加权参考**
- 权重上限：不得覆盖编辑对重要性/质量的判断
- 长期效应：某类话题持续获得高 👍，可适度提高同类话题的搜索优先级

**去重（语义判断，不是hash比对）：**
读取 `history.json` 中所有已发布条目的 `title` 字段，作为有判断力的编辑，理解这些标题覆盖了哪些话题、事件、机构。选题时主动绕开已报道过的相同或高度相似话题，规则如下：
- **相同事件/机构 + 无实质新进展** → 跳过（例：上期已报荣威集团豪宅，本期没有新动态，不得再选）
- **相同话题有明确新进展** → 可选，标注 🔄，正文须点明进展内容，不得复述旧料
- **长期追踪议题**（tracking.json中的）→ 只要有新进展就选，不受去重限制
- hash比对可作为辅助参考，但不是唯一判断依据，同一事件不同URL仍可能是重复

**内容质量过滤（选题前强制执行）：**
以下类型直接排除，不进入候选池——这是编辑的基本判断力：
- **旅游PR / 氛围文**：标题含"芭提雅依然平静""酒吧记得你名字""逃离全球重压""风和日丽"之类 → 无信息量，丢弃
- **广告/软文**：SEO课程、营销培训、无新闻价值的开发商项目发布会 → 丢弃
- **重复视角**：同一事件（如中东战争/航班取消）多家媒体重复报道 → 合并为一条，不分开计数
- **低质量猎奇**：情杀、醉驾、普通刑事案件，无外籍或政策关联 → 通常跳过，除非有更大背景意义
- **来源可疑**：Bangkok Post Property / 开发商通稿类，疑似公关稿，无独立报道价值 → 审慎，通常跳过

### 第5步：撰写摘要

每条新闻：
- 标题：中文，首次出现的专有名词附英文
- 正文：150–300字（深度内容可到500字；简单数据50–150字）
- 评论（视情况添加，简单事实不加）：
  💬多一嘴 / ⚠️请注意 / 🤔琢磨着 / 👀看点 / 🌶️辣评 / 😱 / 🤣 / 👍
- 来源：日期 + 媒体名 + 原文链接

**专有名词附英文规则：**
- 需要：泰国机构/政治人物/非常见地名/专业术语
- 不需要：曼谷/芭提雅/泰铢/签证/国家名

### 第6步：生成期数 JSON

将选好的新闻整理为以下格式，保存为 `data/issues/YYYY-MM-DD.json`（永久保留，YYYY-MM-DD 替换为本期日期）：

**`highlights` 字段说明：**
从本期所有文章中，按全局编号顺序（第一个板块的第1条=0，第2条=1，依此类推），选出 **5条最重要、最值得读者第一时间关注** 的文章，填入 `highlights` 列表。这5条将显示在页面顶部"本期要闻 | Highlights"区块，是读者进入页面后第一眼看到的内容，选择标准是新闻价值和读者相关度，不是位置顺序。

```json
{
  "date": "YYYY-MM-DD",
  "issue": N,
  "highlights": [2, 0, 8, 13, 5],
  "sections": {
    "thailand": [
      {
        "title": "...",
        "tags": ["#政治动态"],
        "body": "...",
        "comment": "💬 多一嘴：...",
        "date": "YYYY-MM-DD",
        "source": "Bangkok Post",
        "url": "https://..."
      }
    ],
    "property": [...],
    "bangkok":  [...],
    "pattaya":  [...],
    "cn_thai":  [...]
  }
}
```

**第6步完成后立即验证 JSON 格式：**
```bash
python3 -c "import json; json.load(open('data/issues/YYYY-MM-DD.json')); print('JSON OK')"
```
若验证报错，立即修复（最常见问题：body/title/comment 里有未转义的英文双引号），再继续下一步。

### 第7步：生成 HTML
```bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/build_html.py data/issues/YYYY-MM-DD.json
```

### 第8步：更新记忆文件
- 将本期所有新闻写入 `data/history.json`，格式：`{"title": "...", "date": "YYYY-MM-DD", "issue": N}`（title字段是语义去重的核心，必须写入，不得省略）
- 更新 `data/tracking.json` 中相关追踪议题的 `last_seen` 和 `summary`
- **buffer 写入：** 本期搜集到但未发布的优质稿件（P1/P2，或时效中性的P3），写入 `data/buffer.json`，格式如下：
  ```json
  {
    "hash": "...",
    "title": "...",
    "section": "thailand/property/bangkok/pattaya/cn_thai",
    "importance": "P1/P2/P3",
    "time_sensitive": true,
    "added_date": "YYYY-MM-DD",
    "expires_date": "YYYY-MM-DD（时效性+14天，时效中性+90天）",
    "article": { ... 完整文章对象 ... }
  }
  ```
- **buffer 清理：** 写入前先清除 `data/buffer.json` 中 `expires_date` 已过期的条目

### 第9步：推送到 GitHub
```bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
git add -A
git commit -m "🗞️ Thailand10 第N期 YYYY-MM-DD"
git push origin main
```

### 第10步：通知 Ade
使用 `message` 工具发送 Telegram 消息（**不是 webchat**，必须用 message 工具 + channel:telegram）：

```
action: send
channel: telegram
message:
🗞️ 泰兰德10:00 第N期已发布

📅 YYYY年MM月DD日 周X
📊 本期精选 XX 条新闻

🔗 https://jiuting6.github.io/bangkok-news/thailand10/YYYY-MM-DD.html

【速览】
· [最重要的1-2条标题]
· [第二重要的标题]
```

## 注意事项
- GitHub Pages URL格式：`https://jiuting6.github.io/bangkok-news/...`
- 芭提雅房产只收：North Pattaya / Na Kluea / Wong Amat / Phra Tamnak
- 中泰版块无重磅时直接省略，不强行凑数
- P3文化旅游内容需覆盖全泰国，不做Sukhumvit本地生活
- **JSON 字符串转义（重要）：** `title`、`body`、`comment` 等文本字段内，如含英文双引号 `"` 必须转义为 `\"`，或改用中文引号「」/""。未转义的双引号会导致 JSON 破损，整期无法发布。写完 JSON 后建议用 `python3 -c "import json; json.load(open('data/issues/YYYY-MM-DD.json'))"` 验证格式正确。
