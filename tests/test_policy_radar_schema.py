import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.analyze_rmrb_policy import FIXED_INDUSTRIES, build_analysis_payload, validate_industry_scores
from scripts.rmrb_policy_skill import (
    WorkflowContext,
    build_audit_report,
    build_paths,
    normalize_parent_path,
    resolve_date,
    write_publish_request,
)
from scripts.render_policy_report import write_wps_report


def sample_articles():
    return [
        {
            "title": "推动新质生产力发展",
            "subtitle": "聚焦科技创新和高质量发展",
            "author": "记者甲",
            "page_no": "01",
            "page_name": "要闻",
            "page_title": "第01版：要闻",
            "url": "https://example.com/1",
            "content": "强调新质生产力、科技自立自强、人工智能、数字经济与高质量发展。",
        },
        {
            "title": "守住不发生系统性金融风险底线",
            "subtitle": "持续强化金融监管",
            "author": "记者乙",
            "page_no": "02",
            "page_name": "经济",
            "page_title": "第02版：经济",
            "url": "https://example.com/2",
            "content": "文章涉及金融监管、资本市场、风险防控、地方债和房地产风险。",
        },
    ]


def test_today_date_resolution_uses_shanghai():
    now = datetime(2026, 4, 28, 0, 30, tzinfo=ZoneInfo("UTC"))
    assert resolve_date("today", now=now) == "2026-04-28"


def test_industry_scores_schema_complete():
    payload = build_analysis_payload("2026-04-28", sample_articles(), "full markdown")
    validate_industry_scores(payload["industry_scores"])
    row = payload["industry_scores"][0]
    assert set(["industry", "direction", "policy_tailwind_score", "risk_pressure_score", "market_relevance_score", "signal_strength", "confidence", "time_horizon", "summary", "evidence_articles", "tags"]).issubset(row.keys())


def test_fixed_industry_pool_exists():
    assert "人工智能" in FIXED_INDUSTRIES
    assert "银行" in FIXED_INDUSTRIES
    assert len(FIXED_INDUSTRIES) >= 30


def test_investment_signals_json_loadable():
    payload = build_analysis_payload("2026-04-28", sample_articles(), "full markdown")
    data = {
        "date": payload["date"],
        "source": payload["source"],
        "market": payload["market"],
        "total_policy_scores": payload["total_policy_scores"],
        "top_policy_themes": payload["top_policy_themes"],
        "industry_scores": payload["industry_scores"],
        "risk_alerts": payload["risk_alerts"],
        "watch_tags": payload["watch_tags"],
    }
    assert json.loads(json.dumps(data, ensure_ascii=False))["source"] == "人民日报"


def test_wps_report_contains_title():
    payload = build_analysis_payload("2026-04-28", sample_articles(), "full markdown")
    text = write_wps_report("2026-04-28", payload)
    assert "# 人民日报政策风向日报｜2026-04-28" in text


def test_publish_request_structure(tmp_path: Path):
    report = tmp_path / "wps_report.md"
    report.write_text("# x\n", encoding="utf-8")
    req_path = write_publish_request(tmp_path, "2026-04-28", report)
    data = json.loads(req_path.read_text(encoding="utf-8"))
    assert data["target"] == "kingsoft_doc"
    assert data["action"] == "create_or_update"
    assert data["content_format"] == "markdown"


def test_normalize_parent_path():
    assert normalize_parent_path("人民日报政策风向日报/2026") == ["人民日报政策风向日报", "2026"]
    assert normalize_parent_path("/A//B/") == ["A", "B"]


def test_audit_report_passes_without_publish(tmp_path: Path):
    date_str = "2026-04-28"
    paths = build_paths(tmp_path, date_str)
    paths.source_dir.mkdir(parents=True, exist_ok=True)
    paths.full_md.write_text("full markdown", encoding="utf-8")
    paths.articles_jsonl.write_text('{"title":"x"}\n', encoding="utf-8")
    paths.index_json.write_text("{}", encoding="utf-8")
    context = WorkflowContext(
        project_root=tmp_path,
        output_root=tmp_path,
        date_str=date_str,
        title=f"人民日报政策风向日报｜{date_str}",
        crawler_script=tmp_path / "rmrb_crawler.py",
        paths=paths,
    )
    payload = build_analysis_payload(date_str, sample_articles(), "full markdown")
    prompts = {name: "ok" for name in ["daily_summary_prompt.md", "policy_radar_prompt.md", "industry_score_prompt.md", "wps_report_prompt.md"]}
    report = build_audit_report(context, payload, prompts, publish_requested=False)
    assert report["passed"] is True
    assert any(item["name"] == "fixed_industry_pool" and item["ok"] for item in report["checks"])
