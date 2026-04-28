---
name: rmrb-policy-radar
description: Read one day of People's Daily (人民日报) crawler output, generate an A-share-focused policy radar, full fixed-industry-pool scoring, extra policy theme tags, total policy scores, and a WPS-ready markdown report. Use when the user wants a 人民日报政策风向标日报 for A股政策导向研究, wants full fixed-industry coverage across common A-share sectors, or wants to publish the resulting report through an existing OpenClaw Kingsoft/WPS document capability.
---

# 人民日报政策风向标

Use this skill for single-day 人民日报 policy-text analysis built on top of the existing crawler output. Keep the lens on A股政策分析、行业导向和研究记录, not general social-field research.

## Inputs

Run from the project root:

```bash
python scripts/rmrb_policy_skill.py --date today
python scripts/rmrb_policy_skill.py --date 2026-04-28 --no-publish
python scripts/rmrb_policy_skill.py --date today --auto-crawl --publish-wps
```

Supported flags:

- `--date today|YYYY-MM-DD`
- `--output <dir>`
- `--auto-crawl`
- `--no-publish`
- `--publish-wps`
- `--crawler-script <path>`
- `--stage2-mode auto|off|required`
- `--stage2-agent <agent-id>`
- `--stage2-session-id <session-id>`
- `--stage2-timeout <seconds>`
- `--audit-only`
- `--kdocs-file-id <file-id>`
- `--kdocs-parent-path <folder/subfolder>`

## Workflow

1. Resolve the requested date in Asia/Shanghai.
2. Reuse the existing crawler output under `data/rmrb/YYYY-MM-DD/`.
3. If required files are missing and `--auto-crawl` is set, call the existing crawler instead of rewriting crawl logic.
4. Read `articles.jsonl`, `full.md`, and `index.json`.
5. Build article digests, policy theme evidence, full fixed-industry-pool scores, extra theme tags, and total policy scores.
6. Build workflow artifacts for repeatable OpenClaw use:
   - `inputs/analysis_input.json`
   - `inputs/article_digest.json`
   - `inputs/article_chunks.json`
   - `meta/source_index_snapshot.json`
   - `meta/workflow_manifest.json`
   - `meta/openclaw_analysis_brief.md`
7. Run a workflow audit before report generation. If the SOP checks fail, stop and write `meta/audit_report.json` instead of continuing.
8. Generate report outputs:
   - `daily_summary.md`
   - `policy_radar.md`
   - `industry_scores.json`
   - `investment_signals.json`
   - `wps_report.md`
   - `analysis_result.json`
   - `openclaw_publish_request.json` when direct publishing is unavailable
9. Run OpenClaw second-stage enhancement automatically when enabled. Stage 1 builds structured inputs and a base report. Stage 2 asks an OpenClaw agent to rewrite the report into a stronger A-share policy research daily and replaces `wps_report.md` on success.
10. If `--publish-wps` is enabled, publish the final markdown to a Kdocs/WPS intelligent document automatically. Prefer updating `--kdocs-file-id` when provided, otherwise create a new `.otl` document under `--kdocs-parent-path`.
11. If direct publishing is unavailable, leave a publish request file and report `pending_openclaw_skill`.

## Outputs

All outputs are written to:

`data/rmrb/YYYY-MM-DD/analysis/`

Stable top-level entry files:

- `daily_summary.md`
- `policy_radar.md`
- `industry_scores.json`
- `investment_signals.json`
- `wps_report.md`
- `analysis_result.json`
- `openclaw_publish_request.json`

Repeatable workflow subdirectories:

- `inputs/` for structured source digests and chunks
- `outputs/` for canonical generated report files
- `meta/` for workflow metadata, audit results, OpenClaw handoff material, stage-2 execution results, and publish results

## Boundaries

- Analyze one day only.
- Base every conclusion on the crawled 人民日报 text and article metadata.
- Keep the primary output lens on A股政策导向、行业映射和风险提示.
- Always score the full fixed industry pool, even if many industries remain neutral.
- Allow extra theme tags when supported by the text.
- Do not invent policy facts absent from the source text.
- Do not output explicit buy, sell, or hold advice.
- Do not predict specific prices.
- Do not add OCR, image analysis, or database dependencies in this version.

## Publishing

Preferred: publish with an existing OpenClaw Kingsoft/WPS document capability.

Fallback: generate `openclaw_publish_request.json` with the markdown path so another OpenClaw workflow can publish it later.

## Prohibitions

- Do not replace the crawler with a new implementation.
- Do not hardcode external commercial LLM API keys.
- Do not mix logs into stdout. Stdout must remain pure JSON.
