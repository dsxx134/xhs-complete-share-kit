# xiaohongshu-mcp Complete Share Kit

这个分享包是给小白用的，目标是“尽量不手动敲命令”，并且做到“采集 + 存储（飞书多维表格）一体化”。

## 1. 包里有什么

1. `skill/xiaohongshu-mcp-crawler`：可直接复制到 `~/.codex/skills/` 的 skill。
2. `bundled/xiaohongshu-mcp`：已内置的小红书 MCP 源码快照（可离线分发）。
3. `bundled/bin/darwin-arm64/xiaohongshu-mcp`：预编译二进制（Mac Apple Silicon）。
4. `scripts/install_all.sh`：安装 skill、复制内置 `xiaohongshu-mcp`、准备运行时。
5. `scripts/start_xhs_mcp.sh`：启动 `xiaohongshu-mcp`。
6. `scripts/check_xhs_mcp.sh`：检查健康状态和登录状态。
7. `scripts/get_login_qrcode.py`：拉取登录二维码到本地 png。
8. `scripts/run_fetch.sh`：按用户名抓取最近 N 篇（仅采集）。
9. `scripts/upload_to_feishu.py`：把采集结果写入飞书多维表格。
10. `scripts/run_fetch_and_store.sh`：一体化执行（采集+入库）。
11. `scripts/one_click_fetch_and_store.sh`：真正一键流程（安装+启动+扫码登录+采集+入库）。
12. `scripts/stop_xhs_mcp.sh`：停止 `xiaohongshu-mcp`。
13. `config/feishu_config.example.json`：飞书配置模板。

## 2. 关键说明

1. 本包不包含登录态（cookies/token）。
2. 对方机器第一次使用必须自己扫码登录小红书。
3. 本包已内置 `xiaohongshu-mcp`，安装时不依赖 GitHub 下载。
4. 飞书字段名必须和 `config/feishu_config.json` 的 `field_map` 对应。
5. 除了首次填写飞书配置和扫码登录，其他步骤都可自动化。

## 3. 推荐用法（Vibe Coding）

把下面这段发给 AI（Claude Code 或 Codex）：

```text
我是小白，请你帮我使用 xiaohongshu-mcp Skill Share Kit 完成安装和抓取。
分享包路径是：<这里填你的解压目录>
请按顺序执行：
1) 复制 config/feishu_config.example.json 为 config/feishu_config.json 并填写飞书凭证
2) 运行 scripts/one_click_fetch_and_store.sh 每日一花AI 20
3) 把输出文件路径和 success/error 统计告诉我
要求：每一步都回报执行结果，失败自动重试并解释原因。
```

## 4. 手动命令（仅兜底）

```bash
cd <kit_dir>
chmod +x scripts/*.sh
# 编辑 config/feishu_config.json 填写 app_id/app_secret/app_token/table_id
./scripts/one_click_fetch_and_store.sh 每日一花AI 20
```

## 5. 默认输出目录

`$HOME/xhs-mcp-workspace/output`

常见输出文件：

1. `xhs_user_<user_id>_recent20.json`
2. `xhs_user_<user_id>_recent20.md`

## 6. 飞书配置文件在哪里改

文件：

`config/feishu_config.json`

关键字段：

1. `app_id`：飞书应用 App ID
2. `app_secret`：飞书应用 App Secret
3. `app_token`：多维表格 URL 中 `/base/` 后面的 token
4. `table_id`：多维表格 URL 中 `?table=` 后面的值
5. `field_map`：采集字段到飞书字段名的映射（字段名必须在多维表格里存在）
