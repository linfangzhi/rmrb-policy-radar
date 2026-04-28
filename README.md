# 📰 人民日报政策风向标 · People's Daily Policy Radar

<div align="center">

**AI-Powered Policy Analysis Pipeline for Investment Intelligence**

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-blueviolet.svg)
![Workflow](https://img.shields.io/badge/Stage%201%20%E2%86%92%20Stage%204-Progress-green)

> *From raw newspaper pages to structured investment signals — automated.*

</div>

---

## 📋 Overview

**人民日报政策风向标 (RMRB Policy Radar)** is an end-to-end policy analysis pipeline that:

1. **Crawls** daily People's Daily digital edition
2. **Analyzes** content for policy themes and industry impact
3. **Generates** structured reports with investment signals
4. **Publishes** to WPS/Kdocs or local documents

<div align="center">

### 🔧 Complete Workflow Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  STAGE 1    │     │   STAGE 2    │     │   STAGE 3    │     │   STAGE 4    │
│  DATA       │────▶│  POLICY      │────▶│ REPORT       │────▶│ PUBLISH &    │
│  ACQUISITION│     │  ANALYSIS    │     │  GENERATION  │     │ DELIVERY     │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
      │                    │                    │                    │
      ▼                    ▼                    ▼                    ▼
   Crawl pages        Theme detection      Markdown reports     WPS/Kdocs
                      Industry scoring     JSON signals         Local files
                      Risk assessment      Policy radar         OpenClaw session
```

</div>

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Git (for cloning)
- LLM API access (optional, for Stage 2 analysis)
- OpenClaw (optional, for skill integration)

### Installation

```bash
# Clone the repository
git clone https://github.com/linfangzhi/rmrb-policy-radar.git
cd rmrb-policy-radar

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### First Run — Full Pipeline (Stage 1 → Stage 4)

```bash
# Execute complete workflow for yesterday's edition
python3 scripts/rmrb_policy_skill.py \
    --date yesterday \
    --auto-crawl \
    --stage2-mode auto

# Or specify exact date
python3 scripts/rmrb_policy_skill.py \
    --date 2026-04-28 \
    --auto-crawl \
    --stage2-mode required \
    --publish-wps
```

---

## 📊 Stage-by-Stage Breakdown

### 🔍 Stage 1: Data Acquisition (Crawler)

Automatically fetches People's Daily digital edition content.

**Commands:**

```bash
# Single day crawl
python3 rmrb_crawler.py --date 2026-04-28

# Multi-day range
python3 rmrb_crawler.py --start-date 2026-04-01 --end-date 2026-04-28

# Custom URL (specific page)
python3 rmrb_crawler.py --url "https://paper.people.com.cn/rmrb/pc/layout/202604/28/node_01.html"
```

**Output Files:**

| File | Format | Description |
|------|--------|-------------|
| `full.md` | Markdown | Complete newspaper in markdown |
| `articles.jsonl` | JSONL | One article per line (machine-readable) |
| `index.json` | JSON | Crawl metadata and statistics |
| `failed.jsonl` | JSONL | Failed articles for retry |

**Output Structure:**
```
data/rmrb/2026-04-28/
├── full.md              ← Merged newspaper content
├── articles.jsonl       ← Structured article data (137+ articles)
├── index.json           ← Crawl metadata
├── failed.jsonl         ← Retry queue
└── articles/            ← Individual article markdown files
    ├── 20260428_01_001_headline.md
    └── ... (30+ pages × multiple articles)
```

**Configuration:**

```bash
# Adjust request timing and retry behavior
python3 rmrb_crawler.py \
    --date 2026-04-28 \
    --min-sleep 1 --max-sleep 5 \
    --retries 3 --timeout 15
```

---

### 🧠 Stage 2: Policy Analysis (Analyzer)

Applies AI-based policy theme detection and industry impact scoring.

**Analysis Pipeline:**

```
articles.jsonl → Chunking → LLM Prompt → Theme Classification
                                                      ↓
                                              Industry Scoring ← Validation
                                                      ↓
                                              Signal Generation ──▶ JSONL Output
```

**Key Features:**

- **20+ Policy Themes**: 稳增长, 新质生产力, 科技自立自强, etc.
- **30+ Industries**: 银行, AI芯片, 新能源, 医药, etc.
- **Multi-Signal Detection**: Positive/Negative/Mixed/Watch signals
- **Validation Schema**: JSON schema validation for output integrity

**Commands:**

```bash
# Run analysis with auto-enhanced LLM processing
python3 scripts/analyze_rmrb_policy.py \
    --input data/rmrb/2026-04-28/articles.jsonl \
    --output-dir data/rmrb/2026-04-28/analysis

# Audit mode only (validate existing analysis)
python3 scripts/analyze_rmrb_policy.py --audit-only
```

**Industry Score Schema:**

```json
{
  "industry": "人工智能",
  "policy_tailwind_score": 8.5,
  "market_relevance_score": 9.2,
  "signal_strength": "strong_positive",
  "key_themes": ["新质生产力", "AI+"],
  "risk_factors": []
}
```

---

### 📝 Stage 3: Report Generation (Renderer)

Transforms analysis results into human-readable reports.

**Report Types:**

| Type | Output | Use Case |
|------|--------|----------|
| **Daily Summary** | Markdown | Quick overview for readers |
| **Policy Radar** | Markdown + JSON | Investment signal dashboard |
| **WPS Report** | Document file | Professional publishing format |

**Commands:**

```bash
# Generate all report types
python3 scripts/render_policy_report.py \
    --input-dir data/rmrb/2026-04-28/analysis/ \
    --output-dir data/rmrb/2026-04-28/reports/

# Generate WPS-compatible document (requires Kdocs/WPS integration)
python3 scripts/render_policy_report.py \
    --format wps \
    --kdocs-file-id <your-file-id>
```

**Report Output:**
```
reports/
├── daily_summary.md      ← Executive summary with key signals
├── policy_radar.md       ← Industry radar chart data + narrative
└── investment_signals.json  ← Structured JSON for downstream systems
```

---

### 📤 Stage 4: Publish & Delivery (Skill Wrapper)

Orchestrates the complete workflow and handles publishing.

**Full Pipeline Command:**

```bash
# End-to-end: Crawl → Analyze → Report → Publish
python3 scripts/rmrb_policy_skill.py \
    --date 2026-04-28 \
    --auto-crawl \
    --stage2-mode auto \
    --publish-wps \
    --kdocs-file-id <file-id> \
    --kdocs-parent-path "人民日报政策风向日报/自动发布"
```

**Stage 2 Enhancement Options:**

| Mode | Description |
|------|-------------|
| `auto` | Uses LLM if available, falls back to rule-based |
| `off` | Disables Stage 2 enhancement (faster) |
| `required` | Fails if no LLM configured |

**Audit Gate:**

The skill includes built-in validation before proceeding:
1. ✅ Source files exist (`full.md`, `articles.jsonl`)
2. ✅ Analysis results pass schema validation
3. ✅ Report templates render correctly
4. ⛔ **Stops on audit failure** — prevents corrupted output

---

## ⚙️ Configuration

### Policy Analysis Config (`config.policy.example.yaml`)

```yaml
# Copy to config.policy.yaml and customize
market: A股
output_root: ./data/rmrb

publish:
  enabled: false              # Set true for auto-publish
  kdocs_parent_path: "日报/自动发布"
  require_audit_pass: true    # Critical safety flag

analysis:
  timezone: Asia/Shanghai
  max_articles_per_chunk: 12  # LLM context window management
  max_chars_per_chunk: 12000
  
  fixed_industries:           # Pre-defined industry list
    - 银行
    - 券商
    - AI芯片
    - 新能源
    # ... (30+ industries)

scoring:
  weight_positive: 0.7        # Positive signal weighting
  weight_negative: 0.3        # Negative signal weighting
```

---

## 🤖 Automation & Scheduling

### Crontab (Daily at 07:00)

```cron
0 7 * * * cd /path/to/rmrb-claw && \
    .venv/bin/python scripts/rmrb_policy_skill.py \
        --date yesterday \
        --auto-crawl \
        --stage2-mode auto \
        --publish-wps >> logs/cron.log 2>&1
```

### systemd Timer (Production)

**Service file:** `/etc/systemd/system/rmrb-policy.service`
```ini
[Unit]
Description=RMRB Policy Analysis Pipeline
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/opt/rmrb-claw
ExecStart=/opt/rmrb-claw/.venv/bin/python scripts/rmrb_policy_skill.py \
    --date %i --auto-crawl --stage2-mode auto
User=your-user
```

**Timer file:** `/etc/systemd/system/rmrb-policy.timer`
```ini
[Unit]
Description=Run Policy Analysis Daily

[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Enable:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rmrb-policy.timer
```

---

## 🧪 OpenClaw Skill Integration

For full automation with AI agent orchestration:

```bash
# Run via OpenClaw session (Stage 2 enhancement included)
python3 scripts/rmrb_policy_skill.py \
    --date yesterday \
    --stage2-mode auto \
    --stage2-agent xiaodaidai \
    --stage2-session-id <session-id> \
    --stage2-timeout 600
```

**Skill Capabilities:**
- ✅ Auto-crawl when data missing
- ✅ Audit gate enforcement
- ✅ Stage 2 AI enhancement (optional)
- ✅ WPS/Kdocs publishing
- ✅ Report formatting and delivery

---

## 📁 Project Structure

```
rmrb-claw/
├── rmrb_crawler.py              ← Stage 1: Newspaper crawler
├── test_rmrb_crawler.py         ← Crawler unit tests
├── requirements.txt             ← Python dependencies
├── config.policy.example.yaml   ← Configuration template
│
├── scripts/
│   ├── analyze_rmrb_policy.py   ← Stage 2: Policy analyzer
│   ├── render_policy_report.py  ← Stage 3: Report renderer
│   └── rmrb_policy_skill.py     ← Stage 4: Pipeline orchestrator
│
├── prompts/                     ← LLM prompt templates
│   ├── daily_summary_prompt.md
│   ├── industry_score_prompt.md
│   ├── policy_radar_prompt.md
│   └── wps_report_prompt.md
│
├── schemas/                     ← JSON schema validation
│   ├── industry_scores.schema.json
│   └── investment_signals.schema.json
│
├── workflow/                    ← Pipeline orchestration
│   └── pipeline_manifest.json
│
├── data/                        ← Output directory (gitignored)
└── logs/                        ← Runtime logs (gitignored)
```

---

## 🔐 Security & Compliance

### Data Handling

- **No external uploads**: All processing happens locally
- **Public content only**: Crawls publicly available newspaper pages
- **Config isolation**: `config.policy.yaml` excluded from git; use `.env.example` template

### Rate Limiting (Built-in)

```bash
--min-sleep 1    # Minimum 1 second between requests
--max-sleep 5    # Maximum 5 seconds (adaptive delay)
--retries 3      # Retry failed articles 3 times
--timeout 15     # Request timeout in seconds
```

---

## 📚 Example Output: April 26, 2026 Analysis

<details>
<summary>Click to view sample industry scores</summary>

```json
[
    {
        "industry": "人工智能",
        "policy_tailwind_score": 9.1,
        "market_relevance_score": 8.7,
        "signal_strength": "strong_positive",
        "key_themes": ["新质生产力", "AI+", "科技自立自强"],
        "risk_factors": []
    },
    {
        "industry": "新能源",
        "policy_tailwind_score": 7.8,
        "market_relevance_score": 9.0,
        "signal_strength": "positive",
        "key_themes": ["绿色低碳", "能源安全"],
        "risk_factors": ["产能过剩"]
    }
]
```

</details>

---

## ⚠️ Disclaimer

**This tool is for educational and research purposes only.**

- Policy analysis results are **not investment advice**
- Industry scores use heuristics + LLM — accuracy not guaranteed
- The authors assume no liability for investment decisions made based on this output
- Crawling respects robots.txt; please do not abuse the service

> *Use at your own risk. We're just a bunch of nerds writing scripts, not financial advisors.* 🎩

---

## 📜 License

**MIT License** — Free to use, modify, and distribute. See `LICENSE` for details.

---

<div align="center">

**Built with ❤️ by [linfangzhi](https://github.com/linfangzhi)**  
*Turning newspaper pages into data points since 2026*

[🔗 GitHub Repository](https://github.com/linfangzhi/rmrb-policy-radar) | 
[📖 OpenClaw Skill Docs]() |
[💬 Issues & PRs Welcome]

</div>
