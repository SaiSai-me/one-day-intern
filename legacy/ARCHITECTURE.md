# 一日实习生 · 架构文档

> 本文档面向技术人员，解释系统整体设计、组件边界和数据流。
> 产品创意见 [一日实习生.txt](一日实习生.txt)，快速开始见 [README.md](README.md)。

---

## 一、设计哲学

**引擎是说明书，剧本是分幕的提示词弹药，Agent 是玩家自带的主机，飞书是画面，平台是发行方+直播间。**

核心洞察：与其写一个传统的游戏引擎代码去调用 LLM API，不如让能执行shell、能读写文件、本身就是 LLM 的 AI Agent **直接充当引擎**。Agent 读了 [engine/ENGINE.md](engine/ENGINE.md) 这本"操作手册"，就能当导演（控流程）+ 全体演员（即兴生成NPC对白）。

这带来几个关键优势：
- **零后端推理成本**：运行时LLM算力用玩家本地的Agent
- **零部署门槛**：不需要服务器跑游戏，不需要API key配置
- **天然即兴**：NPC对白就是Agent的自然语言输出，不需要额外调用
- **Agent中立**：任何能跑shell+读写文件+遵循自然语言指令的Agent都能当引擎（Trae / Claude Code / Codex CLI / Gemini CLI 等）

---

## 二、系统分层

