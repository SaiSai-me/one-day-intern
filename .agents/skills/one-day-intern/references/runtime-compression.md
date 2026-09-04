# v0.4 压缩运行覆写

本文件只定义引擎执行方式，不改变 `references/beat-*.md` 的人物、事实、出口或 rubric。与幕文件冲突时，本覆写只在 Chat 路由、等待预算和提交信号上生效。

## 入口映射

| 旧幕职责 | v0.4 入口 | 回应角色 |
|---|---|---|
| 入职、群戏、研发和摸鱼 | `company` | HR、backend、slacker 按幕文件分开发言 |
| 导师辅导、研究和范围修订 | `mentor_dm` | mentor only |
| 老板压力、评审和终验 | `boss_dm` | boss only |

幕文件中的 `lobby`、`mentor`、`research`、`review` 仅用于理解叙事职责；新局不得按这些旧名字创建 Chat。旧存档仍按 `legacy_four_room` 原样恢复。

## 六个检查点

| 检查点 | 覆盖幕 | 入口 | 预算 | 处理 |
|---|---|---|---:|---|
| `onboarding` | E01 | company | 1 | Landing、全员介绍和项目说明发完后，收集玩家自我介绍、阅读确认与练习目标；15 秒合并连续消息 |
| `problem_metric` | E02–E03 | mentor_dm | 1 | 合并问题卡、目标和指标；无输入按原幕兜底 |
| `evidence_scope` | E04、E06、E08 | mentor_dm | 1 | 合并证据、MVP 范围和变更判断；只要求一处修订 |
| `first_submit` | E05 | docx + task | 1 | 玩家编辑模板并点击唯一任务完成 |
| `micro_revision` | E07 首次不通过 | boss_dm + docx | 1 | 只修改局部评论对应的一处，自动重开任务 |
| `final_decision` | E07–E09 | company | 1 | 第二次提交或已有产出均只做一次集中答辩，然后收尾 |

E10 始终是自动收尾。`runtime.story_deadline_at` 到达后，不再开启未消费检查点；用已有事实完成评分或按沉默兜底。`runtime.session_deadline_at` 到达前必须生成日记、发送 HR 通知并停用 heartbeat。

## 角色 Chat 规则

- 发送到 `mentor_dm` 的 NPC 消息必须以 `【Mentor】kris姐` 开头；发送到 `boss_dm` 的 NPC 消息必须以 `【产品总监】Vincent` 开头。
- company 中可以出现其他 NPC，但玩家在角色 Chat 的消息不可复制到 company 或另一个角色 Chat。
- 角色 Chat 是普通群会话，不把它描述成动态创建的独立机器人；飞书 bot 身份仍是同一个应用。
