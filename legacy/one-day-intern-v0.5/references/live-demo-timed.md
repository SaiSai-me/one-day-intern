# v0.5 直播演示运行协议

目标：让候选人在加入前体验岗位。固定产品经理样例，主讲 5:40，20 秒机动；现场运行窗口最多四分钟。预跑对话和首稿退回，现场仅回复老板、修订 PRD、点击唯一任务完成。所有界面与回执来自真实飞书，不生成假聊天或固定成功结果。

## 模式与事实来源

读取 [人物与业务事实](world-and-personas.md)、[CLI 契约](lark-cli-contract.md)、[工作对象适配器](artifact-adapters.md)、[原版五项 rubric](prd-task.md) 和 [演示材料](../assets/live-demo-materials.md)。不执行这些参考中的 E01–E10 时序；本文件覆盖资源数量以外的准备/等待/结业规则，单局仍只创建三个 Chat、一份 Docx、一个任务。

权限只检查 contact（身份）、im（玩家消息读取、bot 发言）、task、docs、drive（局部评论）；不要求 calendar/sheets，不创建日程、数据看板。本地演示材料作为岗位说明，无需依赖完整版远程 Landing。先按 [权限准备](permission-setup.md) 检查 user 登录和 bot 权限；缺失时停止外部写入并按 lark-shared 修复。调用任何飞书业务能力前仍须读对应 lark-* Skill，使用当前 CLI help/schema 核对；复用原版身份，不能换身份绕过错误。

“准备直播演示”授权本局三群、Docx、任务及 NPC 消息，也授权把明确标注的演示首稿作为预跑样例完成一次任务提交、真实评审和退回。它不授权代演示者发送现场输入 A/B。素材中的标准答案只给演示者，不写进候选人的未完成 PRD，也不在其未提交时用来评分。

## 状态和入口

使用 `scripts/state-tool.py init --mode live_demo --purpose live`，其余参数与原版一致；`--session-deadline-at` 不需要，准备态两个 deadline 为 null。彩排局用 `--purpose rehearsal`，run_id 均沿用 `pm-one-day-<时间>` 前缀。

schema_version 保持 4，新字段仅短版出现：

```json
{"mode":"live_demo","current_beat":"DEMO","demo":{"stage":"preparing","purpose":"live","live_started_at":null,"decision":null,"submission":null}}
```

阶段：`preparing → prepared → decision → revision → finalizing → finished`。前两阶段 status=initializing，现场为 running；正常交付 completed，主动结束或无有效交付超时为 aborted。`current_beat` 始终为 DEMO，不声称完成 E01–E10；完整版六个 checkpoint 固定为 0（不适用）。

所有转换用 `state-tool.py demo <action> --state <path> --owner-id <runner> --at <ISO时间>`；先获取或续租 90 秒租约。普通 `patch` 仅补充工具返回的工作对象、回执、游标和收尾标志，不修改 mode、demo、status 或 deadline。`decision/submit` 再加 `--evidence-file <本地JSON路径>`。脚本不调用飞书、不替 AI 做语义评价；运行器必须从真实回查归一化 evidence，禁止从预期答案合成成功证据。

新准备请求发现同一用途的活跃演示局时复用；多个候选局列出 run_id/purpose/stage 供选择。不自动转换完整版存档，不因准备彩排而停止其他体验。只有用户明确要求另一局或彩排局时才新建。准备一个可展示的完整彩排成品后，再准备现场局，避免串局。

## 准备：真实评审一次，再停止待命

1. 自检并识别玩家，创建本地准备态，获取租约。bot 创建 company 并发首条 HR 消息验证能力，再创建 mentor_dm、boss_dm。群名含“直播演示”或“彩排”和 run_id 后缀。老板/导师严格各在自己的 Chat；公司群由 HR、Ethan 发言，不复制老板私聊到公司群。
2. bot 创建唯一文档，内容为演示材料中的岗位背景及标注“演示者预跑样例”的首稿。保留每段 block ID；用户获得编辑权限、bot 可以读取和局部评论。user 创建唯一任务，描述包括文档链接、五项交付要求和“点击完成即提交，验收结果以评审结论为准”。
3. 将预跑首稿原文写日志，`who=engine, data.source=presenter_seed`；不是候选人的现场判断。对同一 GUID 完成任务，再回查 done；读取真实 Docx 正文与 revision 按 rubric 评分。样例预期 2/5；若实际内容不同，按事实记录，不能强制改分凑戏剧。
4. 对“看播放量是否上涨”所在 block 留唯一局部评论，使用素材里的可操作反馈；回查评论关联，再重开同一 GUID 并回查 open。写 round=1、state/status=changes_requested、last_reviewed_revision、feedback_block_id、comment_ids。若定位失败、评论权限不足或实际分数不是 2，保留 preparing 并说明准备未完成；短版核心展示不降级为聊天点评。
5. 按素材发送老板、研发、导师各一条冲突消息。发言共用一个 bot，消息前缀代表角色，不宣称多个独立机器人。剧情提及“AI 自动成片”是业务功能名称，允许出现；不在 NPC 消息中讲幕后技术。
6. 登记以下回执后执行 `demo ready`。记录本局实际三群、任务、PRD 链接到 `runs/<run_id>/presentation-links.md`，不存在的链接标“未取得”，不拼造群链接。链接记录留在被 Git 忽略的 runs 中，不进入发布包。
7. **prepared 不创建 heartbeat、不轮询、不消费任何输入、没有倒计时**。释放租约，结束 Codex 回合，告诉演示者已准备且需要“开始直播演示”激活；这里允许结束，不套用完整版持续运行要求。

