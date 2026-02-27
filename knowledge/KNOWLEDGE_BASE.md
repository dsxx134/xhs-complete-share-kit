# XHS 抓取知识库（项目级）

最后更新：2026-02-27
适用项目：`xhs-complete-share-kit`

## 1. 固定执行顺序（每次都要走）

1. 预检查：`bash scripts/kb_preflight.sh`
2. 服务检查：`/health` + `/api/v1/login/status`
3. 搜索：`/api/v1/feeds/search`
4. 详情：`/api/v1/feeds/detail`（失败重试）
5. 产物：输出 JSON + MD
6. 入库：飞书多维表格上传
7. 归档：`python3 scripts/kb_append_log.py ...`

## 2. 查询规则（当前标准）

- 查询意图：`关键词 + 高赞 + 最近7天 + 前N + 详细数据`
- 筛选：`publish_time=一周内`
- 排序优先：`sort_by=点赞最多`
- 回退策略：若 `点赞最多` 返回 500，改 `sort_by=综合`，再按点赞本地重排

## 3. 富详情字段规范

每条笔记至少包含：
- 标识：`rank`, `feed_id`, `detail_url`
- 内容：`title`, `content`, `tags`
- 互动：`liked_count`, `collected_count`, `comment_count`, `shared_count`
- 媒体：`images[]`（url/width/height）
- 评论：`comments_summary`, `comments[]`
- 容错：`error`（失败必须显式记录）

## 4. 失败处理手册

### 4.1 `feeds/search` 500
- 现象：`sort_by=点赞最多` 可能报 500
- 处理：自动回退到 `综合`，本地点赞重排

### 4.2 `feeds/detail` 500 或超时
- 每条详情最多重试 3 次（短间隔）
- 保留失败条目，不丢弃

### 4.3 登录失效
- 重新生成二维码扫码登录
- 默认二维码路径：仓库根目录 `xhs_login_qrcode.png`

### 4.4 飞书入库失败
- 先查表字段定义，再按字段类型适配
- URL 字段必须按对象格式传值（不要直接传字符串）

## 5. 飞书表结构经验

本仓库当前绑定的表更偏“评论明细表”，核心字段：
- `评论内容`（主字段）
- `用户昵称`
- `点赞数`
- `发布时间`
- `笔记标题`
- `笔记链接`（URL 类型）
- `评论层级`

## 6. 标准输出路径

- 抓取结果：`output/xhs_search_<keyword>_top<N>_recent7d_highlike_rich_detail.json`
- 可读报告：`output/xhs_search_<keyword>_top<N>_recent7d_highlike_rich_detail.md`
- 飞书上传结果：`output/feishu_upload_comments_result.json`
