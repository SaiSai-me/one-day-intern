# lark-cli 工具库速查(一日实习生版)

> 基于 `lark-cli v1.0.65`(https://github.com/larksuite/cli)整理。
> 本文档**按"游戏动作"组织**,不按 API 组织——目的是让引擎(本地 agent)在驱动剧情时能直接查到"这一步该敲什么命令"。
> 所有命令都已在本机安装验证(`which lark-cli` → `/opt/homebrew/bin/lark-cli`)。

---

## 0. 调用约定(先读这个)

### 三层命令结构

| 层级 | 形式 | 何时用 |
|---|---|---|
| 快捷命令 | `lark-cli <域> +<动作>` | **优先用**。AI 友好,智能默认值,如 `im +messages-send` |
| 类型化 API | `lark-cli <域> <资源> <方法>` | 快捷命令覆盖不到时,如 `im reactions create` |
| 原始 API | `lark-cli api GET/POST /open-apis/...` | 兜底,可打 2500+ 全部开放平台端点 |

### 全局通用参数

```bash
--as user|bot        # 身份:user=以你本人操作(需扫码授权), bot=以应用机器人操作(无需授权)
--dry-run            # 只打印请求不执行 —— 调试剧本必备
--jq '<expr>'        # 过滤 JSON 输出,如 --jq '.data.chat_id'
--format json|pretty|table|ndjson|csv
--idempotency-key    # 幂等键,防止剧情事件重复发送(im/task 支持)
```

### 风险等级

每条命令 `--help` 标注 `read | write | high-risk-write`。**high-risk-write 必须先经用户确认再加 `--yes`**,禁止静默重试。

### 身份选择心法(一日实习生场景)

- **bot 身份** = "虚构公司的同事们"。发消息、建群、发卡片都用 bot,玩家看到的是 NPC 在说话。**bot 无需用户扫码,当前即可用**。
- **user 身份** = "玩家本人"。建日程到玩家自己的日历、以玩家名义创建文档等,需要玩家扫码授权。
- bot 看不到用户的个人资源(日历/云盘);给玩家日历建日程要么用 user 身份,要么 bot 建日程再邀请玩家(`--attendee-ids`)。

---

## 1. 认证与环境(开机检查)

```bash
lark-cli whoami                          # 当前身份/应用/token 状态(JSON)
lark-cli auth status                     # user + bot 两个身份的详细状态
lark-cli doctor                          # 健康检查:配置/认证/连通性

# 首次配置(创建飞书自建应用,阻塞式,给用户浏览器链接)
lark-cli config init --new

# user 身份登录(推荐 split-flow,agent 场景)
lark-cli auth login --recommend --no-wait --json   # ① 拿 verification_url + device_code
lark-cli auth qrcode <url> --output qr.png          # ② 生成二维码给用户扫
lark-cli auth login --device-code <code>            # ③ 用户确认扫完后再轮询
# 人类直接在终端跑更简单:
lark-cli auth login --recommend

# 缺权限时增量授权
lark-cli auth login --scope "im:chat:read calendar:calendar.event:create"
lark-cli auth check --scope "task:task:write"       # exit 0=有权限
```

---

## 2. 游戏动作 → 命令映射

### 2.1 入职(开局:建群、拉人、欢迎)

```bash
# 建实习群(bot 建群并自任管理员,拉玩家进群)
lark-cli im +chat-create --as bot --name "🏢 跳动大厂·产品部" \
  --description "一日实习生入职群" --users ou_玩家openid --set-bot-manager
# 返回 .data.chat_id (oc_xxx) —— 全天剧情的舞台,存下来!

# NPC 发欢迎语(text / markdown 均可)
lark-cli im +messages-send --as bot --chat-id oc_xxx \
  --markdown "**【HR·小美】** 欢迎新同学!今天你的导师是老王,10 点站会别迟到~"

# 改群名/群描述(剧情推进,如"需求评审作战室")
lark-cli im +chat-update --as bot --chat-id oc_xxx --name "新群名"
```

**给玩家发私聊**(P2P,用 `--user-id`):
```bash
lark-cli im +messages-send --as bot --user-id ou_xxx --text "老板喊你去工位一趟"
```

### 2.2 派活(任务)

```bash
# 派任务给玩家(bot 派,assignee 是玩家 open_id)
lark-cli task +create --as bot --summary "写一份「宠物社交」功能 PRD" \
  --description "下午 3 点评审,总监会到场" \
  --due "2026-07-04T15:00:00+08:00" --assignee ou_玩家openid
# ⚠️ 已验证(v1.0.65):--due 只接受 ISO 8601 / Unix 时间戳;
#    --help 里写的 relative:+2d 格式实际会报错,引擎需自行换算 ISO 时间

# 催活(加评论)/ 提醒 / 完成检查
lark-cli task +comment --as bot --task-guid <guid> --content "进度怎么样了?总监在问"
lark-cli task +reminder ...            # 设提醒
lark-cli task +get-my-tasks --as user  # 玩家视角看自己的任务
lark-cli task +complete ...            # 标记完成(玩家交活时)
```

### 2.3 日程(站会、评审会、一对一)

```bash
# bot 建日程并邀请玩家(bot 身份建在应用日历,玩家收到邀请)
lark-cli calendar +create --as bot --summary "☀️ 晨会站会" \
  --start "2026-07-04T10:00:00+08:00" --end "2026-07-04T10:15:00+08:00" \
  --attendee-ids ou_玩家openid --description "每人 30 秒同步进展"

# 玩家视角:看今日议程 / 回复日程邀请
lark-cli calendar +agenda --as user
lark-cli calendar +rsvp --as user ...   # accept/decline/tentative
```

### 2.4 群聊互动(剧情核心循环)

**NPC 说话**(多角色靠消息前缀区分,单 bot 演全员):
```bash
lark-cli im +messages-send --as bot --chat-id oc_xxx --markdown "**【后端·杠子】** 这需求做不了,排期到明年"
```

**回复玩家的消息**(可开话题串):
```bash
lark-cli im +messages-reply --as bot --message-id om_xxx --text "【导师·老王】我觉得可以先拆个 MVP"
```

**表情回复**(已读/嘲讽/点赞,NPC 情绪表达):
```bash
lark-cli im reactions create ...        # 给消息加 emoji reaction
```

**监听玩家发言**(引擎的"耳朵",阻塞等待,**必须有界**):
```bash
lark-cli event consume im.message.receive_v1 --timeout 120s --max-events 1 \
  --jq '{chat_id: .event.message.chat_id, text: .event.message.content, sender: .event.sender.sender_id.open_id}'
# stderr 出现 "[event] ready event_key=..." 后才算就绪
# 退出码 0 = 正常(收满/超时);优雅停止用 SIGTERM,禁止 kill -9
```

### 2.5 剧情选择(交互卡片按钮——分支剧情的关键)

> ⚠️ **前置(一次性人工配置)**:飞书开发者后台 → 应用 → **事件与回调 → 回调配置** 需手动开启,否则 `card.action.trigger` 收不到,且无任何报错。

```bash
# 发带按钮的卡片(如:「接下需求」vs「当场反驳」)
# 卡片 JSON 构造流程必须先读内置文档,禁止手写:
lark-cli skills read lark-im references/card/lark-im-card-create.md
lark-cli im +messages-send --as bot --chat-id oc_xxx --msg-type interactive --content '<卡片JSON>'

# 监听玩家点了哪个按钮
lark-cli event consume card.action.trigger --timeout 300s --max-events 1
# 输出含 action_value(按钮携带值)、token(30 分钟内可更新原卡片,最多 2 次)、card_content(原卡片 DSL)
# 更新卡片(比如按钮点完变灰):POST /open-apis/interactive/v1/card/update,见
lark-cli skills read lark-im references/lark-im-card-action-reply.md
```

### 2.6 开会(视频会议)

```bash
lark-cli vc +meeting-join --as bot --meeting-no <会议号>     # bot 真实入会
lark-cli vc +meeting-message-send ...                        # 会中发文字/表情
lark-cli vc +meeting-list-active --as user                   # 查进行中的会
lark-cli vc +detail --meeting-ids <id>                       # 拿 note_id/minute_token
# 会议开始/结束事件(user 身份):
# vc.meeting.participant_meeting_started_v1 / _ended_v1
```
> 降级方案:无 vc 权限时,"开会"用 日程(2.3)+ 群内文字轰炸(2.4)模拟,效果同样成立。

### 2.7 干活产出(玩家写 PRD / 文档被评审)

```bash
# 建文档(评审命题作文;写 --content 前必须先读内置格式文档)
lark-cli skills read lark-doc references/lark-doc-create.md   # 必读
lark-cli docs +create --as bot --content '<XML或Markdown>' [--doc-format markdown]

lark-cli docs +fetch ...        # 读玩家写的文档(NPC 评审时"看稿")
lark-cli docs +update ...       # 往文档里加"评审批注"
lark-cli docs +search --as user # 搜索文档
# 轻量产物用 Drive 原生 Markdown 更简单:
lark-cli markdown +create / +fetch / +patch / +overwrite / +diff
```

### 2.8 摸鱼与打卡(彩蛋系统)

```bash
lark-cli attendance user_tasks query --as user   # 查玩家真实打卡记录(彩蛋:上班时长)
lark-cli approval instances create ...           # 发起"摸鱼申请"式恶搞审批(需审批定义)
lark-cli approval tasks approve/reject ...       # NPC 秒批/秒拒
```

### 2.9 下班(实习日记生成与发布)

```bash
# 日记 = 引擎汇总全天行为日志 → 渲染 HTML → 发布拿分享链接
lark-cli apps +create --as user ...                             # 一次性:建妙搭应用容器
lark-cli apps +html-publish --app-id <app_id> --path ./diary/   # 发布整个目录,返回访问 URL
# 或把日记发回群里收尾:
lark-cli im +messages-send --as bot --chat-id oc_xxx --markdown "**【HR·小美】** 你的实习日记已生成:<url> 明天…没有明天了"
```

### 2.10 查人(open_id 解析)

```bash
lark-cli contact +get-user --as user                 # 不带 user_id = 查自己(拿玩家 open_id)
lark-cli contact +search-user --as user --query 张三  # 按名字搜人
```

---

## 3. 实时事件键速查(引擎的感知系统)

```bash
lark-cli event list              # 全部事件键
lark-cli event schema <key>      # 看某事件的字段结构(含 jq_root_path)
lark-cli event status            # 事件总线守护进程状态
lark-cli event stop              # 停守护进程
```

| 事件键 | 身份 | 游戏用途 |
|---|---|---|
| `im.message.receive_v1` | bot | **玩家在群里/私聊说话了** → 推进剧情 |
| `card.action.trigger` | bot | **玩家点了剧情选择按钮**(需后台开回调配置) |
| `im.chat.member.user.added_v1` | bot | 玩家进群了 → 触发欢迎剧情 |
| `im.message.reaction.created_v1` | bot | 玩家给消息点了表情 → 隐藏互动 |
| `im.message.message_read_v1` | bot | 玩家已读私聊 → "已读不回"检测(摸鱼判定) |
| `vc.meeting.participant_meeting_started_v1/_ended_v1` | user | 会议开始/结束 → 会议剧情起止 |
| `task.task.update_user_access_v2` | user\|bot | 任务状态变化 → 玩家交活了 |

**消费契约**(引擎必须遵守):
1. 一律有界消费:`--timeout <D>` 和/或 `--max-events <N>`,引擎用循环调度,禁止无界挂起
2. 就绪信号:stderr 打印 `[event] ready event_key=<key>` 后事件流才有效
3. 停止用 SIGTERM(`kill <pid>`),**禁止 `kill -9`**(会泄漏服务端订阅)
4. 退出码:0=正常(收满/超时),1-5=各类失败(stderr 有 JSON 错误)

---

## 4. 安全与稳健规则(来自官方 lark-shared,引擎必须内置)

1. **禁止输出 appSecret / accessToken 明文**(日志、日记、群消息里都不行)
2. 文件路径只用**相对路径**(CLI 拒绝绝对路径和 `..`)
3. high-risk-write 操作:先向玩家确认,确认后才加 `--yes`;失败禁止静默重试
4. 授权链接和 device_code **不可缓存复用**;展示二维码后要等用户明确说"扫完了"再轮询
5. 剧情消息统一带 `--idempotency-key`(如 `pack-event-id`),防止重试导致 NPC 复读

---

## 5. 遇到没覆盖的功能怎么办

```bash
lark-cli schema <service>.<resource>.<method>   # 查任意方法的参数/类型/scope
lark-cli skills read <skill名> [文件路径]         # 读 CLI 内置的权威指南(版本匹配,优先于本文档)
lark-cli skills list                             # 列出全部内置技能
lark-cli api GET /open-apis/...                  # 原始 API 兜底
# 找不到接口时用探索技能:lark-openapi-explorer
```

> **本文档定位**:游戏动作层的速查索引。写具体 payload(卡片 JSON、文档 XML)前,以 `lark-cli skills read` 的内置文档为准——它与 CLI 版本强一致。
