# 一日实习生 One-Day Intern

> 在你的真实飞书里，上一天虚构的班。

一日实习生是一套由 Codex 驱动的产品经理互动实习体验。Codex 扮演导演和 NPC，飞书群聊、任务、日历、文档和电子表格充当游戏舞台。

## 正式交付物

本项目只维护两个正式交付物：

1. **Codex Skill**：源码位于 `.agents/skills/one-day-intern/`，发布包为 [`dist/codex/one-day-intern-codex-v0.4.0.zip`](dist/codex/one-day-intern-codex-v0.4.0.zip)。
2. **GitHub Pages Landing Page**：源码位于 `web/`，只负责产品介绍、配置引导和 Skill 下载。

网站不提供账号、市场、上传、收藏、直播看板或后端服务，也不依赖 Supabase。

## 开始体验

### 准备

- Codex Desktop
- 一个可使用自建应用的飞书账号
- 已安装并授权所需飞书能力
- Python 3

### 安装 Skill

下载并解压 [`one-day-intern-codex-v0.4.0.zip`](dist/codex/one-day-intern-codex-v0.4.0.zip)。解压后的目录应包含：

```text
.agents/
└── skills/
    └── one-day-intern/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── assets/
        ├── references/
        ├── scripts/
        └── tests/
```

用 Codex Desktop 打开该目录，然后发送：

```text
开始实习
```

中断后可以发送“继续实习”从本地存档恢复。

## 开发与验证

### Skill

```bash
python3 -m unittest discover \
  -s .agents/skills/one-day-intern/tests -v

python3 .agents/skills/one-day-intern/scripts/validate-skill.py \
  .agents/skills/one-day-intern

python3 .agents/skills/one-day-intern/scripts/build-release.py \
  .agents/skills/one-day-intern \
  dist/codex/one-day-intern-codex-v0.4.0.zip

python3 .agents/skills/one-day-intern/scripts/validate-skill.py \
  .agents/skills/one-day-intern \
  --release-zip dist/codex/one-day-intern-codex-v0.4.0.zip
```

### Landing Page

```bash
cd web
npm ci
npm run dev
```

生产构建：

```bash
npm run build
```

构建前会自动把正式 Codex Skill 包同步到网站下载目录。推送到 `main` 后，GitHub Actions 会测试 Skill、校验发布包、审计网页依赖并部署 GitHub Pages。

## 仓库结构

```text
一日实习生/
├── .agents/skills/one-day-intern/   # 正式 Skill 源码
├── .github/workflows/               # GitHub Pages 构建与校验
├── dist/codex/                      # 当前正式 Skill 包
├── web/                             # 单页 Landing Page
└── legacy/                          # 历史方案与旧产物，不参与正式构建
```

## 数据安全

- 飞书认证信息不得写入 Skill、日志或发布包。
- `runs/` 和 `legacy/runs/` 均被 Git 忽略。
- 开局后的建群、建任务和建日程属于真实飞书写入，只会在玩家明确开始后执行。

历史适配器、通用引擎、剧情包、平台原型和旧发布物统一存放在 [`legacy/`](legacy/README.md)，不再作为正式产品维护。
