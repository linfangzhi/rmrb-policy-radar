#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

FIXED_INDUSTRIES = [
    "银行", "券商", "保险", "地产", "建筑基建", "消费", "食品饮料", "医药", "新能源", "电力", "煤炭", "石油石化",
    "有色金属", "钢铁", "化工", "汽车", "低空经济", "人工智能", "半导体", "算力", "数据要素", "软件信创",
    "通信", "军工", "机器人", "高端制造", "农业", "环保", "物流航运", "文化传媒", "旅游", "教育",
]

WATCH_TAGS = [
    "稳增长", "扩内需", "新质生产力", "科技自立自强", "金融监管", "资本市场", "地方债", "地产风险", "民营经济", "外贸",
    "出口链", "粤港澳大湾区", "乡村振兴", "人口老龄化", "银发经济", "能源安全", "粮食安全", "产业升级", "价格改革",
    "安全生产", "绿色低碳", "数字经济", "数据要素", "人工智能+", "制造强国",
]

THEME_RULES: dict[str, dict[str, Any]] = {
    "稳增长": {"keywords": ["稳增长", "扩大内需", "投资", "消费", "项目建设", "基础设施", "促消费"], "industries": ["建筑基建", "消费", "食品饮料", "地产"]},
    "新质生产力": {"keywords": ["新质生产力", "科技创新", "高质量发展", "产业升级", "先进制造"], "industries": ["高端制造", "人工智能", "机器人", "半导体"]},
    "科技自立自强": {"keywords": ["科技自立自强", "关键核心技术", "自主可控", "国产替代"], "industries": ["半导体", "软件信创", "通信", "高端制造"]},
    "数字经济": {"keywords": ["数字经济", "数据要素", "算力", "平台", "数字化"], "industries": ["数据要素", "算力", "软件信创", "通信"]},
    "人工智能+": {"keywords": ["人工智能", "大模型", "智能化", "算法"], "industries": ["人工智能", "算力", "软件信创", "机器人"]},
    "金融监管": {"keywords": ["金融监管", "风险防控", "监管", "资本市场", "非法金融", "防风险"], "industries": ["银行", "券商", "保险"]},
    "地产风险": {"keywords": ["房地产", "保交楼", "化债", "地方债", "债务", "风险处置"], "industries": ["地产", "银行", "建筑基建"]},
    "能源安全": {"keywords": ["能源安全", "电力", "煤炭", "油气", "保供"], "industries": ["电力", "煤炭", "石油石化", "新能源"]},
    "绿色低碳": {"keywords": ["绿色低碳", "碳达峰", "碳中和", "节能", "环保"], "industries": ["新能源", "环保", "电力"]},
    "粮食安全": {"keywords": ["粮食安全", "种业", "耕地", "农业", "乡村振兴"], "industries": ["农业"]},
    "外贸": {"keywords": ["外贸", "出口", "订单", "国际市场", "跨境"], "industries": ["物流航运", "汽车", "消费"]},
    "低空经济": {"keywords": ["低空经济", "无人机", "通航"], "industries": ["低空经济", "军工", "高端制造"]},
}

