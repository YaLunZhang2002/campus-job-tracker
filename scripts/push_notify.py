import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# Fix stdout encoding
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
INBOX_PATH = DATA_DIR / "daily_inbox_jobs.json"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def send_push():
    push_key = os.getenv("PUSH_KEY", "").strip()
    if not push_key:
        print("[i] 未配置 PUSH_KEY 密钥，跳过移动端微信推送。（可在 GitHub 仓库 Settings -> Secrets 中添加 PUSH_KEY）")
        return

    today_str = datetime.now().strftime("%m月%d日")
    
    inbox_jobs = []
    if INBOX_PATH.exists():
        try:
            with open(INBOX_PATH, "r", encoding="utf-8") as f:
                inbox_jobs = json.load(f)
        except Exception:
            pass

    soe_cnt = sum(1 for j in inbox_jobs if j.get("module") == "央国企龙头")
    mt_cnt = sum(1 for j in inbox_jobs if j.get("is_mt") or j.get("module") == "管培生计划")
    foreign_cnt = sum(1 for j in inbox_jobs if j.get("module") == "外企（中国）" or j.get("is_foreign"))
    internet_cnt = sum(1 for j in inbox_jobs if j.get("module") == "互联网大厂")

    title = f"☀️ 2027秋招早报 ({today_str}): 待审仓上新 {len(inbox_jobs)} 岗"
    
    lines = [
        f"### 🎯 今日 8:00 秋招情报雷达自动巡检完成",
        f"- 📅 **巡检日期**：{today_str}",
        f"- ⚡ **待审流转仓**：当前共有 **{len(inbox_jobs)}** 个重点名企新批次待决策",
        f"- 🏛️ **央国企龙头**：{soe_cnt} 家",
        f"- 🎓 **综合管培生**：{mt_cnt} 家",
        f"- 🌍 **知名外企**：{foreign_cnt} 家",
        f"- 🌐 **互联网大厂**：{internet_cnt} 家",
        "",
        "#### 🌟 今日重点待审名企 TOP 5：",
    ]
    for j in inbox_jobs[:5]:
        pos = (j.get("positions") or ["核心业务岗"])[0]
        lines.append(f"1. **{j.get('company')}** · {pos} ({j.get('tier')}级 | {j.get('module')})")
    
    lines.append("")
    lines.append("👉 **点击直达 GitHub Pages 作战看板进行一键分流决策与投递！**")
    
    content = "\n".join(lines)

    # 1. ServerChan (SCT)
    if push_key.startswith("SCT"):
        url = f"https://sctapi.ftqq.com/{push_key}.send"
        data = urllib.parse.urlencode({"title": title, "desp": content}).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
                print("[+] Server酱 微信推送成功！")
        except Exception as e:
            print(f"[!] Server酱 推送失败: {e}")

    # 2. PushPlus
    elif len(push_key) == 32:
        url = "http://www.pushplus.plus/send"
        payload = json.dumps({"token": push_key, "title": title, "content": content, "template": "markdown"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
                print("[+] PushPlus 微信推送成功！")
        except Exception as e:
            print(f"[!] PushPlus 推送失败: {e}")

    # 3. 飞书自定义机器人 Webhook
    elif "open.feishu.cn" in push_key:
        payload = json.dumps({
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": title}},
                "elements": [{"tag": "markdown", "content": content}]
            }
        }).encode("utf-8")
        req = urllib.request.Request(push_key, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
                print("[+] 飞书机器人推送成功！")
        except Exception as e:
            print(f"[!] 飞书机器人推送失败: {e}")

    # 4. 企业微信自定义机器人 Webhook
    elif "qyapi.weixin.qq.com" in push_key:
        payload = json.dumps({
            "msgtype": "markdown",
            "markdown": {"content": f"## {title}\n{content}"}
        }).encode("utf-8")
        req = urllib.request.Request(push_key, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
                print("[+] 企业微信机器人推送成功！")
        except Exception as e:
            print(f"[!] 企业微信机器人推送失败: {e}")
    else:
        print(f"[!] 未识别的 PUSH_KEY 格式，请检查密钥设置。")

if __name__ == "__main__":
    send_push()