每个写动作都先 receipt-begin、成功回查后 receipt-done，稳定 key 包含 run_id。`demo ready` 检查的 action key 与 receipt-done 归一化字段如下（另存原始安全回执供回查，不包含凭证）：

| key | 必需结果字段 |
|---|---|
| `demo.chat.company / mentor_dm / boss_dm` | 各自 `chat_id` |
| `demo.document / demo.task` | 各自 `document_token` / `task_guid` |
| `demo.seed.submit` | `task_guid`, `task_status="done"` |
| `demo.seed.review` | `score=2`, `revision`, `document_token` |
| `demo.seed.comment` | `comment_id`, `block_id` |
| `demo.seed.reopen` | `task_guid`, `task_status="open"` |
| `demo.drama.boss / backend / mentor` | 发送成功的 `message_id` |

准备完成时 review 与所有回执必须指向同一文档、同一 GUID 和同一条未解决局部评论。若开播前文档被改，任务已完成或评论被解决，不能盲目开始；回查并修复这同一套准备对象，再准备好。

## 现场：边讲边操作

收到“开始直播演示”先核对指定局的对象仍符合准备态，获取租约后 `demo start`。该命令原子记录 live_started_at、story_deadline_at=开始+210秒、session_deadline_at=开始+240秒。准备发生在昨天也不影响此计时。重复 start、恢复和暂停不重置或顺延四分钟预算；需要重新完整演示时另建彩排局，不清零旧局。

start 后创建/复用绑定本任务和确切 run_id 的唯一 heartbeat，prompt 明确 mode=live_demo、按本协议恢复、prepared 不推进、finalizing 优先清理、仅在有意义变化/失败/需用户动作时通知。写入 heartbeat_id；本回合持续处理，不能把 heartbeat 当现场低延迟触发器。若 Codex 自动化不可用，保持本回合有界轮询并如实记录，不能声称已配置恢复唤醒。

每轮先检查控制指令与 deadline，再分别用 user 拉取三个 Chat、回查唯一任务；事件只唤醒。决策仅接受开始时间之后、目标玩家在 boss_dm 的完整文字消息；准备期间或其他 Chat 的普通消息只推进游标，不算现场决策。取消 15 秒合并等待，一条完整消息立即语义判定，允许 protect/evidence/accept_all/reject_only/unclear，必须记录理由，不用关键词脚本评分。

`demo decision` 的 JSON：

```json
{"message_id":"om_真实ID","chat_id":"oc_老板Chat","sender_id":"ou_玩家","created_at":"带时区ISO时间","observed_at":"回查时间","text":"玩家原文","judgment":"protect","reason":"根据实际目标、成本与分期说明给出的判断"}
```

命令保存原文、精确 ID、来源和判断后进入 revision。老板再针对实际理由回应；合理分期可说“先验证，再加。可以。”，全部接下则指出三周/两周约束，裸拒绝则指出缺理由。已消费消息不会重复加分；不等额外对话才让演示者改文档。需要补写已判定的老板回复时复用 `demo.decision.reply` 回执，不重复判定。

任务完成与修改可以先于老板回复送达，但只有处理完合法决策后才评审，回查当前任务 done 和文档最新版，不丢失提前到达的任务信号。读失败保持阶段，不凭聊天里“改好了”确认提交。

## 修订与验收

同一 GUID 确认为 done 后，读取最新 PRD revision 和正文。`revision <= last_reviewed_revision` 时只提示“尚未检测到修改，请修改后重新提交”；重开同一任务作为无效提交复位，使用包含当前完成时间的幂等 key，不算新一轮评审，不消耗唯一有效微修订。有效二次提交之后永不再次重开。读取或评论故障保持事实状态，不能预写 accepted 或解决评论。

`demo submit` 的 JSON 来自本次 task get、docs fetch 与 AI 语义评审：

