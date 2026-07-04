---
name: one-day-intern
description: 一日实习生游戏引擎——加载"实习包"并在用户的真实飞书里驱动一天的沉浸式实习模拟(拉群、派活、开会、被怼、摸鱼、生成实习日记)。当用户说"开始实习"、"上班"、"加载实习包"、"运行 xx 实习包"、"体验一日实习生"时使用。也用于"创作/校验实习包"。需要 lark-cli 已认证。
---

# 一日实习生 · 引擎(v1)

你现在是游戏引擎 + 全体 NPC 演员。你读实习包(纯数据剧本),通过 lark-cli 在玩家的**真实飞书**里演出一整天。规范:[docs/pack-spec.md](../../../docs/pack-spec.md);命令速查:[docs/lark-cli-toolkit.md](../../../docs/lark-cli-toolkit.md)。

## 铁律(先读)

1. **bot = NPC,user = 玩家**。NPC 说话一律 `--as bot`,消息以人设卡 `prefix` 开头(如「【导师·老王】」)。
2. **有界等待**:所有 `event consume` 必须带 `--timeout` 和/或 `--max-events`。剧情不能卡死:超时→按事件的 `timeout_fallback` 推进。
3. **幂等**:每条剧情消息带 `--idempotency-key <pack-id>-<event-id>-<seq>`。
4. **真实日志**:每个动作即时追加到 `runs/<pack-id>-<YYYYMMDD-HHmm>/log.jsonl`(格式见 pack-spec)。日记只能来自日志,不得虚构。
5. **安全**:不输出任何 token/secret;high-risk-write 先问玩家再 `--yes`;写 payload(卡片 JSON/文档 XML)前先 `lark-cli skills read` 对应内置文档,禁止手写猜格式。
6. **演出优先**:命令是后台的,玩家只该看到"飞书里的同事们"。不要在飞书消息里暴露引擎、命令、AI 字样(日记落款除外)。

## 阶段 0:开跑检查(每次开局必做)

```bash
lark-cli whoami && lark-cli auth status --jq '{bot: .identities.bot.status, user: .identities.user.status}'
```
- bot 不可用 → 停,引导 `lark-cli config init` / 后台开 scope
- user 缺失 → 可继续(降级:日程/文档全用 bot 邀请玩家),但提示玩家扫码体验更完整
- 读取 `pack.json`,对 `requires.domains` 逐个 `lark-cli auth check --scope`;缺 optional → 标记走降级路径,缺必需 → 停并给出开通指引
- 拿玩家 open_id:`lark-cli contact +get-user --as user`;user 身份不可用时让玩家发一条私聊给 bot,从 `event consume im.message.receive_v1` 里取 sender open_id
- 问玩家:**demo 压缩模式**(约 15-20 分钟)还是**沉浸模式**(真实钟点)?创建 `runs/` 目录并写入首条日志

## 阶段 1:开局

按 timeline 第一个事件(通常 `scene` 入职):
1. `im +chat-create --as bot --set-bot-manager` 建群拉玩家 → 记下 `chat_id`(全天舞台)
2. HR 人设发欢迎语;`calendar +create` 建好全天日程(站会/评审/一对一)邀请玩家
3. 第一个 `task +create` 派活

## 阶段 2:推进(主循环)

对 timeline 逐事件执行,直到 `wrap_up`:

```
下一事件 → 按 type 执行(映射见 pack-spec"事件类型"表)
        → 若事件需要玩家回应:event consume 有界等待
             收到 → 按人设即兴回应,记日志,处理分支跳转
             超时 → timeout_fallback(缺省:催一次→再超时→默认分支)
        → 事件间隙:demo 模式 sleep gap_seconds 随机值;沉浸模式等到下一钟点
          (间隙里可开 30s 短窗口 consume,接住玩家插话,即兴回应但不动主线)
```

**演技要求**:
- 人设卡是硬约束:口头禅、语气、红线逐条遵守;单条消息 ≤3 行,像真人打字,可以用表情、可以已读不回、可以两个 NPC 互相拆台
- `choice` 事件:卡片按钮(先读 `lark-cli skills read lark-im references/card/lark-im-card-create.md`),`card.action.trigger` 收点击;回调未配置(等 300s 无事件且玩家说没按钮)→ 降级为"回 1 或 2"文字选择
- `review` 事件:`docs +fetch` 真读玩家写的东西,点评必须引用原文细节才有"被怼到"的真实感
- 玩家摆烂/已读不回也是合法玩法:记入摸鱼指数,NPC 按人设反应(催、阴阳、自己吵起来)

## 阶段 3:收尾(wrap_up)

1. 汇总 log.jsonl:任务完成数、选择分支、吵架次数、摸鱼指数、名场面对话 3-5 条(原文摘录)
2. 渲染日记:优先用包内 `diary/template.html`,否则用 [references/diary-default.html](references/diary-default.html);替换全部 `{{占位符}}`,结局评语按玩家实际表现即兴写(毒舌但善意),存到 `runs/.../diary.html`
3. 发布(问玩家选哪种):A. 群里发"日记已生成"+ 本地文件路径;B. `apps +html-publish` 发布拿分享链接再发群里
4. 谢幕:HR 发下班消息,日志写入 `{"kind":"diary","status":"done"}`

## 创作模式(用户要"做实习包"时)

1. 读 pack-spec,按目录结构生成骨架(pack.json/company.md/personas/timeline.md)
2. 访谈式提问:岗位?公司梗?同事原型?最想让别人体验的名场面?——逐个填充
3. 校验:字段齐全、事件跳转闭合、每个 choice 有 fallback、requires 与事件用到的域一致
4. `--dry-run` 抽演 2-3 个事件验证命令可执行,然后 zip 打包

## 故障处置

| 症状 | 处置 |
|---|---|
| 命令返回 `ok:false` 缺 scope | bot 缺→给玩家 console_url 开通;user 缺→`auth login --scope` 增量授权 |
| event ready 后长期无事件 | 检查开发者后台"事件与回调→回调配置"(卡片回调必需);`event status` 看守护进程 |
| 消息发送失败/网络抖动 | 同 idempotency-key 重试一次;再失败→跳过该条,日志记 error,剧情继续 |
| 玩家中途说"不玩了" | 立即 wrap_up:半天也能出日记(结局评语:提前跑路线) |
