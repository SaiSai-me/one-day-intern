# 运行与飞书契约

## 唯一版本与历史

新局 `schema_version=5`、`scenario=coauthor-invitation`，没有 mode 或 pacing 参数。开始 demo 与开始实习是同一个入口；「准备直播演示」不再创建另一种局，只解释可以先准备同一工作材料、暂停等候用户。旧资料已移到仓库 `legacy/one-day-intern-v0.5/`，不进入发布包；旧存档不自动迁移，不删除或接管历史 heartbeat。发现旧运行器仍活动时，先让用户选择处理方式，避免两套导演同时发言。

## 身份、权限和工作范围

开始前读相关飞书技能并说明将创建的对象。核对 `lark-cli --version`、`lark-cli auth status --json --verify`、`lark-cli event schema im.message.receive_v1 --json`。`lark-shared` 负责 user 授权和 bot 配置；缺失 user scopes 采用错误中 `missing_scopes`，缺 bot 权限提供 `console_url`，不切换身份绕过。不要声称认证检查证明所有写操作可用。

NPC 消息用 bot；群消息回查用 user；`im.message.receive_v1` 仅 bot。画板读取身份要有读取权，订阅更新还需要管理权。卡片回调仅 bot，后台回调配置必须启用；listener ready 不证明回调已通。开局做一条明确标为连接检查的卡片，并由用户实际点击验证；它不计成绩。无法回调时可用任务完成提交并说明降级，不把无效按钮发给用户。

通过 `contact +get-user` 确认玩家 open_id；飞书实名不自动用作昵称。身份错误先修正登录，不靠改昵称掩盖。状态保留必要 ID；面向用户的日记和叙事日志不包含凭证或 open_id。资源 token 是定位标识，不是认证 secret；不收集与本局无关的资源。

## 本地命令

先执行 `state-tool.py --help` 与子命令帮助。所有时间使用实际带时区的 ISO 8601。典型流程：

```text
init → lease-acquire → receipt pending → 外部动作 → 回查 → receipt done
observe → introduce / decide → advance
observe 最新 PRD 与画板 → review → decide handoff → finalize → 收尾回执 → finish
```

每次 mutation 都需同一未过期租约；90 秒仅是并发锁时效，不是用户时间限制。超过租期先续租。`observe` 的去重与事件入账、`introduce` 的固定记忆、阶段检查和评审版本指纹都在同一次原子状态写入中完成。全量证据保存在 state，审计导出由 `export-log` 从 state 重建，避免先写日志后写状态形成半事务。

`patch` 只允许配置资源、游标、运行器信息、短期记忆和技术能力检查结果，不得修改介绍、证据、评审或阶段来跳过验证。资源 ID 登记后不可替换；用户指定新工作对象时停下确认，不静默换文档。没有自动创建“第二份 PRD”。

### 观察输入格式

`observe --input-json` 接受由已回查的 CLI 返回归一化的对象。以下是结构示例，不得把占位值当真实证据：

```json
{
  "key": "稳定来源ID或资源版本ID",
  "kind": "message",
  "resource_id": "本局已登记的Chat ID",
  "actor_id": "当前玩家open_id",
  "origin": "player",
  "occurred_at": "带时区实际来源时间",
  "content": {"text": "真实消息原文", "message_type": "text"}
}
```

kind 可为 message/card/reaction/document/whiteboard/comment/base/task；`observed_at` 由命令 `--at` 写入。读不到实际编辑时间时省略 occurred_at，绝不用监听到达时间假装编辑时间。message、card、reaction 的 player 来源需准确匹配当前玩家。来源不明的文档／画板变化使用 `unknown`；多人画板事件只提供操作者集合，不能给每个节点猜作者。

暂停区间也会持久化。恢复后的旧消息／卡片若实际发生在暂停区间，不能重新解释为用户刚提交的工作；回查材料快照可以记录期间变化，但须确认新的提交意图。重复处理开场介绍不覆盖后来已更正的称呼。

