#!/usr/bin/env python3
"""
Thailand10 HTML 生成器
用法：python3 build_html.py <issue_json_file>
输出：HTML文件写入 thailand10/YYYY-MM-DD.html
      同时更新 thailand10/index.html 归档列表
"""

import json
import sys
import os
from datetime import datetime

WEEKDAYS_ZH = ["周一","周二","周三","周四","周五","周六","周日"]

SECTIONS = [
    {"id":"thailand",  "icon":"🇹🇭", "cn":"泰国",       "en":"Thailand",         "cls":"thai"},
    {"id":"property",  "icon":"📊", "cn":"房产专题",    "en":"Property",          "cls":"property"},
    {"id":"bangkok",   "icon":"🌆", "cn":"曼谷",        "en":"Bangkok",           "cls":"bkk"},
    {"id":"pattaya",   "icon":"🏖️","cn":"芭提雅",      "en":"Pattaya",           "cls":"pattaya"},
    {"id":"cn_thai",   "icon":"🇨🇳🇹🇭","cn":"中泰动态","en":"China-Thailand",    "cls":"cn"},
]

def tag_html(tag_text, tag_type="normal"):
    cls = {"tracking":"tracking","urgent":"urgent","china":"china"}.get(tag_type,"")
    return f'<span class="tag {cls}">{tag_text}</span>'

def article_html(a, idx):
    tags_html = ""
    for t in a.get("tags", []):
        ttype = "normal"
        if "🔄" in t: ttype = "tracking"
        if "⚠️" in t: ttype = "urgent"
        tags_html += tag_html(t, ttype)

    comment_html = ""
    if a.get("comment"):
        comment_html = f'<div class="article-comment">{a["comment"]}</div>'

    date_str = a.get("date","")
    source   = a.get("source","")
    url      = a.get("url","#")

    return f'''
    <div class="article-item" id="a{idx}">
      <div class="article-tags">{tags_html}</div>
      <div class="article-title">{a["title"]}</div>
      <div class="article-body">{a["body"]}</div>
      {comment_html}
      <div class="article-source">
        <span>📅 {date_str}</span>
        <span class="source-dot">·</span>
        <span>来源：{source}</span>
        <span class="source-dot">·</span>
        <a href="{url}" target="_blank" rel="noopener">→ 阅读原文</a>
      </div>
    </div>'''

def section_html(section, articles):
    if not articles:
        return ""
    items_html = "\n".join(article_html(a, i) for i, a in enumerate(articles))
    count = len(articles)
    return f'''
  <div class="section">
    <div class="section-header {section['cls']}">
      <span class="section-icon">{section['icon']}</span>
      <span class="section-title-cn">{section['cn']}</span>
      <span class="section-count">({count}条)</span>
      <span class="section-title-en">{section['en']}</span>
    </div>
    <div class="article-list">
      {items_html}
    </div>
  </div>'''

def build_issue(issue_data, output_dir):
    date_str  = issue_data["date"]          # "2026-02-28"
    issue_num = issue_data.get("issue", "")
    dt        = datetime.strptime(date_str, "%Y-%m-%d")
    weekday   = WEEKDAYS_ZH[dt.weekday()]
    total     = sum(len(issue_data["sections"].get(s["id"],[]))
                    for s in SECTIONS)

    sections_html = ""
    for sec in SECTIONS:
        arts = issue_data["sections"].get(sec["id"], [])
        sections_html += section_html(sec, arts)

    # 上下期导航（简单，由归档index处理）
    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>泰兰德10:00 | {date_str} {weekday}</title>
  <link rel="stylesheet" href="../assets/style-thailand10.css">
</head>
<body>

<header class="site-header">
  <div class="header-inner">
    <div class="header-kicker">Thailand 10:00 &nbsp;·&nbsp; 第 {issue_num} 期</div>
    <div class="header-title">🇹🇭 泰兰德<span>10:00</span></div>
    <div class="header-meta">
      <strong>{date_str} &nbsp;{weekday}</strong>
      <span>共 {total} 条精选新闻</span>
      <span>政治 · 经济 · 房产 · 科技 · 外国人事务</span>
    </div>
  </div>
</header>

<main class="main-content">
  {sections_html}
</main>

<footer class="site-footer">
  <div class="footer-nav">
    <a href="index.html">← 归档列表</a>
    <a href="../index.html">首页</a>
    <a href="../moments/index.html">素坤逸拾光</a>
  </div>
  <div>Bangkok News Hub · 泰兰德10:00 · {date_str}</div>
</footer>

</body>
</html>'''

    filename = f"{date_str}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] 生成: {filepath} ({total}条)")
    return filename, date_str, total, weekday

def update_archive(output_dir, filename, date_str, total, weekday):
    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_entry = f'''    <div class="archive-item">
      <a href="{filename}">🇹🇭 {date_str} {weekday}</a>
      <span class="archive-date">{date_str}</span>
      <span class="archive-count">{total}条</span>
    </div>'''

    marker = "<!-- 归档条目由脚本自动插入 -->\n  <div id=\"archive-entries\">"
    replacement = f'{marker}\n{new_entry}'
    content = content.replace(marker, replacement)

    # 移除"即将发布"占位符
    content = content.replace(
        '\n    <div style="color:#bbb; font-family:var(--font-ui); font-size:14px; padding:40px 0; text-align:center;">\n      第一期即将发布...\n    </div>', ''
    )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] 归档更新: {date_str}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 build_html.py <issue.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        issue_data = json.load(f)

    base_dir   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "thailand10")

    filename, date_str, total, weekday = build_issue(issue_data, output_dir)
    update_archive(output_dir, filename, date_str, total, weekday)
