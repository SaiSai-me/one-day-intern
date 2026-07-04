# 一日实习生 One-Day Intern

> 你好!我是今天的一日实习生酱~
> 基于 飞书 + 本地 AI Agent 的游戏化实习模拟器开源平台。
> 在家抠脚,好想实习!怎么办 → 打开一日实习生,当场上班。

下载一个「实习包」,接上你本地的 AI Agent(如 Claude Code)和个人飞书,沉浸式地在一家虚构公司上一天班:被派活、建日程、拉进群、开会吵架、评审被怼、摸鱼划水,下班自动生成一份可分享的搞笑实习日记。

## 仓库结构

| 路径 | 内容 |
|---|---|
| [一日实习生.txt](一日实习生.txt) | 产品创意与定位 |
| [docs/tech-route.md](docs/tech-route.md) | 技术路线与架构 |
| [docs/lark-cli-toolkit.md](docs/lark-cli-toolkit.md) | lark-cli 工具库速查(按游戏动作组织) |
| [docs/pack-spec.md](docs/pack-spec.md) | 实习包格式规范 v1 |
| `.claude/skills/one-day-intern/` | 游戏引擎(Claude Code Skill) |
| [packs/pm-one-day/](packs/pm-one-day/) | 示例实习包:产品经理·一日实习 |
| `web/` | 在线平台(Next.js + Supabase,实习包市场) |
| [index.html](index.html) / [posters.html](posters.html) | 产品文档页与宣传海报(像素风) |

## 快速开始(玩家)

```bash
# 1. 安装飞书 CLI 并认证(需飞书开放平台自建应用)
npx @larksuite/cli@latest install
lark-cli config init --new     # 首次:引导创建飞书应用
lark-cli auth login --recommend

# 2. 在本仓库目录打开 Claude Code,对它说:
#    「加载 pm-one-day 实习包,开始上班!」
```

## 快速开始(平台开发)

```bash
cd web && npm install && npm run dev
```

## 架构一句话

**实习包是数据,引擎是技能,飞书是舞台,网站是货架。**
详见 [docs/tech-route.md](docs/tech-route.md)。
