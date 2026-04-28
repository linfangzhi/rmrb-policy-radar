#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analyze_rmrb_policy import FIXED_INDUSTRIES, build_analysis_payload, load_jsonl, validate_industry_scores
from render_policy_report import write_daily_summary, write_policy_radar, write_wps_report

SH_TZ = ZoneInfo("Asia/Shanghai")
DEFAULT_OUTPUT = Path("./data/rmrb")


@dataclass
class SkillPaths:
    root: Path
    source_dir: Path
    analysis_dir: Path
    inputs_dir: Path
    outputs_dir: Path
    meta_dir: Path
    full_md: Path
    articles_jsonl: Path
    index_json: Path


@dataclass
class WorkflowContext:
    project_root: Path
    output_root: Path
    date_str: str
    title: str
    crawler_script: Path
    paths: SkillPaths


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="人民日报政策风向标完整工作流")
    p.add_argument("--date", required=True, help="today or YYYY-MM-DD")
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--auto-crawl", action="store_true")
    p.add_argument("--no-publish", action="store_true")
    p.add_argument("--publish-wps", action="store_true")
    p.add_argument("--crawler-script", default="")
    p.add_argument("--stage2-mode", choices=["auto", "off", "required"], default="auto")
    p.add_argument("--stage2-agent", default="xiaodaidai")
    p.add_argument("--stage2-session-id", default="")
    p.add_argument("--stage2-timeout", type=int, default=600)
    p.add_argument("--audit-only", action="store_true")
    p.add_argument("--kdocs-file-id", default=os.environ.get("RMRB_KDOCS_FILE_ID", ""))
    p.add_argument("--kdocs-parent-path", default=os.environ.get("RMRB_KDOCS_PARENT_PATH", "人民日报政策风向日报"))
    return p.parse_args()


def resolve_date(raw: str, now: datetime | None = None) -> str:
    if raw == "today":
        now = now or datetime.now(SH_TZ)
        return now.astimezone(SH_TZ).date().isoformat()
    return datetime.fromisoformat(raw).date().isoformat()


def find_crawler_script(project_root: Path, explicit: str = "") -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates += [project_root / "rmrb_crawler.py", project_root / "scripts" / "rmrb_crawler.py"]
    for path in candidates:
        if path.exists():
            return path.resolve()
    raise FileNotFoundError("cannot find rmrb crawler script")


def build_paths(output_root: Path, date_str: str) -> SkillPaths:
    source_dir = output_root / date_str
    analysis_dir = source_dir / "analysis"
    return SkillPaths(
        root=output_root,
        source_dir=source_dir,
        analysis_dir=analysis_dir,
        inputs_dir=analysis_dir / "inputs",
        outputs_dir=analysis_dir / "outputs",
        meta_dir=analysis_dir / "meta",
        full_md=source_dir / "full.md",
        articles_jsonl=source_dir / "articles.jsonl",
        index_json=source_dir / "index.json",
    )


