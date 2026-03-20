# Thailand10 Publish Cron 任务提示词
# 每周一 & 周四 09:30 BKK 触发，负责从内容池选编并发布

## 你的任务
从 `data/news_pool.json` 选编本期新闻，写完整正文，生成 HTML，推送 GitHub Pages，通知 Ade。
**不抓取新闻，不调用 web_search。** 所有原料来自 news_pool.json。

## 工作目录
`/Users/Ade/.openclaw/workspace/bangkok-news/`

---

## 执行步骤

### 第1步：确定期数和日期
- 读取 `thailand10/index.html`，数一下现有归档条目数，+1 即为本期期号
- 今天日期即为本期日期（格式：YYYY-MM-DD）

### 第2步：读取记忆文件
- `data/news_pool.json`       → **唯一原料来源**，取 `status=pending` 且 `expires_date >= 今日` 的条目
- `data/buffer.json`          → 内容储备库，pool 可用条目不足10条时从此补充
- `data/editorial_feedback.md` → **主编反馈日志，必读**，将历史教训内化为编辑判断

### 第3步：编辑选题（核心工作）

**可用原料 = news_pool.json 中 status=pending 且未过期的条目**

每条已有：`title_cn`、`summary_cn`、`importance`、`section_hint`、`source`、`url`

**选题三原则（按优先级严格执行）：**
1. **重要性优先：** 以新闻本身的重要性、时效性和影响力为核心，编辑判断第一
2. **原料限定：** 只能从 pool 选，不得自行 web_search 补充
3. **板块关联度：** 重要性相近时，以板块相关性决定归属

**版块配额（全部动态，无硬性下限）：**
- 📡 政经动态（`thailand`）：无上限，兜底板块
- 🏠 房地产（`property`）：有则收，无则0
- 🛺 曼谷（`bangkok`）：**严格只收曼谷本地新闻**，section_hint=bangkok 的条目
- 🌅 芭提雅（`pattaya`）：有则收，聚焦北芭/Na Kluea/Wong Amat/Phra Tamnak
- 🚅 中泰（`cn_thai`）：触发式，无重磅直接省略

**每期发布量：**
- **硬性下限：** 10条（不足则补 buffer.json 存稿）
- **软性参考值：** 25条，新闻密集期可突破
- **溢出：** 超出25条的优质稿件不丢弃，存入 `data/buffer.json`

**新闻重要性分级：**
- P1：影响外国人的政策/签证/安全、重大突发事件 → 必收
- P2：政治重大变化、AI泰国相关（#AI基建 #AI应用）、具体楼盘动态（#新楼盘）、本地有料奇闻（#本地奇闻）→ 优先
- P3：旅游促销、社会犯罪、品牌活动 → 版面宽裕时收录，作为节奏调剂

**每期频率控制（编辑节奏）：**
- `#经济数据`（GDP/泰铢汇率/通胀/利率）：每期最多 **1条**，除非数据异常或政策重大转向
- `#楼市大盘`（整体市场趋势报告）：每期最多 **1条**，优先选 `#新楼盘` 具体项目替代
- `#政治`（组阁/党派例行进展）：每期最多 **2条**，无实质变化不选
- `#AI基建` `#AI应用`：主动寻找，有则必收，读者关注度高
- `#本地奇闻`：每期 **1-2条** 作为节奏调剂，避免全篇都是硬新闻

**内容储备库（buffer.json）调用：**
- pool 可用条目不足10条时，从 buffer.json 补充
- 调取规则：P1/P2 > P3；时效性内容优先；与本期内容不重复
- 时效性内容（time_sensitive=true）有效期15天，超出不调用
- 时效中性内容（time_sensitive=false）有效期30天

### 第4步：撰写正文

对每条选中的新闻，基于 `title_cn` 和 `summary_cn` 扩写完整正文：

