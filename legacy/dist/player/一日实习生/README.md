# 🎮 一日实习生 · 玩家快速开始

## 3步开玩

### 1. 前置准备
- 安装 Trae：https://www.trae.cn
- 安装 lark-cli 并配置飞书（如果还没装）：
  ```bash
  npx @larksuite/cli@latest install
  lark-cli config init --new  # 按提示配置飞书自建应用
  lark-cli auth login --recommend  # 扫码登录你的飞书账号
  lark-cli auth status  # 确认 bot 和 user 都是 ready
  ```

### 2. 打开工作区
解压本压缩包，用 **Trae 打开「一日实习生」这个文件夹**（必须打开整个文件夹，不能只打开单个文件）。

### 3. 开始实习
在 Trae 对话框里说：
- `开始demo` → 约20分钟快速体验
- `5分钟速通` → 最快看完剧情
- `开始实习` → 选择模式正式玩

游戏会自动在你的飞书建群，拉你和NPC们一起上班，全程在飞书聊天就行！

## 游戏中控制
随时可以在飞书或Trae对话框说：
- `快进` / `加速` → 节奏加快
- `慢点` / `等等` → 节奏放慢/暂停
- `跳过` / `next` → 直接下一幕
- `继续上班` → 中途退出后可以从存档恢复

## 问题排查
- 收不到NPC消息？检查 `lark-cli auth status` 两个身份是否都是 ready
- Trae找不到技能？确认你是用Trae打开的「一日实习生」整个文件夹，不是单个文件
- 详细教程见官网：（替换成你的网站URL）