def ensure_crawled(date_str: str, output_root: Path, auto_crawl: bool, crawler_script: Path, analysis_dir: Path) -> SkillPaths:
    paths = build_paths(output_root, date_str)
    required = [paths.full_md, paths.articles_jsonl, paths.index_json]
    if all(path.exists() for path in required):
        return paths
    if not auto_crawl:
        missing = [str(path) for path in required if not path.exists()]
        raise FileNotFoundError(f"missing required crawler outputs: {missing}")
    output_root.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(crawler_script), "--date", date_str, "--output", str(output_root)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.stderr:
        analysis_dir.mkdir(parents=True, exist_ok=True)
        (analysis_dir / "crawler_stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"crawler failed: {result.stdout or result.stderr}")
    return paths


def load_articles_jsonl(date_dir: Path) -> list[dict[str, Any]]:
    return load_jsonl(date_dir / "articles.jsonl")


def load_full_md(date_dir: Path) -> str:
    full_md = date_dir / "full.md"
    return full_md.read_text(encoding="utf-8") if full_md.exists() else ""


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_prompt(project_root: Path, name: str) -> str:
    path = project_root / "prompts" / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def mirror_output(output_path: Path, canonical_name: str, content: str) -> Path:
    mirror_path = output_path.parent.parent / canonical_name
    write_text(mirror_path, content)
    return mirror_path


def mirror_json_output(output_path: Path, canonical_name: str, data: object) -> Path:
    mirror_path = output_path.parent.parent / canonical_name
    write_json(mirror_path, data)
    return mirror_path


def build_openclaw_analysis_brief(context: WorkflowContext, payload: dict[str, Any], prompts: dict[str, str]) -> str:
    chunks = payload["analysis_input"].get("chunks", [])
    total_scores = payload.get("total_policy_scores", {})
    lines = [
        f"# OpenClaw 分析简报｜{context.date_str}",
        "",
        "该文件用于把已抓取的人民日报数据交给 OpenClaw 或其他上层工作流进一步生成更高质量文本。核心目标是形成面向 A 股研究的政策导向日报，而不是泛社会领域调研。",
        "",
        "## 工作流目标",
        "",
        "1. 基于当天人民日报文章生成今日新闻摘要。",
        "2. 提炼政策风向、主题标签与风险信号。",
        "3. 对 A 股固定行业池全部行业做结构化打分，不得缺行业。",
        "4. 额外生成可解释的主题标签和行业映射。",
        "5. 生成可发布到金山文档的日报。",
        "",
        "## Prompt 参考",
        "",
        "### daily_summary_prompt.md",
        "",
        prompts.get("daily_summary_prompt.md", ""),
        "",
        "### policy_radar_prompt.md",
        "",
        prompts.get("policy_radar_prompt.md", ""),
        "",
        "### industry_score_prompt.md",
        "",
        prompts.get("industry_score_prompt.md", ""),
        "",
        "### wps_report_prompt.md",
        "",
        prompts.get("wps_report_prompt.md", ""),
        "",
        "## 总评分摘要",
        "",
        f"- policy_friendliness_score: {total_scores.get('policy_friendliness_score', '')}",
        f"- macro_support_score: {total_scores.get('macro_support_score', '')}",
        f"- industrial_stimulus_score: {total_scores.get('industrial_stimulus_score', '')}",
        f"- risk_warning_score: {total_scores.get('risk_warning_score', '')}",
        f"- financial_regulation_score: {total_scores.get('financial_regulation_score', '')}",
        f"- market_relevance_score: {total_scores.get('market_relevance_score', '')}",
        f"- overall_comment: {total_scores.get('overall_comment', '')}",
        "",
        "## 结构化输入摘要",
        "",
        f"- 日期：{context.date_str}",
        f"- 文章数：{payload['analysis_input'].get('article_count', 0)}",
        f"- 分块数：{len(chunks)}",
        f"- 固定行业池数量：{len(payload.get('industry_scores', []))}",
        f"- 观察标签：{'、'.join(payload.get('watch_tags', []))}",
        "",
        "## 文章分块",
        "",
    ]
    for chunk in chunks:
        lines.append(f"### Chunk {chunk['chunk_id']} ({chunk['article_count']} 篇)")
        lines.append("")
        for row in chunk.get("digest", [])[:10]:
            lines.append(f"- 《{row['title']}》 {row['page_title']} | {row['classification']} | {row['url']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_daily_summary_file(outputs_dir: Path, date_str: str, payload: dict[str, Any]) -> Path:
    path = outputs_dir / "daily_summary.md"
    content = write_daily_summary(date_str, payload)
    write_text(path, content)
    mirror_output(path, "daily_summary.md", content)
    return path


def write_policy_radar_file(outputs_dir: Path, date_str: str, payload: dict[str, Any]) -> Path:
    path = outputs_dir / "policy_radar.md"
    content = write_policy_radar(date_str, payload)
    write_text(path, content)
    mirror_output(path, "policy_radar.md", content)
    return path


def write_industry_scores_file(outputs_dir: Path, payload: dict[str, Any]) -> Path:
    path = outputs_dir / "industry_scores.json"
    validate_industry_scores(payload["industry_scores"])
    write_json(path, payload["industry_scores"])
    mirror_json_output(path, "industry_scores.json", payload["industry_scores"])
    return path


def write_investment_signals_file(outputs_dir: Path, payload: dict[str, Any]) -> Path:
    path = outputs_dir / "investment_signals.json"
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
    write_json(path, data)
    mirror_json_output(path, "investment_signals.json", data)
    return path


def write_wps_report_file(outputs_dir: Path, date_str: str, payload: dict[str, Any]) -> Path:
    path = outputs_dir / "wps_report.md"
    content = write_wps_report(date_str, payload)
    write_text(path, content)
    mirror_output(path, "wps_report.md", content)
    return path


def write_publish_request(analysis_dir: Path, date_str: str, report_path: Path) -> Path:
    path = analysis_dir / "openclaw_publish_request.json"
    data = {
        "target": "kingsoft_doc",
        "action": "create_or_update",
        "title": f"人民日报政策风向日报｜{date_str}",
        "content_file": str(report_path),
        "content_format": "markdown",
        "note": "请由 OpenClaw 金山文档 Skill 创建或更新智能文档",
    }
    write_json(path, data)
    return path


def run_json_command(cmd: list[str], cwd: Path | None = None) -> dict[str, Any]:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"command failed: {' '.join(cmd)}")
    text = (result.stdout or result.stderr).strip()
    start = text.find("{")
    if start < 0:
        raise RuntimeError(f"json output not found: {' '.join(cmd)}")
    return json.loads(text[start:])


def normalize_parent_path(raw: str) -> list[str]:
    return [part.strip() for part in raw.split("/") if part.strip()]


def deep_get(data: Any, path: list[str], default: Any = "") -> Any:
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


def build_audit_report(context: WorkflowContext, payload: dict[str, Any], prompts: dict[str, str], publish_requested: bool) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add_check(name: str, ok: bool, detail: str, severity: str = "error") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail, "severity": severity})

    required_sources = [context.paths.full_md, context.paths.articles_jsonl, context.paths.index_json]
    add_check("source_files", all(path.exists() for path in required_sources), "、".join(str(path) for path in required_sources))
    add_check("article_count", payload["analysis_input"].get("article_count", 0) > 0, f"article_count={payload['analysis_input'].get('article_count', 0)}")
    add_check("full_markdown", bool(payload["analysis_input"].get("full_md_excerpt", "").strip()), "full.md 已加载")
    add_check("prompt_files", all(bool(text.strip()) for text in prompts.values()), f"prompt_count={len(prompts)}")
    add_check("fixed_industry_pool", len(payload.get("industry_scores", [])) == len(FIXED_INDUSTRIES), f"industry_scores={len(payload.get('industry_scores', []))}, fixed_pool={len(FIXED_INDUSTRIES)}")

    try:
        validate_industry_scores(payload["industry_scores"])
        add_check("industry_schema", True, "industry_scores schema ok")
    except Exception as exc:  # noqa: BLE001
        add_check("industry_schema", False, str(exc))

    if publish_requested:
        kdocs_bin = shutil.which("kdocs-cli")
        add_check("kdocs_cli", bool(kdocs_bin), kdocs_bin or "kdocs-cli not found")
        if kdocs_bin:
            try:
                auth_status = run_json_command([kdocs_bin, "auth", "status"], cwd=context.project_root)
                add_check("kdocs_auth", bool(auth_status.get("authenticated")), auth_status.get("source", "unknown auth source"))
            except Exception as exc:  # noqa: BLE001
                add_check("kdocs_auth", False, str(exc))

    passed = all(item["ok"] or item["severity"] != "error" for item in checks)
    return {
        "passed": passed,
        "date": context.date_str,
        "publish_requested": publish_requested,
        "checks": checks,
    }


