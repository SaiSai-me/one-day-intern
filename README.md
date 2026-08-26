# 一日实习生 · One-Day Intern

一个像素风的产品经理一日实习体验页面。

## 本地运行

```bash
npm ci
npm run dev
```

打开 <http://localhost:3000>。

## 发布

推送 `main` 分支后，`.github/workflows/deploy-pages.yml` 会自动构建并发布到 GitHub Pages。

首次发布前，在仓库的 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。

项目页地址通常是 `https://<用户名>.github.io/<仓库名>/`；如果仓库名为 `<用户名>.github.io`，则是用户主页地址。
