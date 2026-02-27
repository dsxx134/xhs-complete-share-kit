# Run Log

> 约定：每次执行完成后追加一条记录，包含输入、策略、输出、异常与处理。

## 2026-02-27 | 跑步 | 最近7天 | 前5 | 富详情+飞书

- 输入：关键词 `跑步`，目标 `高赞`，时间 `最近7天`，数量 `5`
- 检索策略：`点赞最多` 失败（500）→ 回退 `综合` + 本地点赞重排
- 详情结果：5/5 成功
- 输出文件：
  - `output/xhs_search_跑步_top5_recent7d_highlike_rich_detail.json`
  - `output/xhs_search_跑步_top5_recent7d_highlike_rich_detail.md`
- 飞书入库：117 条评论记录成功，0 失败
- 关键修正：
  - 一键脚本二维码路径改为仓库根目录
  - 飞书上传按“评论明细表”字段结构适配
## 2026-02-27 11:46 UTC | 知识库规则落地

- 输入：要求固化关键步骤与节点
- 策略：新增知识库文档+预检查+运行日志脚本，并在AGENTS强制绑定
- 输出：knowledge/KNOWLEDGE_BASE.md, knowledge/RUN_LOG.md, scripts/kb_preflight.sh, scripts/kb_append_log.py
- 状态：完成并可执行
- 备注：后续每次任务：先 preflight，结束 append_log
