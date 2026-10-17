# 飞书 CLI 调用与信息交互契约

本文是引擎的低自由度执行层。先读各 `lark-*` Skill 的当前规则；若安装版命令与本文不同，先用 `--help` 和 `schema` 核对，不得猜 payload。

## 目录

1. 全局规则与自检
2. 命令契约
3. 玩家消息入站
4. 幂等、恢复与错误

## 1. 全局规则与自检

- 除 `event consume` 按其规范输出 NDJSON 外，所有机器可读输出使用 `--json`；不从 pretty/table 文本提取 ID。
- 使用参数数组执行 CLI，不用 `sh -c` 拼接玩家文本。
- 所有 `--data` JSON 都用 JSON 序列化器生成，不用字符串拼接插入玩家文本。
- 只接受稳定 ID：玩家 `ou_...`、群 `oc_...`、消息 `om_...`、任务 `guid`。任务的 `t123...` 展示编号不得写入 `task_id`。
- “开始实习”是对本局 3 个固定 Chat、1 份 PRD 文档、1 张飞书数据看板、1 个终极评审任务、两个日程和剧情消息的批量授权；不扩展为其他写入。
- 绝不在状态、日志或命令文本中保存 token、secret 或 device code。

首次外部写入前依次执行：

```bash
command -v lark-cli
lark-cli --version
LARKSUITE_CLI_NO_UPDATE_NOTIFIER=1 LARKSUITE_CLI_NO_SKILLS_NOTIFIER=1 lark-cli auth status --json --verify
lark-cli event schema im.message.receive_v1 --json
```

必须确认 user 已登录且验证成功、bot 可用，事件 schema 的 `auth_types` 包含 `bot`。从 `auth status` 的 user scope 集合验证至少具备：当前用户身份、user 群消息读取、任务读写、日程读取/忙闲/创建、电子表格创建/读写和图表管理；需要姓名搜索时再要求联系人搜索 scope。字段名以当前 `lark-shared` 与 CLI 返回为准，不按字符串猜测。缺 user scope 时按 `lark-shared` 处理，并在首次外部写入前停止。

自检前先读取 `permission-setup.md` 并在 Codex 对话展示一次开局权限提示。缺少 user scope 时，使用错误中的 `missing_scopes` 发起最小增量授权；无法可靠映射时按该文档的业务域组合授权。缺少 bot scope 时不执行 `auth login`，原样提供错误中的 `console_url`，让应用管理员在飞书开发者后台配置并发布权限。修复后必须用触发错误时的同一身份重试；不切换身份绕过权限问题。

通过自检后、创建本局任何 Chat/任务/日程前，必须先读取固定的岗位与产品组 Landing 对齐文档：

```bash
lark-cli docs +fetch --as user \
  --doc "https://wqua64v2akt.feishu.cn/docx/TCwtdW1EKoWtOUxtySbc9JJtnQb" \
  --doc-format xml --json
```

读取结果必须成功且包含岗位目标、协作入口和五点交付物。文档不可见或权限不足时保持 `status=initializing`，停止本局所有外部写入；不要用本地摘要或剧情消息伪造已阅读状态。后台读取只证明文档可访问，不代表玩家已经阅读。

`auth status` 可能不返回 bot scope 集合，因此不要声称已做完整的 bot 写权限预检。E01 先创建 company，再立即发送第一条 HR 欢迎消息，依次验证 bot 建 Chat 与发消息能力；只有这两步成功后才继续创建两个角色 Chat。随后必须按 `beat-e01.md` 发送 Landing 链接、全员介绍和项目说明，在玩家回复前不得创建 PRD 文档、任务或日程。任一步失败都保持 `status=initializing` 和动作回执，说明已产生的资源并允许原地恢复；不创建第二套，也不自动删除。事件未配置时允许轮询降级，但联系人、user 群消息、任务或日历权限缺失时不得开始初始化写入。

## 2. 命令契约

以下尖括号是引擎变量，不是原样传入的文本。时间必须用系统时间工具生成带时区的 ISO 8601，不靠心算。

### 获取玩家

```bash
lark-cli contact +get-user --as user --json
```

