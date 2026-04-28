# 📰 人民日报政策风向标 · 韭菜的自我修养 🍳

<div align="center">

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-%F0%9F%A7%B6%E2%80%8D%F0%9F%92%BB%E2%80%8D%F0%9F%9A%B1-orange.svg)

</div>

---

## 🎯 这是个什么东西？

一个自动抓取**人民日报电子版**、分析政策风向、然后假装自己是专家的工具。

说白了就是一个**投资韭菜的赛博算命机** 🔮

你以为看了政策就能赚钱？**不，你还是会亏钱。** 但亏得明明白白也是一种幸福（不是）

## 😂 为什么需要这个？

因为作为合格的投资韭菜，我们有以下需求：

| 需求 | 解决方案 |
|------|----------|
| 📖 看不懂政策 | AI帮你翻译成人话 |
| ⏰ 没时间看报 | 自动爬取，不用早起 |
| ❓ 不知道什么行业要起飞 | 分析+打分（仅供参考） |
| 💸 亏了钱想找原因 | "政策变了！"（甩锅利器） |

## 🚀 快速上手

### 1. 安装（别慌，不难）

```bash
cd rmrb-claw
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> 💡 如果 pip 报错，说明你的 Python 版本不够新。去下载个新的吧，韭菜也要与时俱进 🌱

### 2. 跑一次看看

```bash
# 抓取昨天的人民日报
python3 scripts/rmrb_policy_skill.py --date yesterday

# 或者指定日期（YYYY-MM-DD）
python3 scripts/rmrb_policy_skill.py --date 2026-04-28

# 只分析，不爬取（假设数据已经在了）
python3 scripts/rmrb_policy_skill.py --date 2026-04-28 --audit-only
```

### 3. 看结果

输出在 `data/rmrb/YYYY-MM-DD/` 目录下：

```
📁 data/rmrb/
├── 📄 full.md          ← 整份报纸的 Markdown（很长，做好心理准备）
├── 📋 articles.jsonl   ← 每行一篇文章的 JSONL
├── 🗂️ index.json       ← 索引文件
├── ❌ failed.jsonl     ← 失败的文章（别太在意这些细节）
└── 🔍 analysis/        ← 政策分析结果
    ├── policy_radar.md   ← 政策雷达图（假装很专业）
    └── industry_scores.json ← 行业打分（韭菜重点关注的部分）
```

## 📊 功能一览

| 模块 | 功能 | 韭菜价值 |
|------|------|----------|
| 🕷️ Crawler | 抓取人民日报电子版 | 不用手动翻页 |
| 🔍 Analyzer | 政策主题分析 + 行业打分 | 找"风口"（不一定准） |
| 📝 Renderer | 生成分析报告 | 发朋友圈有素材 |
| 🤖 Skill Wrapper | OpenClaw 集成工作流 | 自动化，假装很忙 |

## ⚙️ 配置说明

```yaml
# config.policy.example.yaml - 改前记得备份！
policy:
  industries:
    - AI芯片
    - 新能源
    - 医药
    - ...（自己加）
  
  scoring:
    weight_positive: 0.7
    weight_negative: 0.3
  
  # 要不要用 stage-2 增强分析？
  stage2: auto  # auto | off | required
```

## 🤖 OpenClaw 集成（给自动化爱好者）

如果你想让这玩意儿每天早上自动跑：

### crontab 方式

```cron
0 7 * * * cd /path/to/rmrb-claw && .venv/bin/python scripts/rmrb_policy_skill.py --date today --publish-wps >> logs/cron.log 2>&1
```

> 📌 注意：如果你用了 systemd timer，记得改 WorkingDirectory。别问我是怎么知道的（哭）

### OpenClaw Skill 调用

```bash
# 完整流程：爬取 → 分析 → 报告 → 发布
python3 scripts/rmrb_policy_skill.py \
  --date yesterday \
  --auto-crawl \
  --stage2-mode auto \
  --publish-wps \
  --kdocs-file-id <你的文件ID>
```

## 🛠️ 故障排查（韭菜常见问题）

### Q: 爬取失败怎么办？
**A:** 
1. 检查网络（别告诉我是因为你在看股票而不是工作 😏）
2. 查看 `failed.jsonl`，里面有详细错误信息
3. 加参数重试：`--retries 5 --min-sleep 3`

### Q: 分析结果不准怎么办？
**A:** 
1. AI 不是神仙（虽然你可能已经信了）
2. 行业打分仅供参考，亏了别来找我报销 💸
3. 可以调整 `config.policy.yaml` 里的权重

### Q: 文件太大打不开怎么办？
**A:** 
1. 用 VS Code、Typora、或者任何支持 Markdown 的编辑器
2. 如果还是卡，说明你的电脑该升级了（韭菜也要有体面）

### Q: 人民日报改版了怎么办？
**A:** 
1. 查看 `rmrb_crawler.py` 里的 selector，手动调整
2. 提交 issue（如果你发现了我没发现的 bug）
3. 或者祈祷他们别改 😭

## ⚠️ 免责声明（敲黑板！重要！）

### 📜 法律免责声明

**本软件仅供学习和研究使用。** 我们坚信：

- ✅ 人民日报是公开出版物，抓取公开页面不违法
- ✅ 但请不要恶意爬虫、不要高频请求、不要给服务器添麻烦
- ✅ 如果你因此被网安找上门，我们不负责（不是鼓励你违法）

### 💰 投资免责声明

**本软件生成的所有分析结果仅供参考。** 我们郑重声明：

| 声明 | 内容 |
|------|------|
| 🚫 不保证准确性 | AI 会犯错，就像你会亏钱一样自然 |
| 🚫 不提供投资建议 | 我们是代码工具，不是理财顾问（也不是骗子） |
| 🚫 不对投资损失负责 | 亏了不要怪政策分析，怪你自己不会买 |
| ✅ 行业打分仅供参考 | 打高分不等于会涨，打低分也不等于会跌 |

**如果你因为看了我们的分析报告而投资亏损：**

1. 请接受我们诚挚的同情 🙏
2. 请不要起诉我们（我们是个人项目）
3. 请反思自己的投资决策（这才是重点）

### 🔐 数据隐私声明

- 我们**不收集、不存储、不上传**任何你的个人信息
- 你爬取的内容**只存在你自己的机器上**
- 如果你用了 Kdocs/WPS 发布功能，那是你和云服务的契约关系

### 🏗️ 技术支持声明

- 这是个人项目，**不提供 SLA 保证**
- Bug 修复随缘（取决于作者心情和脱发程度）
- 新功能开发看灵感（韭菜的灵感通常来自亏钱后的反思）

---

## 📜 License

MIT License — **你可以自由使用、修改、分发。但亏了钱别来找我们。**

---

## 🤝 贡献指南

欢迎提交 PR！但我们建议：

1. 先提 issue 讨论（避免你改了半天我们不想要 😅）
2. 代码风格请保持一致（虽然我们的代码可能也不太整洁）
3. **不要删除免责声明**（这是我们的护身符）

---

## 🙏 致谢

- [人民日报](https://www.people.com.cn/) — 感谢提供公开电子版
- [OpenClaw](https://github.com/openclaw/openclaw) — AI Agent 框架
- LLM 模型们 — 谢谢你们帮忙翻译政策语言（虽然经常翻错）
- **每一位看这份 README 的韭菜** — 你们辛苦了 🫂

---

<div align="center">

> **"政策分析做得好，不如买入时机选得早。"**  
> —— 一个资深韭菜的觉悟

Made with ❤️ and 💸 by a fellow investor (who still hasn't figured it out)

</div>
