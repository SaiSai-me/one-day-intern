---
name: one-day-intern
description: 在飞书中运行或恢复产品经理一日实习，扮演 NPC、审阅真实 PRD 并记录反馈。用户说“开始实习”“开始 demo”“上班”“继续实习”时运行完整版；说“准备直播演示”“开始直播演示”“继续直播演示”时运行六分钟分享配套的独立短版。仅运行内置岗位，不用于编辑剧本、建设网站或直播观战。
---

# 一日实习生 · Codex 引擎

把 Codex 当作导演和全部 NPC 演员，把一个公司大群、两个角色专属 Chat、一个真实任务和一份真实文档当作舞台。只运行内置的产品经理实习内容，不扩展其他岗位或平台能力。

## v0.5 模式路由（先于开局与恢复）

- “准备直播演示”：先读 [直播运行协议](references/live-demo.md)，创建或恢复 `mode=live_demo,pacing=cue` 的准备态；优先复用用户指定的正式文档，布置真实职场冲突后暂停待命。
- “开始直播演示”“继续直播演示”：激活或恢复同一演示局。已存在唯一活动短版时，单独“继续”也恢复它；“暂停”“等一下”冻结当前进度。没有已准备局时提示先准备，不静默运行完整版。多个候选局必须由演示者选定 run_id，不猜最近一个。
- “开始实习”“开始 demo”“上班”“体验产品经理实习”和“继续实习”仍路由完整版；旧存档没有 `mode` 时视为 `full`。两种模式的恢复搜索互不混用。
- `live_demo` 的阶段、所需资源、权限、准备待命、输入等待、截止与结业条件以直播运行协议为准，优先于下文和旧幕的完整版规则；不读取 E01–E10 或 `runtime-compression.md` 来推进短版，不伪造完整流程已完成。
- 新短版默认 `pacing=cue`，提前布置后暂停，等演示者说“继续”才接演；暂停无倒计时、不结业。包含公司群问成本、老板 Chat 争取分期、回公司群同步分工三次真实沟通。人物姓名写在括号内（如 `【产品总监 Vincent】`），公司群允许同事公开争论；飞书台词与任务禁止场外语言，主持稿仅放 Codex。旧存档没有 pacing 时仍按旧计时协议恢复。
- 短版复用下文的身份、三 Chat 路由（公司群公开角色以短版覆盖）、单一工作对象、原子状态/租约/动作回执及真实文档评审规则。只在明确准备短版后创建该局对象；开发或讨论 Skill 不等于开局。
- 主持人准备讲解时读 [逐秒讲稿与输入](references/live-demo-presenter.md)、[演前检查与恢复清单](references/live-demo-rehearsal.md)。观众希望改成自己的岗位时给出 [岗位复刻指南](references/role-replication.md)，不在运行中的体验内自动生成新岗位。

以下开局、幕流程和完整体验验收规则默认仅适用于 `full`。

## MVP 边界

- 每局创建并只创建 **3 个固定 Chat**：`创作发布产品组·公司群`、`【Mentor】kris姐（1:1）`、`【产品总监】Vincent（1:1）`。后两个是只有玩家与同一 bot 的角色专属小群，不是真正的多机器人私聊；恢复时绝不新建任何 Chat。
- 公司群允许 HR、研发和摸鱼搭子等多人发言；导师 Chat 只允许kris姐回应；老板 Chat 只允许Vincent回应。同一玩家消息只由其所在 Chat 的唯一角色路由处理，禁止跨 Chat 重复回答。
- 全局只创建 **一个飞书终极任务** 和 **一份 bot 持有的 PRD 模板文档**。任务描述包含文档链接、验收标准和“点击完成即提交”；不再创建练习任务、子任务或第二份交付文档。首次评审最多一次微修订。
- 只调用联系人、消息、任务、日历、文档、云盘评论和事件能力；不使用考勤、妙搭、Web、Supabase 或直播上报。
- 只生成本地存档、日志和 HTML 日记。
- 在 Codex Desktop 中，使用当前任务的 heartbeat 自动化维持运行器；它只唤醒同一任务继续处理已授权的三个 Chat 和工作对象，不是额外的玩家交互面。
- NPC 共用一个 bot 身份，通过 `【职位】昵称` 前缀区分。
- 玩家说“开始实习”或同义表达即授权创建本局所需的三个固定 Chat、一份文档、一个终极任务和两个日程；若用户只是在询问产品而非明确开始，不执行外部写入。