- **标题：** 使用 `title_cn`（已有中英对照，直接用）
- **正文：** 150–300字（深度内容可至500字；简单数据50–150字）
- **city_tag：** 从 pool 条目的 `city_tag` 字段直接取用（如 `#曼谷`、`#泰国`）；若原始城市不在5大城市内，直接写原始值（如 `#华欣`）
- **topic_tag：** 从 pool 条目的 `topic_tag` 字段直接取用（9个主题之一：#时政 #经济 #治安 #旅居 #社会 #房产 #科技 #中泰 #健康）
- **来源：** 日期 + 媒体名 + 原文链接（url 字段）

**专有名词附英文规则：**
- 需要：泰国机构/政治人物/非常见地名/专业术语（正文首次出现）
- 不需要：曼谷/芭提雅/泰铢/签证/常见国家名

### 第5步：生成期数 JSON

将选好的新闻整理为以下格式，保存为 `data/issues/YYYY-MM-DD.json`：

**`highlights` 字段：** 从本期所有文章中，按全局编号顺序（第一个板块第1条=0），选出5条最重要的，填入 `highlights` 列表。显示在页面顶部"本期要闻"区块。

```json
{
  "date": "YYYY-MM-DD",
  "issue": N,
  "highlights": [2, 0, 8, 13, 5],
  "sections": {
    "thailand": [
      {
        "title": "...",
        "city_tag": "#泰国",
        "topic_tag": "#时政",
        "body": "...",
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

**生成后立即验证 JSON 格式：**
```bash
python3 -c "import json; json.load(open('data/issues/YYYY-MM-DD.json')); print('JSON OK')"
```
若报错，立即修复（最常见：body/title/comment 里有未转义的英文双引号 `"` → 改为 `\"`）。

### 第6步：生成 HTML
```bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/build_html.py data/issues/YYYY-MM-DD.json
```

### 第7步：更新记忆文件

**更新 news_pool.json：**
将本期选用的条目 `status` 改为 `"published"`，并加上：
```json
"published_issue": N,
"published_date": "YYYY-MM-DD"
```

**更新 buffer.json（溢出写入）：**
本期未选用但 P1/P2 的优质稿件，写入 buffer.json：
```json
{
  "id": "...",
  "title_cn": "...",
  "section_hint": "...",
  "importance": "P1/P2/P3",
  "time_sensitive": true,
  "added_date": "YYYY-MM-DD",
  "expires_date": "YYYY-MM-DD",
  "article": { ... 完整文章对象 ... }
}
```
写入前清除已过期条目（expires_date < 今日）。

**归档（仅追加，不用于去重）：**
将本期所有发布条目追加写入 `data/published_history_thai10.json`：
```json
{"title": "...", "date": "YYYY-MM-DD", "issue": N}
```

### 第8步：推送到 GitHub
```bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
git add -A
git commit -m "🗞️ Thailand10 第N期 YYYY-MM-DD"
git push origin main
```

### 第9步：通知 Ade
使用 `message` 工具发送 Telegram 消息（**必须用 message 工具 + channel:telegram + to:"818033361"，不是 webchat**）：

```
🗞️ 泰兰德10:00 第N期已发布

📅 YYYY年MM月DD日 周X
📊 本期精选 XX 条新闻

🔗 https://jiuting6.github.io/bangkok-news/thailand10/YYYY-MM-DD.html

【速览】
· [最重要的1-2条标题]
· [第二重要的标题]
```

---

## 注意事项
- **⚠️ 不得调用 web_search**，所有选编原料只能来自 news_pool.json + buffer.json
- 若 news_pool.json 完全为空（ingest cron 从未运行），则一次性运行 fetch_rss.py + fetch_brave.py 兜底，并将结果临时处理入库后再选编
- GitHub Pages URL格式：`https://jiuting6.github.io/bangkok-news/...`
- JSON 字符串内英文双引号必须转义为 `\"`，或改用中文引号「」/""
- 空板块不显示，不为填充板块降低编辑标准
