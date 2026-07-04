# 一日实习生 · 技术路线

> 对应产品定义:[一日实习生.txt](../一日实习生.txt)。命令层细节见 [lark-cli-toolkit.md](lark-cli-toolkit.md)。

## 一句话架构

**实习包是数据,引擎是技能,飞书是舞台,网站是货架。**

```
┌──────────────────────┐        ┌───────────────────────────────────┐
│  在线平台 web/        │  下载   │  本地 Runner(玩家自己的电脑)      │
│  Next.js + Supabase  │ ─────→ │  Claude Code(或任意支持 skill 的   │
│  实习包画廊/详情       │  实习包 │  agent)                           │
│  上传/下载/计数        │  (zip) │   ├─ 引擎 skill: one-day-intern    │
│  部署 Vercel          │        │   ├─ 实习包: packs/pm-one-day      │
└──────────▲───────────┘        │   └─ lark-cli(26 官方 skills)      │
           │ 创作者上传           └──────────────┬────────────────────┘
           │                                    │ im / calendar / task
┌──────────┴───────────┐                        │ docs / event / cards
│  创作者(大厂打工人)    │                        ▼
│  用引擎的"创作模式"     │              玩家的真实飞书
│  把日常沉淀成实习包     │        (拉群、派活、开会、被怼、摸鱼)
└──────────────────────┘                        │ 下班
                                                ▼
                                    HTML 实习日记(可分享/可截图)
                                    可经 lark-cli apps +html-publish 发布成链接
```

## 三个组件与选型理由

### ① 实习包(Intern Pack)—— 纯数据,零代码

- **形态**:一个目录(分发时 zip),含 `pack.json` 元数据 + 人设卡 + 时间轴剧本 + 任务素材 + 日记模板。格式规范见 [pack-spec.md](pack-spec.md)。
- **为什么是纯数据而不是可执行代码**:
  - 安全——玩家下载陌生人的包,不该下载任意可执行逻辑;剧本是给 AI 读的自然语言,引擎负责解释执行
  - 创作门槛——创作者写 Markdown 就能出包,这正是产品定位("把创作变简单")
  - 跨包复用——人设/事件/任务是独立文件,可拆积木(产品文档中的"内容飞轮")

### ② 本地引擎(one-day-intern skill)—— AI 即是运行时

- **形态**:标准 Claude Code Skill(`SKILL.md` + references),读实习包 → 驱动 lark-cli → 监听事件 → 即兴演出 → 记日志 → 出日记。
- **为什么选"用户自己的 agent"而不是自研 runtime**:
  - 产品定义就是"接上自己本地的 AI Agent"——AI 调用成本归玩家,平台零推理成本
  - lark-cli 官方 skills 就是 Claude Code 格式(`npx skills add larksuite/cli`),生态天然对齐
  - NPC 的"即兴发挥"(吵架、怼人、接梗)本质是 LLM roleplay,剧本只给骨架,血肉靠模型——这恰好只有 agent 运行时能做
- **交互回路**:`event consume`(WebSocket→NDJSON,有界消费)收玩家消息/按钮点击 → 引擎按人设卡生成回应 → `im +messages-send` 发回。交互卡片(`card.action.trigger`)承载分支选择。
- **多角色问题**:一个自建应用只有一个 bot。NPC 用消息前缀「【角色名】」+ 卡片署名区分。未来可选:企业版多应用、或接入消息卡片的 avatar 定制。

### ③ 在线平台(web/)—— 内容货架

- **形态**:Next.js(App Router)+ Supabase(Postgres 存包元数据 + Storage 存 zip),部署 Vercel。像素风蓝白视觉延续现有海报(index.html / posters)。
- **为什么不做桌面端**:原文档担心"本地 AI 调用"需要桌面端——但本地 AI 由玩家的 agent 承担后,网站只剩内容平台职责(浏览/上传/下载/评分),标准 Web 即可,省一个技术栈。
- **为什么 Supabase**:元数据(结构化查询、排序、计数)+ 大文件(zip)+ 后续可加的账号体系(创作者身份),一个后端全覆盖;本机已接入 Supabase MCP,开发链路最短。
- 备选:飞书妙搭(`lark-cli apps`)也能托管全栈应用(aiforce.cloud 域名),适合做"纯飞书生态版";demo 阶段选 Vercel 因为面向站外传播。

## 认证与安全模型

| 身份 | 扮演 | 授权方式 | 现状 |
|---|---|---|---|
| bot(应用机器人) | 全体 NPC | 后台开 scope 即可,无需扫码 | ✅ 就绪 |
| user(玩家本人) | 玩家 | OAuth 扫码,scope 可增量 | 需玩家扫码 |

- 玩家的 app_id/secret 只存在本机(`lark-cli config`),平台不经手任何凭证
- 实习包不含凭证、不含可执行代码;引擎遵守 lark-cli 安全规则(high-risk-write 需确认、禁输出 token、幂等键防复读)

## 一天的生命周期(运行时序)

```
开局  im +chat-create(建群拉玩家)→ +messages-send(HR 欢迎)
      calendar +create(站会/评审/一对一 全天日程)→ task +create(第一个活)
        ↓
推进  loop: 按 timeline 触发下一事件(NPC 发言/卡片选择/派活/开会)
            event consume 有界等待玩家回应(消息 / 按钮 / 交任务)
            LLM 按人设卡即兴回应,分支走向写入行为日志(JSONL)
        ↓
收尾  统计日志(完成度/吵架次数/摸鱼指数)→ 渲染像素风 HTML 日记
      → 群里发日记 + 可选 apps +html-publish 出分享链接
```

**时间压缩**:`pack.json` 里 `time_scale` 字段。demo 模式一天 ≈ 15 分钟(事件间隔按倍率缩放);沉浸模式跟随真实时钟。

## 风险与对策

| 风险 | 对策 |
|---|---|
| 玩家飞书 scope 开不全(个人版租户) | 每个剧情动作在 toolkit 里标了降级路径(如 vc 不可用→群聊模拟开会) |
| `card.action.trigger` 收不到 | 开发者后台"事件与回调→回调配置"需手动开启,onboarding 文档强提示 |
| event consume 挂死 | 引擎契约:一律 `--timeout`/`--max-events` 有界消费,循环调度 |
| NPC 复读(重试副作用) | 剧情消息统一 `--idempotency-key <pack-event-id>` |
| 陌生实习包安全性 | 包为纯数据;引擎白名单化可执行动作,写操作遵守确认规则 |