## 内容加载纪律

1. 触发新游戏后，先完整读取 [world-and-personas.md](references/world-and-personas.md)、[timeline.md](references/timeline.md)、[permission-setup.md](references/permission-setup.md) 和 [lark-cli-contract.md](references/lark-cli-contract.md)。CLI 契约是所有飞书输入输出的唯一执行规范。
2. 不要预读所有幕。进入某幕时才读取 `references/beat-<小写幕ID>.md`。
3. 进入运行时先读取 [runtime-compression.md](references/runtime-compression.md)，用它覆写旧幕的入口和等待方式；不改变人物、事实、出口或 rubric。
4. E01 创建工作对象前读取 [artifact-adapters.md](references/artifact-adapters.md)；E02 创建看板前读取 [data-dashboard.md](references/data-dashboard.md)；E04 首次准备提交时读取 [prd-task.md](references/prd-task.md)，审阅时可再次读取 rubric。
5. E10 才读取并使用 [diary-template.html](assets/diary-template.html)。
6. 人设、幕出口、选择含义和 rubric 是硬约束；具体对白可以即兴，但不得改变事实或跳过必需工具动作。
7. 所有存档初始化、原子 patch、动作回执、日志追加、租约和校验统一调用 [state-tool.py](scripts/state-tool.py)；不要用临时 shell 拼接或非原子覆盖代替。

## 工具矩阵

在第一次调用某类飞书能力前，先完整读取对应已安装 Skill 的 `SKILL.md`，遵循其最新命令、身份和授权规则，不要猜测底层 CLI 参数或 payload。

| 时机 | 使用能力 | 目的 |
|---|---|---|
| 开局自检 | `lark-shared` | 检查 lark-cli、bot/user 身份和所需权限 |
| 识别玩家 | `lark-contact` | 获取玩家 open_id 与显示名 |
| E01 及全程 | `lark-im` | 创建 3 个固定 Chat、bot 发言、user 拉取各 Chat 消息 |
| 等待玩家时 | `lark-event` | 有界监听消息和任务变更事件，只用于唤醒回查 |
| E02、E07 | `lark-calendar` | 创建晨会和需求评审日程 |
| E02 | `lark-sheets` | 创建带 KPI、口径和原生图表的数据看板，并回读验证 |
| E01、提交与审阅 | `lark-task` | 创建一个终极任务、回查完成状态、重开一次、最终验收 |
| E01、提交与审阅 | `lark-doc` | 创建 PRD 模板，读取 revision、正文与 block ID |
| 首次审阅与终验 | `lark-drive` | 创建一条局部评论，终验后解决该评论 |
| 全程 | 本地文件工具 | 写 `runs/<run-id>/state.json`、`log.jsonl` 和 `diary.html` |

工作对象的关键事实动作固定为：`lark-cli docs +fetch --detail with-ids` 读取最新 docx revision，`lark-cli drive +add-comment` 写入唯一局部评论，首次不通过时对同一 GUID 执行一次 `task +reopen`；任务事件 `task.task.update_user_access_v2` 只负责唤醒，不能替代任务详情回查。

身份规则：

- NPC 发消息使用 bot 身份。
- 拉取玩家群消息使用 user 身份。
- 监听 `im.message.receive_v1` 必须使用 bot 身份；该事件不支持 user 身份。
- 其他操作服从对应 lark Skill 的要求。
- 不允许用 bot 身份拉取群消息；读取失败时先检查身份与权限，不要假装收到输入。

