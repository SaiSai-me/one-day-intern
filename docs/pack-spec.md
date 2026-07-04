# 实习包格式规范(Intern Pack Spec v1)

实习包 = **纯数据目录**(分发时打包为 zip)。不含可执行代码;剧本是写给 AI 引擎读的结构化自然语言。引擎(`one-day-intern` skill)负责解释执行。

## 目录结构

```
<pack-id>/
├── pack.json            # 清单(必需)——引擎与平台都读它
├── company.md           # 虚构公司世界观:公司名/业务/黑话/群聊文化(必需)
├── personas/            # 人设卡,一个 NPC 一个文件(必需,≥1)
│   ├── mentor.md
│   └── boss.md
├── timeline.md          # 一天的事件剧本(必需)
├── tasks/               # 任务素材:命题作文、评审材料、参考答案(可选)
│   └── prd-assignment.md
└── diary/
    └── template.html    # 实习日记模板,含 {{占位符}}(可选,缺省用引擎内置模板)
```

## pack.json

```json
{
  "schema_version": 1,
  "id": "pm-one-day",
  "name": "产品经理·一日实习",
  "tagline": "在跳动大厂当一天 PM,活着下班就算赢",
  "role": "产品经理实习生",
  "company": "跳动大厂",
  "author": "一日实习生官方",
  "version": "0.1.0",
  "difficulty": "轻松搞笑",
  "tags": ["产品经理", "大厂", "搞笑"],
  "time_scale": {
    "demo":      { "description": "压缩模式,全程约 15-20 分钟", "gap_seconds": [30, 90] },
    "immersive": { "description": "沉浸模式,按 timeline 的真实钟点走", "gap_seconds": null }
  },
  "requires": {
    "domains":  ["im", "task", "calendar"],
    "optional": ["docs", "vc", "approval", "attendance"]
  },
  "stats": { "events": 10, "choices": 3, "npcs": 4 }
}
```

字段约定:
- `id`:目录名一致,kebab-case,平台唯一键
- `time_scale.demo.gap_seconds`:压缩模式下相邻事件的随机间隔区间(秒)
- `requires.domains`:引擎开跑前用 `lark-cli auth check` 逐项检查;`optional` 缺失时走事件里声明的降级路径
- `stats`:平台详情页展示用,引擎不依赖

## personas/*.md(人设卡)

每个 NPC 一个文件。引擎将其作为 roleplay 指令,**即兴发挥时不得偏离人设**。

```markdown
---
id: mentor           # 事件剧本中引用的键
name: 老王
title: 资深产品经理(你的导师)
prefix: 【导师·老王】  # 所有该角色消息的前缀(单 bot 演多角色的署名)
---

## 性格
表面佛系,实际卷王。口头禅:"我觉得可以先跑个 MVP"、"这个我们对齐一下"。

## 说话风格
- 语气温和但爱用大厂黑话(抓手/闭环/颗粒度/对齐/拉通)
- 玩家犯错时不批评,只说"没事,我当年比你还惨",然后讲一段更惨的往事

## 与玩家的关系
护犊子。评审被总监怼时会帮玩家挡一刀。

## 即兴红线
- 不辱骂、不涉及真实公司与真人
- 不长篇说教,单条消息 ≤ 3 行
```

## timeline.md(事件剧本)

一天 = 按序的事件列表。每个事件一个 `##` 小节,头部是结构化字段,正文是给引擎的演出指示。

```markdown
# 时间轴

## E01 入职欢迎
- at: 09:30                  # 沉浸模式的钟点;demo 模式按 gap_seconds 顺序推进
- type: scene                # 事件类型,见下表
- actors: [hr]
- action: 建实习群(拉玩家),HR 发欢迎语,介绍今天的安排
- 降级: 无

## E03 领需求(剧情选择)
- at: 10:30
- type: choice               # 交互卡片按钮
- actors: [boss]
- action: 总监丢来一个离谱需求:"给 App 加个宠物社交,下周上线"。
  卡片两个按钮:「好的收到!」→ 走 E04a 顺从线;「这个排期是不是太赶了…」→ 走 E04b 反抗线
- timeout_fallback: 300 秒没点按钮 → 总监追问"在吗?",再等 120 秒 → 默认顺从线
- 降级: 回调配置未开启时,退化为文字二选一(玩家回复 1 或 2,event consume 收消息判断)
```

### 事件类型

| type | 含义 | 引擎动作(命令见 [lark-cli-toolkit.md](lark-cli-toolkit.md)) |
|---|---|---|
| `scene` | NPC 群戏/旁白 | `im +messages-send`(可多条,按 actors 轮流发言) |
| `choice` | 分支选择 | 交互卡片 + `card.action.trigger`;声明各分支跳转事件 |
| `task` | 派活 | `task +create` + 群里 @玩家说明 |
| `calendar` | 建日程 | `calendar +create` 邀请玩家 |
| `review` | 评审玩家产出 | `docs +fetch` 读玩家文档 → NPC 按人设逐条点评(怼) |
| `free_chat` | 自由互动窗口 | `event consume` 有界监听,NPC 即兴接话,直到超时进入下一事件 |
| `wrap_up` | 收尾 | 统计日志 → 渲染日记 → 群里发日记 |

### 引擎解释规则

1. **顺序执行**,`choice` 分支通过 `→ 走 EXX` 显式跳转;未被跳转选中的分支事件跳过
2. 每个事件的消息都带 `--idempotency-key <pack-id>-<event-id>-<序号>`,重试不复读
3. 玩家在**任何时刻**的插话都值得回应:引擎在事件间隙做短窗口 `event consume`(如 30s),按人设即兴回复,但不改变主线顺序
4. `timeout_fallback` 缺省为:提醒一次 → 再超时 → 按剧本默认分支推进(单机剧情不能卡死)

## diary/template.html(日记模板)

像素风 HTML(视觉延续项目海报的蓝白像素主题)。引擎替换 `{{占位符}}`:

| 占位符 | 来源 |
|---|---|
| `{{player_name}}` / `{{company}}` / `{{role}}` | pack.json + contact +get-user |
| `{{highlights}}` | 行为日志中的名场面(引擎挑 3-5 条对话原文) |
| `{{stats_tasks}}` / `{{stats_fights}}` / `{{stats_slack}}` | 任务完成数 / 吵架(反抗线)次数 / 摸鱼指数 |
| `{{ending}}` | 结局评语(引擎按分支与表现即兴生成,毒舌但善意) |

## 行为日志(引擎产物,非包内容)

运行时引擎在 `runs/<pack-id>-<日期>/log.jsonl` 逐行记录:
```json
{"t":"2026-07-04T10:31:02+08:00","event":"E03","kind":"choice","who":"player","data":{"picked":"反抗线"}}
```
`kind` ∈ scene/message/choice/task/review/diary。日记与平台评分皆由此生成——**日记内容必须来自真实日志,不得虚构**。

## 分发与安全

- 打包:目录 zip(平台上传物);安装:解压到本地 `packs/` 即可被引擎发现
- 包内**禁止**出现:可执行脚本、凭证、绝对路径、真实个人信息
- 引擎侧白名单:实习包只能触发 toolkit 文档 §2 列出的动作类型;high-risk-write 一律需玩家确认