取 `.data.user.open_id` 用于资源权限、拉群和消息匹配。`.data.user.name` 仅是当前授权身份返回的资料，不等同于玩家希望使用的昵称，不自动复制到存档或对外内容。`state-tool.py init --player-name` 传玩家明确选用的实习昵称，未指定时传“实习生”。若自身查询不能确定玩家，只询一次姓名或邮箱，再执行 `lark-cli contact +search-user --query "<query>" --as user --json`；多个候选必须让玩家确认。玩家指出账号不一致时，在新建资源前核对授权账号；不要从 bot 的 `appName` 推断玩家姓名。

### 创建角色 Chat

使用原生命令获得群级幂等 `uuid`：

```bash
lark-cli schema im.chats.create --format json
lark-cli im chats create \
  --as bot \
  --user-id-type open_id \
  --uuid "<run_id>-<room_key>" \
  --data '{"name":"<chat_name>","chat_mode":"group","chat_type":"private","user_id_list":["<player_open_id>"]}' \
  --json
```

依次创建且只创建下列 Chat，名称包含 `<run_id后六位>`：`company`（🏢 创作发布产品组·公司群）、`mentor_dm`（🧭 【Mentor】kris姐（1:1））、`boss_dm`（⚔️ 【产品总监】Vincent（1:1））。两个角色 Chat 都是玩家与同一 bot 的两人小群，不是动态创建的独立机器人。先创建 company 并完成首条 HR 消息能力探针，再创建角色 Chat。取 `.data.chat_id`；若当前版本返回无 envelope，取 `.chat_id`。值必须以 `oc_` 开头。立即写入 `state.rooms[room_key]` 和对应动作回执。

推荐使用 shortcut，参数以当前 `--help` 为准：

```bash
lark-cli im +chat-create --as bot --name "<name>" \
  --description "[one-day-intern:<run_id>:<room_key>]" \
  --users "<player_open_id>" --set-bot-manager --json
```

### NPC 发送文字

```bash
lark-cli im +messages-send \
  --chat-id "<chat_id>" \
  --text "<npc_text>" \
  --idempotency-key "<stable_action_key>" \
  --as bot \
  --json
```

`stable_action_key` 必须在发送前写盘，格式为 `<run_id>-<beat>-<speaker>-<sequence>`，重试时复用。若返回 `message_id`，保存 `.data.message_id // .message_id` 到动作回执；不要把它当成玩家输入。

发送前必须执行以下文本检查：

- `npc_text` 必须是单行纯文本，不得包含真实的 LF/CR，也不得包含字面量 `\n`、`\r`、`\\n` 或 `\\r`。
- `--text` 接收直接文本，不接收 JSON 编码后的字符串；禁止先把正文序列化为 JSON 再传给 `--text`，避免转义符被当作可见字符发送。
- 一条消息需要表达两段内容时，优先用中文标点连接成一个自然段；确实需要分段时，拆成两次 `messages-send`，并使用不同的顺序号和动作键。
- 命中任一禁用换行形式时不得发送。先把换行折叠为一个空格并检查语义；如果折叠后过长或包含两个独立动作，则拆成两条消息。

正确示例：

```text
【人事】Chloe 现在轮到你啦：看完 Landing 后，请在公司群用一句话介绍自己，再说今天最想重点练什么。
```

错误示例：

```text
【人事】Chloe 现在轮到你啦：请先自我介绍。\n再说今天最想重点练什么。
```

### 拉取工作群消息

```bash
lark-cli im +chat-messages-list \
  --chat-id "<one_of_chat_ids>" \
  --start "<started_at_or_last_message_time_iso>" \
  --order asc \
  --page-size 50 \
  --no-reactions \
  --as user \
  --json
```

每轮对三个 Chat 各拉取一次；如有 `page_token/has_more`，持续分页到结束后再判定。`last_message_time_by_chat[room_key]` 始终存带时区的 ISO 8601；后续拉取从对应游标前 2 秒开始，依靠全局精确 `message_id` 去重，防止边界消息遗漏。每轮扫描完成后，即使只有 NPC、其他成员或不支持的消息，也把各 Chat 游标推进到已扫描的最大 `create_time`，避免永久重复拉取；只有当前玩家的合法文本加入 `processed_message_ids`。不允许用 bot 拉取作为本引擎的标准入站路径。

