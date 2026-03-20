# 泰兰德10:00 / Thailand 10:00 — 完整策划案

**版本：** v0.3
**更新：** 2026-02-26
**状态：** 试运营中（第2期已发布），改进进行中

---

## 一、产品定位

面向**曼谷/芭提雅外籍长居者**的双周中文新闻简报。
精选泰国政经、房产、城市生活动态，以中文深度摘要呈现，辅以编辑评论，省去读者自行搜索的时间成本。

- **目标读者：** 在泰外籍华人，尤其是 Sukhumvit / 芭提雅北部长居者
- **语言：** 中文为主，专有名词首次出现附英文对照
- **发布渠道：** GitHub Pages 静态网站
- **网址：** https://jiuting6.github.io/bangkok-news/

---

## 二、发布节奏

| 刊次 | 时间 | Cron |
|------|------|------|
| 周四刊 | 每周四 09:30 BKK | `30 9 * * 4 @ Asia/Bangkok` |
| 周一刊 | 每周一 09:30 BKK | `30 9 * * 1 @ Asia/Bangkok` |

Sub-agent 全自动执行：抓取 → 选题 → 撰稿 → 生成 HTML → 推送 GitHub → 通知。

---

## 三、板块结构（动态配额）

| 板块 | 图标 | 说明 | 配额 |
|------|------|------|------|
| **政经动态** | 📡 | 政治/经济/科技基建/签证外国人事务 | 无上限，兜底板块 |
| **房地产** | 🏠 | 全泰精选房产动态 | 动态，可为0 |
| **曼谷** | 🛺 | 严格只收曼谷本地新闻 | 动态，可为0 |
| **芭提雅** | 🌅 | 聚焦北芭/Na Kluea/Wong Amat/Phra Tamnak | 动态，可为0 |
| **中泰** | 🚅 | 触发式：无重磅直接省略 | 动态，可为0 |

**原则：宁缺毋滥。空板块不显示，不为填充板块而降低编辑标准。**

---

## 四、每期发布量

- **硬性下限（Hard Floor）：** 10条。低于此须启用内容储备库或加大搜索力度
- **软性参考值（Soft Ceiling）：** 25条。新闻密集期可突破，无硬性上限
- **溢出处理：** 超出25条的优质稿件存入内容储备库（`data/buffer.json`），供淡季调取

---

## 五、选题三原则（优先级顺序）

1. **原料优先** — 以本期实际扫描到的新闻为第一基础，有什么选什么，不虚构不补填
2. **重要性优先** — 以新闻本身的重要性、时效性和影响力为核心筛选标准，编辑判断永远第一
3. **板块关联度** — 在重要性相近的情况下，以与板块的相关性决定归属，不为填充板块而降标

---

## 六、新闻重要性分级

| 级别 | 内容 | 处理 |
|------|------|------|
| **P1** | 影响外国人的政策、重大安全事件、追踪议题重要进展 | 必收 |
| **P2** | 政治走向、经济指标、科技基建落地、房产重大动态 | 优先收录 |
| **P3** | 全国文化娱乐旅游、生活服务 | 版面宽裕时收录，或存入储备库 |

---

## 七、内容储备库（Editorial Buffer）

**文件：** `data/buffer.json`

存稿分两类：

| 类型 | 内容示例 | 有效期 |
|------|---------|--------|
| **时效性内容** | 政策/经济数据/安全事件 | 14天 |
| **时效中性内容** | 新开酒店/餐厅/寺庙/地标/生活指南 | 90天（读者不感知时间差）|

**调取规则：**
- 每期新鲜内容不足10条时启用
- 优先级：P1/P2 > P3；时效性内容 > 时效中性内容
- 与本期已有内容不重复

---

## 八、新闻库与 Tracking

**文件：** `data/published_history.json`、`data/tracking.json`、`data/buffer.json`

每条新闻入库字段：

```json
{
  "hash": "去重用",
  "title": "标题",
  "section": "建议板块",
  "importance": "P1/P2/P3",
  "time_sensitive": true,
  "date": "原文日期",
  "published": false,
  "published_issue": null,
  "tracking": false,
  "popularity": { "up": 0, "down": 0 },
  "weight_bonus": 0.0
}
```

**持续追踪（🔄）：** 重要议题（如新内阁组建、签证政策改革）跨期持续追踪，有进展时标注 🔄，存于 `data/tracking.json`。

---

## 九、受欢迎度权重机制（Popularity Bonus）

- **来源：** 读者 👍🏻 / 👎🏻 反馈，每条新闻独立累计
- **作用范围：** 仅在**重要性相近（同P级）的候选稿件之间**作为加权 tiebreaker
- **权重上限：** 不覆盖编辑对重要性/质量的判断；编辑判断永远第一
- **长期效应：** 某类话题持续获得高 👍，可适度提高同类话题的搜索优先级
- **实现：** 前端 👍👎 点击 → 写入静态 JSON（或未来接 API）→ sub-agent 读取权重

---

## 十、每条新闻格式规范

```
标题：中文，首次出现专有名词附英文
正文：150–300字（深度内容可至500字；简单数据50–150字）
编辑评论（视情况添加）：
  💬 多一嘴  ⚠️ 请注意  🤔 琢磨着  👀 看点  🌶️ 辣评
来源：日期 + 媒体名 + 原文链接
```

**专有名词附英文规则：**
- 需要：泰国机构/政治人物/省府/非常见地名/专业术语（首次出现）
- 不需要：曼谷/芭提雅/泰铢/签证/常见国家名

**来源核实原则：** 必须抓取并阅读原文，不得仅凭搜索摘要编写内容，不得使用地产中介/广告网站作为新闻来源。

---

## 十一、搜索策略

**每期必跑（RSS + Brave双轨）：**

RSS 抓取：`python3 scripts/fetch_rss.py 4 > /tmp/raw_rss.json`

Brave 搜索关键词组（11组，英文+泰文）：
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

曼谷专属补充（每期加跑）：
- `Bangkok city news Sukhumvit local 2026`
- `Bangkok Metropolitan Administration event development 2026`

中泰触发式（有重磅才跑）：
- `China Thailand investment railway scandal event 2026`

---

## 十二、待实现功能清单

| 优先级 | 功能 | 状态 |
|--------|------|------|
| 🔴 高 | Sub-agent prompt 改进（弹性板块/曼谷严格过滤/buffer逻辑） | 待实现 |
| 🔴 高 | 板块重命名：泰国 → 政经 | 待实现 |
| 🟡 中 | `data/buffer.json` 结构设计与调取逻辑 | 待实现 |
| 🟡 中 | 手机端字体增大一档 | 待实现 |
| 🟡 中 | 👍🏻👎🏻 用户反馈按钮（前端+数据存储） | 待实现 |
| 🟢 低 | Moments（素坤逸拾光）专栏启动 | 待开坑 |

---

## 十三、项目文件结构

```
bangkok-news/
├── index.html              # 主页/归档列表
├── PROJECT.md              # 本策划案
├── thailand10/
│   ├── index.html          # 期数归档
│   └── YYYY-MM-DD.html     # 每期正文
├── moments/                # 素坤逸拾光（待开坑）
├── data/
│   ├── published_history.json        # 已发布hash，去重用
│   ├── tracking.json       # 持续追踪议题
│   ├── rotation.json       # 长期内容轮播
│   └── buffer.json         # 内容储备库（待建）
├── assets/                 # 静态资源
└── scripts/
    ├── cron_prompt_thailand10.md  # Sub-agent执行手册
    ├── fetch_rss.py               # RSS抓取脚本
    └── build_html.py              # HTML生成脚本
```