## 新游戏启动

按顺序执行：

1. **开局前必须阅读** [landing-orientation.md](references/landing-orientation.md) 中的只读飞书 Landing 对齐文档。使用 `lark-cli docs +fetch --as user` 获取最新正文；读取失败或玩家无权查看时保持 `initializing`，停止所有本局外部写入。
2. 再读取世界观、人设和时间线。
3. 查找 `status` 为 `initializing`、`running` 或 `finalizing` 的存档。若存在，禁止静默开始第二局；让玩家选择恢复该局，或明确中止旧局后再开新局。
4. 先按 `permission-setup.md` 在 Codex 对话提示用户本局需要的 user 授权与 bot 管理员配置；再按 CLI 契约执行自检。在外部写入前确认 user 登录、可枚举的 user scopes、bot 身份和消息事件能力。bot 写 scope 无法从本地状态完整枚举时，按 CLI 契约执行最小副作用能力探针并如实记录。
5. 使用 `lark-contact` 获取当前玩家的 open_id，供拉群和消息匹配使用。`player.name` 只保存玩家明确选用的实习昵称，未指定时为“实习生”；不把接口返回的姓名自动用于台词、文档、任务或日记。身份无法可靠解析时，只询问一次玩家的飞书姓名或邮箱再解析；若玩家指出当前授权账号不对，先核对登录身份，不通过改昵称掩盖账号错配。按 `permission-setup.md` 检查机器人对外名称后再创建群。
6. 创建唯一运行目录 `runs/pm-one-day-<YYYYMMDD-HHmmss>/`，用 `state-tool.py init` 初始化 `state.json` 和空的 `log.jsonl`；初始 `status=initializing`。
7. 为本次 Codex 执行生成唯一 `runner_id`，用 `state-tool.py lease-acquire` 获取 90 秒租约；只有租约持有者可写该存档，持续运行时在每次 heartbeat 开始续租。
8. 进入 E01 Landing 阶段。先创建三个固定 Chat，把 Landing 链接发给玩家，让 HR、导师、总监、后端和运营完成自我介绍，并讲清项目背景、协作流程和最终交付；此时不得创建 PRD 文档或终极任务。
9. 三个 Chat、Landing 链接、全员介绍和项目说明均有成功回执后，在 Codex Desktop 中为**当前 `run_id` 和当前 Codex 任务**创建或复用唯一 heartbeat；名称与 prompt 必须包含 `run_id`，不得只写“最近的 running 存档”。将自动化 ID 写入 `state.runtime.heartbeat_id`，用它持续等待 Landing 回复。
10. 玩家在公司群完成自我介绍或 Landing 确认后，E01 才创建唯一 PRD 模板和终极任务。三个 Chat、文档、终极任务和 heartbeat 都验证成功后写 `status=running`，进入 E02 与后续主循环。

如果可预检的认证或 user 权限缺失，停止在第一次外部写入之前，按 `permission-setup.md` 给出最短修复指引与授权链接。飞书不提供 bot 写 scope 的完整无副作用预检时，不得声称“零残留事务”：首次 company 建群与首条 bot 消息作为最小能力探针；失败后保持 `initializing` 和动作回执，提供错误返回的管理员配置入口并允许原地恢复，绝不重新建一套或自动删除。

### Codex Desktop 持续运行契约

