# 🎯 2027 届秋招全网实时情报雷达与全流程作战看板 (GitHub Actions 自动化版)

> **全自动云端托管 · 每天早 8:00 准时自动抓取 · 0 本地命令 · 手机/电脑随开随看 · 支持微信早报推送**

---

## ✨ 核心特性

- ⏰ **每天早 8:00 全自动运行**：由微软 GitHub Actions 云端服务器 7×24 小时定时驱动，**彻底无需开启电脑、无需手动敲任何 cmd 命令**。
- 🌐 **真全网多源实时数据流**：聚合 `sin0317`（121 家名企实况）、`xixicc2027`（402 岗实时结构化流）、`Campus2026` 与官方直聘网申系统数据库（400+ 权威直聘入口），告别死链与虚假动态。
- 🎯 **深度适配背景与智能分级**：专为工科/建筑专硕背景量身定制，涵盖【央国企龙头】、【管培生计划】、【外企（中国）】、【互联网大厂非技术/运营】与【全品类头部大厂】，算法打标 S/A/B 级匹配度。
- 📥 **GTD (Inbox Zero) 极致待审流转仓**：支持【⏳ 待决策】、【✅ 已入库】、【🚫 已忽略】与【📋 全部候选】四态分流，即点即归档，告别状态错乱。
- 📱 **免费全终端看板 (GitHub Pages)**：自动部署至 GitHub Pages，生成专属免费网页链接，手机微信、iPad 或电脑浏览器随时点开查看最新岗位。
- 🔔 **手机早报实时推送 (可选)**：支持 Server酱、PushPlus、企业微信或飞书机器人，早上 8:01 自动将《今日秋招上新战报》推送到手机微信！

---

## 🚀 1 分钟开箱配置指南

只需 3 步，即可将本项目跑在你的 GitHub 云端：

### 第一步：在 GitHub 上创建一个新仓库
1. 打开 [GitHub 创建新仓库页面](https://github.com/new)；
2. 仓库名称填入：`campus-job-tracker`（公开 Public 或私有 Private 均可）；
3. **不要**勾选 "Add a README file"（保持空仓库），点击 **Create repository**。

### 第二步：将本地项目推送到你的 GitHub 仓库
在本项目根目录下，你可以**直接双击运行 `deploy_to_github.bat`**，或者在终端执行以下命令（将 `<你的GitHub用户名>` 替换为真实用户名）：

```bash
git init
git add .
git commit -m "🚀 初始化 2027 届秋招情报雷达自动化项目"
git branch -M main
git remote add origin https://github.com/<你的GitHub用户名>/campus-job-tracker.git
git push -u origin main
```

### 第三步：开启 GitHub Pages 专属网页访问
1. 进入你刚刚创建的 GitHub 仓库页面，点击顶部的 **Settings** ➔ 侧边栏的 **Pages**；
2. 在 **Build and deployment** 下方的 **Source** 选择：
   - 选择 **GitHub Actions**（推荐，流水线自动发布）；
   - 或者选择 **Deploy from a branch** ➔ 分支选择 `main` ➔ 目录选择 `/ (root)` ➔ 点击 **Save**；
3. 等待约 1 分钟，页面顶部就会出现你的专属在线看板网址：
   `https://<你的GitHub用户名>.github.io/campus-job-tracker/`
   *(收藏到手机微信或浏览器书签，每天起床点开就是最新情报！)*

---

## 🔔 (可选) 配置手机微信早报推送

如果你希望每天早上 8:01 手机微信自动收到《今日秋招早报》：

1. 获取微信推送 Token：
   - **方式 A (Server酱)**：微信扫码登录 [Server酱](https://sct.ftqq.com/)，复制以 `SCT` 开头的 SendKey。
   - **方式 B (PushPlus)**：微信扫码登录 [PushPlus](https://www.pushplus.plus/)，复制 32 位 Token。
2. 配置到 GitHub 仓库：
   - 进入你的 GitHub 仓库 ➔ **Settings** ➔ **Secrets and variables** ➔ **Actions**；
   - 点击 **New repository secret**；
   - Name 填入：`PUSH_KEY`；
   - Secret 填入你复制的 Key/Token；
   - 点击 **Add secret** 即可！

---

## 📂 项目工程架构

```
campus-job-tracker/
├── .github/
│   └── workflows/
│       └── daily_recruitment_sync.yml   # ⭐ GitHub Actions 每天早 8:00 (UTC 00:00) 自动触发流水线
├── data/
│   ├── job_tracking_db.json             # 个人已投递实战台账数据库（自动隔离防重）
│   ├── daily_inbox_jobs.json            # 每日 30 席精选待审流转仓
│   ├── official_portals.json            # 400+ 真实权威名企官方直聘系统数据库
│   └── removed_job_ids.json             # 永久隔离黑名单
├── scripts/
│   ├── multi_source_spider.py           # 🚀 全网多源真实实时网络抓取引擎
│   ├── sync_and_rank.py                 # 🎯 智能清洗、算法分级打分并生成 index.html
│   └── push_notify.py                  # 📱 移动端微信早报推送模块
├── index.html                           # 🖥️ 交互式作战看板 (GitHub Pages 根文件，随开随用)
├── 秋招每日岗位追踪与投递台账.md         # 📋 Markdown 分区投递总台账
├── requirements.txt                     # 极简 Python 依赖清单
├── .gitignore                           # Git 规范忽略配置
├── deploy_to_github.bat                 # 🚀 Windows 本地一键初始化并推送至 GitHub 脚本
└── README.md                            # 项目开箱与使用文档
```

---

## 🛡️ 数据安全与隐私保障

- 个人实战投递台账（`data/job_tracking_db.json`）仅记录企业名称与投递状态，不包含个人身份证号或密码等敏感信息；
- 若设置仓库为 **Private（私有仓库）**，只有你个人具有访问权限；
- 支持在 GitHub 网页端的 Actions 标签页点击 **Run workflow** 随时手动触发即时更新。
