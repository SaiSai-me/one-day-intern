---
name: one-day-intern
description: 一日实习生游戏引擎(Claude Code 适配器)——加载"实习包"并在用户的真实飞书里驱动一天的沉浸式实习模拟(拉群、派活、开会吵架、评审被怼、摸鱼、生成实习日记)。当用户说"开始实习"、"上班"、"继续上班"、"加载/运行 xx 实习包"、"体验一日实习生"时使用。也用于"创作/校验实习包"。需要 lark-cli 已认证。
---

# 一日实习生 · Claude Code 适配器

**引擎的完整规范在 [engine/ENGINE.md](../../../engine/ENGINE.md)——现在就去读它,并严格按它执行。**
本文件只补充 Claude Code 环境的适配细节:

1. **长循环**:用 Bash 执行 `lark-cli event consume --timeout ...` 的阻塞等待,一次对话轮内循环推进;上下文吃紧时靠 `runs/<run_id>/state.json` 无损续跑(摘要压缩后重读 state 即可)
2. **续跑触发**:用户说"继续上班"→ 找最近的 `runs/*/state.json`,恢复主循环;超过 deadline 的幕按 fallback 快进补齐
3. **渐进加载纪律**:开局只读 `pack.json` + `timeline.md`(幕索引)+ 人设卡;每幕的 `beats/EXX.md` 到幕才读——不要提前读完全部剧本,省上下文也防剧透式演砸
4. **写 payload 前**(卡片 JSON/文档 XML):先 `lark-cli skills read` 对应内置文档,禁止手写猜格式
5. 默认日记模板在 [references/diary-default.html](references/diary-default.html)
