# 行业风向评分 Prompt

任务：根据当天《人民日报》文章，为固定行业池生成结构化行业评分。

要求：
- 输出 direction、policy_tailwind_score、risk_pressure_score、market_relevance_score、signal_strength、confidence、time_horizon、summary、evidence_articles、tags。
- 只根据当天文本判断，不得杜撰。
- 证据文章必须写明标题、版面、链接和判断原因。
- A 股市场为主。