def publish_to_kdocs(report_path: Path, title: str, kdocs_file_id: str = "", kdocs_parent_path: str = "") -> dict[str, Any]:
    kdocs_bin = shutil.which("kdocs-cli")
    if not kdocs_bin:
        raise RuntimeError("kdocs-cli not found")

    with tempfile.TemporaryDirectory(prefix="rmrb-kdocs-") as tmpdir:
        tmp = Path(tmpdir)
        markdown = report_path.read_text(encoding="utf-8")
        file_id = kdocs_file_id.strip()
        created = False

        if not file_id:
            create_payload = {
                "file_type": "file",
                "name": f"{title}.otl",
                "on_name_conflict": "rename",
            }
            parent_path = normalize_parent_path(kdocs_parent_path)
            if parent_path:
                create_payload["parent_path"] = parent_path
            create_payload_path = tmp / "create.json"
            create_payload_path.write_text(json.dumps(create_payload, ensure_ascii=False), encoding="utf-8")
            create_result = run_json_command([kdocs_bin, "drive", "create-file", f"@{create_payload_path}"], cwd=report_path.parent)
            file_id = str(
                create_result.get("id")
                or create_result.get("file_id")
                or deep_get(create_result, ["data", "id"])
                or deep_get(create_result, ["data", "file_id"])
                or deep_get(create_result, ["data", "data", "id"])
                or deep_get(create_result, ["data", "data", "file_id"])
                or ""
            )
            if not file_id:
                raise RuntimeError(f"failed to parse kdocs file id: {create_result}")
            created = True
        else:
            query_payload = {"file_id": file_id, "params": {"blockIds": ["doc"]}}
            query_path = tmp / "query.json"
            query_path.write_text(json.dumps(query_payload, ensure_ascii=False), encoding="utf-8")
            query_result = run_json_command([kdocs_bin, "otl", "block-query", f"@{query_path}"], cwd=report_path.parent)
            data = query_result.get("data", query_result)
            block = data.get("block") or data.get("doc") or {}
            children = block.get("children") or block.get("childIds") or []
            if children:
                delete_payload = {"file_id": file_id, "params": {"blockId": "doc", "startIndex": 0, "endIndex": len(children)}}
                delete_path = tmp / "delete.json"
                delete_path.write_text(json.dumps(delete_payload, ensure_ascii=False), encoding="utf-8")
                run_json_command([kdocs_bin, "otl", "block-delete", f"@{delete_path}"], cwd=report_path.parent)

        insert_payload = {"file_id": file_id, "title": title, "content": markdown, "pos": "begin"}
        insert_payload_path = tmp / "insert.json"
        insert_payload_path.write_text(json.dumps(insert_payload, ensure_ascii=False), encoding="utf-8")
        run_json_command([kdocs_bin, "otl", "insert-content", f"@{insert_payload_path}"], cwd=report_path.parent)
        link_result = run_json_command([kdocs_bin, "drive", "get-file-link", f"file_id={file_id}"], cwd=report_path.parent)
        return {
            "status": "published",
            "file_id": file_id,
            "created": created,
            "link": link_result.get("link") or link_result.get("url") or deep_get(link_result, ["data", "url"]) or deep_get(link_result, ["data", "data", "url"]) or deep_get(link_result, ["data", "link_url"]) or deep_get(link_result, ["data", "data", "link_url"]) or "",
        }


