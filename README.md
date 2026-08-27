# 一日实习生 · One-Day Intern

> 在你的真实飞书里，上一天虚构的班。

这是一个开源的 Codex Skill：让 Codex 在飞书中扮演导演和全部 NPC，带你体验一场完整的产品经理一日实习。你会经历入职、用户研究、方案取舍、技术评审和终审答辩，结束后获得一份基于真实游玩记录生成的实习日记。

## 先看介绍

打开 [一日实习生宣传页](https://saisai-me.github.io/one-day-intern/)，浏览完整玩法、任务链和使用说明。

## 安装并开始

1. 下载 [产品经理实习包](https://saisai-me.github.io/one-day-intern/one-day-intern-player-v1.0.0.zip)。
2. 解压到一个独立文件夹，并用 Codex Desktop 打开该文件夹。
3. 确认已配置并授权飞书联系人、即时消息、任务、日历和事件监听能力。
4. 在 Codex 中发送：`开始实习`。

也可以说“上班”“开始 demo”或“体验产品经理实习”。中断后发送“继续实习”即可从本地存档恢复。

## 开源 Skill 源码

Skill 源码位于 `.agents/skills/one-day-intern/`，包括剧情、人设、飞书工具契约、本地存档和实习日记生成脚本。欢迎提交 Issue 和 Pull Request，扩展剧情或改进体验。

## 运行要求

- Codex Desktop
- 可使用自建应用的飞书账号

开局后会在你的飞书中创建本局所需的工作群、任务和日程；运行状态、日志和日记只保存在本地 `runs/` 目录，不上传到网站。