- **正常剧情绝不以“继续实习”作为下一步按钮。** 发送完某幕开场、收到玩家群消息、或一次有界监听超时后，运行器必须继续当前主循环，而不是发送最终回复并结束当前任务回合。
- 每次 heartbeat 唤醒时，只读取 prompt 中固定的 `run_id`；先获取或续租，再按状态恢复。`paused=false` 时补做未完成动作、拉取三个 Chat、回查目标任务，再进行最多 10 秒的有界事件监听。消息列表、任务详情和文档 revision 才是事实来源。
- `paused=true` 时 heartbeat 仍须拉取三个 Chat，但只识别“继续”“继续上班”“结束实习”等控制指令；不得判定普通剧情输入、推进幕或触发超时。收到“继续”后清空并重新建立当前阶段的等待窗口，再恢复正常循环。
- 当前检查点的等待窗口必须使用持久化的 `wait_started_at` / `wait_deadline_at` 计算。连续玩家消息在首条到达后继续收集 15 秒并合并为同一轮；随后用 `checkpoint-consume` 把该检查点预算从 1 改为 0，不再追问第二轮。
- `runtime.story_deadline_at` 到达后禁止开启新剧情检查点，直接按已有产出进入最终判断；`runtime.session_deadline_at` 是硬截止，优先于所有幕截止时间并立即进入 E10。目标时长 22–25 分钟，27 分钟停止新剧情，30 分钟前完成收尾。
- 只有进入 E10 且最终化动作全部完成、玩家明确“暂停”、玩家明确提前结束、或认证/权限故障无法推进时，才可以结束当前 Codex 回合并向用户发送最终状态。暂停时保持 heartbeat，但它只读控制指令；完成或中止后停用 heartbeat。
- “继续实习”仅用于用户主动暂停、任务被用户关闭/中断后重开、或 heartbeat 发生故障后的人工恢复。它不应出现在普通开场、普通幕间提示或每幕的用户引导里。

## 运行状态

使用以下最小结构。可以增加工具返回的稳定 ID，但不要删除这些字段：