def try_publish_with_openclaw_wps_skill(report_path: Path, title: str, kdocs_file_id: str = "", kdocs_parent_path: str = "") -> dict[str, Any]:
    return publish_to_kdocs(report_path, title, kdocs_file_id=kdocs_file_id, kdocs_parent_path=kdocs_parent_path)


def build_openclaw_chain_request(context: WorkflowContext) -> dict[str, Any]:
    brief_path = context.paths.meta_dir / "openclaw_analysis_brief.md"
    prompt = "\n".join([
        f"请基于 {brief_path}、analysis/inputs/analysis_input.json、analysis/inputs/article_digest.json、analysis/industry_scores.json 和 analysis/investment_signals.json，",
        "生成一份更高质量的 A 股政策研究日报。",
        "要求：",
        "1. 面向 A 股政策导向和行业研究，不做社会调研口径。",
        "2. 必须覆盖固定行业池全部行业，允许重点行业重点展开。",
        "3. 保留 total_policy_scores 的六维评分和一句话总评。",
        "4. 保留 watch_tags，并允许补充额外主题标签。",
        "5. 输出应可直接替换 analysis/wps_report.md 并供金山文档发布。",
        "6. 只输出最终 markdown 正文，不要输出解释、前言、代码块围栏或额外说明。",
    ])
    return {
        "target": "openclaw_agent",
        "action": "generate_policy_report",
        "date": context.date_str,
        "title": context.title,
        "inputs": {
            "brief_file": str(brief_path),
            "analysis_input_file": str(context.paths.inputs_dir / "analysis_input.json"),
            "article_digest_file": str(context.paths.inputs_dir / "article_digest.json"),
            "industry_scores_file": str(context.paths.analysis_dir / "industry_scores.json"),
            "investment_signals_file": str(context.paths.analysis_dir / "investment_signals.json"),
        },
        "message": prompt,
    }


