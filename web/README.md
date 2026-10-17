# 一日实习生 · Landing Page

网站是“一日实习生”的单页 Landing Page，只承担产品介绍和 Codex Skill 体验包分发：

- 介绍产品概念与体验流程
- 下载 `one-day-intern-codex-v0.6.0.zip` Codex Skill 体验包（共同署名邀请，唯一版本、无倒计时）
- 引导用户配置飞书并开始实习

网站不提供账号、实习包市场、上传、收藏、直播看板或其他后端功能，也不依赖 Supabase。

## 本地开发

```bash
npm install
npm run dev
```

打开 <http://localhost:3000>。

## 生产构建

```bash
npm run build
```

当前使用 Next.js 静态导出，构建产物位于 `out/`，可直接发布到 GitHub Pages。

## 发布到 GitHub Pages

仓库根目录的 `.github/workflows/deploy-pages.yml` 会在推送 `main` 分支时自动构建并发布网站。

1. 将仓库推送到 GitHub（默认分支使用 `main`）。
2. 在仓库的 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。
3. 等待 Actions 中的 `Deploy website to GitHub Pages` 完成。
4. 在 **Settings → Pages** 查看访问地址，项目页通常为 `https://<用户名>.github.io/<仓库名>/`。

工作流会自动为项目页设置 `basePath`；如果仓库名是 `<用户名>.github.io`，则会按用户主页处理，不添加额外路径。
