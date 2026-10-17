# 直播短版：同事在场，导演喊停

新短版默认 `demo.pacing="cue"`。主讲稿目标仍为 5:40，但运行器不以墙钟时间判失败或自动结业。先布置真实飞书对象和开场，停在冲突发生的一刻；演示者在 Codex 说「继续」才接演。用 [操作稿](live-demo-presenter.md) 和 [预写输入](../assets/live-demo-materials.md) 带演示者走，不让他临场猜入口或编答案。

旧存档没有 pacing 时仍为 timed，遵循 [旧计时协议](live-demo-timed.md)，不改写其已完成或超时的历史。完整版入口仍运行 E01–E10，不能混用这份协议。

## 舞台与场外

飞书是角色工作的地方：群名、NPC 消息、任务描述和评论只能说工作内容。不出现「彩排」「直播」「演示者」「现场窗口」「倒计时」「输入 A/B」「预跑」「5/5 能力评分」「AI 引擎」「提前准备的台词」。产品功能里的 AI 自动成片、五天 demo 是业务语言，可以出现。

Codex、讲稿、本地日志负责说明这是模拟、素材来源和真实处理结果。使用预写输入时记录 `source=presenter_script`，不算候选人独立能力；不在飞书角色对话里解释这件事。机器人原生身份标识不做伪装，主持人 How 环节说明同一 bot 扮演多位角色。虚构数据说明留在主持稿或原文档已有来源说明，不拿虚构数据讲招聘成效。

前缀统一：`【人事 Chloe】`、`【Mentor kris姐】`、`【产品总监 Vincent】`、`【技术负责人 Ethan】`、`【运营 Aria】`。姓名都在括号内，后面空一格接台词，单行纯文本。此规范覆盖短版引用的旧人设前缀。

三个入口：公司群「🏢 青橙视频·创作发布产品组」、导师「🧭 【Mentor kris姐】」、老板「⚔️ 【产品总监 Vincent】」。公司群允许 Vincent、Ethan、Aria、Chloe 公开讨论和争论；导师 Chat 只有 kris姐，老板 Chat 只有 Vincent。老板公开发言是独立群消息，不转发私聊。玩家发言只在原 Chat 被接住，不跨群重复回答。

## 准备并停住

先按 lark-shared 和各业务 Skill 检查原身份与能力，读 [人设](world-and-personas.md)、[适配器](artifact-adapters.md)、[rubric](prd-task.md)。NPC bot 发言、用户身份读群和操作任务、文档与评论沿用已有 owner identity。

1. 在 `runs/pm-one-day-*/state.json` 找到唯一活动 cue 局就复用；多个才需指定。用户要求在已结束体验上重新布置时，新建本地运行记录，显式关联旧 run_id 和同一套对象；不篡改旧计时结果，不重复建三个群、文档、任务。`init --mode live_demo --pacing cue --purpose live`。
2. 用户指定正式文档时必须复用原文档，先读最新 XML 正文与 revision，保存基线，保留既有修改。不要再塞入故意写坏的首稿，不要求凑 2/5。不知道是哪份时先查已有状态和标题再确认。新用户才创建一份岗位模板。
3. 唯一任务的标题和描述用工作语言，包含真实文档链接和「标题前圆圈勾上即提交」。已完成任务用于下一轮范围确认时，更新同一 GUID 的交付要求并重开，保留之前的评审证据在本地。针对实际缺口留一条局部评论；已完善文档可以只补「验收约定」，不能虚构退回史。保存评论真实 ID。
4. 发送 [材料](../assets/live-demo-materials.md) 中的准备台词：HR 给任务入口，运营与研发亮出立场，导师给沟通框架，老板提出新增需求。**最后停在公司群 Vincent 要求实习生牵头定范围**，还不发送 Ethan 的反驳，不消费用户输入。
5. 所有写动作先 pending 后 done，沿用 state-tool 的租约和回执。登记 `demo.chat.<room>(chat_id)`、`demo.prepared.document(document_token,revision)`、`demo.prepared.task(task_guid,task_status="todo")`、`demo.prepared.scene(message_id)`；基线 review.last_reviewed_revision 必须来自评论创建后的真实读取，避免评论自己的 revision 被算成玩家修改。
6. `demo ready` 原子设 prepared、paused=true。不给两个全局 deadline，不创建 heartbeat。交付本局带真实链接的「直播操作卡」，写清断点和第一条复制输入，释放租约后结束当前 Codex 回合。准备完不会自动演完。

## 继续、暂停与三次沟通

命令统一 `python3 scripts/state-tool.py demo <action> --state <path> --owner-id <runner> --at <ISO>`，先取得 90 秒租约。

- 在 Codex 发「继续」「继续直播演示」「开始直播演示」：prepared 用 `demo resume` 进入 alignment；已暂停用 resume 回原阶段，阶段、已发消息、已消费输入不清零。单独「继续」只路由唯一活动 cue 局，不复活 finished 局。
- 在 Codex 或本局群发「暂停」「等一下」：`demo pause`，停止 NPC 队列、输入消费、评审、评论和任务写入，停止/暂停本局 heartbeat，清空 heartbeat_id 并释放租约。暂停后不靠 heartbeat 自动恢复，也不因隔了几天而结业。飞书内不发场外暂停说明。
- 暂停前已经消费的沟通保留；暂停期间的新消息和提交不当作下一段输入，resume 记录 resumed_at。需要提交时让演示者在继续后再点完成，不代发输入。
- 「结束」「停止直播演示」才 demo stop，按实际产出收尾；cue 模式禁止 demo timeout。

