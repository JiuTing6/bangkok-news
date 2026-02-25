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
- `data/history.json`    → 已发布hash，用于去重
- `data/tracking.json`   → 持续追踪议题，本期如有进展需标注 🔄
- `data/rotation.json`   → 长期内容轮播记录

### 第3步：抓取新闻原料
运行 RSS 抓取（过去4天，周四刊；过去4天含周末，周一刊）：
```bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/fetch_rss.py 4 > /tmp/raw_rss.json
```

同时用 web_search 补充搜索（英文+泰文，见下方关键词组）。

**Brave搜索关键词组（每期必跑）：**
1. `Thailand politics coalition government 2026` [EN]
2. `Thailand People's Party OR Pheu Thai OR Bhumjaithai` [EN]
3. `ข่าวการเมืองไทย รัฐบาล ล่าสุด` [TH]
4. `Thailand economy GDP inflation central bank 2026` [EN]
5. `เศรษฐกิจไทย ล่าสุด 2569` [TH]
6. `Thailand data center cloud AI investment 2026` [EN]
7. `Thailand visa expat foreigner policy 2026` [EN]
8. `Pattaya luxury condo "Wong Amat" OR "Na Kluea" OR "North Pattaya" 2026` [EN]
9. `พัทยาเหนือ คอนโด หรู ต่างชาติ 2569` [TH]
10. `Thailand property market luxury foreign buyer 2026` [EN]
11. `อสังหาริมทรัพย์ ไทย ต่างชาติ ซื้อ 2569` [TH]
（中泰触发式：只在有重磅时搜 `China Thailand investment railway scandal 2026`）

### 第4步：编辑选题（核心工作）

**精选原则：宁少勿滥，不凑数**

按版块分配（配额为上限）：
- 🇹🇭 泰国：7–8条（政治/经济/科技基建/社会/外国人签证）
- 📊 房产专题：3–4条（全泰，精选重要动态）
- 🌆 曼谷：5–6条（城市/交通/安全/房产）
- 🏖️ 芭提雅：4–5条（社区旅游前置，房产精准聚焦北芭提雅/Na Kluea/Wong Amat/Phra Tamnak）
- 🇨🇳🇹🇭 中泰：0–3条（无重磅可跳过）

**优先级：**
- P1：影响外国人的政策、重大安全事件、追踪议题重要进展 → 必收
- P2：政治走向、经济指标、科技基建落地、房产重大动态 → 优先
- P3：全国文化娱乐旅游（非Sukhumvit本地） → 填充用

**去重：**与 `history.json` 中的hash比对，已发布的跳过。
追踪议题有进展时，可更新已有议题，标注 🔄持续追踪。

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

将选好的新闻整理为以下格式，保存为 `/tmp/issue_thailand10.json`：

```json
{
  "date": "YYYY-MM-DD",
  "issue": N,
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

### 第7步：生成 HTML
```bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
python3 scripts/build_html.py /tmp/issue_thailand10.json
```

### 第8步：更新记忆文件
- 将本期所有新闻的 hash 写入 `data/history.json`
- 更新 `data/tracking.json` 中相关追踪议题的 `last_seen` 和 `summary`

### 第9步：推送到 GitHub
```bash
cd /Users/Ade/.openclaw/workspace/bangkok-news
git add -A
git commit -m "🗞️ Thailand10 第N期 YYYY-MM-DD"
git push origin main
```

### 第10步：通知 Ade
发送 webchat 消息：
```
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
