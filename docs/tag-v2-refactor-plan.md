# Thailand10 Tag v2 重构计划
> 制定时间：2026-03-19
> 状态：待执行（/new 后开始）

---

## 背景

原有 tag 系统（40+个随意生长的 tag）导致 Newsroom UI 在 PC 占4行、Mobile 占半屏。
本次重构引入两层结构：city_tag（城市）+ topic_tag（主题），并重设 ingest 控量逻辑。

**已完成（2026-03-18）：**
- city_tag + topic_tag 字段结构已上线（10个topic）
- 存量513条已迁移
- newsroom.html 双层筛选 UI 已上线
- translate.py / publish.md 已更新

---

## 本次待执行

### 一、Topic 从10个调整为9个

原10个 → 合并 #旅游/#生活/#文化/#教育 → **#旅居**

**最终9个Topic + 每日限额：**

| 级别 | Topic | 每日限额 | 覆盖内容 |
|---|---|---|---|
| 一级 | #时政 | 5条 | 政治/外交/地缘/政府决策 |
| 一级 | #经济 | 5条 | 宏观经济/金融/贸易/能源价格/BOI |
| 一级 | #安全 | 5条 | 犯罪/交通事故/灾害/骗局预警 |
| 一级 | #旅居 | 5条 | 旅游/生活/美食/文化/教育/签证移民/健康日常 |
| 一级 | #社会 | 5条 | 社会事件/奇闻/人情味故事 |
| 二级 | #房产 | 3条 | 房地产/基建/开发商/买房政策 |
| 二级 | #科技 | 3条 | AI/新能源技术/数据中心/智慧城市 |
| 二级 | #中泰 | 3条 | 中泰双边/中国投资/华人社区 |
| 二级 | #健康 | 3条 | 医疗/食品安全/公共卫生/药品 |

**理论上限：** 5×5 + 4×3 = 37条，实际预计25-30条/天

---

### 二、RSS源调整（停用Brave）

**停用 fetch_brave.py**（保留脚本但不在orchestrator调用）

**RSS源从6个扩展到9个（均为Bangkok Post分类 + 原有其他源）：**

新增BP分类（3个）：
- `https://www.bangkokpost.com/rss/data/thailand.xml` → #时政 #安全 #社会
- `https://www.bangkokpost.com/rss/data/business.xml` → #经济 #科技 #中泰
- `https://www.bangkokpost.com/rss/data/life.xml`     → #旅居

保留（6个）：
- BP topstories / BP property
- Thaiger全站 / Thaiger Bangkok
- Khaosod English / The Nation / Pattaya Mail

去掉：Brave的4个搜索组

---

### 三、Filter 重写（核心变化）

**文件：** `scripts/filter.py`

**原逻辑：** LLM判断泰国相关性（keep/skip）

**新逻辑：**
1. LLM对每条新闻判断：
   - `topic_tag`：归入9个topic之一（不相关泰国本地则直接淘汰）
   - `relevance_score`：0.1-0.9，该新闻与所属topic的关联度
2. relevance_score < 0.4 → 直接淘汰
3. 输出字段新增：`topic_tag`、`relevance_score`

**注意：** city_tag 继续由 translate.py 生成（需要看内容定城市）

---

### 四、Dedup 升级（新增控量逻辑）

**文件：** `scripts/dedup.py`

**原逻辑：** 语义去重（与pool历史比较）

**新增逻辑（去重后执行）：**
1. 按 topic_tag 分组
2. 每个topic内按 relevance_score 降序排列
3. 各topic按限额截断：一级topic取前5条，二级topic取前3条
4. 合并输出，总量≤37条

**TOPIC_LIMITS 配置：**
```python
TOPIC_LIMITS = {
    "#时政": 5, "#经济": 5, "#安全": 5, "#旅居": 5, "#社会": 5,
    "#房产": 3, "#科技": 3, "#中泰": 3, "#健康": 3,
}
```

---

### 五、Translate 调整

**文件：** `scripts/translate.py`

- `topic_tag`：**不再生成**，直接从输入继承（filter已确定）
- `relevance_score`：**不再生成**，直接从输入继承
- `city_tag`：继续生成（9个城市规则同前，#更多地区兜底）
- `importance`：继续生成（P1/P2/P3，仅用于前端展示）
- `tags`：继续输出 `[]`

---

### 六、Orchestrator 调整

**文件：** `experiment/prompts/orchestrator.md`

- 第3步：去掉 `fetch_brave.py` 调用
- Telegram通知模板：去掉 `板块` 行，改为显示各topic入库数

---

### 七、存量迁移

**脚本：** `scripts/migrate_tags.py`（更新后重跑）

存量pool中需要合并的topic_tag：
- `#旅游` → `#旅居`
- `#生活` → `#旅居`
- `#文化` → `#旅居`
- `#教育` → `#旅居`
- `#健康`（如有）→ `#健康`（保持）

---

### 八、Newsroom UI 调整

**文件：** `newsroom.html`

- TOPIC_TAGS 数组：从10个更新为9个（去掉#旅游/#生活/#文化/#教育，加#旅居/#中泰/#健康）
- Brave 小圆点标记：保留（存量有 origin="brave" 的条目）
- 城市筛选逻辑：不变

---

### 九、Publish 提示词调整

**文件：** `experiment/prompts/publish.md`

- Topic列表更新为9个
- section结构保持不变（版面组织）

---

## 执行顺序

1. 备份 news_pool.json
2. 存量迁移（migrate_tags.py）
3. 改 fetch_rss.py（新增3个BP源）
4. 改 filter.py（核心重写）
5. 改 dedup.py（新增控量）
6. 改 translate.py（精简字段）
7. 改 orchestrator.md（去Brave，更新通知模板）
8. 改 newsroom.html（9个topic按钮）
9. 改 publish.md（topic列表）
10. git push
11. 手动跑一次 ingest 验证全链路

---

## 注意事项

- filter.py 和 dedup.py 改动影响每日 cron，改完后当天手动跑一次验证
- relevance_score 阈值 0.4 可以后续根据实际数据调整
- Brave API key 保留在 fetch_brave.py，随时可重启
- 存量条目无 relevance_score 字段，Newsroom 不展示分数（仅内部字段）