INDUSTRY_RULES: dict[str, dict[str, Any]] = {
    "银行": {"pos": ["金融", "银行", "信贷", "服务实体经济"], "risk": ["风险防控", "地方债", "地产风险"]},
    "券商": {"pos": ["资本市场", "直接融资", "改革", "上市公司"], "risk": ["严监管", "风险防控", "违法违规"]},
    "保险": {"pos": ["养老", "保障", "普惠金融"], "risk": ["严监管", "风险防控"]},
    "地产": {"pos": ["城市更新", "住房保障", "稳楼市"], "risk": ["房地产", "化债", "去库存", "风险处置"]},
    "建筑基建": {"pos": ["基建", "项目建设", "重大工程", "投资"], "risk": ["地方债", "化债"]},
    "消费": {"pos": ["扩内需", "促消费", "消费升级"], "risk": ["需求不足", "价格", "外需回落"]},
    "食品饮料": {"pos": ["消费", "内需", "餐饮", "农产品"], "risk": ["食品安全", "价格波动"]},
    "医药": {"pos": ["医疗", "医药", "健康", "创新药"], "risk": ["集采", "监管"]},
    "新能源": {"pos": ["绿色低碳", "新能源", "储能", "风电", "光伏"], "risk": ["产能过剩", "消纳", "价格战"]},
    "电力": {"pos": ["电力", "能源安全", "保供"], "risk": ["安全生产", "保供压力"]},
    "煤炭": {"pos": ["煤炭", "保供", "能源安全"], "risk": ["安全生产", "减排"]},
    "石油石化": {"pos": ["油气", "能源安全", "炼化"], "risk": ["国际油价", "地缘政治"]},
    "有色金属": {"pos": ["资源保障", "新材料", "新能源"], "risk": ["价格波动", "外部扰动"]},
    "钢铁": {"pos": ["制造业", "基建", "重大工程"], "risk": ["产能", "环保约束"]},
    "化工": {"pos": ["新材料", "制造业升级", "化工"], "risk": ["安全生产", "环保"]},
    "汽车": {"pos": ["汽车", "新能源车", "出口"], "risk": ["价格竞争", "外贸摩擦"]},
    "低空经济": {"pos": ["低空经济", "无人机", "通航"], "risk": ["监管", "安全"]},
    "人工智能": {"pos": ["人工智能", "智能化", "算法", "新质生产力"], "risk": ["监管", "安全"]},
    "半导体": {"pos": ["芯片", "半导体", "自主可控", "关键核心技术"], "risk": ["卡脖子", "外部封锁"]},
    "算力": {"pos": ["算力", "数据中心", "数字基础设施"], "risk": ["投资过热", "能耗"]},
    "数据要素": {"pos": ["数据要素", "数据流通", "数字经济"], "risk": ["数据安全", "合规"]},
    "软件信创": {"pos": ["软件", "操作系统", "国产化", "信创"], "risk": ["合规", "监管"]},
    "通信": {"pos": ["通信", "5G", "网络基础设施"], "risk": ["国际摩擦", "投入回报"]},
    "军工": {"pos": ["国防", "军工", "装备"], "risk": ["节奏波动", "预算约束"]},
    "机器人": {"pos": ["机器人", "自动化", "智能制造"], "risk": ["估值过热", "技术落地"]},
    "高端制造": {"pos": ["高端制造", "先进制造", "装备"], "risk": ["投资周期", "外部限制"]},
    "农业": {"pos": ["农业", "粮食安全", "种业", "乡村振兴"], "risk": ["灾害", "价格波动"]},
    "环保": {"pos": ["环保", "绿色低碳", "污染治理"], "risk": ["财政约束", "回款周期"]},
    "物流航运": {"pos": ["物流", "航运", "外贸", "供应链"], "risk": ["外需波动", "地缘风险"]},
    "文化传媒": {"pos": ["文化", "传播", "内容产业"], "risk": ["内容监管"]},
    "旅游": {"pos": ["文旅", "消费", "服务业"], "risk": ["需求波动", "突发事件"]},
    "教育": {"pos": ["教育", "人才", "技能", "职业教育"], "risk": ["监管", "财政约束"]},
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def article_text(article: dict[str, Any]) -> str:
    return normalize_text(" ".join([
        article.get("title", ""),
        article.get("subtitle", ""),
        article.get("author", ""),
        article.get("page_name", ""),
        article.get("page_title", ""),
        article.get("content", ""),
    ]))


def build_article_digest(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    digest = []
    for article in articles:
        text = article_text(article)
        digest.append({
            "title": article.get("title", ""),
            "page_no": article.get("page_no", ""),
            "page_name": article.get("page_name", ""),
            "page_title": article.get("page_title", ""),
            "url": article.get("url", ""),
            "classification": classify_article(article),
            "excerpt": text[:240],
            "word_count": article.get("word_count", 0),
        })
    return digest


def classify_article(article: dict[str, Any]) -> str:
    text = article_text(article)
    if any(k in text for k in ["防风险", "风险处置", "严监管", "安全生产", "化债", "地方债"]):
        return "风险预警信号"
    if any(k in text for k in ["意见", "方案", "政策", "机制", "部署", "要求"]):
        return "明确政策信号"
    if any(k in text for k in ["会议", "座谈", "强调", "推进", "实施"]):
        return "强政策信号"
    if any(k in text for k in ["报道", "记者", "采访", "消息"]):
        return "一般新闻报道"
    return "常规宣传性报道"


def chunk_articles_for_llm(articles: list[dict[str, Any]], max_articles: int = 10, max_chars: int = 10000) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_len = 0
    for article in articles:
        size = len(article_text(article))
        if current and (len(current) >= max_articles or current_len + size > max_chars):
            chunks.append(current)
            current = []
            current_len = 0
        current.append(article)
        current_len += size
    if current:
        chunks.append(current)
    return chunks


def render_analysis_input(articles: list[dict[str, Any]], full_md: str) -> dict[str, Any]:
    chunks = chunk_articles_for_llm(articles)
    return {
        "article_count": len(articles),
        "digest": build_article_digest(articles),
        "chunks": [
            {
                "chunk_id": idx + 1,
                "article_count": len(chunk),
                "digest": build_article_digest(chunk),
            }
            for idx, chunk in enumerate(chunks)
        ],
        "full_md_excerpt": full_md[:12000],
    }


def _make_evidence(article: dict[str, Any], reason: str) -> dict[str, str]:
    return {
        "title": article.get("title", ""),
        "page_no": article.get("page_no", ""),
        "page_name": article.get("page_name", ""),
        "url": article.get("url", ""),
        "reason": reason,
    }


def analyze_themes(articles: list[dict[str, Any]]) -> dict[str, Any]:
    theme_hits: dict[str, list[dict[str, str]]] = defaultdict(list)
    for article in articles:
        text = article_text(article)
        for theme, rule in THEME_RULES.items():
            matches = [kw for kw in rule["keywords"] if kw in text]
            if matches:
                theme_hits[theme].append(_make_evidence(article, f"命中关键词：{'、'.join(matches[:3])}"))
    top_policy_themes = []
    for theme, evidences in sorted(theme_hits.items(), key=lambda item: len(item[1]), reverse=True):
        related_industries = THEME_RULES[theme]["industries"]
        strength = min(5, max(1, len(evidences)))
        top_policy_themes.append({
            "theme": theme,
            "strength": strength,
            "related_industries": related_industries,
            "summary": f"{theme} 在当日文章中出现 {len(evidences)} 次有效证据，主要映射到 {'、'.join(related_industries[:4])}。",
            "evidence_articles": evidences[:5],
        })
    return {"theme_hits": theme_hits, "top_policy_themes": top_policy_themes[:6]}


def score_total_policy(top_policy_themes: list[dict[str, Any]], articles: list[dict[str, Any]]) -> dict[str, Any]:
    all_text = " ".join(article_text(a) for a in articles)
    macro_support = 1 + sum(k in all_text for k in ["稳增长", "扩大内需", "项目建设", "消费"])
    industrial = 1 + sum(k in all_text for k in ["新质生产力", "科技创新", "产业升级", "先进制造"])
    risk_warning = 1 + sum(k in all_text for k in ["风险", "监管", "安全生产", "化债"])
    financial_regulation = 1 + sum(k in all_text for k in ["金融监管", "资本市场", "防风险", "监管"])
    market_relevance = min(5, max(1, len({i for t in top_policy_themes for i in t.get("related_industries", [])}) // 4 + 1))
    policy_friendliness = min(5, max(1, 2 + len(top_policy_themes) // 2 + (1 if macro_support >= 4 else 0)))
    return {
        "policy_friendliness_score": policy_friendliness,
        "macro_support_score": min(5, macro_support),
        "industrial_stimulus_score": min(5, industrial),
        "risk_warning_score": min(5, risk_warning),
        "financial_regulation_score": min(5, financial_regulation),
        "market_relevance_score": min(5, market_relevance),
        "overall_comment": "当日政策文本以稳增长、产业升级与风险防控并行为主要特征。",
    }


def score_industries(articles: list[dict[str, Any]], top_policy_themes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    theme_by_industry: dict[str, list[str]] = defaultdict(list)
    for theme in top_policy_themes:
        for industry in theme.get("related_industries", []):
            theme_by_industry[industry].append(theme["theme"])

    results = []
    for industry in FIXED_INDUSTRIES:
        rule = INDUSTRY_RULES.get(industry, {"pos": [], "risk": []})
        pos_hits: list[dict[str, str]] = []
        risk_hits: list[dict[str, str]] = []
        for article in articles:
            text = article_text(article)
            pos = [kw for kw in rule["pos"] if kw in text]
            risk = [kw for kw in rule["risk"] if kw in text]
            if pos:
                pos_hits.append(_make_evidence(article, f"正向关键词：{'、'.join(pos[:3])}"))
            if risk:
                risk_hits.append(_make_evidence(article, f"风险关键词：{'、'.join(risk[:3])}"))
        tailwind = min(5, 1 + len(pos_hits))
        risk_pressure = min(5, 1 + len(risk_hits))
        market_relevance = min(5, 1 + len(theme_by_industry.get(industry, [])))
        signal_strength = min(5, max(tailwind, risk_pressure, market_relevance))
        confidence = 1 if not pos_hits and not risk_hits else min(5, 2 + len(pos_hits) + len(risk_hits))

        if tailwind >= 4 and risk_pressure <= 2:
            direction = "positive"
        elif risk_pressure >= 4 and tailwind <= 2:
            direction = "negative"
        elif tailwind >= 3 and risk_pressure >= 3:
            direction = "mixed"
        elif signal_strength >= 3:
            direction = "watch"
        else:
            direction = "neutral"

        if any(tag in ["新质生产力", "科技自立自强", "人工智能+", "数字经济", "制造强国"] for tag in theme_by_industry.get(industry, [])):
            time_horizon = "medium"
        elif risk_pressure >= 4:
            time_horizon = "short"
        elif tailwind >= 4:
            time_horizon = "long"
        else:
            time_horizon = "medium"

        tags = list(dict.fromkeys(theme_by_industry.get(industry, [])))[:3]
        summary = "；".join(filter(None, [
            f"正向信号 {len(pos_hits)} 条" if pos_hits else "",
            f"风险信号 {len(risk_hits)} 条" if risk_hits else "",
            f"关联主题：{'、'.join(tags)}" if tags else "",
        ])) or "当日未出现强相关政策文本，维持中性观察。"

        results.append({
            "industry": industry,
            "direction": direction,
            "policy_tailwind_score": tailwind,
            "risk_pressure_score": risk_pressure,
            "market_relevance_score": market_relevance,
            "signal_strength": signal_strength,
            "confidence": min(5, confidence),
            "time_horizon": time_horizon,
            "summary": summary,
            "evidence_articles": (pos_hits + risk_hits)[:5],
            "tags": tags,
        })
    return results


def build_risk_alerts(industry_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alerts = []
    for row in industry_scores:
        if row["risk_pressure_score"] >= 4 or row["direction"] == "negative":
            risk_name = row["tags"][0] if row["tags"] else f"{row['industry']}风险"
            alerts.append({
                "risk": risk_name,
                "level": row["risk_pressure_score"],
                "related_industries": [row["industry"]],
                "summary": row["summary"],
                "evidence_articles": row["evidence_articles"][:3],
            })
    return alerts[:6]


def pick_watch_tags(top_policy_themes: list[dict[str, Any]], industry_scores: list[dict[str, Any]]) -> list[str]:
    tags = [theme["theme"] for theme in top_policy_themes]
    for row in industry_scores:
        tags.extend(row.get("tags", []))
    ordered = []
    for tag in tags:
        if tag in WATCH_TAGS and tag not in ordered:
            ordered.append(tag)
    return ordered[:8]


def select_report_industries(industry_scores: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    rows = sorted(
        industry_scores,
        key=lambda row: (row["signal_strength"], row["policy_tailwind_score"], row["market_relevance_score"], -row["risk_pressure_score"]),
        reverse=True,
    )
    selected = [row for row in rows if row["signal_strength"] >= 3 or row["direction"] in {"positive", "negative", "mixed", "watch"}]
    return selected[:limit]


def build_industry_direction_buckets(industry_scores: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets = {key: [] for key in ["positive", "mixed", "watch", "neutral", "negative"]}
    for row in sorted(industry_scores, key=lambda item: (item["signal_strength"], item["market_relevance_score"], item["policy_tailwind_score"]), reverse=True):
        buckets[row["direction"]].append(row)
    return buckets


def build_analysis_payload(date_str: str, articles: list[dict[str, Any]], full_md: str) -> dict[str, Any]:
    theme_data = analyze_themes(articles)
    industry_scores = score_industries(articles, theme_data["top_policy_themes"])
    total_scores = score_total_policy(theme_data["top_policy_themes"], articles)
    risk_alerts = build_risk_alerts(industry_scores)
    watch_tags = pick_watch_tags(theme_data["top_policy_themes"], industry_scores)
    report_industries = select_report_industries(industry_scores)
    industry_direction_buckets = build_industry_direction_buckets(industry_scores)
    return {
        "date": date_str,
        "source": "人民日报",
        "market": "A股",
        "analysis_input": render_analysis_input(articles, full_md),
        "article_digest": build_article_digest(articles),
        "total_policy_scores": total_scores,
        "top_policy_themes": theme_data["top_policy_themes"],
        "industry_scores": industry_scores,
        "report_industries": report_industries,
        "industry_direction_buckets": industry_direction_buckets,
        "risk_alerts": risk_alerts,
        "watch_tags": watch_tags,
    }


def validate_industry_scores(data: list[dict[str, Any]]) -> None:
    required = {
        "industry", "direction", "policy_tailwind_score", "risk_pressure_score", "market_relevance_score",
        "signal_strength", "confidence", "time_horizon", "summary", "evidence_articles", "tags",
    }
    for row in data:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"industry score missing fields: {sorted(missing)}")
        if row["industry"] not in FIXED_INDUSTRIES:
            raise ValueError(f"unknown industry: {row['industry']}")
        if row["direction"] not in {"positive", "negative", "neutral", "mixed", "watch"}:
            raise ValueError(f"invalid direction: {row['direction']}")
        if row["time_horizon"] not in {"short", "medium", "long"}:
            raise ValueError(f"invalid time_horizon: {row['time_horizon']}")
