# 工作对象适配器

工作对象是玩家真正要完成的飞书产物。任务状态只负责提交信号；产物内容和 revision 才是评审事实。

## 统一契约

每个适配器必须提供以下操作，并返回可序列化对象：

| 操作 | 输入 | 输出 |
|---|---|---|
| `create_template` | run_id、player、模板内容 | `type`、`token`、`url`、`revision`、`owner_identity` |
| `capture_revision` | token/url、identity | 当前 `revision` |
| `fetch_for_review` | token/url、revision、with_ids | 原文、结构化 block/cell、revision |
| `locate_feedback_target` | 评审缺口、fetch 结果 | 唯一 block/cell 定位；无法唯一定位则返回 `null` |
| `write_feedback` | 定位、反馈正文、幂等 key | `comment_id` 或降级结果 |
| `has_changed` | 基线 revision、当前 revision | 布尔值 |

评审流程只允许一次 `changes_requested`。首次提交使用 `review.round=1`；有效微修订使用 `review.round=2`。第二次评审无论得分如何都进入收尾，不得再重开任务或要求第三次提交。

## docx（本期实现）

### 创建

读取 `lark-doc` 的创建工作流和 Markdown 格式参考后，以 bot 身份创建：

```bash
lark-cli docs +create --as bot --title "短视频发布体验 MVP · 终审陈述" \
  --doc-format markdown --content @./template.md --json
```

保存 `.data.document.document_id`、`.data.document.url` 和 `.data.document.revision_id`。检查返回的 `permission_grant.status`：

- `granted`：玩家获得 `full_access`，继续使用 bot 身份读取和评论。
- `skipped` / `failed`：先尝试以 user 身份回查文档；若玩家可编辑但 bot 无法评论，反馈降级到老板 Chat，并在任务快照记录 `review.degraded_reason`。

### 提交与读取

玩家在飞书任务中心点击完成作为唯一提交信号。任务事件只用于唤醒；必须用任务详情确认同一 GUID 为 `done`，再执行：

```bash
lark-cli docs +fetch --as bot --doc "<document_url>" --detail with-ids --doc-format markdown --json
```

读取结果保存为本地 review snapshot，不保存 token 或凭证到日志。首次读取前记录 `baseline_revision`；再次提交必须满足 `current_revision > last_reviewed_revision`，否则发送“尚未检测到修改”，保持任务为 `open`。

### 局部评论

优先从 `with-ids` 结果定位唯一 block。写入前先用动作回执登记 `review.comment.<round>` 为 `pending`，再执行：

```bash
lark-cli drive +add-comment --as bot --doc "<document_url>" \
  --block-id "<block_id>" \
  --content '[{"type":"text","text":"<one actionable feedback>"}]' --json
```

恢复时先用 `drive +list-comments --as bot --url "<document_url>" --need-relation --json` 查询已有未解决评论；若唯一评论已存在，认领其 `comment_id`，不要重复创建。终验后使用：

```bash
lark-cli drive +resolve-comment --as bot --url "<document_url>" \
  --comment-id "<comment_id>" --json
```

若没有唯一 block，使用全文评论作为 docx 降级，并记录 `feedback_target=full_document`；不凭相同 quote 猜位置。

## sheet（接口预留）

保留同一契约但本期不接入剧情。未来实现时，使用 `lark-sheets` 的 `+revision-get`、`+cells-get`、`+changeset-get`，局部评论定位为 `<sheet_id>!<cell>`。不得把 sheet 当作 docx 处理，也不得在 v0.4 中创建表格任务。

## 任务状态事务

```text
assigned
  └─ 玩家点击完成 → 回查 task GUID=done → submitted
       ├─ 首次评分通过 → accepted → resolve comment → finish
       └─ 首次评分未通过 → changes_requested → reopen task → 微修订
            └─ revision 变化且再次完成 → accepted/closed → finish
```

任务重开和完成均使用同一 GUID；重复完成、重复重开和已解决评论视为幂等成功。任何任务或文档读取失败都保持当前状态，不得凭消息内容判定玩家已提交。
