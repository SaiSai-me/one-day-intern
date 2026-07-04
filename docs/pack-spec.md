# 实习包格式规范(Intern Pack Spec v2)

实习包 = **纯数据目录**(分发时打包为 zip)。不含可执行代码;剧本是写给 AI 引擎读的、**按幕拆分的提示词包**。引擎规范见 [engine/ENGINE.md](../engine/ENGINE.md)。

> v2 相对 v1 的变化:幕(beat)拆成独立文件按需加载;新增判定 rubric 与量表规则;人设卡增加关系记忆种子;压缩模式为默认。

## 目录结构

```
<pack-id>/
├── pack.json            # 清单(必需)
├── company.md           # 虚构公司世界观(必需)
├── personas/            # 人设卡,一个 NPC 一个文件(必需,≥1)
├── timeline.md          # 幕索引:一天的骨架总表(必需)
├── beats/               # 每幕一个提示词文件,引擎到幕才读(必需)
│   ├── E01.md
│   └── ...
├── tasks/               # 任务素材:命题、评审弹药、隐藏情报(可选)
└── diary/template.html  # 日记模板(可选,缺省用引擎内置)
```

**设计原理(渐进披露)**:引擎开局只读 pack.json + timeline.md + 人设卡;`beats/EXX.md` 是分段装填的提示词弹药,到幕才进上下文——既省 token,也避免 AI 提前"知道结局"演砸。

## pack.json

```json
{
  "schema_version": 2,
  "id": "pm-one-day",
  "name": "产品经理·一日实习",
  "tagline": "在跳动大厂当一天 PM,活着下班就算赢",
  "role": "产品经理实习生",
  "company": "跳动大厂",
  "author": "一日实习生官方",
  "version": "0.2.0",
  "difficulty": "轻松搞笑",
  "tags": ["产品经理", "大厂", "搞笑"],
  "default_mode": "demo",
  "time_scale": {
    "demo":      { "description": "压缩模式(默认),全程约 15-20 分钟", "gap_seconds": [30, 90] },
    "immersive": { "description": "沉浸模式,按幕表真实钟点走", "gap_seconds": null }
  },
  "gauges": ["好感度_boss", "摸鱼指数", "吵架次数", "任务完成"],
  "requires": { "domains": ["im", "task", "calendar"], "optional": ["docs", "attendance"] },
  "stats": { "events": 10, "choices": 3, "npcs": 5 }
}
```

- `gauges`:本包用到的量表,引擎在 state.json 里初始化为 0;增减规则写在各幕的 `判定:` 区块里
- `default_mode`:demo(压缩)是产品默认——引擎必须全程在线,压缩模式对玩家和算力都友好

## timeline.md(幕索引)

只放骨架总表,供引擎开局一次读入。一行一幕:

```markdown
| 幕 | at | type | actors | 出口 | 摘要 |
|---|---|---|---|---|---|
| E01 | 09:30 | scene | hr,mentor | E02 | 入职欢迎,建群拉人 |
| E03 | 10:30 | choice | boss | E04a / E04b | 领需求:顺从或反抗 |
| ... |
```

- `出口`:默认下一幕;choice 幕列出全部分支目标(与幕文件内的按钮定义一致)
- 幕的详细演出指示**一律**放 `beats/EXX.md`,索引里不展开

## beats/EXX.md(幕文件 = 一段提示词弹药)

```markdown
# E07 需求评审(BOSS 战)
- type: review
- actors: [boss, backend, mentor]
- 监听: im.message.receive_v1(玩家有 3 轮回应机会,每轮 180s)
- timeout_fallback: 玩家整幕沉默 → 老王代答,摸鱼指数+2,进 E08

## 演出
建日程「⚔️ 宠物社交需求评审」。docs +fetch 真读玩家的 PRD(什么都没交→现场口头汇报)。
点评必须引用玩家原文逐条怼;弹药库见 tasks/prd-assignment.md。
老王在玩家被怼到第 2 轮时挡刀。

## 判定
- 玩家用了隐藏情报(夸杠子技术强)→ 杠子秒软,评审通过,好感度_boss +1,记名场面
- 玩家有理有据反驳 ≥1 轮 → 吵架次数+1,大锤说"有点意思",好感度_boss +1
- rubric(PRD 质量,0-3 分):用户是谁 / 核心场景 / MVP 范围各 1 分;≥2 分评审通过
- 全程沉默 → 摸鱼指数+2
```

### 幕类型(type)

| type | 含义 | 引擎动作(命令见 [lark-cli-toolkit.md](lark-cli-toolkit.md)) |
|---|---|---|
| `scene` | NPC 群戏/旁白 | `im +messages-send`,actors 轮流发言 |
| `choice` | 分支选择 | 交互卡片 + `card.action.trigger`;幕文件声明按钮与跳转 |
| `task` | 派活 | `task +create` + 群里说明 |
| `calendar` | 建日程 | `calendar +create` 邀玩家 |
| `review` | 评审玩家产出 | `docs +fetch` 真读 + rubric 判定 |
| `free_chat` | 自由互动窗口 | 常听模式自然覆盖;本类型只用于"整幕就是闲聊"的场景 |
| `wrap_up` | 收尾 | 结算 log → 日记 → 谢幕 |

### 幕文件通用字段

- `监听:` 本幕主要听什么事件(默认 im 消息;choice 幕听卡片回调)
- `timeout_fallback:` 玩家沉默时的推进方式(**必填**——单机剧情不能卡死;沉默也是输入,通常伴随摸鱼指数变化)
- `判定:` 量表增减规则与 rubric,导演逐条执行,禁止凭感觉打分
- `降级:` 所需 optional 域缺失时的替代演法

## personas/*.md(人设卡)

```markdown
---
id: boss
name: 大锤
title: 产品总监
prefix: 【总监·大锤】
initial_memory: "对新实习生零期待,但暗中观察"   # 可选:写入 state.memory 的关系种子
---
## 性格 / 说话风格 / 与玩家的关系 / 即兴红线
(同 v1;红线必填:不辱骂、不涉真实公司真人、单条消息行数上限)
```

**关系是活的**:引擎把每幕的关键互动摘要滚动写入 `state.json.memory`(上午吵的架,下午评审会被记仇)。人设卡只提供初始种子,后续演变由运行时记忆驱动。

## 三栏契约(创作者必读)

| 你写死的 | AI 即兴的 | 玩家输入面 |
|---|---|---|
| 幕的时间点/顺序/类型、人物人设、任务命题、choice 选项与跳转、判定 rubric、公司风格 | 对白措辞、接玩家插话、评审点评内容(引用真实产出)、日记文案(来自日志) | 群聊/私聊、按钮、交任务、写文档、表情、沉默 |

创作时的心法:**你是在写剧本杀的主持人手册,不是在写台词本**。给约束和弹药,别给逐字稿。

## 行为日志与判定(引擎产物)

运行时文件与格式见 [engine/ENGINE.md](../engine/ENGINE.md) 的 `runs/` 一节。规范层面的两条铁律:
1. 日记与评分**只能**来自 log.jsonl,不得虚构
2. 判定按幕文件 `判定:` 区块执行,量表全程可追溯

## 分发与安全

- 打包:目录 zip;安装:解压到本地 `packs/` 即可被引擎发现
- 包内**禁止**:可执行脚本、凭证、绝对路径、真实个人信息
- 引擎白名单:包只能触发本规范列出的幕类型;high-risk-write 一律需玩家确认