```
┌─────────────────────────────────────────────────────────────┐
│                    平台层（Platform）                        │
│         Next.js + Supabase：市场 + 直播观战                  │
│  实习包上传/下载/浏览 | opt-in状态上报 | /runs/<id>直播页    │
└──────────────────────────┬──────────────────────────────────┘
                           │ zip下载 / opt-in RPC上报
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               本地Agent层（Runner = 玩家自带AI）             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Skill适配器（.trae/ 或 .claude/）                    │  │
│  │  - 启动/续跑流程                                      │  │
│  │  - 一句话调速指令识别                                  │  │
│  │  - 上下文管理                                         │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │ 读取                               │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │  ENGINE.md（引擎规范 = 操作手册）                     │  │
│  │  导演职责 + 演员职责 + 主循环 + 判定规则 + 故障处置    │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │ 调用                               │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │  lark-cli（飞书命令行工具）                           │  │
│  │  发消息/卡片/任务/日程/监听事件/读写文档              │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │ 读写                               │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │  runs/（运行存档）                                    │  │
│  │  state.json（世界状态）+ log.jsonl（行为日志）        │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ 操作飞书
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  飞书层（Stage = 舞台）                      │
│     群聊 | 私聊 | 卡片按钮 | 任务 | 日程 | 文档 | 会议      │
│                    （玩家唯一交互面）                        │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ 加载
┌──────────────────────────┴──────────────────────────────────┐
│               实习包层（Pack = 剧本弹药）                    │
│  packs/<id>/：纯Markdown+JSON，分幕提示词，无代码            │
│  pack.json | company.md | timeline.md | personas/ | beats/  │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、五大组件详解

### 1. 实习包（Pack）——纯数据剧本

| 位置 | [packs/](packs/) |
|---|---|
| 格式 | Markdown + JSON（zip打包分发） |
| 是否含可执行代码 | ❌ 禁止 |
| 创作者工具 | [lark-workflow-editor.html](lark-workflow-editor.html) 可视化编排器 |
| 格式规范 | [docs/pack-spec.md](docs/pack-spec.md) |

目录结构：
```
<pack-id>/
├── pack.json         # 元信息、默认时间参数、所需权限
├── company.md        # 虚构公司世界观
├── timeline.md       # 幕索引（一天骨架）
├── personas/*.md     # NPC人设卡（职位、性格、口头禅、红线）
├── beats/EXX.md      # 各幕详细演出指令（到幕才加载）
├── tasks/*.md        # 任务素材/评审弹药（可选）
└── diary/            # 自定义日记模板（可选）
```

**设计原则**：渐进披露——开局只读pack.json+timeline+personas，幕文件按需加载，省上下文也防AI提前知道结局演砸。

### 2. 引擎规范（ENGINE.md）——Agent的操作手册

| 位置 | [engine/ENGINE.md](engine/ENGINE.md) |
|---|---|
| 性质 | 自然语言规范文档（Agent中立） |
| 作用 | 告诉Agent"怎么当导演和演员" |

核心内容：
- 三栏契约（写死/即兴/输入的边界）
- 主循环（常听模式）
- state.json和log.jsonl格式
- 演技规范（对白格式、延迟、人设遵守）
- 判定规则（rubric）
- 开局/收尾/故障处置流程
- 平台上报接口（opt-in）

### 3. Skill适配器——Agent环境适配层

不同Agent有不同的工具调用方式，Skill是引擎规范在特定Agent上的适配。

| Agent | 位置 |
|---|---|
| Trae | [.trae/skills/one-day-intern/](.trae/skills/one-day-intern/SKILL.md) |
| Claude Code | [.claude/skills/one-day-intern/](.claude/skills/one-day-intern/SKILL.md) |

适配器补充：
- 启动触发词（"开始实习"/"上班"等）
- 调速指令识别（快进/慢一点/暂停/X分钟速通）
- 该Agent环境下的工具调用方式
- 默认节奏预设表（demo-fast/demo/demo-chill/immersive）
- 日记模板位置

### 4. lark-cli——操作飞书的手

| 文档 | [docs/lark-cli-toolkit.md](docs/lark-cli-toolkit.md) |
|---|---|
| 版本 | v1.0.65+ |
| 身份 | bot身份（NPC操作）+ user身份（玩家操作） |

关键命令模式：
- 消息：`lark-cli im +messages-send`（NPC说话）
- 监听：`lark-cli event consume <event_key> --timeout <秒>`（听玩家说话/点按钮）
- 任务：`lark-cli task +create`（派活）
- 日程：`lark-cli calendar +create`（建会议）
- 文档：`lark-cli docs +create/+fetch`（写PRD/评审）

### 5. 平台（web/）——发行方+直播间

| 位置 | [web/](web/) |
|---|---|
| 技术栈 | Next.js 15 + Supabase |
| 功能 | 实习包市场（上传/下载/浏览）、观战直播面板 |

直播机制：玩家开局时opt-in开启，引擎每30秒批量上报幕转场/量表/名场面到Supabase RPC，生成 `/runs/<id>` 实时观战页。局终凝固为日记回放页，作为社交分发物。

---

## 四、核心运行机制

### 4.1 主循环（常听模式）

这是引擎的心脏，在 [engine/ENGINE.md](engine/ENGINE.md#主循环常听模式引擎的心脏) 有详细描述：

```
开局（自检→拿open_id→问模式→初始化state→执行E01）
  ↓
┌───────────────────────────────────────────────┐
│  deadline = 当前幕的截止时间（从timing计算）   │
│  lark-cli event consume im.message.receive_v1 │
│      --timeout <deadline - now> --max-events 1│
│  ├─ 收到事件 → 补漏读消息 → NPC即兴回应       │
│  │           → 更新state/log → 继续loop       │
│  └─ 超时 → 触发下一幕：                        │
│           读beats/下一幕.md → 执行幕动作      │
│           → 更新current_beat/deadline         │
│                                               │
│  choice幕改听card.action.trigger              │
│  wrap_up幕 → 退出循环 → 收尾出日记            │
└───────────────────────────────────────────────┘
```

**关键设计**：幕是背景里自动到来的钟声，不是轮流说话的闸门。玩家随时可以插话，引擎默认竖着耳朵听。

### 4.2 节奏系统（Timing）

所有时间参数存在 `state.json.timing`，运行时可随时修改，无需重启。

预设档位：

| 预设 | 总时长 | gap_seconds | choice_timeout | silence_nudge | think_delay |
|---|---|---|---|---|---|
| demo-fast（速通） | ~10min | [15,35] | 25s | 50s | [2,5] |
| demo（标准） | ~18-22min | [40,80] | 45s | 90s | [3,8] |
| demo-chill（慢） | ~28-35min | [70,130] | 70s | 150s | [5,12] |
| immersive | ~60-90min | 真实钟点×0.12~0.25 | 120s | 240s | [5,15] |

一句话调速指令（玩家在飞书或终端说即可）：
- 快进/加速/速通 → demo-fast
- 慢一点/慢点 → gap×1.5
- 暂停/停一下 → paused=true
- 继续/go on → 恢复
- X分钟速通 → 动态重算gap
- 跳过/next → 立即进下一幕

### 4.3 双通道感知（防漏消息）

WebSocket事件流是**门铃**（1-2秒到达），但Agent思考期间可能漏消息。因此：
1. 门铃响（收到event）后
2. 先调用 `lark-cli im +chat-messages-list` 从cursor游标**补读全部新消息**
3. 再统一回应，更新cursor
4. 写盘

### 4.4 世界状态（state.json）

```json
{
  "run_id": "pm-one-day-20260715-1400",
  "pack_id": "pm-one-day",
  "mode": "demo",
  "chat_id": "oc_xxx",
  "player_open_id": "ou_xxx",
  "current_beat": "E05",
  "beat_deadline": "2026-07-15T14:25:00+08:00",
  "cursor": { "last_message_id": "om_xxx", "last_message_time": "..." },
  "gauges": { "好感度_boss": 1, "摸鱼指数": 2, "吵架次数": 1, "任务完成": 0 },
  "memory": ["E03玩家选了反抗线", "玩家叫杠子'杠哥'"],
  "branch_flags": { "E03": "rebel" },
  "timing": { "preset": "demo", "gap_seconds": [40,80], "paused": false },
  "report": { "enabled": false }
}
```

每次状态变化立即原子写盘，终端崩了说「继续上班」就能无损续跑。

### 4.5 行为日志（log.jsonl）

逐行JSON追加，是判定和日记的**唯一事实来源**，禁止虚构：

```json
{"t":"2026-07-15T14:05:00+08:00","beat":"E01","kind":"message","who":"hr","text":"欢迎新同学！"}
{"t":"2026-07-15T14:06:30+08:00","beat":"E01","kind":"message","who":"player","text":"谢谢大家！"}
{"t":"2026-07-15T14:20:00+08:00","beat":"E03","kind":"choice","who":"player","text":"rebel","data":{"option":"当场反驳"}}
```

### 4.6 NPC对白生成

**不需要调用外部LLM API——Agent本身就是LLM**。Agent读了personas人设卡后，自然地以该角色的口吻生成回复，格式为`【职位·名字】对白内容`，单条≤3行，think_delay秒后发出。

这是整个架构最优雅的地方：
- 不需要配置OpenAI/DeepSeek API key
- 不需要额外网络请求
- 不同Agent用各自的模型，天然适配
- Agent本身能理解上下文和人设，不需要特殊prompt工程

---

## 五、认证与安全模型

| 身份 | 扮演 | 授权方式 |
|---|---|---|
| bot | 全体NPC | 飞书开发者后台配置scope，无需扫码 |
| user | 玩家本人 | OAuth扫码授权，增量scope |

- bot感知范围仅限它创建/在场的会话
- 所有剧情容器（群/文档/任务）由bot创建
- 玩家凭证只存本机，平台不经手
- high-risk-write操作需玩家确认
- 日记生成只基于log.jsonl，不读取其他数据
- 平台上报opt-in，默认关闭，绝不上传open_id/凭证/私聊内容

---

## 六、当前进度与技术债务

| 模块 | 状态 |
|---|---|
| lark-cli 认证/基础命令 | ✅ 已验证可用 |
| event consume 事件流 | ✅ NDJSON流、有界消费契约已验证 |
| bot发消息/建群/派任务/建日程 | ✅ dry-run+真发已验证 |
| 编排器（lark-workflow-editor.html） | ✅ 可用，已支持文件管理、导出zip |
| engine/ENGINE.md v2 | ✅ 主循环/三栏契约/判定/续跑已定义 |
| Trae Skill适配器 | ✅ 已创建，含调速机制 |
| Claude Code Skill适配器 | ✅ 已更新 |
| 示例包 pm-one-day | ⚠️ pack.json格式需更新到time_scale v2 |
| 卡片回调（card.action.trigger） | ⚠️ 需后台手动开回调配置 |
| 平台（web/ Next.js） | 🚧 基础框架有，市场/直播未完工 |
| 日记HTML妙搭发布 | 🚧 待联调 |
| 沉浸式续跑（8小时模式） | 🚧 state.json已支持，长上下文管理待验证 |

---

## 七、文档地图

```
README.md                 ← 所有人从这里开始
ARCHITECTURE.md           ← 你在这里（技术总览）
一日实习生.txt             ← 产品原始创意
engine/ENGINE.md          ← 引擎规范（Agent运行时必读）
docs/
  pack-spec.md            ← 实习包格式规范
  lark-cli-toolkit.md     ← 飞书CLI游戏动作速查
  tech-route.md           ← 早期技术路线思考（历史参考）
.trae/skills/one-day-intern/  ← Trae适配器
.claude/skills/one-day-intern/ ← Claude Code适配器
packs/pm-one-day/         ← 官方示例包
lark-workflow-editor.html ← 可视化编排器
web/                      ← 平台网站代码
```
