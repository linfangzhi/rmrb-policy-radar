#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


def _evidence_line(evidence: dict[str, Any]) -> str:
    page = evidence.get("page_no") or ""
    page_name = evidence.get("page_name") or ""
    return f"《{evidence.get('title', '')}》({page}版{page_name})"


def _theme_evidence(theme: dict[str, Any], limit: int = 3) -> str:
    return "；".join(_evidence_line(e) for e in theme.get("evidence_articles", [])[:limit]) or "暂无"


def _industry_tag_text(row: dict[str, Any]) -> str:
    return "、".join(row.get("tags", [])) or "-"


def write_daily_summary(date_str: str, payload: dict[str, Any]) -> str:
    digest = payload.get("article_digest", [])
    themes = payload.get("top_policy_themes", [])
    grouped: dict[str, list[dict[str, Any]]] = {
        "要闻与高层政策": [],
        "宏观经济与稳增长": [],
        "产业政策与科技方向": [],
        "金融监管与资本市场": [],
        "区域战略与民生": [],
        "国际环境与外部变量": [],
    }
    for row in digest:
        title = row.get("title", "")
        text = row.get("excerpt", "") + title
        if any(k in text for k in ["总书记", "中央", "会议", "部署", "要闻"]):
            grouped["要闻与高层政策"].append(row)
        elif any(k in text for k in ["内需", "消费", "投资", "经济", "增长"]):
            grouped["宏观经济与稳增长"].append(row)
        elif any(k in text for k in ["科技", "创新", "制造", "人工智能", "产业"]):
            grouped["产业政策与科技方向"].append(row)
        elif any(k in text for k in ["金融", "监管", "资本市场", "银行", "证券"]):
            grouped["金融监管与资本市场"].append(row)
        elif any(k in text for k in ["区域", "乡村", "民生", "教育", "医疗"]):
            grouped["区域战略与民生"].append(row)
        else:
            grouped["国际环境与外部变量"].append(row)

    lines = [f"# 今日新闻摘要｜{date_str}", "", "以下摘要基于当日《人民日报》已采集文章整理，偏重新闻脉络与主题归纳，不直接给出投资建议。", ""]
    if themes:
        theme_text = "、".join(theme["theme"] for theme in themes[:6])
        lines += [f"从整体现象看，当日重点主题集中在 {theme_text} 等方向，说明官方叙事在稳增长、产业升级和风险防控之间保持同步推进。", ""]
    for section, items in grouped.items():
        if not items:
            continue
        lines += [f"## {section}", ""]
        lines.append(f"当日该板块共归入 {len(items)} 篇重点文章，主要关注点如下：")
        for item in items[:6]:
            lines.append(f"- {_evidence_line(item)}：{item.get('excerpt', '')[:140]}。")
        lines.append("")
    lines += [
        "## 小结",
        "",
        "整体看，当日新闻叙事并不是单线条推进，而是同时覆盖高层部署、实体经济、重点产业、金融监管与外部环境。对于后续研究，更值得跟踪的是同一主题是否在未来数日持续扩散、是否从原则表述进一步落到部门部署和地方执行层面。",
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def write_policy_radar(date_str: str, payload: dict[str, Any]) -> str:
    scores = payload["total_policy_scores"]
    themes = payload.get("top_policy_themes", [])
    risks = payload.get("risk_alerts", [])
    report_industries = payload.get("report_industries", [])
    industry_buckets = payload.get("industry_direction_buckets", {})

    lines = [f"# 政策风向标｜{date_str}", "", "## 一、总判断", ""]
    lines.append(
        f"当日政策文本整体呈现政策友好度 {scores['policy_friendliness_score']}/5、宏观支持 {scores['macro_support_score']}/5、产业刺激 {scores['industrial_stimulus_score']}/5、风险警示 {scores['risk_warning_score']}/5、金融监管 {scores['financial_regulation_score']}/5、市场相关度 {scores['market_relevance_score']}/5。{scores['overall_comment']}"
    )
    lines += ["", "## 二、核心主题与政策含义", ""]
    for theme in themes:
        lines += [
            f"### {theme['theme']}",
            "",
            f"- 信号强度：{theme['strength']}/5",
            f"- 相关行业：{'、'.join(theme['related_industries'])}",
            f"- 政策含义：{theme['summary']}",
            f"- 证据文章：{_theme_evidence(theme)}",
            "- 观察重点：关注该主题是否由宣传表述转化为部门细则、项目推进或监管口径变化。",
            "",
        ]
    lines += [
        "## 三、政策信号分层",
        "",
        "- 常规宣传性报道：主要承担定调和氛围铺垫作用。",
        "- 一般新闻报道：提供地方实践、行业案例和执行侧线索。",
        "- 明确政策信号：常伴随部署、方案、要求、机制等措辞，说明政策意图更具体。",
        "- 强政策信号：通常表现为高层会议、重点表述反复出现，或跨版面强化同一主题。",
        "- 风险预警信号：更多指向地产、债务、金融监管、安全生产等底线管理主题。",
        "",
    ]
    if report_industries:
        lines += ["## 四、行业映射", ""]
        for row in report_industries[:8]:
            lines.append(
                f"- **{row['industry']}**：方向为 {row['direction']}，政策顺风 {row['policy_tailwind_score']}/5，风险压力 {row['risk_pressure_score']}/5，市场相关度 {row['market_relevance_score']}/5。{row['summary']}"
            )
        lines.append("")
    if industry_buckets:
        lines += ["## 五、固定行业池风向概览", ""]
        for key, label in [("positive", "正向"), ("mixed", "多空交织"), ("watch", "重点观察"), ("negative", "偏负向")]:
            rows = industry_buckets.get(key, [])[:8]
            if rows:
                lines.append(f"- {label}：" + "、".join(row["industry"] for row in rows))
        lines.append("")
    if risks:
        lines += ["## 六、风险预警", ""]
        for risk in risks:
            evidence_text = "；".join(_evidence_line(e) for e in risk.get("evidence_articles", [])[:2]) or "暂无"
            lines += [f"- {risk['risk']}（级别 {risk['level']}/5）：{risk['summary']} 证据包括 {evidence_text}。"]
        lines.append("")
    lines += [
        "## 七、A股观察口径",
        "",
        "从 A 股研究视角看，当日更适合提炼政策主线、主题扩散路径和风险压制点，而不是给出结论式交易指令。若某一主题在多篇文章、多个版面和不同层级主体表述中持续出现，其对中期行业预期的影响通常强于单篇报道。",
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def write_wps_report(date_str: str, payload: dict[str, Any]) -> str:
    title = f"人民日报政策风向日报｜{date_str}"
    scores = payload["total_policy_scores"]
    themes = payload.get("top_policy_themes", [])
    report_industries = payload.get("report_industries", [])
    all_industries = payload.get("industry_scores", [])
    industry_buckets = payload.get("industry_direction_buckets", {})
    risks = payload.get("risk_alerts", [])
    watch_tags = payload.get("watch_tags", [])

    lines = [f"# {title}", "", "## 一、今日总览", ""]
    lines.append(
        "当日《人民日报》传递出的政策信号总体呈现出“稳增长托底、产业升级主线推进、风险防控不放松”的组合特征。与单纯的刺激式叙事不同，文本重心更偏向高质量发展、科技和产业能力建设、重点领域风险处置以及中长期结构优化。对研究端来说，关键不在于单篇文章的态度，而在于多个主题是否在不同版面持续得到强化，并形成可追踪的政策主线。"
    )
    lines.append(
        f"综合评分显示，政策友好度为 {scores['policy_friendliness_score']}/5，宏观稳增长支持为 {scores['macro_support_score']}/5，产业刺激强度为 {scores['industrial_stimulus_score']}/5，风险警示强度为 {scores['risk_warning_score']}/5，金融监管强度为 {scores['financial_regulation_score']}/5，对 A 股市场的相关程度为 {scores['market_relevance_score']}/5。若用一句话概括，当日基调是“增长与转型并举，支持与约束并存”。"
    )
    if watch_tags:
        lines.append(f"从主题标签上看，今日更值得优先跟踪的方向包括：{'、'.join(watch_tags)}。")
    lines += ["", "## 二、今日新闻摘要", ""]
    for theme in themes[:6]:
        lines.append(f"### {theme['theme']}")
        lines.append("")
        lines.append(f"{theme['summary']} 主要依据包括 {_theme_evidence(theme)}。从文本分布看，该主题并非孤立出现，而是与相关产业、监管和宏观表述形成交叉印证。")
        lines.append("")

    lines += ["## 三、政策风向标", "", "| 政策方向 | 今日信号 | 强度 | 相关行业 | 判断 |", "|---|---|---:|---|---|"]
    for theme in themes[:6]:
        lines.append(
            f"| {theme['theme']} | {theme['summary']} | {theme['strength']} | {'、'.join(theme['related_industries'][:4])} | 关注是否进一步转化为部门细则、项目推进或监管口径变化 |"
        )

    lines += ["", "## 四、A 股行业风向评分", "", "| 行业 | 方向 | 政策顺风 | 风险压力 | 市场相关度 | 信号强度 | 时间维度 | 标签 |", "|---|---|---:|---:|---:|---:|---|---|"]
    for row in report_industries:
        lines.append(
            f"| {row['industry']} | {row['direction']} | {row['policy_tailwind_score']} | {row['risk_pressure_score']} | {row['market_relevance_score']} | {row['signal_strength']} | {row['time_horizon']} | {_industry_tag_text(row)} |"
        )

    lines += ["", "## 五、固定行业池风向总览", ""]
    for key, label in [("positive", "正向顺风行业"), ("mixed", "多空交织行业"), ("watch", "重点观察行业"), ("negative", "风险压制行业"), ("neutral", "中性行业")]:
        rows = industry_buckets.get(key, [])
        if rows:
            names = "、".join(row["industry"] for row in rows)
            lines.append(f"- **{label}**：{names}")
    lines += ["", "## 六、重点主题解读", ""]
    for theme in themes[:6]:
        lines += [
            f"### {theme['theme']}",
            "",
            f"1. 文章依据：{_theme_evidence(theme)}",
            f"2. 政策含义：{theme['summary']} 这一类表述通常意味着政策层面对相关方向保持持续关注，短期看有助于稳定预期，中期则需观察是否形成可执行的制度、投资或监管安排。",
            f"3. 相关行业：{'、'.join(theme['related_industries'])}",
            "4. 后续观察点：重点跟踪是否出现部委口径、地方配套、专项工程、财政金融工具或监管细则的跟进。",
            "",
        ]

    lines += ["## 七、风险提示", ""]
    if risks:
        for risk in risks:
            evidence_text = "；".join(_evidence_line(e) for e in risk.get("evidence_articles", [])[:3]) or "暂无"
            lines.append(
                f"- **{risk['risk']}**：级别 {risk['level']}/5。{risk['summary']} 从文本角度看，这类表述更多承担底线管理和预期约束功能，相关证据包括 {evidence_text}。"
            )
    else:
        lines.append("- 当日未出现特别集中的高等级风险信号，但金融监管、债务、安全生产和外部环境仍是常驻观察项。")

    lines += ["", "## 八、今日结论", ""]
    lines.append(
        "综合来看，今日政策基调偏向稳中求进，既强调高质量发展和重点产业方向，也强调风险处置和底线管理。行业主线更偏向科技升级、数字化、先进制造、能源安全以及内需相关方向；需要警惕的则是地产、债务、金融监管和安全生产等领域的约束性信号。后续最值得跟踪的，不是某个孤立结论，而是这些主题是否在未来几个交易日继续被跨版面、跨部门和跨区域重复强化。"
    )
    lines += ["", "## 附录：固定行业池完整评分", "", "| 行业 | 方向 | 政策顺风 | 风险压力 | 市场相关度 | 信号强度 | 置信度 | 时间维度 | 标签 |", "|---|---|---:|---:|---:|---:|---:|---|---|"]
    for row in all_industries:
        lines.append(
            f"| {row['industry']} | {row['direction']} | {row['policy_tailwind_score']} | {row['risk_pressure_score']} | {row['market_relevance_score']} | {row['signal_strength']} | {row['confidence']} | {row['time_horizon']} | {_industry_tag_text(row)} |"
        )
    lines += ["", "以上内容仅用于政策文本分析和投资研究记录，不构成具体投资建议。", ""]
    return "\n".join(lines).strip() + "\n"