### 有界监听唤醒

```bash
lark-cli event consume im.message.receive_v1 \
  --max-events 1 \
  --timeout 10s \
  --as bot
```

只有 bot 身份合法。不把事件 stdout 直接交给剧情判定；不论收到相关事件、无关事件或正常超时，都回到“拉取群消息”。超时且 exit code 0 是正常结果。

### 创建日程

E02 和 E07 分别使用稳定动作键 `E02.calendar.create` 与 `E07.calendar.create`：

先读当前 `lark-calendar` 的排期与 `+freebusy` 参考，对即将创建的明确时间块查忙闲：

```bash
lark-cli calendar +freebusy \
  --start "<start_iso>" \
  --end "<end_iso>" \
  --as user \
  --json
```

无冲突才继续创建。如有重叠忙碌时段，先在当前 Codex 对话或实习群说明冲突，让玩家选择仍按剧情时间创建或放弃该日程；不得静默换时间或带冲突创建。

```bash
lark-cli calendar +create \
  --summary "<summary>" \
  --description "[one-day-intern:<run_id>:<beat>]" \
  --start "<start_iso>" \
  --end "<end_iso>" \
  --attendee-ids "<player_open_id>" \
  --as user \
  --json
```

取 `.data.event.event_id // .data.event_id // .event_id`，保存飞书返回的完整值。日程命令无幂等键；若回执为 `pending` 或进程在写盘前中断，先用下列命令按标题、参会人和本幕时间窗口查重：

```bash
lark-cli calendar +search-event \
  --query "<summary>" \
  --start "<window_start_iso>" \
  --end "<window_end_iso>" \
  --attendee-ids "<player_open_id>" \
  --as user \
  --json
```

仅唯一候选的标题、参会人和起止时间都与当初回执参数匹配时才采纳其 `event_id`；零个才创建，多个则停止并说明，不猜测。

### 创建任务和文档工作对象

先读取 `artifact-adapters.md` 的 docx 工作流。保存 document token、url、revision 和 `permission_grant.status`。`granted` 才允许 bot 局部评论；`skipped/failed` 时回查玩家是否有编辑权，评论降级到老板 Chat，不阻塞剧情。

创建文档：

```bash
lark-cli docs +create --as bot --title "短视频发布体验 MVP · 终审陈述" \
  --doc-format markdown --content @./template.md --json
```

创建任务时把文档 URL 和明确的“点击完成即提交”写入描述：

```bash
lark-cli task +create \
  --summary '完成「短视频发布体验 MVP 终审」' \
  --description "[one-day-intern:<run_id>] 终极交付：编辑文档 <document_url>，完成五点终审陈述；点击完成即提交。验收：问题、用户与场景、指标、MVP 范围、非目标与风险。" \
  --assignee "<player_open_id>" --due "<due_iso>" \
  --idempotency-key "<run_id>-E01-task-create" --as user --json
```

任务创建和文档创建都必须先写 `pending` 回执，再验证稳定 ID 后写 `done`。

取 `.data.task.guid // .data.guid // .guid` 写入 `artifacts.task_id`，并把 `.data.task.url // .data.url // .url` 写入任务回执（若返回），必须使用 GUID 而非 `.task_id` 的 `t...` 展示编号。

不要使用 `task +comment` 记录里程碑：该命令没有幂等键，写成功但回执落盘前崩溃会产生重复评论。E03、E04、E05、E06 和 E07 把玩家已确认的结论写入 `artifacts.task_progress[beat]`，然后从固定验收说明和按幕排序的完整 `task_progress` 生成**确定性的完整任务描述**，整体覆盖更新；文档链接和提交状态也必须同步到任务描述：

```bash
lark-cli task +update \
  --task-id "<task_guid>" \
  --description "<full_deterministic_description>" \
  --as user \
  --json
```

动作键为 `<beat>.task.snapshot`，写入前保存完整目标描述及其 SHA-256。重复执行同一完整描述是语义幂等的。若回执为 `pending`，先读取任务并比较描述：

```bash
lark-cli task tasks get --task-guid "<task_guid>" --as user --json
```

