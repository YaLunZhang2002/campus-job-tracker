@echo off
chcp 65001 >nul
title 2027 秋招情报雷达 - 推送到 YaLunZhang2002/campus-job-tracker
echo ======================================================================
echo   🚀 正在推送到 GitHub: https://github.com/YaLunZhang2002/campus-job-tracker.git
echo ======================================================================
echo.
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo   ✅ 恭喜！项目已成功推送到 YaLunZhang2002/campus-job-tracker！
    echo ======================================================================
    echo.
    echo 接下来最后一步：
    echo 1. 打开你的 GitHub 仓库: https://github.com/YaLunZhang2002/campus-job-tracker/settings/pages
    echo 2. 在 Build and deployment 下方的 Source 选择 "GitHub Actions"；
    echo.
    echo 之后每天早上 08:00，云端服务器将自动抓取全网最新秋招岗位并更新网页！
    echo 专属在线作战看板地址为:
    echo 👉 https://yalunzhang2002.github.io/campus-job-tracker/
    echo ======================================================================
) else (
    echo.
    echo [!] 推送遇到问题：
    echo 如果提示 "Repository not found"，说明你还没有在 GitHub 上点击创建仓库！
    echo 请先打开浏览器访问：https://github.com/new?name=campus-job-tracker
    echo 点击绿色的 "Create repository" 创建空仓库后，再次双击本脚本即可！
)

echo.
pause