def extract_stage2_markdown(agent_result: dict[str, Any]) -> str:
    text = agent_result.get("finalAssistantVisibleText") or agent_result.get("finalAssistantRawText") or ""
    text = text.strip()
    if text.startswith("```markdown"):
        text = text[len("```markdown"):]
    elif text.startswith("```"):
        text = text[len("```"):]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip() + "\n" if text.strip() else ""


def run_openclaw_stage2(context: WorkflowContext, chain_request: dict[str, Any], agent_name: str, session_id: str, timeout_seconds: int) -> dict[str, Any]:
    resolved_session_id = session_id or f"rmrb-stage2-{context.date_str}"
    cmd = [
        "openclaw", "agent",
        "--agent", agent_name,
        "--session-id", resolved_session_id,
        "--message", chain_request["message"],
        "--json",
        "--timeout", str(timeout_seconds),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    raw_stdout = result.stdout.strip()
    raw_stderr = result.stderr.strip()
    if result.returncode != 0:
        raise RuntimeError(raw_stderr or raw_stdout or f"openclaw stage2 failed with code {result.returncode}")
    candidate_text = raw_stdout if "{" in raw_stdout else raw_stderr
    start = candidate_text.rfind('\n{\n  "payloads"')
    if start >= 0:
        start += 1
    else:
        start = candidate_text.rfind('{"payloads"')
    if start < 0:
        start = candidate_text.find("{")
    if start < 0:
        raise RuntimeError("openclaw stage2 returned non-json output")
    payload = json.loads(candidate_text[start:])
    markdown = extract_stage2_markdown(payload.get("meta", {}))
    if not markdown:
        raise RuntimeError("openclaw stage2 returned empty markdown")
    return {
        "session_id": resolved_session_id,
        "agent": agent_name,
        "raw": payload,
        "markdown": markdown,
        "stderr": raw_stderr,
    }


def write_workflow_static_files(project_root: Path) -> None:
    workflow_dir = project_root / "workflow"
    schemas_dir = project_root / "schemas"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)

    pipeline_spec = {
        "name": "rmrb-policy-radar",
        "version": "1.0",
        "steps": [
            {"id": "crawl", "description": "Use existing rmrb_crawler.py to ensure daily source files exist."},
            {"id": "load", "description": "Load full.md, articles.jsonl, index.json and build structured input."},
            {"id": "analyze", "description": "Generate theme, industry, risk, and score outputs."},
            {"id": "report", "description": "Render daily summary, policy radar, and WPS report."},
            {"id": "publish", "description": "Create publish request or call an existing OpenClaw WPS capability."},
        ],
    }
    industry_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "industry", "direction", "policy_tailwind_score", "risk_pressure_score", "market_relevance_score",
                "signal_strength", "confidence", "time_horizon", "summary", "evidence_articles", "tags",
            ],
        },
    }
    investment_schema = {
        "type": "object",
        "required": ["date", "source", "market", "total_policy_scores", "top_policy_themes", "industry_scores", "risk_alerts", "watch_tags"],
    }
    write_json(workflow_dir / "pipeline_manifest.json", pipeline_spec)
    write_json(schemas_dir / "industry_scores.schema.json", industry_schema)
    write_json(schemas_dir / "investment_signals.schema.json", investment_schema)


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    write_workflow_static_files(project_root)

    output_root = Path(args.output)
    date_str = resolve_date(args.date)
    title = f"人民日报政策风向日报｜{date_str}"
    initial_paths = build_paths(output_root, date_str)
    crawler_script = find_crawler_script(project_root, args.crawler_script)
    paths = ensure_crawled(date_str, output_root, args.auto_crawl, crawler_script, initial_paths.analysis_dir)
    context = WorkflowContext(project_root=project_root, output_root=output_root, date_str=date_str, title=title, crawler_script=crawler_script, paths=paths)

    result_summary = {
        "success": False,
        "date": date_str,
        "source_dir": str(paths.source_dir),
        "analysis_dir": str(paths.analysis_dir),
        "daily_summary": "",
        "policy_radar": "",
        "industry_scores": "",
        "investment_signals": "",
        "wps_report": "",
        "publish_status": "skipped",
        "wps_title": title,
        "error": "",
    }

    try:
        paths.analysis_dir.mkdir(parents=True, exist_ok=True)
        paths.inputs_dir.mkdir(parents=True, exist_ok=True)
        paths.outputs_dir.mkdir(parents=True, exist_ok=True)
        paths.meta_dir.mkdir(parents=True, exist_ok=True)

        articles = load_articles_jsonl(paths.source_dir)
        full_md = load_full_md(paths.source_dir)
        index_data = load_json(paths.index_json)
        if not articles:
            raise RuntimeError("articles.jsonl is empty or unreadable")

        payload = build_analysis_payload(date_str, articles, full_md)
        prompts = {
            name: read_prompt(project_root, name)
            for name in ["daily_summary_prompt.md", "policy_radar_prompt.md", "industry_score_prompt.md", "wps_report_prompt.md"]
        }

        write_json(paths.inputs_dir / "analysis_input.json", payload["analysis_input"])
        write_json(paths.inputs_dir / "article_digest.json", payload["article_digest"])
        write_json(paths.inputs_dir / "article_chunks.json", payload["analysis_input"].get("chunks", []))
        write_json(paths.meta_dir / "source_index_snapshot.json", index_data)
        write_text(paths.meta_dir / "openclaw_analysis_brief.md", build_openclaw_analysis_brief(context, payload, prompts))
        chain_request = build_openclaw_chain_request(context)
        write_json(paths.meta_dir / "openclaw_chain_request.json", chain_request)
        write_json(paths.meta_dir / "workflow_manifest.json", {
            "name": "rmrb-policy-radar",
            "date": date_str,
            "source_dir": str(paths.source_dir),
            "analysis_dir": str(paths.analysis_dir),
            "crawler_script": str(crawler_script),
            "steps": ["crawl", "load", "analyze", "report", "publish"],
            "prompt_files": list(prompts.keys()),
            "positioning": "A股政策分析与行业导向",
            "requires_full_fixed_industry_pool": True,
        })

        publish_requested = args.publish_wps and not args.no_publish
        audit_report = build_audit_report(context, payload, prompts, publish_requested=publish_requested)
        write_json(paths.meta_dir / "audit_report.json", audit_report)
        if args.audit_only:
            result_summary.update({
                "success": audit_report["passed"],
                "error": "" if audit_report["passed"] else "audit failed",
                "audit_status": "passed" if audit_report["passed"] else "failed",
            })
            print(json.dumps(result_summary, ensure_ascii=False, indent=2))
            return 0 if audit_report["passed"] else 1
        if not audit_report["passed"]:
            raise RuntimeError("audit failed, see analysis/meta/audit_report.json")

        daily_summary = write_daily_summary_file(paths.outputs_dir, date_str, payload)
        policy_radar = write_policy_radar_file(paths.outputs_dir, date_str, payload)
        industry_scores = write_industry_scores_file(paths.outputs_dir, payload)
        investment_signals = write_investment_signals_file(paths.outputs_dir, payload)
        wps_report = write_wps_report_file(paths.outputs_dir, date_str, payload)

        stage2_status = "skipped"
        stage2_error = ""
        if args.stage2_mode != "off":
            try:
                stage2_result = run_openclaw_stage2(
                    context=context,
                    chain_request=chain_request,
                    agent_name=args.stage2_agent,
                    session_id=args.stage2_session_id,
                    timeout_seconds=args.stage2_timeout,
                )
                write_text(paths.meta_dir / "stage2_wps_report.md", stage2_result["markdown"])
                write_json(paths.meta_dir / "stage2_result.json", {
                    "success": True,
                    "agent": stage2_result["agent"],
                    "session_id": stage2_result["session_id"],
                    "stderr": stage2_result["stderr"],
                })
                write_text(paths.outputs_dir / "wps_report.stage1.md", wps_report.read_text(encoding="utf-8"))
                write_text(paths.outputs_dir / "wps_report.md", stage2_result["markdown"])
                write_text(paths.analysis_dir / "wps_report.stage1.md", (paths.outputs_dir / "wps_report.stage1.md").read_text(encoding="utf-8"))
                write_text(paths.analysis_dir / "wps_report.md", stage2_result["markdown"])
                wps_report = paths.analysis_dir / "wps_report.md"
                stage2_status = "completed"
            except Exception as exc:  # noqa: BLE001
                stage2_error = str(exc)
                write_json(paths.meta_dir / "stage2_result.json", {
                    "success": False,
                    "agent": args.stage2_agent,
                    "session_id": args.stage2_session_id or f"rmrb-stage2-{context.date_str}",
                    "error": stage2_error,
                })
                if args.stage2_mode == "required":
                    raise
                stage2_status = "failed_fallback_stage1"

        publish_request = None
        publish_result: dict[str, Any] | None = None
        if args.publish_wps and not args.no_publish:
            try:
                publish_result = try_publish_with_openclaw_wps_skill(
                    wps_report,
                    title,
                    kdocs_file_id=args.kdocs_file_id,
                    kdocs_parent_path=args.kdocs_parent_path,
                )
                result_summary["publish_status"] = publish_result["status"]
                write_json(paths.meta_dir / "publish_result.json", publish_result)
            except Exception as exc:  # noqa: BLE001
                publish_request = write_publish_request(paths.analysis_dir, date_str, wps_report)
                publish_result = {"status": "pending_openclaw_skill", "error": str(exc)}
                result_summary["publish_status"] = publish_result["status"]
                write_json(paths.meta_dir / "publish_result.json", publish_result)
        elif args.no_publish:
            publish_request = write_publish_request(paths.analysis_dir, date_str, wps_report)
            result_summary["publish_status"] = "skipped"
        else:
            publish_request = write_publish_request(paths.analysis_dir, date_str, wps_report)
            result_summary["publish_status"] = "pending_openclaw_skill"

        analysis_result = {
            "success": True,
            "date": date_str,
            "source_dir": str(paths.source_dir),
            "analysis_dir": str(paths.analysis_dir),
            "article_count": len(articles),
            "fixed_industry_count": len(FIXED_INDUSTRIES),
            "publish_request": str(publish_request) if publish_request else "",
            "publish_status": result_summary["publish_status"],
            "publish_result": publish_result or {},
            "audit_status": "passed",
            "stage2_status": stage2_status,
            "stage2_error": stage2_error,
            "inputs_dir": str(paths.inputs_dir),
            "outputs_dir": str(paths.outputs_dir),
            "meta_dir": str(paths.meta_dir),
        }
        write_json(paths.analysis_dir / "analysis_result.json", analysis_result)

        result_summary.update({
            "success": True,
            "daily_summary": str(paths.analysis_dir / "daily_summary.md"),
            "policy_radar": str(paths.analysis_dir / "policy_radar.md"),
            "industry_scores": str(paths.analysis_dir / "industry_scores.json"),
            "investment_signals": str(paths.analysis_dir / "investment_signals.json"),
            "wps_report": str(paths.analysis_dir / "wps_report.md"),
            "audit_status": "passed",
            "stage2_status": stage2_status,
            "stage2_error": stage2_error,
            "publish_result": publish_result or {},
        })
        print(json.dumps(result_summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        result_summary["error"] = str(exc)
        print(json.dumps(result_summary, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
