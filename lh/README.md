# 每日 AI 资讯聚合推送系统

本项目通过 GitHub Actions 自动抓取中英文 AI 资讯，提取热点并推送到飞书群。

## 功能特点
- **中英比例**：6:4（英文 6 条，中文 4 条）
- **中英对照**：英文资讯标题及内容均提供中英对照
- **多源聚合**：
  - 英文：Hacker News, Reddit, OpenAI Blog, DeepMind Blog
  - 中文：机器之心, 量子位, 36氪
- **定时推送**：每天北京时间早上 7:00 自动运行

## 部署步骤

1. **创建 GitHub 仓库**：
   在 GitHub 上创建一个新仓库（例如 `ai-news-pusher`）。

2. **上传代码**：
   将本项目的所有文件上传到该仓库。

3. **配置 GitHub Secrets**：
   在仓库设置中（Settings > Secrets and variables > Actions），添加以下两个 Secret：
   - `FEISHU_WEBHOOK_URL`: 您的飞书机器人 Webhook 地址。
   - `OPENAI_API_KEY`: 您的 OpenAI API Key（用于热点提取与翻译）。

4. **开启 Actions**：
   默认情况下，GitHub Actions 在新仓库中可能需要手动确认开启。进入 Actions 标签页，确保 Workflow 已启用。

## 手动运行
您可以进入 GitHub Actions 页面，选择 "Daily AI News Push" 工作流，点击 "Run workflow" 立即触发推送测试。
