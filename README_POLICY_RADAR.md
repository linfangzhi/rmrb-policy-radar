# 人民日报政策风向标 Skill

## 1. 用途

本模块在现有 `rmrb_crawler.py` 的基础上，读取单日人民日报文章，生成：

- 今日新闻摘要
- 面向 A 股研究的政策风向标分析
- 固定行业池全量行业政策风向评分
- 额外政策主题标签、风险提示与总评分
- 适合金山文档 / 智能文档使用的日报 Markdown

## 2. 与 `rmrb_crawler.py` 的关系

本阶段不重写爬虫。

- 数据来源优先使用已有 crawler 输出
- 当输入文件缺失且启用 `--auto-crawl` 时，调用现有 `rmrb_crawler.py`
- 如需兼容性调整，应优先做小修而不是重构。本版本未改动原爬虫

## 3. 单日运行方式

```bash
python scripts/rmrb_policy_skill.py --date today
python scripts/rmrb_policy_skill.py --date 2026-04-28
python scripts/rmrb_policy_skill.py --date 2026-04-28 --output ./data/rmrb
python scripts/rmrb_policy_skill.py --date today --auto-crawl --stage2-mode required --stage2-agent xiaodaidai
python scripts/rmrb_policy_skill.py --date today --auto-crawl --publish-wps --kdocs-parent-path "人民日报政策风向日报/自动发布"
python scripts/rmrb_policy_skill.py --date today --audit-only
```

## 4. 自动采集方式

如果当天数据不存在，可以让 Skill 先调用爬虫：

```bash
python scripts/rmrb_policy_skill.py --date today --auto-crawl
```

默认会检查：

- `data/rmrb/YYYY-MM-DD/full.md`
- `data/rmrb/YYYY-MM-DD/articles.jsonl`
- `data/rmrb/YYYY-MM-DD/index.json`

## 5. 如何生成日报

```bash
python scripts/rmrb_policy_skill.py --date today --no-publish
```

输出目录：

```text
data/rmrb/YYYY-MM-DD/analysis/
├── daily_summary.md
├── policy_radar.md
├── industry_scores.json
├── investment_signals.json
├── wps_report.md
├── analysis_result.json
├── openclaw_publish_request.json
├── inputs/
│   ├── analysis_input.json
│   ├── article_digest.json
│   └── article_chunks.json
├── outputs/
│   ├── daily_summary.md
│   ├── policy_radar.md
│   ├── industry_scores.json
│   ├── investment_signals.json
│   └── wps_report.md
└── meta/
    ├── source_index_snapshot.json
    ├── workflow_manifest.json
    ├── audit_report.json
    ├── openclaw_analysis_brief.md
    ├── openclaw_chain_request.json
    ├── stage2_result.json
    └── publish_result.json
```

说明：

- 根目录文件是给外部工作流和旧调用方式直接读取的稳定入口
- `inputs/` 保存分析输入和分块结果，方便 OpenClaw 二次分析
- `outputs/` 保存标准产物的规范位置
- `meta/` 保存流程清单、输入快照、SOP 审计结果、OpenClaw 分析简报、第二阶段调用链结果和发布结果

## 6. 如何调用金山文档 Skill

优先方案：

```bash
python scripts/rmrb_policy_skill.py --date today --auto-crawl --publish-wps
```

当前项目内未直接内置金山文档 API，也不自行实现金山 API。

因此本版本的行为是：

1. 先执行一轮 SOP 审计，检查输入、Prompt、行业池、Schema 以及发布依赖是否正常
2. 审计通过后，第一阶段生成结构化分析与初版 `wps_report.md`
3. 第二阶段默认尝试调用 OpenClaw agent 自动生成增强版研究日报，并覆盖 `wps_report.md`
4. 若启用 `--publish-wps`，脚本会自动同步发布到金山智能文档
5. 如果当前环境不能直接调用，则生成：
   - `openclaw_publish_request.json`

## 7. 输出文件说明

### `daily_summary.md`
偏新闻摘要，1000 到 1500 字左右。

### `policy_radar.md`
偏政策导向、产业方向、风险信号，1500 到 2500 字左右。

### `industry_scores.json`
固定行业池全量行业的结构化评分结果，保留证据文章引用。即使当天缺乏明显信号，也要给出中性或观察判断，不能漏行业。

### `investment_signals.json`
整合总评分、主题、行业评分、风险提示和观察标签，便于未来入库、时间序列化或交给 OpenClaw 继续生成高质量日报。

### `wps_report.md`
适合直接上传到金山智能文档的日报正文。

### `analysis_result.json`
本次执行摘要。

### `openclaw_publish_request.json`
给 OpenClaw 金山文档 Skill 的发布请求描述。

## 8. 行业评分口径

这是一个 **A 股政策分析 Skill**，不是泛社会调研 Skill。所有评分和主题解读，都要尽量回到 A 股行业导向、政策受益方向、风险压制方向和后续观察点。

评分范围统一为 1 到 5：

- `policy_tailwind_score`：政策顺风程度
- `risk_pressure_score`：风险压力强度
- `market_relevance_score`：与 A 股市场相关程度
- `signal_strength`：当天信号强弱
- `confidence`：根据文本证据形成判断的可信度

方向枚举：

- `positive`
- `negative`
- `neutral`
- `mixed`
- `watch`

## 9. 常见问题

### Q1. 没有当天数据怎么办？
启用 `--auto-crawl`，让 Skill 自动调用已有爬虫。

### Q2. 为什么没有直接发到金山文档？
因为当前项目中不重复实现 API，发布依赖已有 OpenClaw 金山文档能力；不可用时会生成 `openclaw_publish_request.json`。

### Q3. 为什么不输出买卖建议？
本 Skill 只做政策文本分析和研究记录，不输出具体投资建议。

### Q4. 某篇文章解析失败会中断吗？
不会。单篇异常会尽量隔离，整体分析继续进行。

## 10. 后续扩展方向

- 接数据库存储结构化结果
- 图片 OCR 和配图信息利用
- 多日时间序列和主题热度趋势
- 行业热度回看与政策主题跟踪
- 与更完整的 OpenClaw 发布工作流联动
- 让 OpenClaw 直接读取 `meta/openclaw_analysis_brief.md` 和 `inputs/*.json`，生成更高质量的研究风格日报
- 增加 cron/heartbeat 集成，实现自动抓取、自动分析、自动发布