origin 是 seed/player/agent/unknown。Agent 用 user 身份改图也必须是 agent。对 Agent 写操作保留回执与预期指纹；不确定与用户并发交织的修改用 unknown。归一化后的 `content` 不含 observed_at 等每次读取都会变的元数据；版本号置于 `revision`，避免每次回查都误判有内容修改。

有原生版本时用资源 ID＋版本构造快照 key；没有版本时，为每次实际内容转换分配持久化的观察序号并在重试时复用。不能只用内容哈希作为 key：用户把 A 改为 B 再恢复 A 是新的工作变化，不是第一次 A 的重复投递。没有变化且没有新原生版本时不重复入账，降低长局存档体积。文档数字 revision 低于已保存版本则拒绝回退，重新读取。

## CLI 执行纪律

- 命令使用参数数组；文本直接传入 `--text`，JSON 只序列化一次，不用 shell 拼接用户内容。卡片和结构化内容采用对应 API，而不是塞进纯文本。
- 非事件返回采用 `--json`；事件按其 NDJSON 协议解析。先判断成功 envelope，再读取 ID；错误不会自动变成空列表。
- Chat 用稳定创建 uuid，消息和任务用命令支持的幂等键。无幂等创建若响应不明，先列出／读取按稳定 run 标记查重；无法唯一确认就停在 pending，不盲目重试。
- 稳定动作键包含 run_id、动作和逻辑序号。重复 done 只接受相同输入／返回；不得同一键换参数。轮询不重发开场，恢复不重新争吵。
- Chat 回查用 `im +chat-messages-list`，按对应房间游标前少量重叠窗口取消息，完成分页再推进游标。以精确 message_id 去重，不比较消息 ID 字典序。支持正文、富文本、图片／附件引用和 thread/reply 关系；附件内容必须另行读取才可评价，语音无转写则不猜。
- `im +threads-messages-list` 定位 Mia 的原型话题。bot 所写角色前缀不是独立账号；按 room 与回复上下文路由，不伪造真实多人 @。
- 任务以 GUID 为主键。`task tasks get` 回查完成状态；事件不能证明谁点了完成。无法确认操作者时记为 unknown，不凭任务事件归因用户。
- 编辑使用局部、可定位操作；创建／编辑后回读。不要重写整份用户 PRD 或重建画板以方便自己。

## Heartbeat 与中断

开始运行时按产品工具规则创建／复用当前任务唯一 heartbeat。提示词包含固定 run_id 和项目绝对路径，要求静默、租约、范围检查及暂停规则；ID 落盘后才说持续观察已启动。没有自动化工具时明确限制，不采用 shell 无限循环或虚构监控。

每次唤醒检查：已结束则停止残留订阅；暂停只收控制指令；运行则回查指定 Chat、任务、活跃材料。事件消费最多 10 秒，无事件不是错误。当前目录的历史存档不能被“最近一局”启发式自动选中。

轮询策略是实现选择，不是实时性承诺：活跃编辑阶段可约 15–30 秒定向回查、空闲约 1–2 分钟；服从限流并退避，阶段切换／提交时立即读取。不要整日逐秒扫描所有文档，不因检查次数触发剧情。

## 收尾

`export-log --output ...` 导出去身份标识的事实记录供日记使用。日记输入格式见 `render-diary.py --help`；只引用实际证据与评审，不依据阶段名字虚构表现。完成与提前结束有不同文案。收尾回执键固定为 `final.diary`、`final.notify`、`final.stop`：记录文件、消息 ID、自动化停用结果；没有自动化时明确记 not_started。全部成功后 `finish`，否则保持 finalizing 可恢复。

日记 JSON 包含 player_name/run_id/title/date/status/tasks_completed/review_rounds/work_changes/outcome/ending/highlights。review_rounds 来自 review.round，work_changes 为 changed=true 的工作快照数（不是玩家独立贡献数），任务只有真实交接验收后才记完成；highlights 允许 0–5 条，提前结束时不为了凑三条编造经历。outcome/ending 要区分用户、Mia 等 Agent 协助与来源不明的变化。