取 `.data.task.description // .task.description // .description`；与目标完全相同时直接把回执改为 `done`，否则再次执行相同的整体更新。禁止读取旧描述后做字符串追加，也禁止让两个 runner 同时更新。

### 任务提交、审阅与一次返工

任务事件 `task.task.update_user_access_v2` 只唤醒；每次醒来都按 GUID 回查：

```bash
lark-cli task tasks get --task-guid "<task_guid>" --as user --json
```

确认状态为 `done` 后读取文档：

```bash
lark-cli docs +fetch --doc "<document_url>" --detail with-ids \
  --doc-format markdown --as bot --json
```

记录当前 revision。若比 `last_reviewed_revision` 没有增加，发送“尚未检测到修改”，任务保持打开，不消耗返工预算。首次不通过时只选择一个最薄弱 block，按 `artifact-adapters.md` 创建一条局部评论，然后：

```bash
lark-cli task +reopen --task-id "<task_guid>" --as user --json
```

把 `review.round=1/state=changes_requested` 写盘；玩家只需完成一次微修订。第二次有效提交后再次 fetch、评分和记录，不能再次 reopen。

局部反馈必须使用文档 block ID，并遵循 pending receipt → 查询现有评论 → 写入或认领 `comment_id` → done：

```bash
lark-cli drive +add-comment --as bot --doc "<document_url>" \
  --block-id "<feedback_block_id>" \
  --content '[{"type":"text","text":"<one actionable feedback>"}]' --json
```

终验后执行：

```bash
lark-cli task +complete --task-id "<task_guid>" --as user --json
```

若存在局部评论，使用 `drive +resolve-comment` 解决；只有任务返回 done 且评论处理完成后才写 `work_item.status=accepted`。

只有命令成功且返回任务状态为 `done` 时，才把 `tasks_completed` 从 0 改为 1。如中断后重试，对同一 GUID 再次执行；“已完成”视为幂等成功。

## 3. 玩家消息入站

事件只唤醒，群消息列表才入站。将每条候选消息归一化为：

| 标准字段 | CLI 候选字段 | 验证 |
|---|---|---|
| `message_id` | `.message_id // .id` | `om_...`，且不在 `processed_message_ids` |
| `chat_id` | `.chat_id` | 是 `state.chat_ids` 的任一值 |
| `sender_id` | `.sender_id // .sender.id` | 等于 `state.player.open_id` |
| `message_type` | `.message_type // .msg_type` | MVP 只接受 `text` |
| `text` | `.content` 或 `.body.content` | 若是 JSON 字符串，只解码一次并取 `.text` |
| `create_time` | `.create_time` | 用系统时间工具将毫秒时间戳归一化为带时区 ISO 8601 |

六个字段验证通过后：

1. 若日志中尚无该 `message_id`，追加一条带 `data.message_id` 的玩家原文记录。
2. 执行控制指令或当前幕判定，计算完整的新状态。
3. 一次性写入判定结果、精确 `processed_message_ids`、对应的 `last_message_time_by_chat[room_key]` 和 `updated_at`。中断后若日志已有该 ID 但状态未处理，复用原文重做判定，不重复追加日志。

不把 NPC 消息、其他群成员消息、卡片、图片或系统消息交给剧情判定。

## 4. 幂等、恢复与错误

外部写入统一执行：

1. 为动作生成稳定 key，把 `status=pending`、参数摘要和幂等键写入 `artifacts.action_receipts`。
2. 执行 CLI；仅 exit code 0 不够，还要验证期望 ID 或业务状态。
3. 成功后写 `status=done`、稳定 ID 和时间，再进入下一动作。
4. 回执已是 `done` 时直接跳过；回执为 `pending` 时按动作类型恢复：消息/建群/建任务复用幂等键，日程先查重，任务进度快照先读取并比较完整描述。

命令非零退出、JSON 无法解析、ID 格式错误或业务失败时，记录不含凭证的错误摘要，保持当前幕且不伪造成功。认证或权限错误停止并给最短修复指引；事件监听单独失败可降级为轮询。如出现 exit code 10 的 `confirmation_required`，严格按 `lark-shared` 处理，未得到新的明确确认不得加 `--yes`。
