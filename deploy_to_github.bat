@echo off
chcp 65001 >nul
title 2027 秋招情报雷达 - 一键推送到 GitHub 云端
echo ======================================================================
echo   🚀 2027 届秋招全网实时情报雷达 - GitHub Actions 云端项目一键部署
echo ======================================================================
echo.
echo 请确保你已经在 GitHub 上新建了一个名为 campus-job-tracker 的仓库！
echo （新建地址：https://github.com/new ，注意不要勾选添加 README）
echo.
set /p REPO_URL="请输入你的 GitHub 仓库地址 (例如 https://github.com/yourname/campus-job-tracker.git): "

if "%REPO_URL%"=="" (
    echo [!] 未输入仓库地址，部署终止。
    pause
    exit /b
)

echo.
echo [*] 正在初始化本地 Git 仓库...
git init
git add .
git commit -m "🚀 初始化 2027 届秋招情报雷达云端全自动项目 (每天早 8:00 自动更新)"
git branch -M main
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo.
echo [*] 正在将代码推送到 GitHub 云端...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo   ✅ 恭喜！项目已成功推送到 GitHub 云端！
    echo ======================================================================
    echo 接下来你只需两步：
    echo 1. 打开你的 GitHub 仓库页面 -> Settings -> Pages；
    echo 2. 在 Source 下拉框中选择 "GitHub Actions"（或 "Deploy from a branch"）；
    echo 之后每天早上 08:00，云端服务器将自动抓取全网最新秋招岗位并更新网页！
    echo 无论手机还是电脑，打开 GitHub Pages 链接即可随时查看！
    echo ======================================================================
) else (
    echo.
    echo [!] 推送失败，请检查网络连接、GitHub 认证信息或仓库地址是否正确。
)

echo.
pause
