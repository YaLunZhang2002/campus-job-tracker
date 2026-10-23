# 🎯 2027 届秋招全网实时情报雷达与全流程作战看板 (GitHub Actions 自动化版)

> **全自动云端托管 · 每天早 8:00 准时自动抓取 · 0 本地命令 · 手机/电脑随开随看 · 支持微信早报推送**  
> 专属在线作战看板：👉 **[https://yalunzhang2002.github.io/campus-job-tracker/](https://yalunzhang2002.github.io/campus-job-tracker/)**

---

## ✨ 核心特性

- ⏰ **每天早 8:00 全自动运行**：由微软 GitHub Actions 云端服务器 7×24 小时定时驱动，**彻底无需开启电脑、无需手动敲任何 cmd 命令**。
- 🌐 **真全网多源实时数据流**：聚合 `sin0317`（121 家名企实况）、`xixicc2027`（402 岗实时结构化流）、`Campus2026` 与官方直聘网申系统数据库（400+ 权威直聘入口），告别死链与虚假动态。
- 🎯 **深度适配背景与智能分级**：专为工科/建筑专硕背景量身定制，涵盖【央国企龙头】、【管培生计划】、【外企（中国）】、【互联网大厂非技术/运营】与【全品类头部大厂】，算法打标 S/A/B 级匹配度。
- 📥 **GTD (Inbox Zero) 极致待审流转仓**：支持【⏳ 待决策】、【✅ 已入库】、【🚫 已忽略】与【📋 全部候选】四态分流，即点即归档，告别状态错乱。
- 📱 **免费全终端看板 (GitHub Pages)**：自动部署至 GitHub Pages，生成专属免费网页链接，手机微信、iPad 或电脑浏览器随时点开查看最新岗位。
- 🔔 **手机早报实时推送 (可选)**：支持 Server酱、PushPlus、企业微信或飞书机器人，早上 8:01 自动将《今日秋招上新战报》推送到手机微信！

---

## 🚀 专属配置与一键推送

本地 Git 仓库已为你完全预配置好：
- **Git 远程源**：`https://github.com/YaLunZhang2002/campus-job-tracker.git`
- **提交作者**：`YaLunZhang2002`
- **部署分支**：`main`

### 仅需两步完成云端部署：

1. **第一步：在 GitHub 上点击创建空仓库**
   - 访问预填链接：👉 **[https://github.com/new?name=campus-job-tracker](https://github.com/new?name=campus-job-tracker)**
   - 仓库名称已预填为 `campus-job-tracker`；
   - 权限选择公开（Public）或私有（Private）均可；
   - **不要**勾选 "Add a README file"，直接点击绿色的 **Create repository** 按钮！

2. **第二步：双击推送代码**
   - 回到本地文件夹 `d:\Internet work\campus-job-tracker`，直接双击运行 **`push_now.bat`**；
   - 代码即可自动推送到 GitHub 云端！

3. **第三步：开启 GitHub Pages 专属网页访问**
   - 进入你的仓库设置：👉 **[https://github.com/YaLunZhang2002/campus-job-tracker/settings/pages](https://github.com/YaLunZhang2002/campus-job-tracker/settings/pages)**；
   - 在 **Build and deployment** 下方的 **Source** 选择 **GitHub Actions**；
   - 稍等约 1 分钟，你的专属在线看板即永久上线：
     👉 **[https://yalunzhang2002.github.io/campus-job-tracker/](https://yalunzhang2002.github.io/campus-job-tracker/)**

---

## 🔔 (可选) 配置手机微信早报推送

如果你希望每天早上 8:01 手机微信自动收到《今日秋招早报》：

1. 微信扫码登录 [Server酱](https://sct.ftqq.com/) 或 [PushPlus](https://www.pushplus.plus/) 获取 SendKey / Token；
2. 打开 GitHub 密钥设置：👉 **[https://github.com/YaLunZhang2002/campus-job-tracker/settings/secrets/actions](https://github.com/YaLunZhang2002/campus-job-tracker/settings/secrets/actions)**；
3. 点击 **New repository secret**：
   - Name 填：`PUSH_KEY`；
   - Secret 填：你复制的 Key/Token；
   - 点击 **Add secret** 即可！
