---
name: one-day-intern
description: 一日实习生游戏引擎(Claude Code 适配器)——加载"实习包"并在用户的真实飞书里驱动一天的沉浸式实习模拟(拉群、派活、开会吵架、评审被怼、摸鱼、生成实习日记)。当用户说"开始实习"、"上班"、"继续上班"、"加载/运行 xx 实习包"、"体验一日实习生"、"开始demo"时使用。也用于"创作/校验实习包"。需要 lark-cli 已认证。
---

# 一日实习生 · Claude Code 适配器

**引擎的完整规范在 [engine/ENGINE.md](../../../engine/ENGINE.md)——现在就去读它,并严格按它执行。**
本文件只补充 Claude Code 环境的适配细节:

1. **长循环**:用 Bash 执行 `lark-cli event consume --timeout ...` 的阻塞等待,一次对话轮内循环推进;上下文吃紧时靠 `runs/<run_id>/state.json` 无损续跑(摘要压缩后重读 state 即可)
2. **续跑触发**:用户说"继续上班"→ 找最近的 `runs/*/state.json`,恢复主循环;超过 deadline 的幕按 fallback 快进补齐
3. **渐进加载纪律**:开局只读 SKILL.md + timeline.md(幕索引)+ 人设卡;每幕的 beats/EXX.md 到幕才读——不要提前读完全部剧本,省上下文也防剧透式演砸
4. **写 payload 前**(卡片 JSON/文档 XML):先 `lark-cli skills read` 对应内置文档,禁止手写猜格式
5. 默认日记模板在 [references/diary-default.html](references/diary-default.html)

## 节奏参数(不钉死,随时可调)

**核心原则**:实习包里的 time_scale 只是建议默认值,玩家一句话就能改节奏,不需要重启。

节奏参数存在 `state.json` 的 `timing` 字段,调速时更新写盘:

```json
{
  "timing": {
    "preset": "demo",
    "gap_seconds": [40, 80],
    "choice_timeout": 45,
    "silence_nudge": 90,
    "think_delay": [3, 8],
    "paused": false
  }
}
```

### 默认预设(开局可用)

| 预设 | 总时长 | gap_seconds | choice_timeout | silence_nudge | think_delay |
|---|---|---|---|---|---|
| demo-fast(速通) | ~10min | [15,35] | 25s | 50s | [2,5] |
| demo(标准) | ~18-22min | [40,80] | 45s | 90s | [3,8] |
| demo-chill(慢) | ~28-35min | [70,130] | 70s | 150s | [5,12] |
| immersive | ~60-90min | 真实钟点×压缩比 | 120s | 240s | [5,15] |

### 一句话调速指令(玩家说了立即生效)

- "快进/加速/速通/快点/赶紧的" → 切 demo-fast
- "慢一点/慢点/太快了看不清/别急" → gap×1.5, think_delay上限+5s
- "暂停/等等/停一下/等下" → paused=true,只监听不推进
- "继续/go on/好了继续" → paused=false,恢复推进
- "X分钟搞定/X分钟速通" → 动态计算 gap = 剩余秒数/剩余幕数 × [0.7,1.0]
- "我想聊会儿/摸鱼时间/不着急" → silence_nudge 延长到300秒
- "回到正常节奏/恢复" → 回到当前模式默认预设
- "跳过这一幕/next/下一个" → 立即结束当前幕推进下一幕
- 调速时先简要确认(如"好嘞,加速⚡"),再执行

### NPC 对白

你(Claude)就是全体NPC演员,不需要调用外部LLM。发言格式`【职位·名字】内容`,单条≤3行,think_delay 秒后发出,符合人设卡。