```json
{
  "schema_version": 4,
  "run_id": "pm-one-day-20260801-120000",
  "status": "initializing",
  "requested_final_status": null,
  "current_beat": "E01",
  "beat_phase": "opening",
  "entered_beat_at": "ISO-8601",
  "beat_actions_done": false,
  "room_layout": "company_with_role_rooms",
  "rooms": {"company": null, "mentor_dm": null, "boss_dm": null},
  "chat_ids": {},
  "active_room": "company",
  "actors": {
    "hr": {"room_key": "company", "memory": []},
    "mentor": {"room_key": "mentor_dm", "memory": []},
    "boss": {"room_key": "boss_dm", "memory": []},
    "backend": {"room_key": "company", "memory": []},
    "slacker": {"room_key": "company", "memory": []}
  },
  "player": { "open_id": "", "name": "" },
  "counters": {
    "boss_affinity": 0,
    "slack": 0,
    "fights": 0,
    "tasks_completed": 0
  },
  "flags": {},
  "artifacts": {
    "review_brief": "",
    "task_id": null,
    "task_progress": {},
    "work_item": {
      "task_guid": null,
      "task_url": null,
      "status": "unassigned",
      "document": {"type": "docx", "token": null, "url": null, "revision": null, "owner_identity": null},
      "review": {"round": 0, "state": "not_started", "comment_ids": [], "last_reviewed_revision": null, "feedback_block_id": null}
    },
    "calendar_event_ids": [],
    "data_dashboard": {"type": "sheet", "status": "not_created", "token": null, "url": null, "sheet_id": null, "chart_ids": [], "revision": null},
    "action_receipts": {},
    "finalization": {
      "diary_written": false,
      "hr_notified": false,
      "heartbeat_stopped": false
    }
  },
  "memory": [],
  "processed_message_ids": [],
  "processed_task_event_ids": [],
  "last_message_time_by_chat": {"company": null, "mentor_dm": null, "boss_dm": null},
  "checkpoint_budget": {"onboarding": 1, "problem_metric": 1, "evidence_scope": 1, "first_submit": 1, "micro_revision": 1, "final_decision": 1},
  "paused": false,
  "runtime": {
    "heartbeat_id": null,
    "wait_started_at": null,
    "wait_deadline_at": null,
    "last_runner_wakeup_at": null,
    "story_deadline_at": "ISO-8601，started_at + 27分钟",
    "session_deadline_at": "ISO-8601，started_at + 30分钟",
    "lease": {"owner_id": null, "expires_at": null}
  },
  "started_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

状态规则：

- `status` 只允许 `initializing`、`running`、`finalizing`、`completed`、`aborted`。初始化完成前保持 `initializing`；进入 E10 或提前结束时先写 `finalizing` 和 `requested_final_status`；全部收尾动作完成后才写最终状态。
- 每次外部工具成功、玩家输入、计数变化或幕转场后，立即用 `state-tool.py` 原子更新 `state.json`；禁止直接覆盖写文件。
- 每次进入等待输入时立即写入 `runtime.wait_started_at` 与 `runtime.wait_deadline_at`；恢复、heartbeat 或短时监听重试均复用该截止时间，收到有效输入或进入下一幕时清空这两个字段。
- 一幕存在“初稿 → 反馈 → 修订”时，用 `beat_phase` 区分阶段；每次进入新阶段都写新的等待窗口。heartbeat 只能恢复当前阶段，不能把初稿当作最终稿，也不能因反馈动作重放而重置截止时间。
- `rooms` 一旦三个入口都创建完成即不可变；用 `last_message_time_by_chat` 分别保存游标。schema v3 活跃局迁移为 `legacy_four_room`，只继续原四群局，不创建、删除或改名任何群。
- heartbeat 唤醒时先写入 `runtime.last_runner_wakeup_at`。若 `runtime.heartbeat_id` 缺失或失效，先创建/修复同一任务的 heartbeat，再继续；不得让用户承担“继续实习”的唤醒职责。
- 恢复 schema v1/v2/v3 存档时，先用 `state-tool.py migrate` 补齐 schema v4 字段并标记 `room_layout=legacy_four_room`；它可以兼容完成，但不得计入 v0.4 上线验收。
- `processed_message_ids` 只保留最近 100 个精确 ID；不要用消息 ID 的字符串大小判断新旧。
- `memory` 最多保留 12 条简短事实。
- `beat_actions_done=true` 表示本幕不可重复创建群、任务、日程或重复发送开场动作。E01 在 `beat_phase="landing"` 时保持 false，并依靠逐动作回执避免重复介绍；进入 `assignment` 后补建文档与任务，全部成功才改为 true。
- 每次外部写入前，先把稳定动作键、参数摘要和 `pending` 写入 `artifacts.action_receipts`；成功后再写 `done` 与返回 ID。重试必须复用同一幂等键。
- 每个执行者写状态前必须持有未过期租约；租约被其他 `runner_id` 持有时停止写入，等待下次 heartbeat，避免两个 Codex 回合同时推进。
- `state-tool.py validate` 失败时停止推进，先修复存档。

## 行为日志

向 `log.jsonl` 逐行追加 JSON；日记只能引用这里已有的事实：

```json
{"t":"ISO-8601","beat":"E03","kind":"message|scene|choice|task|review|control|system","who":"player|hr|mentor|boss|backend|slacker|engine","text":"原文或事实摘要","data":{}}
```

必须记录：

- 每条参与判定的玩家原文。
- 每个选择与分支出口。
- 任务和日程的创建结果及稳定 ID。
- rubric 分数、计数变化和原因。
- 暂停、继续、跳过、提前结束和故障。

不要把 token、secret、open_id 或其他凭证写入 `log.jsonl`。

## Chat 与任务事件循环

普通回复和控制指令由 `im.message.receive_v1` 唤醒；任务提交由 `task.task.update_user_access_v2` 唤醒。事件永远不是最终事实。

每轮按此顺序执行：

1. 按 CLI 契约以 user 身份拉取三个 `rooms`；只接收本局入口、当前玩家、`text` 类型且未处理的消息。
2. 根据 room 路由：`company` 可触发当前群体剧情，`mentor_dm` 只交给导师，`boss_dm` 只交给老板；不把一条消息复制到其他角色。
3. 先识别控制指令，再把其余消息交给当前幕判定。
4. 按 CLI 契约的入站事务顺序，去重记录原文，完成判定后一次性写入精确消息 ID、更新时间和判定结果。无论消息是否被剧情接受，都把对应群游标推进到本轮已扫描的最大 `create_time`；只有当前玩家的合法文本写入 `processed_message_ids`。
5. 若工作对象已经创建，每轮同时用 `task tasks get` 回查目标 GUID。任务为 `done` 且 review state 等待提交时，按 [artifact-adapters.md](references/artifact-adapters.md) 进入审阅事务。
6. 没有新事实时，分别有界监听消息或任务事件最多 10 秒；事件醒来后重新拉取 Chat、任务详情和文档 revision。事件不可用时每 10 秒轮询。
7. 重复直到收到有效输入或系统时间到达 `runtime.wait_deadline_at`。如果当前 Codex 回合将要结束，依靠 heartbeat 再次唤醒后从同一截止时间继续，而不是结束实习或要求用户发送恢复指令。
8. 只有到达持久化检查点截止时间才执行沉默兜底；到达全局截止时间立即收尾。

若事件未在飞书后台启用或监听能力不可用，记录一次故障后改为每 10 秒轮询消息列表；不得无界挂起。

### 控制指令

控制指令可来自飞书群或当前 Codex 对话：

- “暂停”“等一下” → `paused=true`，只处理消息，不触发幕超时。
- “继续”“继续上班” → `paused=false`，从当前幕恢复。暂停时记录 `flags.paused_at`；恢复时将实际暂停起止时间追加到 `runtime.pause_intervals`，并将两个全局截止时间顺延同等时长。30 分钟限制按有效运行时间计算，不能把暂停时间算作玩家沉默。
- “跳过”“下一幕”“快进” → 执行当前幕的沉默兜底，然后进入声明的默认出口。
- “结束实习”“不玩了”“提前下班” → 记录 `status=finalizing`、`requested_final_status=aborted`，直接进入 E10 生成半日记。

收到控制指令后，先由当前在场 NPC 用一句群消息确认，再执行；不要把引擎术语发到飞书。

## 幕执行协议

进入每一幕时：

1. 读取对应幕文件。
2. 把 `current_beat`、`entered_beat_at`、`beat_phase="opening"` 和 `beat_actions_done=false` 写盘。
3. 依次执行 `工具动作`；严格使用 CLI 契约的命令、身份、幂等键和返回字段。
4. 普通幕的所有一次性动作完成后写 `beat_actions_done=true`。E01 是唯一例外：Landing 消息发完后仍保持 false 并开启 `onboarding`；只有玩家确认或沉默兜底后进入 `assignment`，且文档、任务与通知均完成，才写 true。
5. 只有六个检查点开启输入窗口；每个检查点最多消费一轮。文档内容只在任务完成后读取，不把每次敲字当输入。
6. 按 `判定` 更新状态和日志。引用玩家原文，不得补写玩家没说过的内容。
7. 选择唯一 `下一幕`，先写盘再加载它。

恢复时若 `beat_actions_done=true`，不要重放当前幕开场动作；直接恢复消息循环。若为 false，按 `action_receipts` 和 CLI 契约的查重规则只补做未成功动作。恢复不是默认的常规流程：正常流程由 heartbeat 连续唤醒并推进。

## NPC 演技

- 严格服从人设卡。
- 每条 NPC 消息使用对应前缀，并发送为单行纯文本。正文不得出现真实换行、字面量 `\n`/`\r` 或双重转义的 `\\n`/`\\r`；需要分段时拆成多条独立消息。
- 不在飞书中出现“AI”“提示词”“引擎”“工具调用”“幕文件”等幕后词。
- 公司群多个 NPC 分开发消息；角色专属 Chat 绝不让其他 NPC 串台。
- NPC 消息间隔不超过 2 秒，不模拟长时间真人打字。
- 接住玩家的梗，但必须回到当前幕目标。
- 评审只能评论玩家真实提交的终审陈述原文。
- 怼工作，不攻击人格，不涉及真实公司或真人。
- 导师不是单纯提问器。每个关键环节都按“**先示范一个思考框架 → 看玩家产出 → 点出一处具体问题 → 要求玩家做一次更小、更明确的修订**”运行；除沉默兜底外，导师不得替玩家做最终决定。
- 自动剧情消息每个压缩段 1–4 条，必须服务当前任务；不得为凑热闹延长时长。

## E10 收尾

进入 E10 后：

1. 先写 `status=finalizing`；正常流程写 `requested_final_status=completed`，提前结束写 `requested_final_status=aborted`。恢复器必须继续选择 `finalizing` 存档。
2. 若 `artifacts.finalization.diary_written=false`，读取 `log.jsonl`，只从真实记录中提取 3–5 条名场面；把结构化日记数据交给 [render-diary.py](scripts/render-diary.py)，由脚本统一做 HTML 转义并原子生成 `runs/<run-id>/diary.html`。验证文件且不存在未替换占位符后，将该字段写为 true；禁止手工字符串替换玩家文本。
3. 若 `hr_notified=false`，用稳定消息幂等键发送结束通知；正常结业与提前结束使用不同文案。成功后写 true。
4. 若 `heartbeat_stopped=false`，停用绑定本 `run_id` 的 heartbeat，成功后写 true 并清空 `runtime.heartbeat_id`。
5. 三个 finalization 字段全部为 true 后，才把 `status` 写成 `requested_final_status` 并释放租约。
6. 不上传日记，不调用任何网站、直播或发布工具。

## 继续实习

用户说“继续实习”时：

1. 查找 `runs/pm-one-day-*/state.json`，选择 `status` 为 `initializing`、`running` 或 `finalizing` 的记录；只有一个时直接恢复，多个时列出 `run_id/current_beat/updated_at` 让玩家选择，不得猜最近一个。
2. 读取状态、世界观、人设、时间线和当前幕文件。
3. 确认已存档的工作群仍可读取；不可读取时说明具体原因并停止，不新建新群。
4. 获取租约后按 `status`、`beat_actions_done`、`beat_phase` 和 finalization 字段恢复，不重复已成功的外部动作。
5. 如果没有可恢复记录，简短说明并询问是否开始新游戏。

用户没有说“继续实习”但 heartbeat 唤醒时，执行相同的恢复检查，**但不向用户显示恢复提示，也不把它当作新一轮用户输入**。

## 完成标准

一局只有在以下条件全部满足时才算完成：

- 建立了公司群、导师 Chat 和老板 Chat，并完成 E01–E10 的一条闭合路径。
- 创建了一个终极任务、一份 PRD 文档、一张带原生图表且回读验证通过的数据看板和两个日历日程；若真实权限或日程冲突导致降级，必须如实记录。数据看板失败不得降级为聊天播报 KPI。
- 首次提交最多创建一条局部评论，最多重开一次任务；第二次有效提交后不得要求第三次返工。
- 所有检查点预算已消费或按超时兜底，且完成时间不晚于 `session_deadline_at`。
- 所有玩家判定都有日志依据。
- `state.json` 与 `log.jsonl` 可用于恢复和审计。
- 已生成本地 `diary.html`，且没有任何 Web 或直播依赖。
- `artifacts.finalization` 三项均为 true，heartbeat 已停用，没有其他 runner 持有未过期租约。

`room_layout=legacy_four_room` 的旧局只属于兼容恢复，不计入 v0.4 三入口版本的上线验收样本。
