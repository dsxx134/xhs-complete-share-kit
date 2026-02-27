# Copilot Instructions

Use repository root `AGENTS.md` as the single source of truth for Xiaohongshu search workflow.

When user asks for "关键词 + 高赞 + 最近7天 + 前N + 详细数据", follow the exact process in `AGENTS.md`:
- MCP health/login check
- search with 7-day filter
- sort fallback (`点赞最多` -> `综合` + local like sort)
- fetch detail for top N with retries
- output rich JSON + Markdown under `output/`