| 阶段 | 玩家实际沟通 | 对应响应与后果 |
|---|---|---|
| alignment | 在公司群让研发确认最小范围、成本与风险 | Ethan 按真实技术约束答成本，Aria 补用户风险；记录 alignment 后进入 decision |
| decision | 在老板 Chat 提出带理由的分期 | Vincent 接住理由：合理分期才认可；全接则指出排期冲突。记录 decision 后进入 handoff |
| handoff | 在公司群同步范围、验收口径与分工 | Ethan、Aria 分别确认自己收到的工作；缺失则明确标为待补，不虚构同意。记录 handoff 后进入 revision |
| revision | 在原文档补充验收约定，勾选唯一任务 | 回查任务 done、最新 revision 和正文，真实评审，反馈收尾 |

每条用户输入都先以 user 回查确切 Chat、sender、message_id、原文和毫秒时间；列表的分钟级展示时间不够判断边界时用原生消息详情取 create_time，不能自行补秒。只接收 resumed_at 之后的消息，系统/app 消息不当作玩家输入。准备前、暂停中和旧局发言不提前消费。解释来源放本地。用户问怎么操作时，在 Codex 给本阶段现成输入，不启动新的倒计时。

`alignment/handoff/decision --evidence-file` 共同字段：message_id、chat_id、sender_id、created_at、observed_at、text、reason；decision 还需 judgment=`protect|evidence|accept_all|reject_only|unclear`。语义由 Agent 判断，脚本只验证身份、时间、阶段与去重。不要用答案关键词控制通过。

## 同事不能沉默：有节奏地接戏

恢复后先处理用户控制，再拉取三个群与唯一任务。每轮把新发言交给在场角色，**先接住用户刚说的话，再考虑下一条预设对白**。允许质疑与争论，攻击方案不攻击人。

用 `scripts/demo-cues.py --state <path> --at <ISO>` 读取当前到期的一条 NPC 台词，素材来自 `assets/live-demo-cues.json`。每条发前复查 paused 和阶段；使用返回 key 的稳定回执发送、回查、记 done，然后继续循环。pending 提示先查重恢复，不盲目重发。已发台词不会因继续或恢复重播；阶段改变后不补发上阶段积压台词。

- 进场 0–2 秒有两位同事接话，随后约 8–12 秒出现一次新讨论；每阶段最多 3–5 条主动消息，消息短、彼此有因果。API 延迟据实记录，不把计划间隔当实测。
- 等待时只用最多 3 秒的事件监听/轮询间隔，使 NPC 到期发送和玩家回复及时被处理；不再固定等 15 秒合并。每轮优先检查用户输入，不能为了发完队列让玩家等。
- 队列是背景冲突，不提前宣布老板同意、任务通过、开发完成。每次关键回复另用 `demo.reply.<stage>` 回执，根据真实内容生成。Ethan 会从抵触转为愿意排期；Aria 会把话题拉回用户后果；Vincent 会追问为什么，而不是只发固定鼓励。
- 队列耗尽且 60 秒没有新输入时自动 `demo pause`，只在 Codex 说停在哪，保留进度；没有回应不等于决策，不自动演到结束。等待不是无限刷屏。
- cue 的 heartbeat 只负责意外中断恢复。创建时绑定确切 run_id 和当前任务；paused/prepared 时停用并且不推进。活跃时主回合持续处理，不能发送一句开场就结束，把后续全扔给分钟级 heartbeat。

## 文档验收与收尾

任务确认为同一 GUID done 后再读取 Docx：`docs +fetch --as <owner> --doc <url> --detail with-ids --doc-format xml`。XML 取得 IDs；语义比较用规范化正文，不能把 XML 属性/评论导致的 revision 变化当作内容修改。

提交 evidence 沿用旧协议 task_guid、task_status、completed_at、observed_at、document_token、revision、text、五项 rubric，并增加 `baseline_text`（同样规范化）。新正文需与 baseline_text 不同、revision 高于基线、任务完成时间在本次 resumed_at 之后。rubric source 支持 existing_document、presenter_script、live_revision、seed。总分只评价文档；台词来源与独立行为分开记录。

无正文改动：提示具体需要补哪一句，重开同一任务让用户再提交，不消费有效修订。有效提交后只评一次；原评论缺口没有解决就不解决该评论，不伪称通过。解决评论前必须核对相应新段落，而不只看总分。

通过时：同一任务写完整评审快照（业务结论和原文依据），解决实际评论并回查，老板与团队分别给短回应。「范围守门员」只作这次行为的角色调侃。飞书里不出现来源归因、主持人说明或招聘能力评分，完整 rubric 和来源保存在本地。

沿用 `demo.final.snapshot/task/review-message/comment` 回执和 `demo finish` 收尾守卫；有评论才要求解决评论回执。本地日记根据日志记录真实事件，HR 群里只说「范围和验收口径都定了，按这份方案推进」。停止 heartbeat、清空 heartbeat_id、写 finalization 后才 finish；不会因为点圆圈就自动通过。

## 本次准备对象的说明

真实群名可改、bot 自己的旧场外消息可按用户要求改成对应工作语言，先保存原文与编辑回执；绝不修改用户自己的历史回复。不能编辑的历史明确记录限制，不通过改用户名伪造多人账号。用户原文档保持原地址与正文，必要新反馈用评论，现场新增内容由演示者亲自粘贴。
