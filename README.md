# 一日实习生 One-Day Intern

> 在飞书里，和同事一起把一件产品需求做完。

![一日实习生](web/public/intern-hero.jpg)

当前唯一版本是 **v0.6「这条视频，算谁发的？」**。你加入青橙校园视频社区，接手「共同署名邀请」：发出邀请、受邀者接受或拒绝、两边查看结果。没有正式版与演示版之分，没有倒计时，也不会因为阅读或写作时间长自动收尾。

[下载 v0.6 实习包](https://github.com/SaiSai-me/one-day-intern/releases/download/v0.6.0/one-day-intern-codex-v0.6.0.zip) · [查看完整剧本](.agents/skills/one-day-intern/references/scenario.md) · [查看 PRD 工作稿](.agents/skills/one-day-intern/assets/prd.md)

## 这次做什么

六名同学合拍毕业视频，不想每人重传一份。运营活动说明写着「选中谁，就出现在谁的主页」，设计稿却要求受邀者先接受。研发发现两份版本对不上，你需要在群里的这一次争执中提出明确判断，再把决定落实到原型、规则和验收用例里。

设计师 Mia 不是来发题的：她会和你修改同一张画板；研发 Ethan 在 PRD 的具体位置评审。最终交付是可进入开发评审的需求，不是假装产品已经上线。

| 同事 | 负责什么 |
| --- | --- |
| Chloe，人事 | 发入组说明，让你找到工作入口 |
| Kris，产品导师 | 解释材料、协助判断，不代替你做决定 |
| Mia，交互设计师 | 与你修改 P01–P03 原型，核对状态和界面 |
| Ethan，技术负责人 | 确认实现条件，评审真实 PRD |
| Aria，运营 | 提供反馈，处理活动说明的版本差异 |
| Vincent，产品负责人 | 需要负责人拍板时确认取舍 |

开场先阅读 Landing 并自我介绍。你选择的称呼、愿意分享的经历与练习目标会在本局持久保存，后续可以更正；不从账号实名或作品表现猜测背景。

## 在飞书里怎么做事

工作对象是三个 Chat（项目群、导师、负责人）、一份 Landing、一份含可编辑画板的 PRD、一张反馈多维表格和一个交接任务。没有为了走流程强加的日历会议或 KPI 看板。

- 卡片提供真实工作入口，也可以提交问题或申请评审。
- 在反馈表里写判断和理由，不必再抄回群聊。
- 在画板上改 P03 的拒绝状态，同时补 PRD 对应规则。
- 直接回复文档评审评论，修改后仍提交同一个任务。
- 同事读取实际内容和版本变化再回应；点「完成」只是提交，不代表验收通过。

公司、人物、反馈、活动和版本矛盾是虚构素材。角色共用一个飞书机器人，由姓名前缀区分；飞书文档、画板、评论、表格和任务则是在开局后创建的真实工作对象。

## 开始使用

1. 准备 Codex Desktop、Python 3 和飞书 CLI，以及可以配置自建应用的飞书账号。
2. 下载并解压实习包，用 Codex 打开解压目录。
3. 发送「开始实习」。

Codex 先说明创建范围并检查权限，再开始入组。卡片回调、画板管理权限与分享权限要实际验证，不能仅凭 CLI 有命令就宣称连接成功。当前工作区只完成本地版本改造与自动化测试，尚未替用户启动新局或完成租户端到端联调。

| 指令 | 行为 |
| --- | --- |
| 开始实习／上班／开始 demo | 同一个共同署名邀请版本 |
| 暂停 | 保存进度，停止业务推进 |
| 继续实习 | 恢复同一批对象，不重演开场 |
| 结束实习 | 按已有工作收尾，未完成项如实保留 |

不需要每幕说「继续」。桌面运行器通过绑定当前任务和 run_id 的 heartbeat 定向检查；未成功启动自动化时必须说明，不能假装在后台观察。

## 工作流记录的边界

Agent 通过消息、卡片、画板和任务事件唤醒，再读取指定资源。文档正文、评论和反馈记录按工作阶段定向读取和比较；当前 CLI 没有对应消费事件时不杜撰实时推送。

打开 Landing 不等于读懂，解决评论不等于修好，多人编辑快照不等于能确认每处改动的作者。底稿、用户修改、Agent 协助和来源不明的变化分别记录。只读本局工作对象，不扫描其他聊天或云盘文件。

历史源码保留在 [legacy/one-day-intern-v0.5](legacy/one-day-intern-v0.5/SKILL.md)，不进入新包、不作为第二种可选玩法。已有历史存档不删除、不自动改成新剧情；遇到活动旧局先由用户决定如何处理。

## 开发与验证

```bash
python3 -m unittest discover -s .agents/skills/one-day-intern/tests -v
python3 .agents/skills/one-day-intern/scripts/build-release.py .agents/skills/one-day-intern dist/codex/one-day-intern-codex-v0.6.0.zip
python3 .agents/skills/one-day-intern/scripts/validate-skill.py .agents/skills/one-day-intern --release-zip dist/codex/one-day-intern-codex-v0.6.0.zip
```

`web/` 只负责介绍与下载分发，构建会同步 v0.6 包。实习包同时通过 GitHub Release 和 GitHub Pages 分发，下载不需要飞书账号或云盘权限。运行协议和观察细节见 [runtime](.agents/skills/one-day-intern/references/runtime.md) 与 [workflow](.agents/skills/one-day-intern/references/workflow.md)。
