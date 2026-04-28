# 📰 人民日报政策风向标 · Policy Radar for A股韭菜们

<div align="center">

**别盯K线了，看党报。**

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-blueviolet.svg)
![韭菜认证](https://img.shields.io/badge/韭菜认证-已验证-yellow.svg)

> *主力看资金流向，我们看人民日报。毕竟——*  
> *"政策底"这三个字，比什么MACD金叉都来得实在。*

</div>

---

## 📋 这是什么？

**人民日报政策风向标**是一个全自动化的新闻分析管道：

1. **扒** — 每天自动抓取《人民日报》电子版
2. **嚼** — AI分析每篇文章，识别政策信号和行业关联
3. **吐** — 生成结构化行业评分和投资信号报告
4. **发** — 发布到 WPS/Kdocs 或本地文档

<div align="center">

### 🔧 完整工作流程

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   STAGE 1   │     │   STAGE 2    │     │   STAGE 3    │     │   STAGE 4    │
│  新闻采集   │────▶│  政策分析    │────▶│  报告生成    │────▶│  发布交付    │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
      │                    │                    │                    │
      ▼                    ▼                    ▼                    ▼
   爬取报纸页面       主题检测 +           Markdown报告        WPS/Kdocs
                      行业评分             JSON信号            本地文件
                      风险评估             政策雷达图          OpenClaw会话
```

</div>

---

## 🚀 快速上手

### 先决条件

- Python 3.10+（别问，装就完了）
- Git（克隆用）
- LLM API访问（可选，Stage 2分析需要脑子）
- OpenClaw（可选，技能集成用）

### 安装

```bash
# 克隆仓库（别客气）
git clone https://github.com/linfangzhi/rmrb-policy-radar.git
cd rmrb-policy-radar

# 创建虚拟环境（保护你的系统）
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 第一次运行 — 完整流程（Stage 1 → Stage 4）

```bash
# 自动抓取昨天的报纸并分析
python3 scripts/rmrb_policy_skill.py \
    --date yesterday \
    --auto-crawl \
    --stage2-mode auto

# 或者指定具体日期
python3 scripts/rmrb_policy_skill.py \
    --date 2026-04-28 \
    --auto-crawl \
    --stage2-mode required \
    --publish-wps
```

---

## 📊 分阶段说明（韭菜也能看懂）

### 🔍 Stage 1: 新闻采集（爬虫）

自动获取《人民日报》电子版内容。别担心，我们不会把人家网站爬垮的——内置了礼貌延迟。

**命令：**

```bash
# 单日抓取
python3 rmrb_crawler.py --date 2026-04-28

# 多日范围（适合回测）
python3 rmrb_crawler.py --start-date 2026-04-01 --end-date 2026-04-28

# 指定特定页面URL
python3 rmrb_crawler.py --url "https://paper.people.com.cn/rmrb/pc/layout/202604/28/node_01.html"
```

**输出文件：**

| 文件 | 格式 | 说明 |
|------|------|------|
| `full.md` | Markdown | 整版报纸的markdown版本 |
| `articles.jsonl` | JSONL | 每行一篇文章（机器可读） |
| `index.json` | JSON | 抓取元数据和统计信息 |
| `failed.jsonl` | JSONL | 失败文章重试队列 |

**输出目录结构：**
```
data/rmrb/2026-04-28/
├── full.md              ← 合并后的报纸内容
├── articles.jsonl       ← 结构化文章数据（137+篇）
├── index.json           ← 抓取元数据
├── failed.jsonl         ← 重试队列
└── articles/            ← 单篇文章markdown文件
    ├── 20260428_01_001_headline.md
    └── ...（30+个版面 × 多篇）
```

**配置抓取行为：**

```bash
# 调整请求间隔和重试策略
python3 rmrb_crawler.py \
    --date 2026-04-28 \
    --min-sleep 1 --max-sleep 5 \
    --retries 3 --timeout 15
```

---

### 🧠 Stage 2: 政策分析（AI大脑）

用AI检测政策主题、评估行业影响、生成投资信号。

**分析流程：**

```
articles.jsonl → 分块 → LLM提示词 → 主题分类
                                                      ↓
                                              行业评分 ← 验证
                                                      ↓
                                              信号生成 ──▶ JSONL输出
```

**核心功能：**

- **20+ 政策主题**: 稳增长, 新质生产力, 科技自立自强, etc.
- **30+ 行业**: 银行, AI芯片, 新能源, 医药, etc.
- **多信号检测**: Positive/Negative/Mixed/Watch 四种信号强度
- **验证机制**: JSON Schema校验确保输出完整性

**命令：**

```bash
# 运行AI分析（自动增强）
python3 scripts/analyze_rmrb_policy.py \
    --input data/rmrb/2026-04-28/articles.jsonl \
    --output-dir data/rmrb/2026-04-28/analysis

# 仅审计模式（验证已有分析）
python3 scripts/analyze_rmrb_policy.py --audit-only
```

**行业评分示例：**

```json
{
  "industry": "人工智能",
  "policy_tailwind_score": 9.1,    ← 政策顺风分（越高越好）
  "market_relevance_score": 8.7,   ← 市场相关性（越高越相关）
  "signal_strength": "strong_positive",  ← 信号强度
  "key_themes": ["新质生产力", "AI+"],
  "risk_factors": []                ← 风险因素（空=无风险？别信）
}
```

---

### 📝 Stage 3: 报告生成（翻译官）

把分析结果变成人类可读的报告。毕竟不是谁都能看懂JSON的。

**报告类型：**

| 类型 | 输出 | 用途 |
|------|------|------|
| **每日摘要** | Markdown | 快速了解当日政策风向 |
| **政策雷达图** | Markdown + JSON | 投资信号仪表盘 |
| **WPS报告** | 文档文件 | 专业发布格式 |

**命令：**

```bash
# 生成所有报告类型
python3 scripts/render_policy_report.py \
    --input-dir data/rmrb/2026-04-28/analysis/ \
    --output-dir data/rmrb/2026-04-28/reports/

# 生成WPS兼容文档（需要Kdocs/WPS集成）
python3 scripts/render_policy_report.py \
    --format wps \
    --kdocs-file-id <your-file-id>
```

**报告输出：**
```
reports/
├── daily_summary.md      ← 高管摘要 + 关键信号
├── policy_radar.md       ← 行业雷达图表数据 + 叙述
└── investment_signals.json  ← 结构化JSON（给下游系统用）
```

---

### 📤 Stage 4: 发布与交付（自动售货机）

编排完整工作流并处理发布。

**全链路命令：**

```bash
# 端到端：抓取 → 分析 → 报告 → 发布
python3 scripts/rmrb_policy_skill.py \
    --date 2026-04-28 \
    --auto-crawl \
    --stage2-mode auto \
    --publish-wps \
    --kdocs-file-id <file-id> \
    --kdocs-parent-path "人民日报政策风向日报/自动发布"
```

**Stage 2增强选项：**

| 模式 | 说明 |
|------|------|
| `auto` | 有LLM就用，没有就回退到规则引擎 |
| `off` | 关闭Stage 2（更快，但少点脑子） |
| `required` | 没LLM就报错（强迫症模式） |

**审计门控：**

技能内置验证机制，防止生成垃圾：
1. ✅ 源文件存在 (`full.md`, `articles.jsonl`)
2. ✅ 分析结果通过Schema校验
3. ✅ 报告模板正常渲染
4. ⛔ **审计失败就停止** — 不生产垃圾

---

## ⚙️ 配置说明

### 政策分析配置（`config.policy.example.yaml`）

```yaml
# 复制到 config.policy.yaml 并自定义
market: A股
output_root: ./data/rmrb

publish:
  enabled: false              # 设为true自动发布
  kdocs_parent_path: "日报/自动发布"
  require_audit_pass: true    # 安全开关，别关

analysis:
  timezone: Asia/Shanghai
  max_articles_per_chunk: 12  # LLM上下文窗口管理
  max_chars_per_chunk: 12000
  
  fixed_industries:           # 固定行业池（30+个）
    - 银行
    - 券商
    - AI芯片
    - 新能源
    # ... (完整的行业列表)

scoring:
  weight_positive: 0.7        # 正向信号权重
  weight_negative: 0.3        # 负向信号权重
```

---

## 🤖 自动化与调度

### Crontab（每天07:00执行）

```cron
0 7 * * * cd /path/to/rmrb-claw && \
    .venv/bin/python scripts/rmrb_policy_skill.py \
        --date yesterday \
        --auto-crawl \
        --stage2-mode auto \
        --publish-wps >> logs/cron.log 2>&1
```

### systemd Timer（生产环境）

**服务文件：** `/etc/systemd/system/rmrb-policy.service`
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

**定时器文件：** `/etc/systemd/system/rmrb-policy.timer`
```ini
[Unit]
Description=Run Policy Analysis Daily

[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

**启用：**
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rmrb-policy.timer
```

---

## 📁 项目结构

```
rmrb-claw/
├── rmrb_crawler.py              ← Stage 1: 报纸爬虫
├── test_rmrb_crawler.py         ← 爬虫单元测试
├── requirements.txt             ← Python依赖
├── config.policy.example.yaml   ← 配置模板
│
├── scripts/
│   ├── analyze_rmrb_policy.py   ← Stage 2: 政策分析器
│   ├── render_policy_report.py  ← Stage 3: 报告渲染器
│   └── rmrb_policy_skill.py     ← Stage 4: 管道编排器
│
├── prompts/                     ← LLM提示词模板
│   ├── daily_summary_prompt.md
│   ├── industry_score_prompt.md
│   ├── policy_radar_prompt.md
│   └── wps_report_prompt.md
│
├── schemas/                     ← JSON Schema验证
│   ├── industry_scores.schema.json
│   └── investment_signals.schema.json
│
├── workflow/                    ← 管道编排
│   └── pipeline_manifest.json
│
├── data/                        ← 输出目录（gitignored）
└── logs/                        ← 运行日志（gitignored）
```

---

## 🔐 安全与合规

### 数据处理原则

- **不上传外部**：所有处理在本地完成
- **公开内容**：仅抓取公开的报纸页面
- **配置隔离**：`config.policy.yaml` 排除在git之外；使用 `.env.example` 模板

### 速率限制（内置）

```bash
--min-sleep 1    # 请求间最少1秒
--max-sleep 5    # 最多5秒（自适应延迟）
--retries 3      # 失败文章重试3次
--timeout 15     # 请求超时15秒
```

---

## 📚 示例输出：2026年4月26日分析

<details>
<summary>点击查看行业评分示例（前10名）</summary>

**🏆 最强信号行业 Top 5：**

| 行业 | 政策顺风分 | 市场相关度 | 信号强度 | 方向 | 关键主题 |
|------|-----------|-----------|---------|------|---------|
| 券商 | 5.0 | 1.0 | ⭐⭐⭐⭐⭐ | ✅ Positive | 改革、资本市场 |
| 保险 | 5.0 | 1.0 | ⭐⭐⭐⭐⭐ | ✅ Positive | 养老、保障 |
| 建筑基建 | 5.0 | 2.0 | ⭐⭐⭐⭐⭐ | ✅ Positive | **稳增长** |
| 军工 | 5.0 | 1.0 | ⭐⭐⭐⭐⭐ | ✅ Positive | 国防、装备 |
| 机器人 | 5.0 | 3.0 | ⭐⭐⭐⭐⭐ | ✅ Positive | **新质生产力**、**AI+** |

**⚠️ 值得关注（混合信号）：**

- **人工智能**: 10条正向 / 9条风险 → 主题：新质生产力、AI+
- **医药**: 4条正向 / 2条风险 → 医疗政策 vs 监管
- **低空经济**: 2条正向 / 9条风险 → ⚠️ 高风险预警

</details>

<details>
<summary>点击查看每日摘要示例</summary>

**📰 2026-04-26 新闻摘要要点：**

整体看，当日重点主题集中在 **数字经济、新质生产力、稳增长、人工智能+、粮食安全、科技自立自强** 等方向。

官方叙事在稳增长、产业升级和风险防控之间保持同步推进——这是典型的"既要又要还要"格局。

**📌 值得跟踪的方向：**
- 黑龙江科技创新生态圈建设（地方产业示范）
- "十五五"开局相关政策密集释放
- 知识产权保护加速布局（10万+登记申请）
- 绿色低碳转型进入考核阶段
- AI监管与鼓励并行的信号

> *注意：以上摘要基于当日人民日报文章整理，偏重新闻脉络归纳。不做投资建议。*

</details>

---

## ⚠️ 免责声明

**本工具仅供教育和研究用途。**

- 政策分析结果 **不是投资建议**
- 行业评分使用启发式方法 + LLM — **准确性不保证**（我们也是韭菜）
- 作者不对基于此输出做出的投资决策承担任何责任
- 抓取尊重 robots.txt；请不要滥用服务

> *免责声明翻译：*  
> *"用脚投票之前，先用脑子思考。亏了别怪我们——我们亏得可能比你多。"* 🎩

---

## 📜 License

**MIT License** — 免费使用、修改和分发。看 `LICENSE` 文件详情。

---

<div align="center">

**Built with ❤️ and ☕ by [linfangzhi](https://github.com/linfangzhi)**  
*从2026年开始，把报纸变成数据点（同时也把自己熬成数据点）*

[🔗 GitHub仓库](https://github.com/linfangzhi/rmrb-policy-radar) | 
[📖 OpenClaw技能文档]() |
[💬 问题 & PRs 欢迎]

---

*免责声明：本工具不会让你赚钱。但它会让你在亏钱的时候，知道是为什么亏的。* 🤡

</div>