```json
{"observed_at":"回查完成时间","task_guid":"真实GUID","task_status":"done","completed_at":"任务详情完成时间转换为ISO","document_token":"真实文档ID","revision":8,"text":"完整最新正文","rubric":[{"score":1,"quote":"正文中的原句","reason":"评分理由","source":"seed"},{"score":1,"quote":"正文中的原句","reason":"评分理由","source":"seed"},{"score":1,"quote":"现场改动中的原句","reason":"评分理由","source":"live_revision"},{"score":1,"quote":"现场改动中的原句","reason":"评分理由","source":"live_revision"},{"score":1,"quote":"现场改动中的原句","reason":"评分理由","source":"live_revision"}]}
```

rubric 顺序固定为问题、用户场景、指标、MVP、非目标/风险。0 分项 quote 可空，reason 必填。source 通过与首稿快照比对确定，不能将模板归为现场表现。document_token 是资源标识，不是认证 access token。任一关键字段不能从事实取得时停止提交评审，不用当前时间冒充任务完成时间。输入 A/B 的预期是 5/5，但脚本不检查答案关键词或强制通过。

脚本校验身份、时间、版本、引用、阶段和重复消费，原子进入 finalizing，review.state 保持 reviewing；评分 ≥3 表示文档满足标准。docx 的总分含原始模板覆盖的项，不作为个人招聘能力分。任务完成计数仍为 0，只有收尾外部写入验证完成后才写 accepted/closed。

## 收尾、超时与恢复

- 开始后 210 秒停止接收新剧情输入，无有效提交执行 `demo timeout`，记录 aborted；不代写答案。240 秒是停止现场工作/等待的硬界限，外部 API 卡住或清理失败不能保证所有远程动作在界限内完成：到点停止新请求与监听、保存 finalizing 并报告清理未完成；恢复只补清理。临近截止的单次调用必须使用剩余预算作进程 timeout，不无界等网络。
- “暂停/等一下”只暂停剧情消费，四分钟仍继续计时；“继续”清除 paused 并沿用 deadline；“结束实习/提前下班/停止直播演示”执行 `demo stop`。prepared 不会因时间经过触发 timeout。
- 有二次有效提交时更新同一任务的完整描述快照：演示试岗结果、实际分数、首稿与现场来源、三条有原文依据的反馈（范围、指标、风险；缺失则写缺失）。任务 done 仅代表已提交；评分不足明确“已提交，未验收”，不以任务勾选伪装通过。
- 通过时解决原有评论，回查评论已解决和任务 done。记录 `demo.final.snapshot(task_guid)`、`demo.final.task(task_guid,task_status="done")`、通过时的 `demo.final.comment(comment_id,resolved=true)`，不通过不解决未修复评论。处理失败保持 finalizing，恢复只补缺失回执。
- 在 boss_dm 发一条真实验收结果，引用一处现场修改，如“本次文档已验收；你补上了发布完成率，也保留了可见范围确认。反馈见原任务。”；未通过则明确“已提交，未验收”及缺口。使用 `demo.final.review-message` 回执记录 message_id，不能拿范围判断回复当文档验收消息。
- 用已有 render-diary.py 保存本地日记（不作为概念网页展示）。正文写“演示试岗回顾”，不声称完整实习结业或实际上线；日记读 log.jsonl 按 event_id 去重，与最终 state 核对，范围/指标/风险缺失时如实写“未观察到”，凑不齐三个原句时可列三个已记录的状态事实，不虚构玩家话语。引用来源包括 presenter_seed、mentor_hint、presenter_live；导师提示不计个人表现。
- HR 在 company 发“本次试岗演示已结束，具体交付与反馈见原任务。”；无交付则明确未验收。若准备在建群前就失败并被主动结束，HR 通知记为“不适用：未建群”，不伪造发送回执。完成日记、HR 通知和停止本局 heartbeat（若从未创建则记录不适用）后，写三项 finalization 标志并清空 heartbeat_id；执行 `demo finish`，它在真实验收回执齐全后才把 tasks_completed 改为 1，并释放租约。未交付 timeout/stop 不能变成 completed。
- 恢复 `preparing` 补缺失准备动作；`prepared` 回报待命并释放租约，绝不自动 start；decision/revision 沿用原时钟、ID 和最新游标；finalizing 只补日记/通知/评论/快照/停止自动化，不读取新答案。所有 action key 与对象复用，不新建群、文档或任务。

## 演示成功标准

有真实准备、首稿退回、现场决策、revision 变化与二次验收，所有完成回执可回查；完整版测试不受影响。两次逐字旁白与真实切屏彩排均 ≤5:40 才能标记“直播时长已验证”。本地状态测试不等于飞书实测，也不等于人工讲解计时，按 [彩排清单](live-demo-rehearsal.md) 分别记录。
