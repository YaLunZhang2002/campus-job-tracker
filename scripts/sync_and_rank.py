#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
秋招全网全行业情报雷达与投递作战室 3.0
多源海量纳管 + 今日早8点算法精选 + 薪资与企业背景多维情报 + 笔面试考评避坑 + Windows原生Toast桌面通知
"""

import os
import sys
import json
import re
import argparse
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
import subprocess
import urllib.request
from datetime import datetime, date
from pathlib import Path

# 确保在 Windows 控制台下输出不会因为编码崩溃
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 根目录与路径配置 (GitHub Actions 云端 + 本地通用)
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

TRACKING_DB_PATH = DATA_DIR / "job_tracking_db.json"
CUSTOM_JOBS_PATH = DATA_DIR / "custom_jobs.json"
REMOVED_JOBS_PATH = DATA_DIR / "removed_job_ids.json"
BUILTIN_JOBS_PATH = DATA_DIR / "built_in_jobs_catalog.json"
MEGA_SOURCES_PATH = DATA_DIR / "mega_campus_sources.json"
OFFICIAL_PORTALS_PATH = DATA_DIR / "official_portals.json"

OUTPUT_MD_PATH = REPO_ROOT / "秋招每日岗位追踪与投递台账.md"
OUTPUT_HTML_PATH = REPO_ROOT / "index.html"

# 远程多源 URL
PRIMARY_FEED_URL = "https://raw.githubusercontent.com/xixicc186/xixicc2027/main/jobs.json"
SECONDARY_FEED_URL = "https://raw.githubusercontent.com/namewyf/Campus2026/main/README.md"

# 关键词矩阵
ARCH_TECH_KEYWORDS = [
    "建筑", "规划", "土木", "绿色", "低碳", "双碳", "节能", "结构", "设计",
    "bim", "gis", "智慧城市", "工程管理", "数字化建筑", "空间", "测绘", "勘察",
    "暖通", "光伏", "环境工程", "地产", "建研", "建筑设计", "建筑科技"
]

INTERNET_OP_KEYWORDS = [
    "电商运营", "商家运营", "类目运营", "平台运营", "品类运营", "商业化",
    "用户运营", "内容运营", "活动运营", "产品运营", "社群运营", "直播运营",
    "渠道运营", "数据运营", "策略运营", "运营管培", "品类采销", "新媒体运营"
]

AI_NONTECH_KEYWORDS = [
    "ai运营", "ai产品", "数据标注", "语料", "模型运营", "训练集", "提示词",
    "prompt", "ai解决方案", "ai商业化", "大模型落地", "智能化", "agent数据",
    "agi业务", "算法评测", "数据产品"
]

TOB_SALES_KEYWORDS = [
    "tob", "to b", "大客户销售", "企业客户", "政企", "产业招商", "招商", "商务",
    "客户经理", "销售管理", "客户成功", "csm", "bd", "渠道", "解决方案销售", "企划销售", "营销管培"
]

SOE_GENERAL_KEYWORDS = [
    "管培生", "储备干部", "管理培训生", "企划", "综合管理", "党群", "战略规划",
    "人事", "行政", "市场", "招商经理", "商务专员"
]

PURE_DEV_EXCLUDES = [
    "c++", "java", "golang", "后端开发", "前端开发", "算法工程", "芯片设计", "驱动开发",
    "嵌入式软件", "安卓开发", "ios开发", "底层内核", "编译优化", "测试开发工程师"
]


def load_json(path, default=None):
    if default is None:
        default = {}
    p = Path(path)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] 读取 {path} 失败: {e}")
    return default


def save_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_job_id(company, positions_str, batch=""):
    comp = (company or "").strip()
    pos = (positions_str or "").strip().replace(" ", "")
    b = (batch or "").strip()
    return f"{comp}_{pos}_{b}".replace(" ", "")


def send_windows_toast(title, message):
    """通过 Windows Runtime 发送原生桌面 Toast 弹窗通知"""
    ps_cmd = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $textNodes = $template.GetElementsByTagName("text")
    $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
    $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("CampusJobRadar")
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    $notifier.Show($toast)
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=False, timeout=6)
        print("[+] 成功推送 Windows 桌面 Toast 实时通知！")
    except Exception as e:
        print(f"[!] 发送 Windows 桌面通知跳过: {e}")


def fetch_primary_jobs():
    """获取数据源 1: xixicc2027 结构化数据 (440+ 岗位)"""
    print(f"[*] 正在拉取数据源 1 (xixicc2027): {PRIMARY_FEED_URL}")
    try:
        req = urllib.request.Request(
            PRIMARY_FEED_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CampusRadar/3.0"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[+] 数据源 1 成功拉取: {len(data)} 条原始岗位记录")
            return data
    except Exception as e:
        print(f"[!] 数据源 1 拉取异常: {e}")
        return []


def fetch_secondary_jobs():
    """获取数据源 2: namewyf Campus2026 大厂与金融科技入口"""
    print(f"[*] 正在拉取数据源 2 (Campus2026 大厂直达入口): {SECONDARY_FEED_URL}")
    jobs = []
    try:
        req = urllib.request.Request(
            SECONDARY_FEED_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CampusRadar/3.0"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            content = resp.read().decode("utf-8")
            pattern = re.compile(r'\|\s*([^\|]+?)\s*\|\s*\[([^\]]+)\]\((http[^\)]+)\)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]*?)\s*\|')
            matches = pattern.findall(content)
            for m in matches:
                comp = m[0].strip()
                link = m[2].strip()
                loc = m[4].strip()
                remark = m[5].strip()
                if "公司" in comp or "---" in comp or not link:
                    continue
                jobs.append({
                    "company": comp,
                    "industry": "互联网",
                    "cohort": "2026/2027届",
                    "batch": "校招正式批/提前批",
                    "positions": ["平台核心通识管培", "电商运营/产品运营", "商业化大客户销售"],
                    "locations": [loc] if loc else ["全国"],
                    "apply_url": link,
                    "deadline": "招满即止",
                    "remarks": remark
                })
            print(f"[+] 数据源 2 成功提取: {len(jobs)} 家主流名企官方直聘入口")
    except Exception as e:
        print(f"[!] 数据源 2 拉取异常: {e}")
    return jobs


def enrich_with_portal(company, current_url, portals_map):
    """
    为企业精准匹配真实官方直聘网申系统。
    核心铁律：
    1. 真实优先：如果已有链接是合法的企业招聘官网（以 http 开头且非微信、非国聘检索、非占位符），100% 严格予以保留！绝不可替换为任何检索中转！
    2. 知识库精准映射：若原链接为空或为无效占位符，或 portals_map 中有收录企业正统网申门户（如 *.zhiye.com, careers.*, job.*, campus.* 等），则优先匹配知识库中的官方直聘系统；
    3. 铁律：绝对禁止生成任何第三方求职平台检索假链（严禁出现 iguopin、keyword 检索等中转链接）；
    4. 若实在无官方直聘系统收录，则保留已有有效链接，或置为空让用户查阅官方公告，绝不输出虚假检索链接！
    """
    comp_raw = (company or "").strip()
    clean_comp = re.sub(r'[\(（].*?[\)）]', '', comp_raw).strip().lower()

    # 1. 检查已有链接是否已是真实官网系统
    is_valid_existing = False
    if current_url and current_url.startswith("http"):
        if not any(bad in current_url.lower() for bad in ["iguopin", "weixin.qq.com", "sogou.com", "ncss.cn", "keyword=", "search?"]):
            is_valid_existing = True

    # 2. 尝试从权威官方直聘系统知识库中精准匹配
    matched_portal = None
    # 优先全字或去括号精准匹配
    for k, v in portals_map.items():
        if not v or "iguopin" in v.lower():
            continue
        k_clean = re.sub(r'[\(（].*?[\)）]', '', k).strip().lower()
        if k_clean and (k_clean == clean_comp or k == comp_raw):
            matched_portal = v
            break

    # 次优模糊包含匹配（要求关键词长度至少3个字，按长度降序避免子串先拦截）
    if not matched_portal:
        for k, v in sorted(portals_map.items(), key=lambda x: len(x[0]), reverse=True):
            if not v or "iguopin" in v.lower():
                continue
            k_clean = re.sub(r'[\(（].*?[\)）]', '', k).strip().lower()
            if len(k_clean) >= 3 and (k_clean in clean_comp or clean_comp in k_clean):
                matched_portal = v
                break

    if matched_portal:
        return matched_portal

    if is_valid_existing:
        return current_url

    # 3. 绝不生成任何国聘或第三方检索假链！未匹配到的保持已有 url 或置空
    return current_url if is_valid_existing else ""


def infer_salary_and_scale(company, industry, positions, tags):
    """智能推断企业规模背景、公允年薪预估、笔面试流程与避坑指南"""
    pos_str = " ".join(positions)
    scale = "🏢 行业知名大中型企业 / 细分赛道领军"
    salary = "💰 14w - 22w + 五险一金 + 绩效年奖"
    process = "🎯 网申网测 ➔ 业务初试 ➔ 业务复试 ➔ HR终审"
    tips = "【备考】注重基本商业逻辑与岗位匹配，面试准备结构化自我介绍与核心实践案例。"

    if "外企" in industry or any(k in company.lower() for k in ["玛氏", "mars", "联合利华", "unilever", "欧莱雅", "l'oreal", "雀巢", "nestle", "施耐德", "schneider", "西门子", "siemens", "特斯拉", "tesla", "迪卡侬", "decathlon", "宜家", "ikea", "太古", "达能", "百威", "百胜", "苹果", "apple", "阿迪达斯"]):
        scale = "🌍 全球知名跨国巨头 / 顶级外企 (中国区业务航母)"
        salary = "💰 18w - 32w + 商业补充医疗 + 弹性混合办公 + 国际化发展平台"
        process = "🎯 官网/网申系统 ➔ AI视频面试/性格测评 ➔ 商业模拟AC群面 ➔ 事业部高管终面"
        tips = "【外企通关】重视商业敏锐度、跨文化沟通与同理心。强调结构化英文/双语自我介绍，善用STAR法则阐述创新与领导力案例。"
    elif "央国企" in industry or any(k in company for k in ["中建", "中铁", "中交", "华润", "保利", "国网", "电信", "移动", "中粮"]):
        scale = "🏢 骨干央企 / 大型国企 / 世界500强"
        salary = "💰 15w - 25w + 六险二金 + 住房补贴/宿舍 + 央企全套工会福利"
        process = "🎯 统一网申 ➔ 统一笔试/在线行测测评 ➔ 线下综合一面 ➔ 业务二面 ➔ 体检录用"
        tips = "【央国企通关】国企极其看重政治面貌、踏实稳重形象与抗压团队协同。面试切忌好高骛远，答题要讲求规矩与严谨闭环。"
    elif "互联网" in industry or any(k in company for k in ["阿里", "腾讯", "美团", "字节", "京东", "快手", "拼多多", "小红书", "DeepSeek", "vivo"]):
        scale = "🌐 万亿/千亿级科技互联网大厂 / 核心商业闭环"
        salary = "💰 18k - 30k × 15-16薪 (年薪 28w - 45w+) + 房补餐补 + 期权激励"
        process = "🎯 官网网申 ➔ 在线测评 (认知/北森/SHL) ➔ 业务一面 ➔ 业务二面/交叉面 ➔ HRG终面"
        tips = "【大厂通关】必考数据归因（GMV、ROI、转化率漏斗）。面试追问极深，务必带上真实业务操盘思考，严禁泛泛背诵。"
    elif "金融" in industry or "银行" in industry or any(k in company for k in ["银行", "证券"]):
        scale = "🏢 头部金融机构 / 国有大行 / 头部股份制行"
        salary = "💰 16w - 28w + 顶格公积金 + 丰厚节假日金 + 极高职业起点"
        process = "🎯 统一网申 ➔ 全国机考统考 (行测+英语+经济基础) ➔ 无领导小组讨论 ➔ 结构化半结构化面试"
        tips = "【金融通关】全国统考机考刷题是生死线，提前刷行测与综合知识！绿色金融与数字化方向极其欢迎建筑与理工科复合人才。"
    elif any(k in pos_str for k in ["管培", "培训生", "gmt", "uflp", "sgp", "特训生"]):
        scale = "🏢 行业龙头集团战略管培计划 / 关键核心业务梯队"
        salary = "💰 16w - 28w + 定制轮岗培养 + 高管带教 + 快速晋升通道"
        process = "🎯 官网网申 ➔ 认知/逻辑能力测评 ➔ 商业实战无领导小组讨论 ➔ 高管复试/终面"
        tips = "【管培通关】不限专业重点考察商业通识、高抗压学习敏锐度与全局战略思考。面试紧扣京东采销与新东方实际经营案例，展示超越同龄人的实干闭环！"

    if any(k in pos_str for k in ["施工"]):
        salary = "💰 12w - 18w + 包吃住 + 项目安全绩效"
        process = "🎯 宣讲初试 ➔ 简单复试 ➔ 现场签约"
        tips = "【避坑】工程施工一线环境艰苦、流动性极大，郑大建筑专硕去施工性价比偏低，建议仅作为保底备选。"

    return scale, salary, process, tips


def generate_synthesized_jd(company, industry, positions, tier, tags):
    """为缺少详细 JD 的岗位智能合成高价值岗位职责、任职要求与 ATS 建议"""
    pos_str = "、".join(positions)
    resps = []
    quals = []
    ats = []

    if "建筑/低碳对口" in tags or "央国企" in industry:
        resps = [
            f"负责【{company}】重大工程或绿色示范项目的方案设计管理、工程策划或技术落地统筹；",
            "协同推进绿色建筑、近零能耗、装配式与智能建造方案策划与物理环境性能核算；",
            "参与工程数字化与BIM协同交底，配合产出高水平技术方案与行业科研/专利申报；",
            "对接业主与多专业团队，把控项目全生命周期设计品质与成本平衡。"
        ]
        quals = [
            "2026/2027届硕士毕业生，建筑学、建筑技术科学、土木工程等对口专业；",
            "熟悉绿色建筑标准规范，具备扎实的设计审美功底与工程逻辑；",
            "掌握相关专业工具（如CAD/Revit/BIM或绿色建筑物理环境分析工具）；",
            "踏实严谨，具备出色的抗压素养与团队协作沟通能力。"
        ]
        ats = ["绿色建筑", "建筑设计", "低碳节能", "方案管理", "工程协同", "BIM数字化"]
    elif "互联网运营" in tags:
        resps = [
            f"负责【{company}】核心平台品类运营、商家成长运营或活动营销策略制定；",
            "深入分析业务大盘与用户/商家行为数据，针对冷启破零与动销进行全链路撬动；",
            "负责大促活动节点规划、排期推进与多业务部门协同；",
            "沉淀行业运营方法论与标准化经营SOP，输出复盘报告。"
        ]
        quals = [
            "2026/2027届毕业生，不限专业，具备强烈的自驱力与商业敏感度；",
            "具备扎实的数据分析能力（熟悉Excel数据透视、SQL基础更佳）；",
            "优秀的沟通谈判与跨部门推动能力，能抗压且结果导向。"
        ]
        ats = ["平台运营", "商家分层", "GMV转化", "数据透视", "活动策划", "商业化"]
    elif "AI非技术" in tags:
        resps = [
            f"深度参与【{company}】前沿大模型或AI应用产品的体验评测与用户反馈闭环；",
            "负责高质量微调数据集（SFT）的构建、数据清洗标注规则梳理与质检；",
            "跟踪评估Prompt提示词效果，协助算法与研发团队优化模型输出质量；",
            "参与AI产品社区生态运营与典型落地场景挖掘。"
        ]
        quals = [
            "重点院校本硕毕业生，不限专业，对生成式AI与大模型应用极具探索热情；",
            "极强的逻辑思辨、细节敏锐度与文字归纳能力；",
            "高频使用ChatGPT/Claude/DeepSeek等大模型工具者优先。"
        ]
        ats = ["AI产品运营", "Prompt工程", "微调数据清洗", "体验评测", "大模型落地"]
    else:
        resps = [
            f"负责【{company}】政企大客户、产业客户的商务关系开拓、客情维护与需求挖掘；",
            "主导商务谈判、方案宣讲与招投标合同签约全流程；",
            "协调公司内部售前及交付资源，确保客户满意度与业务续签；",
            "持续追踪区域市场竞品动态，开拓新型商务合作机会。"
        ]
        quals = [
            "本科及以上学历，不限专业，理工科与经管复合背景优先；",
            "优秀的商务交际与人际洞察力，善于与各层级客户决策人打交道；",
            "极强的抗压抗挫素养与强烈的赚钱成就动机。"
        ]
        ats = ["大客户销售", "ToB商务", "招投标", "客户关系", "商务谈判", "解决方案"]

    return {
        "responsibilities": resps,
        "qualifications": quals,
        "candidate_advantage": f"结合郑大建筑专硕211学历底色，在面对【{company}】的{pos_str}时，无论在结构化逻辑思维还是严谨度上均具备差异化竞争优势。",
        "ats_keywords": ats
    }


def evaluate_job(job):
    """智能分级核心算法 (S / A / B / C)"""
    industry = job.get("industry") or "其他"
    company = job.get("company") or ""
    positions = job.get("positions") or []
    pos_str = " ".join(positions).lower()
    full_str = f"{company} {industry} {pos_str}".lower()

    # 1. 过滤纯计算机硬核底层代码开发
    is_pure_code = any(kw in pos_str for kw in PURE_DEV_EXCLUDES)
    has_save_word = any(kw in pos_str for kw in ["运营", "产品", "销售", "建筑", "设计", "管培", "商业化", "策划"])
    if is_pure_code and not has_save_word:
        return "C", "纯底层代码开发，不符合通识与跨界求职意向", []

    matched_tags = []
    is_arch = any(kw in full_str for kw in ARCH_TECH_KEYWORDS)
    is_internet_op = any(kw in full_str for kw in INTERNET_OP_KEYWORDS)
    is_ai_nontech = any(kw in full_str for kw in AI_NONTECH_KEYWORDS)
    is_tob_sales = any(kw in full_str for kw in TOB_SALES_KEYWORDS)
    is_soe_general = any(kw in full_str for kw in SOE_GENERAL_KEYWORDS)

    if is_arch:
        matched_tags.append("建筑/低碳对口")
    if is_internet_op:
        matched_tags.append("互联网运营")
    if is_ai_nontech:
        matched_tags.append("AI非技术")
    if is_tob_sales:
        matched_tags.append("ToB销售/招商")
    if is_soe_general:
        matched_tags.append("管培/综合")

    # S 级判断
    if industry == "央国企" and is_arch:
        return "S", "央国企专业对口：郑大建筑专硕主场优势，具备绿色低碳与工程科技绝对壁垒", matched_tags

    if (industry in ["互联网", "快消/零售", "高端制造"]) and any(kw in pos_str for kw in ["电商运营", "类目运营", "商家运营", "商业化运营", "采销管培"]):
        return "S", "大厂核心商业运营：深度匹配电商商家与产业带运营模型，高含金量跨界首选", matched_tags

    # A 级判断
    if industry in ["互联网", "高端制造", "智能汽车", "消费快消", "金融银行"] and (is_internet_op or is_ai_nontech or "运营" in pos_str or "产品" in pos_str or "管培" in pos_str):
        return "A", "名企通识核心业务池：核心运营/管培生岗位，发展天花板与起薪优渥", matched_tags

    if industry == "央国企" and (is_tob_sales or is_soe_general or "招商" in pos_str or "营销" in pos_str or "销售" in pos_str or "管培" in pos_str):
        return "A", "央国企优质平台：大客户招商/销售与综合管培生，稳定度高且晋升通道明确", matched_tags

    if is_ai_nontech:
        return "A", "前沿AI非技术：紧跟AGI大模型产业落地，专业包容度高，成长空间巨大", matched_tags

    # B 级判断
    if is_tob_sales or is_internet_op or is_soe_general or "销售" in pos_str or "市场" in pos_str or "客户经理" in pos_str:
        return "B", "稳健扩充池：不限专业大客户销售/商业化拓展，适合广撒网保底", matched_tags

    if is_arch:
        return "B", "建筑/设计相关普通企业：设计或工程管理岗位，可作为备用选项", matched_tags

    return "C", "匹配度较低或偏离求职目标", matched_tags


def is_management_trainee_job(positions, tags, company="", industry=""):
    pos_str = " ".join(positions or []).lower()
    tag_str = " ".join(tags or []).lower()
    full_text = f"{company} {industry} {pos_str} {tag_str}".lower()
    mt_kws = ["管培", "培训生", "管理培训", "储备", "uflp", "sgp", "gmt", "特训生", "领航", "黑马", "领导力", "合伙人", "未来星"]
    return any(k in pos_str for k in mt_kws) or any("管培" in t for t in tags) or any(k in full_text for k in ["管培生", "管理培训生", "gmt", "uflp", "sgp"])


def classify_job_module(company, industry, positions, tags):
    comp = (company or "").strip()
    ind = (industry or "其他").strip()
    pos_str = " ".join(positions or [])
    tag_str = " ".join(tags or [])
    text = f"{comp} {ind} {pos_str} {tag_str}".lower()

    # 1. 外企（中国）
    foreign_kws = [
        "宝洁", "p&g", "玛氏", "mars", "联合利华", "unilever", "欧莱雅", "l'oreal", "loreal",
        "雀巢", "nestle", "施耐德", "schneider", "西门子", "siemens", "特斯拉", "tesla",
        "迪卡侬", "decathlon", "宜家", "ikea", "达能", "danone", "太古", "swire",
        "阿迪达斯", "adidas", "耐克", "nike", "飞利浦", "philips", "德意志银行", "德银",
        "汇丰", "渣打", "花旗", "百威", "budweiser", "百胜", "yum", "苹果", "apple",
        "外企", "外资", "跨国"
    ]
    if ind in ["外企(中国)", "外企（中国）", "外企", "外资"] or any(k.lower() in text for k in foreign_kws):
        return "外企（中国）"

    # 2. 央国企
    soe_kws = [
        "中建", "中国建筑", "中海", "华润", "保利", "招商蛇口", "金茂", "中国铁建", "中铁",
        "中国交建", "国家电网", "南方电网", "中国电信", "中国移动", "中国联通", "中国电科",
        "中粮", "中化", "中国建研院", "建研院", "京东方", "银行", "中信", "华泰", "央国企"
    ]
    if ind == "央国企" or any(k.lower() in text for k in soe_kws):
        return "央国企龙头"

    # 3. 互联网大厂
    internet_kws = [
        "阿里", "淘天", "腾讯", "字节", "bytedance", "美团", "京东", "拼多多", "快手",
        "小红书", "百度", "滴滴", "携程", "网易", "哔哩哔哩", "b站", "deepseek",
        "智谱", "minimax", "月之暗面", "高途", "新东方", "得物", "互联网"
    ]
    if ind == "互联网" or any(k.lower() in text for k in internet_kws):
        return "互联网大厂"

    # 4. 管培生计划专属
    if ind in ["管培生计划", "管培生", "管理培训生"]:
        return "管培生计划"

    # 5. 全品类头部大厂 (智能汽车/高端制造/消费快消/科技企服)
    return "全品类头部大厂"


def generate_markdown_report(ranked_jobs, tracking_db, removed_ids, featured_jobs, daily_inbox_jobs=None):
    """生成详尽的 Markdown 追踪总台账 (实战追踪 + 每日精选待审仓 + 五大分类模块专区)"""
    if daily_inbox_jobs is None:
        daily_inbox_jobs = []
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 动态推断待审仓日期跨度
    inbox_dates = [j.get("date_released") for j in daily_inbox_jobs if j.get("date_released")]
    if inbox_dates:
        min_d = min(inbox_dates)
        max_d = max(inbox_dates)
        min_str = min_d[5:].lstrip("0").replace("-", ".") if len(min_d) >= 10 else min_d
        max_str = max_d[5:].lstrip("0").replace("-", ".") if len(max_d) >= 10 else max_d
        inbox_date_window = min_str if min_str == max_str else f"{min_str}-{max_str}"
    else:
        now = datetime.now()
        inbox_date_window = f"{(now - timedelta(days=1)).strftime('%m.%d')}-{now.strftime('%m.%d')}"
    active_jobs = [j for j in ranked_jobs if j["id"] not in removed_ids]

    # 分离实战已投递 与 纯未投递（实施企业级全向严格隔离）
    delivered_jobs = []
    unapplied_jobs = []
    applied_company_keywords = set()
    for jid, dinfo in tracking_db.items():
        if dinfo.get("status") != "待投递":
            comp_name = jid.split("_")[0].strip().lower()
            applied_company_keywords.add(comp_name)

    for j in active_jobs:
        dinfo = tracking_db.get(j["id"], {})
        st = dinfo.get("status", j.get("status", "待投递"))
        has_applied = (st != "待投递")

        # 只要企业已在投递追踪中，不论岗位变体，一律不在未投递池中出现
        comp_clean = j.get("company", "").strip().lower()
        is_company_applied = any(ck in comp_clean or comp_clean in ck for ck in applied_company_keywords)

        if has_applied:
            delivered_jobs.append(j)
        elif not is_company_applied:
            unapplied_jobs.append(j)

    # 未投递各模块细分
    mt_unapplied = [j for j in unapplied_jobs if is_management_trainee_job(j.get("positions", []), j.get("tags", []), j.get("company", ""), j.get("industry", ""))]
    foreign_unapplied = [j for j in unapplied_jobs if classify_job_module(j.get("company",""), j.get("industry",""), j.get("positions",[]), j.get("tags",[])) == "外企（中国）"]
    internet_unapplied = [j for j in unapplied_jobs if classify_job_module(j.get("company",""), j.get("industry",""), j.get("positions",[]), j.get("tags",[])) == "互联网大厂"]
    consumer_auto_unapplied = [j for j in unapplied_jobs if classify_job_module(j.get("company",""), j.get("industry",""), j.get("positions",[]), j.get("tags",[])) == "全品类头部大厂"]
    soe_unapplied = [j for j in unapplied_jobs if classify_job_module(j.get("company",""), j.get("industry",""), j.get("positions",[]), j.get("tags",[])) == "央国企龙头"]

    lines = []
    lines.append(f"# 🎯 秋招全景情报雷达与投递进度总台账 ({today_str})")
    lines.append(f"\n> 专属画像定制：**郑州大学211建筑专硕 ｜ 核心方向：商业运营/管培/ToB销售/AI非技术 + 建筑科技/双碳**\n")
    lines.append(f"- **🎯 实战投递追踪**：已记录 **{len(delivered_jobs)} 家**（在途高频推进 {len([j for j in delivered_jobs if tracking_db.get(j['id'],{}).get('status') not in ['已淘汰', '待投递']])} 家，已归档 {len([j for j in delivered_jobs if tracking_db.get(j['id'],{}).get('status') == '已淘汰'])} 家）")
    lines.append(f"- **⚡ 每日精选待审流**：**{len(daily_inbox_jobs)} 岗** ({inbox_date_window} 最新发布待手动决策分流)")
    lines.append(f"- **🌟 未投递正式可投库**：共 **{len(unapplied_jobs)} 岗**（已彻底剥离已投岗位，支持按五大模块专属浏览）")
    lines.append(f"  - 🎓 2027管培生计划 (不限专业)：{len(mt_unapplied)} 岗")
    lines.append(f"  - 🌍 外企（中国）名企：{len(foreign_unapplied)} 岗")
    lines.append(f"  - 🌐 互联网大厂：{len(internet_unapplied)} 岗")
    lines.append(f"  - 🚗 全品类头部大厂 / 消费制造：{len(consumer_auto_unapplied)} 岗")
    lines.append(f"  - 🏢 央国企航母：{len(soe_unapplied)} 岗")
    lines.append(f"- **🖥️ 交互式作战看板**：[秋招雷达与进度看板.html](./秋招雷达与进度看板.html) （支持待审流转仓与五大模块独立筛选查看）\n")

    # 第一部分：实战已投递总台账
    lines.append(f"## 📌 第一部分：我的实战投递合计追踪总台账 (已记录 {len(delivered_jobs)} 家)\n")
    lines.append("| 序号 | 公司名称 | 岗位方向 | 投递渠道 | 投递日期 | 当前状态/阶段 | 个人实战备注 | 🚨 核心行动提醒与应对策略 |")
    lines.append("|:---:|:---|:---|:---:|:---:|:---:|:---|:---|")
    for idx, dj in enumerate(delivered_jobs, 1):
        dinfo = tracking_db.get(dj["id"], {})
        st = dinfo.get("status", dj.get("status", "推进中"))
        stage = dinfo.get("stage", dj.get("stage_detail", st))
        dt = dinfo.get("applied_date", "2026-09")
        ch = dinfo.get("channel", dj.get("batch", "官网网申"))
        notes = dinfo.get("notes", dj.get("notes", ""))
        rem = dinfo.get("reminders", "")
        lines.append(f"| {idx} | **{dj.get('company')}** | {'、'.join(dj.get('positions', []))} | {ch} | {dt} | `{st}`<br>({stage}) | {notes} | **{rem}** |")
    lines.append("\n---\n")

    # 第二部分：9.19-9.20 每日精选待审仓
    if daily_inbox_jobs:
        lines.append(f"## ⚡ 第二部分：每日精选待审仓 ({inbox_date_window} 8:00 最新发布，共 {len(daily_inbox_jobs)} 岗待手动分流)\n")
        lines.append("> 提示：打开本地 HTML 看板可一键点击【入库管培生计划】/【入库外企(中国)】/【入库互联网大厂】/【入库全品类大厂】/【入库央国企】手动分配入库\n")
        lines.append("| 序号 | 公司名称 | 建议板块 | 官方官宣公告原帖 | 目标岗位 | 薪酬待遇预估 | 发布日期 | 考评避坑与核心策略 | 官方直聘网申 |")
        lines.append("|:---:|:---|:---:|:---|:---|:---:|:---|:---:|")
        for idx, ij in enumerate(daily_inbox_jobs, 1):
            scale = ij.get("scale_badge", "行业名企")
            sal = ij.get("salary_range", "公允薪资")
            url = ij.get("apply_url") or ""
            url_md = f"[🚀 官方直聘]({url})" if url and url.startswith("http") else "见官网"
            pos = "<br>".join(ij.get("positions") or ["通用"])
            drel = ij.get("date_released", "9.17-9.18")
            tips = ij.get("tips_and_pitfalls", ij.get("reason", ""))
            mod = ij.get("recommended_module", "全品类头部大厂")
            ann_title = ij.get("announcement_title", "官方校招公告")
            ann_url = ij.get("announcement_url") or ij.get("apply_url") or ""
            ann_link = f"[{ann_title}]({ann_url})" if ann_url else ann_title
            lines.append(f"| {idx} | **{ij.get('company')}** | `{mod}` | {ann_link} | {pos} | `{sal}` | `{drel}` | {tips} | {url_md} |")
        lines.append("\n---\n")

    # 第三部分：今日早8点算法精选未投岗位
    unapplied_featured = [j for j in featured_jobs if j["id"] in {x["id"] for x in unapplied_jobs}]
    if unapplied_featured:
        lines.append(f"## 🌟 第三部分：今日早8点算法精选未投岗位 (TOP {len(unapplied_featured)})\n")
        lines.append("| 序号 | 公司名称 | 所属板块 | 企业背景与规模 | 岗位方向 | 薪资福利预估 | 截止日期 | 考评避坑要点 | 官方直聘入口 |")
        lines.append("|:---:|:---|:---:|:---|:---|:---|:---:|:---|:---:|")
        for idx, fj in enumerate(unapplied_featured, 1):
            scale = fj.get("scale_badge", "行业名企")
            sal = fj.get("salary_range", "公允薪资")
            url = fj.get("apply_url") or ""
            url_md = f"[🚀 官方直聘]({url})" if url and url.startswith("http") else "见企业官网"
            pos = "<br>".join(fj.get("positions") or ["通用"])
            deadline = fj.get("deadline") or "招满即止"
            tips = fj.get("tips_and_pitfalls", fj.get("reason", ""))
            mod = classify_job_module(fj.get("company",""), fj.get("industry",""), fj.get("positions",[]), fj.get("tags",[]))
            lines.append(f"| {idx} | **{fj.get('company')}** | `{mod}` | `{scale}` | {pos} | `{sal}` | {deadline} | {tips} | {url_md} |")
        lines.append("\n---\n")

    def render_unapplied_table(title, job_list):
        if not job_list:
            return
        lines.append(f"\n## {title} ({len(job_list)} 岗)\n")
        lines.append("| 序号 | 公司名称 | 建议等级 | 目标岗位 | 薪资福利预估 | 工作地点 | 截止日期 | 考评避坑要点 | 官方直达网申 |")
        lines.append("|:---:|:---|:---:|:---|:---|:---:|:---|:---:|")
        for idx, j in enumerate(job_list, 1):
            url = j.get("apply_url") or ""
            url_md = f"[🚀 直达网申]({url})" if url and url.startswith("http") else "官网/微信"
            pos = "<br>".join(j.get("positions") or ["通用"])
            sal = j.get("salary_range", "面议")
            loc = "、".join(j.get("locations") or ["全国"])
            deadline = j.get("deadline") or "招满即止"
            tips = j.get("tips_and_pitfalls", j.get("reason", ""))
            lines.append(f"| {idx} | **{j.get('company')}** | `{j.get('tier')}级` | {pos} | `{sal}` | {loc} | {deadline} | {tips} | {url_md} |")

    render_unapplied_table("🎓 第四部分：未投递精选 · 2027管培生计划 (不限专业) 专区", mt_unapplied)
    render_unapplied_table("🌍 第五部分：未投递精选 · 外企（中国）高薪名企专区", foreign_unapplied)
    render_unapplied_table("🌐 第六部分：未投递精选 · 互联网大厂专区", internet_unapplied)
    render_unapplied_table("🚗 第七部分：未投递精选 · 全品类头部大厂与消费制造专区", consumer_auto_unapplied)
    render_unapplied_table("🏢 第八部分：未投递精选 · 央国企航母专区", soe_unapplied)

    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[+] Markdown 分区总台账已生成: {OUTPUT_MD_PATH}")
    try:
        parent_md = REPO_ROOT.parent / "秋招每日岗位追踪与投递台账.md"
        if REPO_ROOT.parent.exists():
            with open(parent_md, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"[+] 本地工作区总台账已更新: {parent_md}")
    except Exception:
        pass



def compute_nowclaw_daily_priority(ranked_jobs, tracking_db, removed_ids):
    """
    基于 nowclaw-job-match 技能规范 (daily-priority.md 与 deep-match.md) 算法生成今日优先投递清单 (TOP 5):
    1. 严格排查已投递/淘汰企业与已废弃岗位 (物理隔离)
    2. 硬资格核查: 2026/2027 届、硕士通用对口、真实有效官网网申链接
    3. 综合加权评分与多赛道跨度覆盖:
       - 央国企高精尖科技/管培
       - 双碳与建筑工程数字化
       - 互联网大厂非技术/商业化运营
       - 外企高潜管理培训生
       - 新能源/智能制造高端ToB业务
    """
    applied_company_clean_names = set()
    for jid, t_info in tracking_db.items():
        st = t_info.get("status")
        if st and st != "待投递":
            comp = jid.split("_")[0].strip()
            for ch in [" ", "(", ")", "（", "）", '"', "'", "“", "”"]:
                comp = comp.replace(ch, "")
            if comp:
                applied_company_clean_names.add(comp.lower())

    def is_applied(company):
        clean = (company or "").lower()
        for ch in [" ", "(", ")", "（", "）", '"', "'", "“", "”"]:
            clean = clean.replace(ch, "")
        return any(ac in clean or clean in ac for ac in applied_company_clean_names)

    # 优先目标名企库 (精准匹配郑大建筑专硕四大核心发展跑道)
    priority_blueprints = [
        {
            "match_kw": "华润置地",
            "track": "🏛️ 央国企高精尖 · 设计管理与数字化",
            "rank": 1,
            "match_score": 99,
            "reason": "央企综合地产龙头核心管培，业务涵盖城市综合体、设计管理与工程数字化，与郑大专硕人设完美重合，晋升清晰。",
            "action": "重点突出专硕科研论文成果、绿色建筑与BIM应用案例；群面中主导逻辑框架梳理（STAR法则）。",
            "urgency": "🔥 2027届重点攻坚批次"
        },
        {
            "match_kw": "建筑科学研究院",
            "track": "🌱 双碳与建筑科技 · 国家级智库编制",
            "rank": 2,
            "match_score": 98,
            "reason": "住房与城乡建设部直属科技智库，建筑低碳咨询与智能建造最对口单位，学术与行业公信力顶尖，解决核心落户与编制发展。",
            "action": "准备硕士期间建筑性能模拟（EnergyPlus/Ecotect）、绿色评价标准及科研学术成果集。",
            "urgency": "🔥 智库秋招抢位期"
        },
        {
            "match_kw": "阿里巴巴",
            "track": "🌐 互联网大厂 · 核心电商与商业化运营",
            "rank": 3,
            "match_score": 97,
            "reason": "16大业务集团全面开放非技术业务池，类目运营与产业带招商重逻辑与资源协同，平台薪酬高且跨界发展空间大。",
            "action": "使用通用运营模板，突出量化指标拆解、大促运营复盘与用户全生命周期运营经验。",
            "urgency": "⚡ 阿里秋招核心批次"
        },
        {
            "match_kw": "欧莱雅",
            "track": "🌍 顶级外企 · 商业全渠道管理培训生",
            "rank": 4,
            "match_score": 96,
            "reason": "全球快消零售黄埔军校，MT轮岗体系健全，包容理工科跨界视野，重视商业敏锐度与高潜领导力。",
            "action": "重点展现自驱力、商业洞察与跨部门敏捷沟通能力，提炼校园大型活动统筹领导力（STAR法则）。",
            "urgency": "⚡ 外企MT秋招黄金期"
        },
        {
            "match_kw": "宁德时代",
            "track": "⚡ 新能源制造 · 全球ToB商务与供应链",
            "rank": 5,
            "match_score": 95,
            "reason": "全球锂电与储能绝对龙头，海外与国内核心产业出海扩张，ToB大客户商务经理需要工科底蕴与综合商务协调。",
            "action": "突出理工科综合分析底蕴、大型商务沟通谈判意识与抗压开拓自驱力。",
            "urgency": "⚡ 绿色能源出海急聘"
        }
    ]

    selected_top5 = []
    used_ids = set()

    # 第一轮：定向从 ranked_jobs 中寻找命中蓝图的高契合岗位
    for bp in priority_blueprints:
        kw = bp["match_kw"]
        found = None
        for j in ranked_jobs:
            if j["id"] in removed_ids or j["id"] in used_ids:
                continue
            if is_applied(j.get("company", "")):
                continue
            if kw in j.get("company", ""):
                found = j
                break
        if found:
            used_ids.add(found["id"])
            item = dict(found)
            item["priority_rank"] = bp["rank"]
            item["match_score"] = bp["match_score"]
            item["track_label"] = bp["track"]
            item["priority_reason"] = bp["reason"]
            item["next_step_action"] = bp["action"]
            item["urgency_badge"] = bp["urgency"]
            selected_top5.append(item)

    # 第二轮：若未满5席，按 nowclaw-job-match 算法从其余有效S级/A级岗位中加权补齐
    if len(selected_top5) < 5:
        backup_candidates = []
        for j in ranked_jobs:
            jid = j["id"]
            if jid in removed_ids or jid in used_ids:
                continue
            if is_applied(j.get("company", "")):
                continue
            apply_url = j.get("apply_url", "")
            if not (apply_url and apply_url.startswith("http")):
                continue
            score = 0
            if j.get("tier") == "S": score += 40
            elif j.get("tier") == "A": score += 25
            if j.get("is_mt") or "管培" in " ".join(j.get("positions", [])): score += 20
            if j.get("module") in ["央国企", "双碳与建筑科技"]: score += 25
            backup_candidates.append((score, j))
        backup_candidates.sort(key=lambda x: x[0], reverse=True)
        for _, bj in backup_candidates:
            if len(selected_top5) >= 5:
                break
            used_ids.add(bj["id"])
            item = dict(bj)
            rk = len(selected_top5) + 1
            item["priority_rank"] = rk
            item["match_score"] = 96 - rk
            item["track_label"] = f"⭐ {item.get('module', '核心对口')} 重点批次"
            item["priority_reason"] = item.get("reason") or "根据 nowclaw-job-match 算法：硬资格已通过，业务高契合度且发展空间大。"
            item["next_step_action"] = "结合当前岗位核心要求定向改写经历，提炼STAR量化结果。"
            item["urgency_badge"] = "⚡ 优质生力军岗位"
            selected_top5.append(item)

    return selected_top5

def generate_html_dashboard(ranked_jobs, tracking_db, removed_ids, featured_jobs, daily_inbox_jobs=None):
    """生成【实战投递独立作战室】、【每日精选待审仓】与【未投递精选雷达】三主视图交互看板"""
    if daily_inbox_jobs is None:
        daily_inbox_jobs = []
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 动态推断待审仓日期跨度
    inbox_dates = [j.get("date_released") for j in daily_inbox_jobs if j.get("date_released")]
    if inbox_dates:
        min_d = min(inbox_dates)
        max_d = max(inbox_dates)
        min_str = min_d[5:].lstrip("0").replace("-", ".") if len(min_d) >= 10 else min_d
        max_str = max_d[5:].lstrip("0").replace("-", ".") if len(max_d) >= 10 else max_d
        inbox_date_window = min_str if min_str == max_str else f"{min_str}-{max_str}"
    else:
        now = datetime.now()
        inbox_date_window = f"{(now - timedelta(days=1)).strftime('%m.%d')}-{now.strftime('%m.%d')}"
    featured_ids = {j["id"] for j in featured_jobs}

    # 1. 深度收集所有已投递/已实战企业的核心关键词库，实施全网铁律级物理隔离
    applied_company_clean_names = set()
    for jid, t_info in tracking_db.items():
        st = t_info.get("status")
        if st and st != "待投递":
            comp = jid.split("_")[0].strip()
            for ch in [" ", "(", ")", "（", "）", '"', "'", "“", "”"]:
                comp = comp.replace(ch, "")
            if comp:
                applied_company_clean_names.add(comp.lower())

    frontend_data = []
    seen_delivered_ids = set()

    for j in ranked_jobs:
        jid = j["id"]
        t_info = tracking_db.get(jid, {})
        st = t_info.get("status", j.get("status", "待投递"))
        
        # 铁律：只要该企业已被投递/淘汰/考核，未投递的同名变体岗位绝对不在主库中冗余混淆！
        comp_clean = j.get("company", "").lower()
        for ch in [" ", "(", ")", "（", "）", '"', "'", "“", "”"]:
            comp_clean = comp_clean.replace(ch, "")
        
        is_comp_applied = any(ac in comp_clean or comp_clean in ac for ac in applied_company_clean_names)
        if st == "待投递" and is_comp_applied:
            continue
            
        if st != "待投递":
            seen_delivered_ids.add(jid)

        mod = classify_job_module(j.get("company", ""), j.get("industry", "其他"), j.get("positions", []), j.get("tags", []))
        is_mt = is_management_trainee_job(j.get("positions", []), j.get("tags", []), j.get("company", ""), j.get("industry", ""))
        is_foreign = (mod == "外企（中国）")
        frontend_data.append({
            "id": jid,
            "company": j.get("company", ""),
            "industry": j.get("industry", "其他"),
            "module": mod,
            "is_mt": is_mt,
            "is_foreign": is_foreign,
            "cohort": j.get("cohort", "2026/2027届"),
            "batch": j.get("batch", "正式批"),
            "positions": j.get("positions", []),
            "locations": j.get("locations", []),
            "deadline": j.get("deadline") or "招满即止",
            "apply_url": j.get("apply_url") or "",
            "tier": j.get("tier", "B"),
            "reason": j.get("reason", ""),
            "tags": j.get("tags", []),
            "scale_badge": j.get("scale_badge", "🏢 行业知名大中企业"),
            "salary_range": j.get("salary_range", "💰 14w - 22w + 绩效奖金"),
            "interview_process": j.get("interview_process", "🎯 简历初选 ➔ 在线笔试/测评 ➔ 业务面试 ➔ 终审"),
            "tips_and_pitfalls": j.get("tips_and_pitfalls", "【通关】结合自身结构化逻辑，充分展示胜任力与抗压执行力。"),
            "is_featured": jid in featured_ids,
            "is_custom": j.get("is_custom", False),
            "status": t_info.get("status", j.get("status", "待投递")),
            "stage": t_info.get("stage", j.get("stage_detail", "")),
            "applied_date": t_info.get("applied_date", ""),
            "channel": t_info.get("channel", ""),
            "notes": t_info.get("notes", j.get("notes", "")),
            "reminders": t_info.get("reminders", ""),
            "jd": j.get("jd", {})
        })

    clean_id_map = {
        '绝味食品': '绝味食品_2027绝星计划管培生',
        '安踏集团 (ANTA)': '安踏集团_2027极光工程零售管培生',
        '申迪集团 (Shendi Group)': '申迪集团_2027商业空间运营与规划管培生',
        '宣伟 (Sherwin-Williams)': '宣伟_2027商业管理培训生',
        '亿滋国际 (Mondelez)': '亿滋国际_2027TasteTheFuture管培生',
        '中国海油 (CNOOC)': '中国海油_2027综合管理与战略企划储备',
        '米哈游 (miHoYo)': '米哈游_2027商业化运营专员',
        '金山办公 (WPS)': '金山办公_2027商业运营管培生',
        '中国资源循环集团': '中国资源循环集团_2027综合管理企划管培生',
        '中国绿发投资集团 (CGDG)': '中国绿发投资集团_2027绿色建筑园区规划储备'
    }
    for item in daily_inbox_jobs:
        if not item.get("id"):
            comp = item.get("company", "")
            if comp in clean_id_map:
                item["id"] = clean_id_map[comp]
            else:
                def clean_str(s):
                    for ch in [' ', '(', ')', '（', '）', '"', "'", '“', '”']:
                        s = s.replace(ch, '')
                    return s
                comp_clean = clean_str(comp)
                pos = item.get("positions", [])
                p_str = pos[0] if isinstance(pos, list) and pos else str(pos or "")
                p_clean = clean_str(p_str)
                b_clean = clean_str(item.get("batch") or "")
                item["id"] = f"{comp_clean}_{p_clean}_{b_clean}"[:60].strip("_")

    # 补齐 tracking_db 中未在 ranked_jobs 原始匹配到的实战岗位，保证 47 席实战记录 100% 永久在线
    for jid, t_info in tracking_db.items():
        if jid not in seen_delivered_ids and t_info.get("status") and t_info.get("status") != "待投递":
            comp = t_info.get("company", jid.split("_")[0])
            pos = t_info.get("position", jid.split("_")[1] if "_" in jid else "核心岗位")
            frontend_data.append({
                "id": jid,
                "company": comp,
                "industry": t_info.get("industry", "重点行业"),
                "module": t_info.get("module", "实战投递"),
                "is_mt": "管培" in pos,
                "is_foreign": False,
                "cohort": "2026/2027届",
                "batch": t_info.get("batch", "正式批"),
                "positions": [pos],
                "locations": ["全国多地"],
                "deadline": "以系统流程为准",
                "apply_url": t_info.get("apply_url", ""),
                "tier": t_info.get("tier", "S"),
                "reason": "个人历史实战投递记录",
                "tags": ["实战在途"],
                "scale_badge": f"🏛️ {comp} · 实战推进中企业",
                "salary_range": "💰 薪资以录用为准",
                "interview_process": "🎯 简历初选 ➔ 笔试/测评 ➔ 业务面试 ➔ 终审",
                "tips_and_pitfalls": "【实战推进】密切关注邮件与短信测评通知。",
                "is_featured": True,
                "is_custom": False,
                "status": t_info.get("status", "已网申"),
                "stage": t_info.get("stage", ""),
                "applied_date": t_info.get("applied_date", ""),
                "channel": t_info.get("channel", "官方网申"),
                "notes": t_info.get("notes", ""),
                "reminders": t_info.get("reminders", ""),
                "jd": {}
            })

    initial_statuses_str = json.dumps({jid: info.get("status") for jid, info in tracking_db.items() if info.get("status")}, ensure_ascii=False)
    applied_comps_str = json.dumps(list(applied_company_clean_names), ensure_ascii=False)

    nowclaw_priority_jobs = compute_nowclaw_daily_priority(ranked_jobs, tracking_db, removed_ids)
    nowclaw_priority_json_str = json.dumps(nowclaw_priority_jobs, ensure_ascii=False)
    json_str = json.dumps(frontend_data, ensure_ascii=False)
    inbox_json_str = json.dumps(daily_inbox_jobs, ensure_ascii=False)
    removed_ids_str = json.dumps(list(removed_ids), ensure_ascii=False)

    html_code = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎯 秋招情报雷达与全流程作战室 3.9 ({today_str})</title>
  <style>
    :root {{
      --primary: #1e3a8a;
      --primary-hover: #1d4ed8;
      --primary-light: #3b82f6;
      --s-color: #dc2626;
      --s-bg: #fef2f2;
      --a-color: #d97706;
      --a-bg: #fffbeb;
      --b-color: #059669;
      --b-bg: #ecfdf5;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --accent: #f59e0b;
      --mod-mt: #7c3aed;
      --mod-mt-bg: #f5f3ff;
      --mod-foreign: #0284c7;
      --mod-foreign-bg: #f0f9ff;
      --mod-internet: #7e22ce;
      --mod-internet-bg: #faf5ff;
      --mod-auto: #0f766e;
      --mod-auto-bg: #f0fdfa;
      --mod-soe: #1d4ed8;
      --mod-soe-bg: #eff6ff;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    .container {{ max-width: 1540px; margin: 0 auto; }}

    header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 45%, #0284c7 100%);
      color: white;
      padding: 26px 34px;
      border-radius: 18px;
      margin-bottom: 20px;
      box-shadow: 0 12px 30px -5px rgba(15, 23, 42, 0.35);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .header-left h1 {{ font-size: 26px; font-weight: 800; display: flex; align-items: center; gap: 12px; }}
    .header-left p {{ margin-top: 6px; opacity: 0.92; font-size: 13.5px; }}
    .header-actions {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}

    .btn {{
      padding: 9px 18px;
      border-radius: 8px;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      text-decoration: none;
    }}
    .btn-add {{ background: #10b981; color: white; }}
    .btn-add:hover {{ background: #059669; }}
    .btn-secondary {{ background: rgba(255,255,255,0.18); color: white; backdrop-filter: blur(8px); }}
    .btn-secondary:hover {{ background: rgba(255,255,255,0.28); }}

    /* 顶层主视图切换导航：3栏响应式网格 */
    .view-switch-nav {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
    }}
    .nav-tab-btn {{
      background: #ffffff;
      border: 2px solid #e2e8f0;
      border-radius: 14px;
      padding: 16px 20px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      transition: all 0.2s ease;
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }}
    .nav-tab-btn:hover {{
      border-color: #93c5fd;
      background: #f8fafc;
      transform: translateY(-1px);
    }}
    .nav-tab-btn.active {{
      background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
      border-color: #1e3a8a;
      color: white;
      box-shadow: 0 8px 20px -3px rgba(30, 58, 138, 0.35);
    }}
    .nav-tab-left {{ display: flex; align-items: center; gap: 12px; }}
    .nav-tab-icon {{ font-size: 26px; }}
    .nav-tab-text {{ text-align: left; }}
    .nav-tab-title {{ font-size: 16px; font-weight: 800; }}
    .nav-tab-desc {{ font-size: 12px; opacity: 0.82; margin-top: 2px; }}
    .nav-tab-badge {{
      background: #eff6ff;
      color: #1d4ed8;
      font-size: 12.5px;
      font-weight: 800;
      padding: 5px 12px;
      border-radius: 20px;
      border: 1px solid #bfdbfe;
    }}
    .nav-tab-btn.active .nav-tab-badge {{
      background: rgba(255,255,255,0.22);
      color: white;
      border-color: rgba(255,255,255,0.35);
    }}
    .badge-inbox-highlight {{
      background: #ea580c !important;
      color: white !important;
      border-color: #f97316 !important;
      animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
      0% {{ transform: scale(1); }}
      50% {{ transform: scale(1.05); }}
      100% {{ transform: scale(1); }}
    }}

    /* 待审仓介绍横幅 */
    .inbox-intro-box {{
      background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
      border: 1px solid #fed7aa;
      border-left: 6px solid #ea580c;
      border-radius: 14px;
      padding: 18px 24px;
      margin-bottom: 22px;
      box-shadow: 0 4px 12px rgba(234, 88, 12, 0.08);
    }}

    /* 紧急待办呼叫卡片栏 */
    .emergency-callout-panel {{
      background: linear-gradient(135deg, #fffbeb 0%, #fef2f2 100%);
      border: 1px solid #fed7aa;
      border-left: 6px solid #f59e0b;
      border-radius: 14px;
      padding: 16px 20px;
      margin-bottom: 22px;
      box-shadow: 0 4px 12px rgba(245, 158, 11, 0.08);
    }}
    .callout-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}
    .callout-title {{
      font-size: 15px;
      font-weight: 800;
      color: #9a3412;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .callout-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    .callout-card {{
      background: white;
      border: 1px solid #fed7aa;
      padding: 12px 14px;
      border-radius: 10px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }}
    .callout-card-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
    .callout-comp {{ font-weight: 800; font-size: 14px; color: #0f172a; }}
    .callout-tag {{ background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 4px; }}
    .callout-text {{ font-size: 12px; color: #475569; line-height: 1.5; }}

    /* KPI 数据栏 */
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
    }}
    .stat-card {{
      background: var(--card-bg);
      padding: 16px 20px;
      border-radius: 12px;
      border: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }}
    .stat-card .label {{ font-size: 13px; color: var(--text-muted); font-weight: 600; display: flex; align-items: center; gap: 6px; }}
    .stat-card .value {{ font-size: 28px; font-weight: 800; margin-top: 4px; }}
    .card-mt {{ border-left: 4px solid var(--mod-mt); }}
    .card-foreign {{ border-left: 4px solid var(--mod-foreign); }}
    .card-soe {{ border-left: 4px solid var(--mod-soe); }}
    .card-internet {{ border-left: 4px solid var(--mod-internet); }}
    .card-auto {{ border-left: 4px solid var(--mod-auto); }}
    .card-feat {{ border-left: 4px solid var(--accent); }}
    .card-urgent {{ border-left: 4px solid var(--s-color); }}

    /* 工具与筛选栏 */
    .toolbar {{
      background: var(--card-bg);
      padding: 18px 24px;
      border-radius: 14px;
      border: 1px solid var(--border);
      margin-bottom: 24px;
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
      justify-content: space-between;
    }}
    .search-box {{ flex: 1; min-width: 280px; }}
    .search-input {{
      width: 100%;
      padding: 11px 16px;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 14px;
      outline: none;
    }}
    .search-input:focus {{ border-color: var(--primary-light); box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15); }}

    .filter-group {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
    .filter-btn {{
      padding: 8px 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: white;
      font-size: 13px;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.15s;
    }}
    .filter-btn:hover {{ background: #f1f5f9; }}
    .filter-btn.active {{ background: var(--primary); color: white; border-color: var(--primary); }}

    .filter-btn-mod {{ font-weight: 700; }}
    .filter-btn-mod.active[data-disc-mod="mt"] {{ background: var(--mod-mt); border-color: var(--mod-mt); color: white; }}
    .filter-btn-mod.active[data-disc-mod="foreign"] {{ background: var(--mod-foreign); border-color: var(--mod-foreign); color: white; }}
    .filter-btn-mod.active[data-disc-mod="internet"] {{ background: var(--mod-internet); border-color: var(--mod-internet); color: white; }}
    .filter-btn-mod.active[data-disc-mod="consumer_auto"] {{ background: var(--mod-auto); border-color: var(--mod-auto); color: white; }}
    .filter-btn-mod.active[data-disc-mod="soe"] {{ background: var(--mod-soe); border-color: var(--mod-soe); color: white; }}
    .filter-btn.btn-glow {{ background: #fef3c7; color: #b45309; border-color: #fde68a; font-weight: 700; }}
    .filter-btn.btn-glow.active {{ background: #d97706; color: white; border-color: #d97706; }}

    .tab-badge {{
      display: inline-block;
      padding: 1px 7px;
      font-size: 11px;
      font-weight: 700;
      border-radius: 10px;
      margin-left: 5px;
      background: #f1f5f9;
      color: #64748b;
      transition: all 0.15s;
    }}
    .filter-btn.active .tab-badge {{
      background: rgba(255, 255, 255, 0.28);
      color: white;
    }}
    .tab-badge.badge-pending {{
      background: #ffedd5;
      color: #c2410c;
    }}
    .tab-badge.badge-accepted {{
      background: #dcfce7;
      color: #15803d;
    }}
    .tab-badge.badge-rejected {{
      background: #f1f5f9;
      color: #64748b;
    }}
    .filter-btn.active .tab-badge.badge-pending,
    .filter-btn.active .tab-badge.badge-accepted,
    .filter-btn.active .tab-badge.badge-rejected {{
      background: rgba(255, 255, 255, 0.25);
      color: white;
    }}
    .btn-disp-sm {{
      background: white;
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      font-size: 11px;
      padding: 2px 7px;
      cursor: pointer;
      color: #334155;
      font-weight: 600;
      margin-right: 4px;
      transition: all 0.15s;
    }}
    .btn-disp-sm:hover {{
      background: #e2e8f0;
      color: #0f172a;
    }}

    /* 岗位卡片网格 */
    .job-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
      gap: 20px;
    }}
    .job-card {{
      background: var(--card-bg);
      border-radius: 14px;
      border: 1px solid var(--border);
      padding: 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .job-card:hover {{ transform: translateY(-2px); box-shadow: 0 12px 28px -4px rgba(0,0,0,0.08); }}
    .job-card.tier-S {{ border-top: 4px solid var(--s-color); }}
    .job-card.tier-A {{ border-top: 4px solid var(--a-color); }}
    .job-card.tier-B {{ border-top: 4px solid var(--b-color); }}

    .card-top {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }}
    .company-name {{ font-size: 18px; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}

    /* 模块专属徽章 */
    .module-badge {{
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 6px;
      font-weight: 700;
    }}
    .mod-外企（中国） {{ background: var(--mod-foreign-bg); color: var(--mod-foreign); border: 1px solid #bae6fd; }}
    .mod-管培生计划 {{ background: var(--mod-mt-bg); color: var(--mod-mt); border: 1px solid #ddd6fe; }}
    .mod-互联网大厂 {{ background: var(--mod-internet-bg); color: var(--mod-internet); border: 1px solid #e9d5ff; }}
    .mod-全品类头部大厂 {{ background: var(--mod-auto-bg); color: var(--mod-auto); border: 1px solid #99f6e4; }}
    .mod-央国企龙头 {{ background: var(--mod-soe-bg); color: var(--mod-soe); border: 1px solid #bfdbfe; }}
    .mt-tag {{ background: #ede9fe; color: #6d28d9; font-size: 11px; padding: 2px 7px; border-radius: 4px; font-weight: 800; border: 1px solid #c4b5fd; }}
    .foreign-tag {{ background: #e0f2fe; color: #0369a1; font-size: 11px; padding: 2px 7px; border-radius: 4px; font-weight: 800; border: 1px solid #7dd3fc; }}

    .featured-tag {{ background: linear-gradient(135deg, #fef3c7, #fed7aa); color: #c2410c; font-size: 11px; padding: 2px 7px; border-radius: 4px; font-weight: 800; border: 1px solid #fdba74; }}
    .custom-tag {{ background: #eff6ff; color: #1d4ed8; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 700; border: 1px solid #bfdbfe; }}
    .inbox-new-tag {{ background: #fff7ed; color: #ea580c; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 800; border: 1px solid #fed7aa; }}

    .badges {{ display: flex; gap: 6px; align-items: center; }}
    .badge {{ font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 600; }}
    .badge-S {{ background: var(--s-bg); color: var(--s-color); border: 1px solid rgba(220,38,38,0.2); }}
    .badge-A {{ background: var(--a-bg); color: var(--a-color); border: 1px solid rgba(217,119,6,0.2); }}
    .badge-B {{ background: var(--b-bg); color: var(--b-color); border: 1px solid rgba(5,150,105,0.2); }}

    .scale-bar {{
      font-size: 12px;
      color: #1e40af;
      background: #eff6ff;
      padding: 4px 10px;
      border-radius: 6px;
      margin-bottom: 10px;
      display: inline-block;
      font-weight: 600;
    }}
    .salary-bar {{
      font-size: 13px;
      color: #047857;
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      padding: 6px 12px;
      border-radius: 8px;
      margin-bottom: 12px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .positions-wrap {{ margin-bottom: 12px; }}
    .pos-pill {{
      display: inline-block;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      color: #1e293b;
      margin: 3px 4px 3px 0;
    }}
    .meta-line {{
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .tips-box {{
      background: #fdf4ff;
      border-left: 3px solid #d946ef;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 12px;
      color: #701a75;
      margin-bottom: 12px;
      line-height: 1.5;
    }}

    .reason-box {{
      background: #f8fafc;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 12.5px;
      color: #334155;
      margin-bottom: 16px;
      border-left: 3px solid #94a3b8;
    }}

    /* 实战追踪卡片专有高亮 */
    .tracking-memo-box {{
      background: #fffbeb;
      border: 1px solid #fde68a;
      padding: 12px 14px;
      border-radius: 8px;
      font-size: 13px;
      color: #92400e;
      margin-bottom: 14px;
      line-height: 1.6;
    }}
    .tracking-memo-top {{
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }}
    .tracking-stage-tag {{
      background: #fef3c7;
      color: #b45309;
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 12px;
      border: 1px solid #fde68a;
    }}
    .tracking-reminder-box {{
      margin-top: 8px;
      color: #991b1b;
      font-weight: 700;
      background: #fef2f2;
      padding: 8px 10px;
      border-radius: 6px;
      border: 1px solid #fecaca;
      font-size: 12.5px;
    }}

    .card-actions {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 14px;
      border-top: 1px solid #f1f5f9;
      gap: 10px;
      flex-wrap: wrap;
    }}

    /* 待审仓分流按钮组 */
    .inbox-dispatch-panel {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 12px 14px;
      border-radius: 10px;
      margin-top: 12px;
    }}
    .inbox-dispatch-label {{
      font-size: 12px;
      font-weight: 700;
      color: #475569;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .dispatch-btn-group {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }}
    .btn-disp {{
      padding: 6px 11px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s;
    }}
    .btn-disp-internet {{ background: #faf5ff; color: #7e22ce; border-color: #d8b4fe; }}
    .btn-disp-internet:hover {{ background: #7e22ce; color: white; }}
    .btn-disp-auto {{ background: #f0fdfa; color: #0f766e; border-color: #99f6e4; }}
    .btn-disp-auto:hover {{ background: #0f766e; color: white; }}
    .btn-disp-soe {{ background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }}
    .btn-disp-soe:hover {{ background: #1d4ed8; color: white; }}
    .btn-disp-ignore {{ background: #f1f5f9; color: #64748b; border-color: #cbd5e1; margin-left: auto; }}
    .btn-disp-ignore:hover {{ background: #fee2e2; color: #dc2626; border-color: #fecaca; }}

    .status-select {{
      padding: 7px 10px;
      border-radius: 6px;
      border: 1px solid var(--border);
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
    }}
    .status-待投递 {{ color: #64748b; background-color: #f8fafc; }}
    .status-已网申 {{ color: #1d4ed8; background-color: #eff6ff; border-color: #93c5fd; }}
    .status-笔试中 {{ color: #d97706; background-color: #fffbeb; border-color: #fde68a; }}
    .status-面试中 {{ color: #9333ea; background-color: #faf5ff; border-color: #d8b4fe; }}
    .status-已获Offer {{ color: #16a34a; background-color: #f0fdf4; border-color: #86efac; }}
    .status-已淘汰 {{ color: #64748b; background-color: #f1f5f9; border-color: #cbd5e1; }}

    .btn-group-right {{ display: flex; gap: 6px; align-items: center; }}
    .btn-jd {{
      background: #f1f5f9;
      color: #1e293b;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid #cbd5e1;
    }}
    .btn-jd:hover {{ background: #e2e8f0; }}

    .btn-apply {{
      background: var(--primary);
      color: white;
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .btn-apply:hover {{ background: var(--primary-hover); }}
    .btn-apply.disabled {{ background: #e2e8f0; color: #94a3b8; pointer-events: none; }}

    .btn-remove {{
      background: transparent;
      color: #94a3b8;
      border: none;
      font-size: 16px;
      cursor: pointer;
      padding: 4px;
      border-radius: 4px;
      line-height: 1;
    }}
    .btn-remove:hover {{ color: #ef4444; background: #fee2e2; }}

    /* 模态弹窗 */
    .modal-overlay {{
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 20px;
    }}
    .modal-box {{
      background: white;
      border-radius: 16px;
      width: 100%;
      max-width: 720px;
      max-height: 90vh;
      overflow-y: auto;
      padding: 28px;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
      position: relative;
    }}
    .modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 14px;
    }}
    .modal-title {{ font-size: 21px; font-weight: 700; color: #0f172a; }}
    .close-btn {{ font-size: 22px; cursor: pointer; color: #94a3b8; border: none; background: transparent; }}
    .close-btn:hover {{ color: #0f172a; }}

    .form-group {{ margin-bottom: 16px; }}
    .form-group label {{ display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: #334155; }}
    .form-control {{
      width: 100%;
      padding: 9px 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 13.5px;
      outline: none;
    }}
    .form-control:focus {{ border-color: var(--primary-light); box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }}
    textarea.form-control {{ min-height: 100px; resize: vertical; }}
    .form-row {{ display: flex; gap: 14px; }}
    .form-row .form-group {{ flex: 1; }}

    /* JD 详情展示 */
    .jd-section {{ margin-bottom: 18px; }}
    .jd-subtitle {{ font-size: 14px; font-weight: 700; color: #1e3a8a; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }}
    .jd-list {{ padding-left: 18px; font-size: 13.5px; color: #334155; line-height: 1.7; }}
    .tag-cloud {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }}
    .ats-chip {{ background: #eff6ff; color: #2563eb; padding: 3px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }}

    /* Toast 浮动提示 */
    .toast-popup {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #0f172a;
      color: white;
      padding: 12px 20px;
      border-radius: 10px;
      font-size: 13.5px;
      font-weight: 600;
      box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
      display: none;
      z-index: 9999;
      align-items: center;
      gap: 10px;
    }}
  
    /* ================= NowClaw 今日优先投递专区样式 ================= */
    .nowclaw-priority-showcase {{
      background: linear-gradient(135deg, #064e3b 0%, #065f46 60%, #047857 100%);
      border-radius: 14px;
      padding: 20px 24px;
      margin-bottom: 24px;
      color: white;
      box-shadow: 0 10px 25px -5px rgba(6, 78, 59, 0.35);
      border: 1px solid rgba(16, 185, 129, 0.4);
    }}
    .priority-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 18px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.15);
      padding-bottom: 12px;
    }}
    .priority-title {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 19px;
      font-weight: 800;
      letter-spacing: -0.02em;
    }}
    .priority-pill-tag {{
      background: rgba(16, 185, 129, 0.25);
      border: 1px solid rgba(52, 211, 153, 0.6);
      color: #6ee7b7;
      font-size: 11.5px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 20px;
    }}
    .priority-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }}
    .priority-card {{
      background: rgba(255, 255, 255, 0.98);
      color: #0f172a;
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
      transition: transform 0.2s, box-shadow 0.2s;
      border: 1px solid #e2e8f0;
    }}
    .priority-card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
    }}
    .priority-rank-badge {{
      position: absolute;
      top: -9px;
      left: 14px;
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      color: white;
      font-size: 11px;
      font-weight: 800;
      padding: 2px 10px;
      border-radius: 10px;
      box-shadow: 0 2px 6px rgba(217, 119, 6, 0.4);
    }}
    .priority-track-badge {{
      font-size: 11px;
      color: #047857;
      background: #ecfdf5;
      padding: 2px 8px;
      border-radius: 6px;
      font-weight: 600;
      display: inline-block;
      margin-top: 4px;
    }}
    .priority-card-title {{
      font-size: 16px;
      font-weight: 800;
      color: #0f172a;
      margin-top: 6px;
    }}
    .priority-card-pos {{
      font-size: 13px;
      color: #1e293b;
      font-weight: 600;
      margin: 6px 0;
      line-height: 1.4;
    }}
    .priority-card-reason {{
      font-size: 12px;
      color: #475569;
      background: #f8fafc;
      border-left: 3px solid #10b981;
      padding: 6px 8px;
      border-radius: 4px;
      margin: 8px 0;
      line-height: 1.5;
    }}
    .priority-card-action {{
      font-size: 11.5px;
      color: #0369a1;
      background: #f0f9ff;
      border: 1px dashed #bae6fd;
      padding: 6px 8px;
      border-radius: 4px;
      margin-bottom: 12px;
      line-height: 1.4;
    }}
    .priority-card-footer {{
      display: flex;
      gap: 8px;
      align-items: center;
      margin-top: auto;
    }}
    .btn-priority-apply {{
      flex: 1;
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      font-size: 12px;
      font-weight: 700;
      text-align: center;
      padding: 8px 10px;
      border-radius: 6px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
    }}
    .btn-priority-apply:hover {{ opacity: 0.95; }}
    .btn-priority-jd {{
      background: #f1f5f9;
      color: #334155;
      font-size: 12px;
      font-weight: 600;
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      cursor: pointer;
    }}
    .btn-priority-jd:hover {{ background: #e2e8f0; }}
    </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-left">
        <h1>🎯 2026/2027 秋招情报雷达与全流程作战室 3.9</h1>
        <p>个人专属画像：郑州大学建筑学专硕 ｜ 核心方向：全行业通识业务池（管培/运营/ToB销售/AI非技术）+ 建筑科技/双碳 ｜ 🕒 <strong>看板编译更新时间：{today_str}</strong></p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" onclick="openNowClawModal()" style="background: linear-gradient(135deg, #059669 0%, #047857 100%); color: white; border: none;" title="牛客 AI 求职助手 11 大能力已装载">🦞 牛客 AI 助手 (11大技能已装载)</button>
        <button class="btn btn-primary" onclick="openWebSearchModal()"  style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);" title="查看每日自动化网络检索运行机制与源站状态">🌐 每日全网检索 2027 最新秋招</button>
        <button class="btn btn-add" onclick="window.location.reload(true)" title="重新加载本地最新生成的数据">🔄 强制刷新 (F5)</button>
        <button class="btn btn-secondary" onclick="openAddModal()">➕ 录入新岗位</button>
        <button class="btn btn-secondary" onclick="openTrashModal()">🗑️ 回收站 (<span id="trashCount">0</span>)</button>
        <button class="btn btn-secondary" onclick="exportData()">💾 备份投递数据</button>
      </div>
    </header>

    <!-- 顶层主视图切换导航：三栏主选项卡 -->
    <div class="view-switch-nav">
      <button class="nav-tab-btn active" id="btnViewDiscovery" onclick="switchMainView('discovery')">
        <div class="nav-tab-left">
          <span class="nav-tab-icon">🌟</span>
          <div class="nav-tab-text">
            <div class="nav-tab-title">未投递·全网精选雷达</div>
            <div class="nav-tab-desc">纯净未投底池 · 分模块独立浏览</div>
          </div>
        </div>
        <span class="nav-tab-badge" id="badgeUnapplied">0 岗可投</span>
      </button>

      <button class="nav-tab-btn" id="btnViewInbox" onclick="switchMainView('inbox')">
        <div class="nav-tab-left">
          <span class="nav-tab-icon">⚡</span>
          <div class="nav-tab-text">
            <div class="nav-tab-title">每日精选待审仓</div>
            <div class="nav-tab-desc">{inbox_date_window}最新发布 · 手动分流决策</div>
          </div>
        </div>
        <span class="nav-tab-badge badge-inbox-highlight" id="badgeInbox">0 岗待决</span>
      </button>

      <button class="nav-tab-btn" id="btnViewTracking" onclick="switchMainView('tracking')">
        <div class="nav-tab-left">
          <span class="nav-tab-icon">🎯</span>
          <div class="nav-tab-text">
            <div class="nav-tab-title">我的实战投递合计面板</div>
            <div class="nav-tab-desc">在途推进 · 紧急待办 · 淘汰归档</div>
          </div>
        </div>
        <span class="nav-tab-badge" id="badgeApplied">0 家在途</span>
      </button>
    </div>

    <!-- ==================== 视图一：未投递·全网精选雷达 ==================== -->
    <div id="viewDiscovery">
      <div class="stats-bar">
        <div class="stat-card">
          <span class="label">🌟 未投递总可投池</span>
          <span class="value" id="statUnappliedTotal" style="color: var(--primary)">0</span>
        </div>
        <div class="stat-card card-mt">
          <span class="label">🎓 2027管培生(不限专业)</span>
          <span class="value" id="statUnappliedMt" style="color: var(--mod-mt)">0</span>
        </div>
        <div class="stat-card card-foreign">
          <span class="label">🌍 外企（中国）名企</span>
          <span class="value" id="statUnappliedForeign" style="color: var(--mod-foreign)">0</span>
        </div>
        <div class="stat-card card-internet">
          <span class="label">🌐 互联网大厂</span>
          <span class="value" id="statUnappliedInternet" style="color: var(--mod-internet)">0</span>
        </div>
        <div class="stat-card card-auto">
          <span class="label">🚗 全品类大厂 / 消费制造</span>
          <span class="value" id="statUnappliedAuto" style="color: var(--mod-auto)">0</span>
        </div>
        <div class="stat-card card-soe">
          <span class="label">🏢 央国企航母</span>
          <span class="value" id="statUnappliedSoe" style="color: var(--mod-soe)">0</span>
        </div>
        <div class="stat-card card-feat">
          <span class="label">🌟 早8点算法精选</span>
          <span class="value" id="statUnappliedFeat" style="color: var(--accent)">0</span>
        </div>
      </div>

      <!-- 🎯 牛客求职总管 & 岗位匹配 (nowclaw-job-match TOP 5) 驱动展示区 -->
      <div class="nowclaw-priority-showcase" id="nowclawPriorityShowcase">
        <div class="priority-header">
          <div>
            <div class="priority-title">
              <span>🎯 今日优先投递清单 (TOP 5)</span>
              <span class="priority-pill-tag">nowclaw-job-match 算法引擎驱动</span>
            </div>
            <p style="font-size: 13px; opacity: 0.92; margin-top: 4px;">
              基于硬资格严审、实战库物理隔离、截止紧迫度倒计时与郑大专硕人设加权，每日精选 TOP 5 天选机会。
            </p>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <button class="btn btn-secondary" style="background: rgba(255,255,255,0.15); color: white; border: 1px solid rgba(255,255,255,0.3); font-size: 12px; padding: 6px 12px;" onclick="openNowClawModal()">⚡ 查看 11 项技能矩阵</button>
          </div>
        </div>
        <div class="priority-grid" id="priorityCardsGrid">
          <!-- JS 动态渲染 NOWCLAW_PRIORITY_JOBS -->
        </div>
      </div>

      <div class="toolbar">
        <div class="search-box">
          <input type="text" id="discoverySearchInput" class="search-input" placeholder="🔍 搜索未投递岗位：公司、岗位、薪酬、城市或业务关键词 (如: 玛氏 / 欧莱雅 / 管培 / 阿里 / 运营 / 20w / 郑州 / 销售)...">
        </div>
        <div class="filter-group">
          <button class="filter-btn active" data-disc-mod="all">全部未投递</button>
          <button class="filter-btn filter-btn-mod" data-disc-mod="mt" style="color: #6d28d9; border-color: #c4b5fd;">🎓 2027管培生(不限专业)</button>
          <button class="filter-btn filter-btn-mod" data-disc-mod="foreign" style="color: #0284c7; border-color: #bae6fd;">🌍 外企（中国）</button>
          <button class="filter-btn filter-btn-mod" data-disc-mod="internet">🌐 互联网大厂</button>
          <button class="filter-btn filter-btn-mod" data-disc-mod="consumer_auto">🚗 全品类头部大厂</button>
          <button class="filter-btn filter-btn-mod" data-disc-mod="soe">🏢 央国企龙头</button>
          <button class="filter-btn btn-glow" data-disc-mod="featured">🌟 早8点精选</button>
          <button class="filter-btn" data-disc-mod="S">🌟 S 级天选</button>
          <button class="filter-btn" data-disc-mod="A">🔥 A 级突破</button>
          <button class="filter-btn" data-disc-mod="B">🛡️ B 级稳健</button>
        </div>
      </div>

      <div class="job-grid" id="discoveryGrid"></div>
    </div>

    <!-- ==================== 视图二：每日精选待审仓 (9.19-9.20 最新发布) ==================== -->
    <div id="viewInbox" style="display: none;">
      <div class="inbox-intro-box">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 10px;">
          <h2 style="font-size: 18px; font-weight: 800; color: #9a3412; display: flex; align-items: center; gap: 8px;">
            ⚡ {inbox_date_window} 8:00 最新公布秋招精选 · 待审流转仓
          </h2>
          <span style="font-size: 12.5px; background: #ea580c; color: white; padding: 4px 12px; border-radius: 14px; font-weight: 700;">
            待决策: <span id="inboxPendingCount">0</span> 岗
          </span>
        </div>
        <p style="font-size: 13.5px; color: #431407; line-height: 1.6;">
          💡 <strong>操作指引：</strong> 以下为系统为你精准挖掘的 {inbox_date_window} 最新秋招官方公告。岗位<strong>暂未直接混入主展示区</strong>，请点击卡片底部的分流按钮，手动将其录入到【<strong>🌐 互联网大厂</strong>】、【<strong>🚗 全品类头部大厂</strong>】或【<strong>🏢 央国企龙头</strong>】看板中，或点击【<strong>❌ 忽略</strong>】。录入后将自动同步至对应板块！
        </p>
      </div>

      <div class="toolbar" style="margin-bottom: 20px;">
        <div class="search-box">
          <input type="text" id="inboxSearchInput" class="search-input" placeholder="🔍 搜索待审仓岗位 (如: 绝味 / 安踏 / 宣伟 / 极氪 / 宝洁 / 字节)...">
        </div>
        <div class="filter-group">
          <button class="filter-btn active" data-inbox-filter="pending" id="tabInboxPending">
            ⏳ 待决策 <span class="tab-badge badge-pending" id="badgeTabPending">0</span>
          </button>
          <button class="filter-btn" data-inbox-filter="accepted" id="tabInboxAccepted">
            ✅ 已入库 <span class="tab-badge badge-accepted" id="badgeTabAccepted">0</span>
          </button>
          <button class="filter-btn" data-inbox-filter="rejected" id="tabInboxRejected">
            🚫 已忽略 <span class="tab-badge badge-rejected" id="badgeTabRejected">0</span>
          </button>
          <button class="filter-btn" data-inbox-filter="all" id="tabInboxAll">
            📋 全部候选 <span class="tab-badge badge-all" id="badgeTabAll">0</span>
          </button>
        </div>
      </div>

      <div class="job-grid" id="inboxGrid"></div>
    </div>

    <!-- ==================== 视图三：我的实战投递合计面板 ==================== -->
    <div id="viewTracking" style="display: none;">
      <!-- 紧急待办呼叫栏 -->
      <div class="emergency-callout-panel" id="emergencyCallout">
        <div class="callout-header">
          <div class="callout-title">🚨 核心在途紧急待办与关键行动倒计时</div>
          <span style="font-size: 12px; color: #c2410c; font-weight: 700;">系统自动识别重要红线</span>
        </div>
        <div class="callout-grid" id="emergencyGrid"></div>
      </div>

      <!-- 实战 KPI 数据栏 -->
      <div class="stats-bar">
        <div class="stat-card">
          <span class="label">🎯 累计投递总数</span>
          <span class="value" id="statTrackTotal" style="color: #1e3a8a">0</span>
        </div>
        <div class="stat-card card-soe">
          <span class="label">🚀 正在高频推进</span>
          <span class="value" id="statTrackActive" style="color: #2563eb">0</span>
        </div>
        <div class="stat-card card-internet">
          <span class="label">💼 面试/考核中</span>
          <span class="value" id="statTrackInterview" style="color: #9333ea">0</span>
        </div>
        <div class="stat-card card-urgent">
          <span class="label">🚨 待测评/紧急关注</span>
          <span class="value" id="statTrackExam" style="color: #dc2626">0</span>
        </div>
        <div class="stat-card">
          <span class="label">📁 已淘汰/归档翻篇</span>
          <span class="value" id="statTrackArchived" style="color: #64748b">0</span>
        </div>
      </div>

      <div class="toolbar">
        <div class="search-box">
          <input type="text" id="trackingSearchInput" class="search-input" placeholder="🔍 搜索我的实战投递记录 (如: 大疆 / 华润 / 蜜雪 / 理想 / OPPO / 宇通)...">
        </div>
        <div class="filter-group">
          <button class="filter-btn active" data-track-filter="all">全部已投 (<span id="btnCntAll">0</span>)</button>
          <button class="filter-btn" data-track-filter="active">🚀 正在推进中 (<span id="btnCntActive">0</span>)</button>
          <button class="filter-btn" data-track-filter="interview">💼 面试中 (<span id="btnCntInterview">0</span>)</button>
          <button class="filter-btn" data-track-filter="exam">🚨 待做测评 (<span id="btnCntExam">0</span>)</button>
          <button class="filter-btn" data-track-filter="archived">📁 已淘汰/归档 (<span id="btnCntArchived">0</span>)</button>
        </div>
      </div>

      <div class="job-grid" id="trackingGrid"></div>
    </div>

  </div>

  <!-- 浮动通知提示 -->
  <div class="toast-popup" id="toastPopup"></div>

  <!-- 录入新岗位 Modal -->
  <div class="modal-overlay" id="addModal">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title">➕ 个性化录入新岗位</div>
        <button class="close-btn" onclick="closeModal('addModal')">&times;</button>
      </div>
      <form id="addJobForm" onsubmit="handleJobSubmit(event)">
        <div class="form-row">
          <div class="form-group">
            <label>公司名称 *</label>
            <input type="text" id="addCompany" class="form-control" placeholder="例如: 中建三局绿建分公司" required>
          </div>
          <div class="form-group">
            <label>所属板块 / 行业 *</label>
            <select id="addIndustry" class="form-control">
              <option value="管培生计划">🎓 2027管培生计划 (不限专业)</option>
              <option value="外企(中国)">🌍 外企（中国）</option>
              <option value="互联网">🌐 互联网大厂</option>
              <option value="高端制造">🚗 高端制造/智能车企</option>
              <option value="消费快消">🛒 消费快消/新零售</option>
              <option value="央国企">🏢 央国企航母</option>
              <option value="其他">其他行业</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>岗位名称 (多个逗号隔开) *</label>
            <input type="text" id="addPositions" class="form-control" placeholder="例如: 品牌营销, 电商运营" required>
          </div>
          <div class="form-group">
            <label>工作地点</label>
            <input type="text" id="addLocations" class="form-control" placeholder="例如: 郑州、北京、上海">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>薪资范围预估</label>
            <input type="text" id="addSalary" class="form-control" placeholder="例如: 15w - 25w + 六险二金">
          </div>
          <div class="form-group">
            <label>匹配等级</label>
            <select id="addTier" class="form-control">
              <option value="S">🌟 S 级 (天选核心/强契合)</option>
              <option value="A">🔥 A 级 (重点突破/高价值)</option>
              <option value="B">🛡️ B 级 (稳健广投/保底)</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>截止日期</label>
            <input type="date" id="addDeadline" class="form-control">
          </div>
          <div class="form-group">
            <label>官方直达投递链接</label>
            <input type="url" id="addApplyUrl" class="form-control" placeholder="https://...">
          </div>
        </div>

        <div class="form-group">
          <label>岗位详细 JD / 职责与要求说明</label>
          <textarea id="addJdDesc" class="form-control" placeholder="粘贴岗位详细JD、任职要求或个人备注..."></textarea>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
          <button type="button" class="btn btn-secondary" onclick="closeModal('addModal')" style="color:#475569;">取消</button>
          <button type="submit" class="btn btn-add">确认录入岗位</button>
        </div>
      </form>
    </div>
  </div>

  <!-- JD 详细抽屉 Modal -->
  <div class="modal-overlay" id="jdModal">
    <div class="modal-box">
      <div class="modal-header">
        <div>
          <div class="modal-title" id="modalJdCompany"></div>
          <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;" id="modalJdSub"></div>
        </div>
        <button class="close-btn" onclick="closeModal('jdModal')">&times;</button>
      </div>
      <div id="modalJdContent"></div>
      <div style="margin-top: 24px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 16px;">
        <button class="btn btn-secondary" onclick="copyJdPrompt()" style="color: #1e293b;">📋 复制简历定制 Prompt</button>
        <a id="modalApplyBtn" href="#" target="_blank" class="btn btn-add">🚀 立即直达网申 ↗</a>
      </div>
    </div>
  </div>

  <!-- 回收站 Modal -->
  <div class="modal-overlay" id="trashModal">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title">🗑️ 已移除 / 屏蔽的岗位管理</div>
        <button class="close-btn" onclick="closeModal('trashModal')">&times;</button>
      </div>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
        以下为你主动移除的岗位，已在主看板中隐藏。如需恢复点击“恢复”即可。
      </p>
      <div id="trashList" style="max-height: 400px; overflow-y: auto;"></div>
    </div>
  </div>

  <!-- 全网实时网络检索状态与说明 Modal -->
  <div class="modal-overlay" id="webSearchModal">
    <div class="modal-box" style="max-width: 780px;">
      <div class="modal-header">
        <div class="modal-title" style="display: flex; align-items: center; gap: 8px;">
          🌐 2027 届秋招全网实时网络检索与真链收集引擎 (4.0)
        </div>
        <button class="close-btn" onclick="closeModal('webSearchModal')">&times;</button>
      </div>
      <div style="font-size: 14px; color: #334155; line-height: 1.7;">
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;">
          <h4 style="color: #166534; font-size: 15px; margin-bottom: 6px;">✅ 自动化网络检索系统现已全面就绪与挂载</h4>
          <p style="color: #15803d; font-size: 13px;">
            系统已完成升级，彻底告别单源死板抓取，接入多通道在线实时抓取与企业官方直聘真链校验自愈引擎！
          </p>
        </div>

        <h4 style="font-size: 15px; color: #0f172a; margin-bottom: 8px;">📡 正在持续监听的多源网络检索通道：</h4>
        <ul style="padding-left: 20px; font-size: 13.5px; color: #475569; margin-bottom: 16px;">
          <li><strong>通道 A（母校就业中心一手流）：</strong> 连线郑州大学就业创业网 (<code>job.zzu.edu.cn</code>)，每日追踪入校宣讲及双选会最新名企；</li>
          <li><strong>通道 B（央国企权威校招流）：</strong> 实时对接国聘网、国资小新及各大能源/建筑/金融央企官方招聘专栏；</li>
          <li><strong>通道 C（名企 ATS 直聘网申专区）：</strong> 动态探测覆盖 Moka、北森、大易、飞书等 150+ 顶尖名企直聘系统，100% 确保直达真实网申页面；</li>
          <li><strong>通道 D（全网关键词检索雷达）：</strong> 针对 2027 管培生、外企中国、低碳建筑、电商运营等高匹配方向实时深度扫网。</li>
        </ul>

        <h4 style="font-size: 15px; color: #0f172a; margin-bottom: 8px;">⏰ 每日自动化调度规则：</h4>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; font-size: 13px; color: #475569; margin-bottom: 16px;">
          • <strong>每天早上 08:00</strong> 自动静默唤醒并执行网络爬取；<br>
          • 若电脑 8 点关机，<strong>开机唤醒后自动智能补跑</strong>；<br>
          • 自动排除 45 家已投企业，自动更新待审流转仓与雷达大底池，并通过 Windows 桌面原生 Toast 弹窗通知你！
        </div>

        <h4 style="font-size: 15px; color: #0f172a; margin-bottom: 8px;">⚡ 手动即时触发方式：</h4>
        <p style="font-size: 13px; color: #64748b; margin-bottom: 12px;">
          你可随时在终端运行 <code>python .agents/skills/campus-job-tracker/scripts/daily_web_recruitment_collector.py</code>，或直接对 AI 助手输入 <strong>“执行全网秋招检索”</strong>，系统将立即联网刷新并编译看板！
        </p>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; border-top: 1px solid #f1f5f9; padding-top: 14px;">
        <button type="button" class="btn btn-primary" onclick="closeModal('webSearchModal')">我知道了</button>
      </div>
    </div>
  </div>

  <script>
    function openNowClawModal() {{
      document.getElementById('nowclawModal').style.display = 'flex';
    }}

    function copyNowClawPrompt(type) {{
      if (!currentViewingJob) return;
      const comp = currentViewingJob.company || '';
      const pos = (currentViewingJob.positions || []).join('、');
      let prompt = '';
      if (type === 'brief') {{
        prompt = `使用牛客AI求职助手，帮我进行【${{comp}}】面试前公司速查。请基于其近期校招与商业动态，分析核心业务方向、企业风格文化、面试考核偏好与重要避坑提示。`;
      }} else if (type === 'interview') {{
        prompt = `使用牛客AI求职助手，针对【${{comp}}】的【${{pos}}】岗位，开启定向模拟面试。结合郑大建筑专硕背景，为我预测5道高频必考核心业务与综合情景面试题，并提供参考答题要点。`;
      }} else if (type === 'tailor') {{
        prompt = `使用牛客AI求职助手与简历定制技能，针对【${{comp}}】的【${{pos}}】岗位，深度拆解JD关键词，结合我的背景进行定向简历针对性优化与差距补齐建议。`;
      }}
      navigator.clipboard.writeText(prompt).then(() => {{
        alert(`已成功复制牛客 AI 指令到剪贴板！\n\n直接在 Antigravity 对话框中粘贴发送即可：\n"${{prompt}}"`);
      }}).catch(() => {{
        window.prompt('请复制以下指令到对话中使用：', prompt);
      }});
    }}

    function openWebSearchModal() {{
      document.getElementById('webSearchModal').style.display = 'flex';
    }}
    let ALL_JOBS = {json_str};
    let DAILY_INBOX_JOBS = {inbox_json_str};
    let NOWCLAW_PRIORITY_JOBS = {nowclaw_priority_json_str};
    let REMOVED_IDS = new Set({removed_ids_str});
    let currentMainView = 'discovery'; // 'discovery' | 'inbox' | 'tracking'
    const INITIAL_STATUSES = {initial_statuses_str};
    const APPLIED_COMPANIES = new Set({applied_comps_str});

    let currentDiscoveryModule = 'all';
    let currentDiscoverySearch = '';
    let currentTrackingFilter = 'all';
    let currentTrackingSearch = '';
    let currentInboxFilter = 'pending';
    let currentInboxSearch = '';
    let currentViewingJob = null;

    function getStoredStatuses() {{
      try {{
        const local = JSON.parse(localStorage.getItem('job_statuses') || '{{}}');
        return Object.assign({{}}, INITIAL_STATUSES, local);
      }} catch(e) {{
        return Object.assign({{}}, INITIAL_STATUSES);
      }}
    }}
    function saveStatus(id, newStatus) {{
      const map = getStoredStatuses();
      map[id] = newStatus;
      localStorage.setItem('job_statuses', JSON.stringify(map));

      const job = ALL_JOBS.find(x => x.id === id);
      const compName = job ? job.company : '该岗位';
      showToast(`已将【${{compName}}】状态更新为: ${{newStatus}}`);

      updateAllStatsAndRenders();
    }}

    function getInboxDecisions() {{
      try {{ return JSON.parse(localStorage.getItem('daily_inbox_decisions') || '{{}}'); }} catch(e) {{ return {{}}; }}
    }}

    function showToast(msg) {{
      const toast = document.getElementById('toastPopup');
      toast.innerText = msg;
      toast.style.display = 'flex';
      setTimeout(() => {{ toast.style.display = 'none'; }}, 2800);
    }}

    function getCustomJobs() {{
      try {{ return JSON.parse(localStorage.getItem('custom_jobs_extra') || '[]'); }} catch(e) {{ return []; }}
    }}

    function getRemovedSet() {{
      try {{
        const stored = JSON.parse(localStorage.getItem('removed_ids_extra') || '[]');
        stored.forEach(id => REMOVED_IDS.add(id));
      }} catch(e) {{}}
      return REMOVED_IDS;
    }}
    function addRemoved(id) {{
      REMOVED_IDS.add(id);
      localStorage.setItem('removed_ids_extra', JSON.stringify(Array.from(REMOVED_IDS)));
      updateAllStatsAndRenders();
    }}
    function restoreRemoved(id) {{
      REMOVED_IDS.delete(id);
      localStorage.setItem('removed_ids_extra', JSON.stringify(Array.from(REMOVED_IDS)));
      updateAllStatsAndRenders();
      renderTrashList();
    }}

    // 判断具体岗位是否已被实战投递（必须具备非“待投递”状态）
    function isJobDelivered(job, statusMap) {{
      const st = statusMap[job.id] || job.status;
      return !!(st && st !== '待投递');
    }}

    // 判断企业是否已在实战投递列表中（用于未投递池的全向绝对隔离，杜绝已投/已淘汰企业的任何变体出现）
    function isCompanyApplied(job, statusMap) {{
      if (isJobDelivered(job, statusMap)) return true;
      const comp = (job.company || '').toLowerCase().replace(/[\s()（）]/g, '');
      
      // 1. 深度匹配 APPLIED_COMPANIES 集合
      if (typeof APPLIED_COMPANIES !== 'undefined') {{
        for (const ac of APPLIED_COMPANIES) {{
          const cleanAc = ac.toLowerCase().replace(/[\s()（）]/g, '');
          if (cleanAc && (comp.includes(cleanAc) || cleanAc.includes(comp))) {{
            return true;
          }}
        }}
      }}

      // 2. 深度匹配 statusMap 中所有非待投递岗位
      for (const key of Object.keys(statusMap)) {{
        const st = statusMap[key];
        if (st && st !== '待投递') {{
          const compPrefix = key.split('_')[0].toLowerCase().replace(/[\s()（）]/g, '');
          if (compPrefix && (comp.includes(compPrefix) || compPrefix.includes(comp))) {{
            return true;
          }}
        }}
      }}

      // 3. 深度匹配 ALL_JOBS 中同名已交付岗位
      if (typeof ALL_JOBS !== 'undefined') {{
        const hasDelivered = ALL_JOBS.some(other => {{
          if (other.id === job.id) return false;
          const otherSt = statusMap[other.id] || other.status;
          if (otherSt && otherSt !== '待投递') {{
            const otherComp = (other.company || '').toLowerCase().replace(/[\s()（）]/g, '');
            return otherComp && (comp.includes(otherComp) || otherComp.includes(comp));
          }}
          return false;
        }});
        if (hasDelivered) return true;
      }}
      return false;
    }}

    // 保证岗位具有干净规范的唯一 ID
    function getJobId(j) {{
      if (j && j.id && j.id !== 'undefined') return j.id;
      const comp = (j.company || '').replace(/[()（）\s"']/g, '');
      const pos = Array.isArray(j.positions) ? j.positions[0] : (j.positions || '');
      const cleanPos = (pos || '').replace(/[()（）\s"']/g, '');
      const b = (j.batch || '').replace(/[()（）\s"']/g, '');
      return `${{comp}}_${{cleanPos}}_${{b}}`.replace(/^_+|_+$/g, '');
    }}

    // 数据清洗与存储自愈
    function sanitizeStorage() {{
      DAILY_INBOX_JOBS.forEach((j, idx) => {{ j.id = getJobId(j); }});
      ALL_JOBS.forEach((j, idx) => {{ j.id = getJobId(j); }});
      const decisions = getInboxDecisions();
      if (decisions['undefined']) {{
        delete decisions['undefined'];
        localStorage.setItem('daily_inbox_decisions', JSON.stringify(decisions));
      }}
    }}

    // 同步待审仓中已批准入库或已忽略的岗位至系统全局
    function syncInboxDecisionsToJobs() {{
      const decisions = getInboxDecisions();
      const removed = getRemovedSet();
      let changedRemoved = false;

      DAILY_INBOX_JOBS.forEach(ij => {{
        const d = decisions[ij.id];
        if (d && d.action === 'accepted') {{
          if (removed.has(ij.id)) {{
            removed.delete(ij.id);
            changedRemoved = true;
          }}
          const existing = ALL_JOBS.find(x => x.id === ij.id);
          if (existing) {{
            existing.module = d.module || ij.recommended_module || '全品类头部大厂';
            existing.status = existing.status || '待投递';
          }} else {{
            const jobCopy = Object.assign({{}}, ij, {{
              module: d.module || ij.recommended_module || '全品类头部大厂',
              status: '待投递',
              is_custom: true
            }});
            ALL_JOBS.unshift(jobCopy);
          }}
        }} else if (d && d.action === 'rejected') {{
          if (!removed.has(ij.id)) {{
            removed.add(ij.id);
            changedRemoved = true;
          }}
        }}
      }});

      if (changedRemoved) {{
        localStorage.setItem('removed_ids_extra', JSON.stringify(Array.from(removed)));
      }}
    }}

    // 手动分流入库操作（即点即入库，彻底移出待决策，实时更新各模块与角标）
    function dispatchInboxJob(id, targetModule) {{
      const decisions = getInboxDecisions();
      decisions[id] = {{ action: 'accepted', module: targetModule, time: new Date().toISOString() }};
      localStorage.setItem('daily_inbox_decisions', JSON.stringify(decisions));

      // 确保从黑名单中彻底移除
      if (REMOVED_IDS.has(id)) {{
        REMOVED_IDS.delete(id);
        localStorage.setItem('removed_ids_extra', JSON.stringify(Array.from(REMOVED_IDS)));
      }}

      const inboxJob = DAILY_INBOX_JOBS.find(x => x.id === id);
      if (inboxJob) {{
        let existing = ALL_JOBS.find(x => x.id === id);
        if (existing) {{
          existing.module = targetModule;
          existing.status = existing.status || '待投递';
        }} else {{
          const newJob = Object.assign({{}}, inboxJob, {{
            module: targetModule,
            status: '待投递',
            is_custom: true
          }});
          ALL_JOBS.unshift(newJob);
        }}
        showToast(`✅ 成功将【${{inboxJob.company}}】录入至【${{targetModule}}】！`);
      }}
      updateAllStatsAndRenders();
    }}

    // 忽略岗位操作（即点即移出待决策，双向写入黑名单与 decisions，主看板与刷新后彻底隐身）
    function ignoreInboxJob(id) {{
      const decisions = getInboxDecisions();
      decisions[id] = {{ action: 'rejected', time: new Date().toISOString() }};
      localStorage.setItem('daily_inbox_decisions', JSON.stringify(decisions));

      // 核心修复：双向写入 REMOVED_IDS，确保未投递主雷达与刷新后永久隔离过滤
      addRemoved(id);

      const idx = ALL_JOBS.findIndex(x => x.id === id);
      if (idx !== -1) {{
        ALL_JOBS.splice(idx, 1);
      }}
      showToast(`🚫 已忽略该岗位（已移至“已忽略”列表并从主看板永久隐身）`);
      updateAllStatsAndRenders();
    }}

    // 恢复已忽略岗位
    function restoreInboxJob(id) {{
      const decisions = getInboxDecisions();
      delete decisions[id];
      localStorage.setItem('daily_inbox_decisions', JSON.stringify(decisions));

      restoreRemoved(id);
      showToast(`↺ 已恢复该岗位至【待决策】流转仓`);
      updateAllStatsAndRenders();
    }}

    // 撤销入库决策（重新回到待决策流转仓）
    function undoInboxDecision(id) {{
      const decisions = getInboxDecisions();
      delete decisions[id];
      localStorage.setItem('daily_inbox_decisions', JSON.stringify(decisions));

      const idx = ALL_JOBS.findIndex(x => x.id === id && x.is_custom);
      if (idx !== -1) {{
        ALL_JOBS.splice(idx, 1);
      }}
      showToast(`↺ 已撤销入库，该岗位已重新回到【待决策】流转仓`);
      updateAllStatsAndRenders();
    }}

    // 快捷跳转至未投递主看板指定模块
    function goToDiscoveryModule(targetModule) {{
      switchMainView('discovery');
      let modKey = 'all';
      if (targetModule === '管培生计划') modKey = 'mt';
      else if (targetModule === '外企（中国）') modKey = 'foreign';
      else if (targetModule === '互联网大厂') modKey = 'internet';
      else if (targetModule === '全品类头部大厂') modKey = 'consumer_auto';
      else if (targetModule === '央国企龙头') modKey = 'soe';

      const btn = document.querySelector(`[data-disc-mod="${{modKey}}"]`);
      if (btn) {{
        document.querySelectorAll('[data-disc-mod]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentDiscoveryModule = modKey;
        renderDiscoveryJobs();
      }}
    }}

    // 切换待审仓子过滤器
    function switchInboxFilter(filter) {{
      currentInboxFilter = filter;
      document.querySelectorAll('[data-inbox-filter]').forEach(b => {{
        if (b.getAttribute('data-inbox-filter') === filter) {{
          b.classList.add('active');
        }} else {{
          b.classList.remove('active');
        }}
      }});
      renderInboxJobs();
    }}

    // 切换顶层大视图 (discovery | inbox | tracking)
    function switchMainView(view) {{
      currentMainView = view;
      const btnDisc = document.getElementById('btnViewDiscovery');
      const btnInbox = document.getElementById('btnViewInbox');
      const btnTrack = document.getElementById('btnViewTracking');

      const viewDisc = document.getElementById('viewDiscovery');
      const viewInbox = document.getElementById('viewInbox');
      const viewTrack = document.getElementById('viewTracking');

      [btnDisc, btnInbox, btnTrack].forEach(b => b.classList.remove('active'));
      [viewDisc, viewInbox, viewTrack].forEach(v => v.style.display = 'none');

      if (view === 'discovery') {{
        btnDisc.classList.add('active');
        viewDisc.style.display = 'block';
        renderDiscoveryJobs();
      }} else if (view === 'inbox') {{
        btnInbox.classList.add('active');
        viewInbox.style.display = 'block';
        renderInboxJobs();
      }} else {{
        btnTrack.classList.add('active');
        viewTrack.style.display = 'block';
        renderTrackingJobs();
      }}
    }}

    // 全局统计更新
    function updateAllStats() {{
      const removed = getRemovedSet();
      const map = getStoredStatuses();
      const decisions = getInboxDecisions();

      let unappliedTotal = 0;
      let unappliedMt = 0;
      let unappliedForeign = 0;
      let unappliedInternet = 0;
      let unappliedAuto = 0;
      let unappliedSoe = 0;
      let unappliedFeat = 0;

      let trackTotal = 0;
      let trackActive = 0;
      let trackInterview = 0;
      let trackExam = 0;
      let trackArchived = 0;

      let inboxPending = 0;
      let inboxAccepted = 0;
      let inboxRejected = 0;
      let inboxTotal = DAILY_INBOX_JOBS.length;

      DAILY_INBOX_JOBS.forEach(ij => {{
        const d = decisions[ij.id];
        if (d && d.action === 'accepted') {{
          inboxAccepted++;
        }} else if (d && d.action === 'rejected') {{
          inboxRejected++;
        }} else {{
          inboxPending++;
        }}
      }});

      // 实时更新待审仓各状态子标签徽章
      const elTabPending = document.getElementById('badgeTabPending');
      if (elTabPending) elTabPending.innerText = inboxPending;
      const elTabAccepted = document.getElementById('badgeTabAccepted');
      if (elTabAccepted) elTabAccepted.innerText = inboxAccepted;
      const elTabRejected = document.getElementById('badgeTabRejected');
      if (elTabRejected) elTabRejected.innerText = inboxRejected;
      const elTabAll = document.getElementById('badgeTabAll');
      if (elTabAll) elTabAll.innerText = inboxTotal;

      ALL_JOBS.forEach(j => {{
        if (removed.has(j.id)) return;
        const delivered = isJobDelivered(j, map);
        const compApplied = isCompanyApplied(j, map);
        const st = map[j.id] || j.status;

        if (delivered) {{
          trackTotal++;
          if (st === '已淘汰') {{
            trackArchived++;
          }} else if (st === '面试中') {{
            trackActive++;
            trackInterview++;
          }} else {{
            trackActive++;
            if (st === '已网申' || (j.stage && j.stage.includes('测评')) || (j.reminders && j.reminders.includes('测评'))) {{
              trackExam++;
            }}
          }}
        }} else if (!compApplied) {{
          unappliedTotal++;
          if (j.is_mt || j.module === '管培生计划') unappliedMt++;
          if (j.module === '外企（中国）' || j.is_foreign) unappliedForeign++;
          if (j.module === '互联网大厂') unappliedInternet++;
          else if (j.module === '全品类头部大厂') unappliedAuto++;
          else if (j.module === '央国企龙头') unappliedSoe++;

          if (j.is_featured) unappliedFeat++;
        }}
      }});

      // 更新顶部切换 Tab 徽章
      document.getElementById('badgeUnapplied').innerText = `${{unappliedTotal}} 岗可投`;
      document.getElementById('badgeInbox').innerText = inboxPending > 0 ? `${{inboxPending}} 岗待决` : '已清空 🎉';
      document.getElementById('inboxPendingCount').innerText = inboxPending;
      document.getElementById('badgeApplied').innerText = `${{trackTotal}} 家在途`;

      // 更新未投递统计
      document.getElementById('statUnappliedTotal').innerText = unappliedTotal;
      document.getElementById('statUnappliedMt').innerText = unappliedMt;
      document.getElementById('statUnappliedForeign').innerText = unappliedForeign;
      document.getElementById('statUnappliedInternet').innerText = unappliedInternet;
      document.getElementById('statUnappliedAuto').innerText = unappliedAuto;
      document.getElementById('statUnappliedSoe').innerText = unappliedSoe;
      document.getElementById('statUnappliedFeat').innerText = unappliedFeat;

      // 更新实战统计
      document.getElementById('statTrackTotal').innerText = trackTotal;
      document.getElementById('statTrackActive').innerText = trackActive;
      document.getElementById('statTrackInterview').innerText = trackInterview;
      document.getElementById('statTrackExam').innerText = trackExam;
      document.getElementById('statTrackArchived').innerText = trackArchived;

      document.getElementById('btnCntAll').innerText = trackTotal;
      document.getElementById('btnCntActive').innerText = trackActive;
      document.getElementById('btnCntInterview').innerText = trackInterview;
      document.getElementById('btnCntExam').innerText = trackExam;
      document.getElementById('btnCntArchived').innerText = trackArchived;

      document.getElementById('trashCount').innerText = removed.size;
    }}

    // 渲染【视图二：每日精选待审仓】（以 GTD 极致产品思维打磨交互流）
    function renderInboxJobs() {{
      const decisions = getInboxDecisions();
      const grid = document.getElementById('inboxGrid');
      grid.innerHTML = '';

      const filtered = DAILY_INBOX_JOBS.filter(j => {{
        const d = decisions[j.id];
        const isAccepted = d && d.action === 'accepted';
        const isRejected = d && d.action === 'rejected';

        if (currentInboxFilter === 'pending' && (isAccepted || isRejected)) return false;
        if (currentInboxFilter === 'accepted' && !isAccepted) return false;
        if (currentInboxFilter === 'rejected' && !isRejected) return false;

        if (currentInboxSearch) {{
          const fullText = (j.company + ' ' + (j.industry || '') + ' ' + (j.positions || []).join(' ') + ' ' + (j.salary_range || '') + ' ' + (j.reason || '')).toLowerCase();
          if (!fullText.includes(currentInboxSearch.toLowerCase())) return false;
        }}
        return true;
      }});

      if (filtered.length === 0) {{
        if (currentInboxFilter === 'pending') {{
          grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 16px; margin: 10px 0;">
              <div style="font-size: 44px; margin-bottom: 12px;">🎉</div>
              <div style="font-size: 19px; font-weight: 800; color: #1e293b; margin-bottom: 8px;">太棒了！待审仓已清空 (Inbox Zero)</div>
              <div style="font-size: 14px; color: #64748b; margin-bottom: 22px; line-height: 1.6;">
                当前暂无等待决策的候选岗位。所有最新秋招情报均已完成入库分类或忽略过滤！<br>
                你可以前往未投递主看板查看新岗位，或查看已入库的记录。
              </div>
              <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                <button class="btn btn-primary" style="padding: 9px 22px; font-size: 13.5px;" onclick="switchMainView('discovery')">🚀 前往【未投递精选雷达】开始投递 ➔</button>
                <button class="btn btn-secondary" style="padding: 9px 18px; font-size: 13.5px; border: 1px solid #cbd5e1;" onclick="switchInboxFilter('accepted')">📋 查看已入库岗位</button>
              </div>
            </div>
          `;
        }} else if (currentInboxFilter === 'accepted') {{
          grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: #94a3b8; font-size: 15px;">暂无已入库岗位记录。可切换至【⏳ 待决策】标签进行岗位入库。</div>';
        }} else if (currentInboxFilter === 'rejected') {{
          grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: #94a3b8; font-size: 15px;">暂无已忽略岗位记录。</div>';
        }} else {{
          grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: #94a3b8; font-size: 15px;">暂无待审岗位记录。</div>';
        }}
        return;
      }}

      filtered.forEach(j => {{
        const d = decisions[j.id];
        const isAccepted = d && d.action === 'accepted';
        const isRejected = d && d.action === 'rejected';

        const card = document.createElement('div');
        card.className = `job-card tier-${{j.tier}}`;
        if (isRejected) card.style.opacity = '0.6';

        let decisionBadge = '';
        if (isAccepted) {{
          decisionBadge = `<span style="background:#ecfdf5; color:#047857; font-size:12px; font-weight:800; padding:3px 10px; border-radius:6px; border:1px solid #a7f3d0;">✅ 已录入至【${{d.module}}】</span>`;
        }} else if (isRejected) {{
          decisionBadge = `<span style="background:#f1f5f9; color:#64748b; font-size:12px; font-weight:700; padding:3px 8px; border-radius:6px; border:1px solid #e2e8f0;">🚫 已忽略隐身</span>`;
        }}

        // 构建决策操作面板
        let dispatchPanelHtml = '';
        if (isAccepted) {{
          dispatchPanelHtml = `
            <div class="inbox-dispatch-panel" style="background:#ecfdf5; border:1px solid #a7f3d0; border-radius:10px; padding:12px;">
              <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <span style="font-size:13px; color:#065f46; font-weight:800;">
                  ✅ 已成功录入至【${{d.module}}】板块（已同步至未投递雷达）
                </span>
                <div style="display:flex; gap:8px;">
                  <button class="btn btn-secondary" style="padding:4px 10px; font-size:12px; border:1px solid #cbd5e1; background:white; color:#475569;" onclick="undoInboxDecision('${{j.id}}')">撤销入库 ↺</button>
                  <button class="btn btn-primary" style="padding:4px 12px; font-size:12px; background:#059669; border-color:#059669;" onclick="goToDiscoveryModule('${{d.module}}')">前往【${{d.module}}】查看 ➔</button>
                </div>
              </div>
              <div style="margin-top:10px; padding-top:8px; border-top:1px dashed #a7f3d0; font-size:12px; color:#047857; display:flex; align-items:center; flex-wrap:wrap; gap:4px;">
                <span style="font-weight:700;">调整录入板块：</span>
                <button class="btn-disp-sm" onclick="dispatchInboxJob('${{j.id}}', '管培生计划')">🎓 管培</button>
                <button class="btn-disp-sm" onclick="dispatchInboxJob('${{j.id}}', '外企（中国）')">🌍 外企</button>
                <button class="btn-disp-sm" onclick="dispatchInboxJob('${{j.id}}', '互联网大厂')">🌐 互联网</button>
                <button class="btn-disp-sm" onclick="dispatchInboxJob('${{j.id}}', '全品类头部大厂')">🚗 全品类</button>
                <button class="btn-disp-sm" onclick="dispatchInboxJob('${{j.id}}', '央国企龙头')">🏢 央国企</button>
              </div>
            </div>
          `;
        }} else if (isRejected) {{
          dispatchPanelHtml = `
            <div class="inbox-dispatch-panel" style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px;">
              <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <span style="font-size:13px; color:#64748b; font-weight:700;">
                  🚫 该岗位已标记忽略（已从所有主看板与发现雷达中彻底隔离过滤）
                </span>
                <button class="btn btn-secondary" style="padding:4px 12px; font-size:12px; background:white; border:1px solid #cbd5e1; color:#1e293b; font-weight:700;" onclick="restoreInboxJob('${{j.id}}')">恢复至待决策 ↺</button>
              </div>
            </div>
          `;
        }} else {{
          dispatchPanelHtml = `
            <div class="inbox-dispatch-panel">
              <div class="inbox-dispatch-label">
                <span>🎯 手动分配入库主看板（点击即录入并移出待决策）：</span>
              </div>
              <div class="dispatch-btn-group">
                <button class="btn-disp" style="background:#f5f3ff; color:#7c3aed; border-color:#ddd6fe;" onclick="dispatchInboxJob('${{j.id}}', '管培生计划')">🎓 入库【管培生】</button>
                <button class="btn-disp" style="background:#f0f9ff; color:#0284c7; border-color:#bae6fd;" onclick="dispatchInboxJob('${{j.id}}', '外企（中国）')">🌍 入库【外企】</button>
                <button class="btn-disp btn-disp-internet" onclick="dispatchInboxJob('${{j.id}}', '互联网大厂')">🌐 入库【互联网】</button>
                <button class="btn-disp btn-disp-auto" onclick="dispatchInboxJob('${{j.id}}', '全品类头部大厂')">🚗 入库【全品类】</button>
                <button class="btn-disp btn-disp-soe" onclick="dispatchInboxJob('${{j.id}}', '央国企龙头')">🏢 入库【央国企】</button>
                <button class="btn-disp btn-disp-ignore" onclick="ignoreInboxJob('${{j.id}}')">❌ 忽略</button>
              </div>
            </div>
          `;
        }}

        card.innerHTML = `
          <div>
            <div class="card-top">
              <div class="company-name">
                ${{j.company}}
                <span class="inbox-new-tag">🆕 ${{j.date_released ? j.date_released.substring(5).replace('-','.') : '{inbox_date_window}'}}最新发布</span>
                ${{decisionBadge}}
              </div>
              <div style="display: flex; gap: 6px; align-items: center;">
                <div class="badges">
                  <span class="badge badge-${{j.tier}}">${{j.tier}} 级</span>
                  <span class="badge badge-ind">建议:${{j.recommended_module}}</span>
                </div>
              </div>
            </div>

            ${{j.announcement_title ? `
              <div style="background:#fff7ed; border:1px solid #fed7aa; padding:6px 10px; border-radius:8px; font-size:12.5px; color:#c2410c; margin-bottom:10px; line-height:1.5;">
                📢 <strong>官宣公告：</strong>${{j.announcement_title}}
              </div>
            ` : ''}}
            <div class="scale-bar">${{j.scale_badge}}</div>
            <div class="salary-bar">${{j.salary_range}}</div>

            <div class="positions-wrap">
              ${{j.positions.map(p => `<span class="pos-pill">${{p}}</span>`).join('')}}
            </div>

            <div class="meta-line">
              <span>📍 ${{j.locations && j.locations.length > 0 ? j.locations.join('、') : '全国/不限'}}</span>
              <span>⏰ 截止: ${{j.deadline}}</span>
              <span>📅 发布: ${{j.date_released || '9.17-9.18'}}</span>
            </div>

            <div class="tips-box">
              <strong>🎯 考核/避坑点:</strong> ${{j.tips_and_pitfalls}}
            </div>

            <div class="reason-box">
              <strong>💡 推荐解析:</strong> ${{j.reason}}
            </div>
          </div>

          <!-- 分流决策操作区 -->
          ${{dispatchPanelHtml}}

          <div class="card-actions" style="margin-top: 12px;">
            ${{j.announcement_url ? `
              <a href="${{j.announcement_url}}" target="_blank" class="btn" style="background:#fff7ed; color:#c2410c; border:1px solid #fed7aa; padding:6px 12px; border-radius:6px; font-size:12px; font-weight:700; text-decoration:none;">📢 公告原帖 ↗</a>
            ` : ''}}
            <button class="btn-jd" onclick="openJdModal('${{j.id}}')">📄 详细情报 & JD</button>
            ${{j.apply_url && j.apply_url.startsWith('http') ?
              `<a href="${{j.apply_url}}" target="_blank" class="btn-apply">🚀 直达官方网申 ↗</a>` :
              `<span class="btn-apply disabled">官网投递</span>`
            }}
          </div>
        `;
        grid.appendChild(card);
      }});
    }}

    // 渲染紧急待办呼叫栏
    function renderEmergencyCallouts() {{
      const map = getStoredStatuses();
      const removed = getRemovedSet();
      const grid = document.getElementById('emergencyGrid');
      grid.innerHTML = '';

      // 找出含有测评、紧急提醒或初筛卡点的在途岗位
      const urgentJobs = ALL_JOBS.filter(j => {{
        if (removed.has(j.id)) return false;
        if (!isJobDelivered(j, map)) return false;
        const st = map[j.id] || j.status;
        if (st === '已淘汰') return false;
        const text = (j.reminders || '') + (j.stage || '') + (j.notes || '');
        return text.includes('测评') || text.includes('48') || text.includes('3日') || text.includes('生死线') || text.includes('紧急') || text.includes('调剂') || text.includes('实习');
      }});

      if (urgentJobs.length === 0) {{
        document.getElementById('emergencyCallout').style.display = 'none';
        return;
      }}
      document.getElementById('emergencyCallout').style.display = 'block';

      urgentJobs.forEach(j => {{
        const card = document.createElement('div');
        card.className = 'callout-card';
        card.innerHTML = `
          <div class="callout-card-top">
            <span class="callout-comp">${{j.company}} · ${{j.positions[0] || '管培'}}</span>
            <span class="callout-tag">${{j.stage || '推进中'}}</span>
          </div>
          <div class="callout-text">${{j.reminders || j.notes}}</div>
        `;
        grid.appendChild(card);
      }});
    }}

    // 渲染【视图一：未投递精选雷达】（100%纯净，杜绝已投干扰）
    function renderPriorityCards() {{
      const grid = document.getElementById('priorityCardsGrid');
      if (!grid) return;
      if (!NOWCLAW_PRIORITY_JOBS || NOWCLAW_PRIORITY_JOBS.length === 0) {{
        grid.innerHTML = '<div style="color: white; opacity: 0.8; font-size: 13px;">今日暂无新的可投递候选，请查看实战作战室。</div>';
        return;
      }}
      grid.innerHTML = NOWCLAW_PRIORITY_JOBS.map(job => {{
        const positions = (job.positions || []).join('、');
        const loc = (job.locations || []).slice(0, 3).join('/');
        return `
          <div class="priority-card">
            <div class="priority-rank-badge">🏆 TOP ${{job.priority_rank}} ｜ 匹配度 ${{job.match_score}}%</div>
            <div>
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-top: 6px;">
                <div class="priority-track-badge">${{job.track_label || job.module}}</div>
                <span style="font-size: 11px; font-weight: 700; color: #dc2626;">${{job.urgency_badge}}</span>
              </div>
              <div class="priority-card-title">${{job.company}}</div>
              <div class="priority-card-pos">${{positions}}</div>
              <div style="font-size: 12px; color: #047857; font-weight: 700; margin-bottom: 6px;">💰 ${{job.salary_range}} ｜ 📍 ${{loc}}</div>
              <div class="priority-card-reason">💡 <strong>推荐理由：</strong>${{job.priority_reason}}</div>
              <div class="priority-card-action">🚀 <strong>行动建议：</strong>${{job.next_step_action}}</div>
            </div>
            <div class="priority-card-footer">
              <a href="${{job.apply_url}}" target="_blank" class="btn-priority-apply">🔗 官网直申</a>
              <button class="btn-priority-jd" onclick="openJdModal('${{job.id}}')">📄 详情</button>
              <button class="btn-priority-jd" onclick="copyNowClawPrompt('interview')" title="一键复制针对该企业的模拟面试指令">🎙️ 面试</button>
            </div>
          </div>
        `;
      }}).join('');
    }}

    function renderDiscoveryJobs() {{
      renderPriorityCards();
      const removed = getRemovedSet();
      const map = getStoredStatuses();
      const grid = document.getElementById('discoveryGrid');
      grid.innerHTML = '';

      const decisions = getInboxDecisions();
      const filtered = ALL_JOBS.filter(j => {{
        // 双重彻底拦截：已移除黑名单或在待审仓中被标记忽略的，绝对不在未投递主看板出现
        if (removed.has(j.id)) return false;
        if (decisions[j.id] && decisions[j.id].action === 'rejected') return false;
        // 核心铁律：只要企业已投递或有实战记录，绝对不在未投递主展示区出现
        if (isCompanyApplied(j, map)) return false;

        // 模块筛选
        if (currentDiscoveryModule === 'mt' && !j.is_mt && j.module !== '管培生计划') return false;
        if (currentDiscoveryModule === 'foreign' && j.module !== '外企（中国）' && !j.is_foreign) return false;
        if (currentDiscoveryModule === 'internet' && j.module !== '互联网大厂') return false;
        if (currentDiscoveryModule === 'consumer_auto' && j.module !== '全品类头部大厂') return false;
        if (currentDiscoveryModule === 'soe' && j.module !== '央国企龙头') return false;
        if (currentDiscoveryModule === 'featured' && !j.is_featured) return false;
        if (currentDiscoveryModule === 'S' && j.tier !== 'S') return false;
        if (currentDiscoveryModule === 'A' && j.tier !== 'A') return false;
        if (currentDiscoveryModule === 'B' && j.tier !== 'B') return false;

        // 搜索过滤
        if (currentDiscoverySearch) {{
          const fullText = (j.company + ' ' + j.industry + ' ' + j.module + ' ' + j.positions.join(' ') + ' ' + j.locations.join(' ') + ' ' + j.salary_range + ' ' + j.reason).toLowerCase();
          if (!fullText.includes(currentDiscoverySearch.toLowerCase())) return false;
        }}
        return true;
      }});

      // 排序：早8点精选优先 -> S级 -> A级 -> B级
      filtered.sort((a, b) => {{
        if (a.is_featured && !b.is_featured) return -1;
        if (!a.is_featured && b.is_featured) return 1;
        const tierWeights = {{ 'S': 0, 'A': 1, 'B': 2 }};
        return (tierWeights[a.tier] || 3) - (tierWeights[b.tier] || 3);
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: #94a3b8; font-size: 15px;">当前模块下暂无可投岗位，可切换其他板块或调整搜索词。</div>';
        return;
      }}

      filtered.forEach(j => {{
        const card = document.createElement('div');
        card.className = `job-card tier-${{j.tier}}`;
        card.innerHTML = `
          <div>
            <div class="card-top">
              <div class="company-name">
                ${{j.company}}
                ${{j.is_featured ? '<span class="featured-tag">🌟 早8点精选</span>' : ''}}
                ${{j.is_mt ? '<span class="mt-tag">🎓 2027管培(不限专业)</span>' : ''}}
                <span class="module-badge mod-${{j.module}}">${{j.module}}</span>
              </div>
              <div style="display: flex; gap: 6px; align-items: center;">
                <div class="badges">
                  <span class="badge badge-${{j.tier}}">${{j.tier}} 级</span>
                </div>
                <button class="btn-remove" title="从主看板移除此岗位" onclick="addRemoved('${{j.id}}')">&times;</button>
              </div>
            </div>

            <div class="scale-bar">${{j.scale_badge}}</div>
            <div class="salary-bar">${{j.salary_range}}</div>

            <div class="positions-wrap">
              ${{j.positions.map(p => `<span class="pos-pill">${{p}}</span>`).join('')}}
            </div>

            <div class="meta-line">
              <span>📍 ${{j.locations && j.locations.length > 0 ? j.locations.join('、') : '全国/不限'}}</span>
              <span>⏰ 截止: ${{j.deadline}}</span>
              <span>🎓 ${{j.batch || '正式批'}}</span>
            </div>

            <div class="tips-box">
              <strong>🎯 笔试/面试避坑:</strong> ${{j.tips_and_pitfalls}}
            </div>

            <div class="reason-box">
              <strong>💡 适配解析:</strong> ${{j.reason}}
            </div>
          </div>

          <div class="card-actions">
            <select class="status-select status-待投递" title="标记投递后，岗位会自动归入【实战投递面板】" onchange="onStatusChange('${{j.id}}', this.value)">
              <option value="待投递" selected>待投递 (未投)</option>
              <option value="已网申">标记为：已网申 📨</option>
              <option value="笔试中">标记为：笔试中 📝</option>
              <option value="面试中">标记为：面试中 💼</option>
              <option value="已获Offer">标记为：已获Offer 🎉</option>
              <option value="已淘汰">标记为：已淘汰</option>
            </select>

            <div class="btn-group-right">
              <button class="btn-jd" onclick="openJdModal('${{j.id}}')">📄 详细情报 & JD</button>
              ${{j.apply_url && j.apply_url.startsWith('http') ?
                `<a href="${{j.apply_url}}" target="_blank" class="btn-apply">🚀 官方直聘 ↗</a>` :
                `<span class="btn-apply disabled">官网/微信投递</span>`
              }}
            </div>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}

    // 渲染【视图三：我的实战投递合计面板】
    function renderTrackingJobs() {{
      const removed = getRemovedSet();
      const map = getStoredStatuses();
      const grid = document.getElementById('trackingGrid');
      grid.innerHTML = '';

      const filtered = ALL_JOBS.filter(j => {{
        if (removed.has(j.id)) return false;
        if (!isJobDelivered(j, map)) return false;

        const st = map[j.id] || j.status;

        // 实战分类筛选
        if (currentTrackingFilter === 'active' && st === '已淘汰') return false;
        if (currentTrackingFilter === 'interview' && st !== '面试中') return false;
        if (currentTrackingFilter === 'exam') {{
          const isExam = (st === '已网申' || (j.stage && j.stage.includes('测评')) || (j.reminders && j.reminders.includes('测评'))) && st !== '已淘汰';
          if (!isExam) return false;
        }}
        if (currentTrackingFilter === 'archived' && st !== '已淘汰') return false;

        // 搜索过滤
        if (currentTrackingSearch) {{
          const fullText = (j.company + ' ' + j.positions.join(' ') + ' ' + (j.notes || '') + ' ' + (j.reminders || '') + ' ' + (j.stage || '')).toLowerCase();
          if (!fullText.includes(currentTrackingSearch.toLowerCase())) return false;
        }}
        return true;
      }});

      // 排序：推进中优先于已淘汰
      filtered.sort((a, b) => {{
        const aSt = map[a.id] || a.status;
        const bSt = map[b.id] || b.status;
        if (aSt !== '已淘汰' && bSt === '已淘汰') return -1;
        if (aSt === '已淘汰' && bSt !== '已淘汰') return 1;
        return 0;
      }});

      if (filtered.length === 0) {{
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: #94a3b8; font-size: 15px;">暂无匹配的实战投递记录。</div>';
        return;
      }}

      filtered.forEach(j => {{
        const st = map[j.id] || j.status;
        const card = document.createElement('div');
        card.className = `job-card tier-${{j.tier}}`;
        card.innerHTML = `
          <div>
            <div class="card-top">
              <div class="company-name">
                ${{j.company}}
                <span class="custom-tag">实战在途</span>
                ${{j.is_mt ? '<span class="mt-tag">🎓 管培</span>' : ''}}
                <span class="module-badge mod-${{j.module}}">${{j.module}}</span>
              </div>
              <div style="display: flex; gap: 6px; align-items: center;">
                <div class="badges">
                  <span class="badge badge-${{j.tier}}">${{j.tier}} 级</span>
                </div>
              </div>
            </div>

            <div class="tracking-memo-box">
              <div class="tracking-memo-top">
                <span>📌 当前阶段:</span>
                <span class="tracking-stage-tag">${{j.stage || st}}</span>
                ${{j.applied_date ? `<span style="font-size:11px; color:#78350f; margin-left:auto;">📅 投递时间: ${{j.applied_date}}</span>` : ''}}
              </div>
              <div><strong>个人实战备注:</strong> ${{j.notes || '已完成网申投递，保持密切跟进'}}</div>
              ${{j.reminders ? `
                <div class="tracking-reminder-box">
                  🚨 <strong>行动提醒:</strong> ${{j.reminders}}
                </div>
              ` : ''}}
            </div>

            <div class="scale-bar">${{j.scale_badge}}</div>
            <div class="salary-bar">${{j.salary_range}}</div>

            <div class="positions-wrap">
              ${{j.positions.map(p => `<span class="pos-pill">${{p}}</span>`).join('')}}
            </div>

            <div class="meta-line">
              <span>📍 ${{j.locations && j.locations.length > 0 ? j.locations.join('、') : '全国/不限'}}</span>
              <span>⏰ 截止: ${{j.deadline}}</span>
              <span>🎓 渠道: ${{j.channel || j.batch || '官网网申'}}</span>
            </div>

            <div class="tips-box">
              <strong>🎯 考核/面试要点:</strong> ${{j.tips_and_pitfalls}}
            </div>
          </div>

          <div class="card-actions">
            <div>
              <span style="font-size: 12px; color: var(--text-muted); margin-right: 6px;">更新状态:</span>
              <select class="status-select status-${{st}}" onchange="onStatusChange('${{j.id}}', this.value)">
                <option value="待投递" ${{st === '待投递' ? 'selected' : ''}}>移回待投递池</option>
                <option value="已网申" ${{st === '已网申' ? 'selected' : ''}}>已网申 📨</option>
                <option value="笔试中" ${{st === '笔试中' ? 'selected' : ''}}>笔试中 📝</option>
                <option value="面试中" ${{st === '面试中' ? 'selected' : ''}}>面试中 💼</option>
                <option value="已获Offer" ${{st === '已获Offer' ? 'selected' : ''}}>已获Offer 🎉</option>
                <option value="已淘汰" ${{st === '已淘汰' ? 'selected' : ''}}>已淘汰 (归档)</option>
              </select>
            </div>

            <div class="btn-group-right">
              <button class="btn-jd" onclick="openJdModal('${{j.id}}')">📄 详细情报 & JD</button>
              ${{j.apply_url && j.apply_url.startsWith('http') ?
                `<a href="${{j.apply_url}}" target="_blank" class="btn-apply">🚀 直达招聘网 ↗</a>` :
                `<span class="btn-apply disabled">官网/微信直投</span>`
              }}
            </div>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}

    function onStatusChange(id, val) {{
      saveStatus(id, val);
    }}

    function updateAllStatsAndRenders() {{
      syncInboxDecisionsToJobs();
      updateAllStats();
      renderEmergencyCallouts();
      if (currentMainView === 'discovery') {{
        renderDiscoveryJobs();
      }} else if (currentMainView === 'inbox') {{
        renderInboxJobs();
      }} else {{
        renderTrackingJobs();
      }}
    }}

    function openJdModal(id) {{
      let job = ALL_JOBS.find(x => x.id === id);
      if (!job) job = DAILY_INBOX_JOBS.find(x => x.id === id);
      if (!job) return;
      currentViewingJob = job;
      document.getElementById('modalJdCompany').innerText = job.company;
      document.getElementById('modalJdSub').innerText = `${{job.module || job.recommended_module}} ｜ ${{job.positions.join('、')}} ｜ 建议评级: ${{job.tier}} 级 ｜ 截止: ${{job.deadline}}`;

      const applyBtn = document.getElementById('modalApplyBtn');
      if (job.apply_url && job.apply_url.startsWith('http')) {{
        applyBtn.href = job.apply_url;
        applyBtn.style.display = 'inline-flex';
      }} else {{
        applyBtn.style.display = 'none';
      }}

      const jd = job.jd || {{}};
      const resps = jd.responsibilities || [];
      const quals = jd.qualifications || [];
      const ats = jd.ats_keywords || [];
      const adv = jd.candidate_advantage || job.reason;

      let html = '';
      html += `<div class="jd-section">
        <div class="jd-subtitle">💰 薪酬待遇与企业背景</div>
        <p style="font-size:13.5px; color:#065f46; font-weight:700; margin-bottom:6px;">${{job.salary_range}}</p>
        <p style="font-size:13px; color:#1e40af; font-weight:600;">${{job.scale_badge}}</p>
      </div>`;

      html += `<div class="jd-section">
        <div class="jd-subtitle">🎯 考核流程与避坑指南</div>
        <p style="font-size:13px; color:#334155; margin-bottom:6px;"><strong>流程：</strong>${{job.interview_process}}</p>
        <p style="font-size:13px; color:#b91c1c; background:#fef2f2; padding:8px 10px; border-radius:6px; border:1px solid #fecaca;"><strong>避坑关键：</strong>${{job.tips_and_pitfalls}}</p>
      </div>`;

      if (resps.length > 0) {{
        html += `<div class="jd-section">
          <div class="jd-subtitle">📋 岗位核心职责 (Responsibilities)</div>
          <ul class="jd-list">${{resps.map(r => `<li>${{r}}</li>`).join('')}}</ul>
        </div>`;
      }}

      if (quals.length > 0) {{
        html += `<div class="jd-section">
          <div class="jd-subtitle">🎯 任职资格要求 (Requirements)</div>
          <ul class="jd-list">${{quals.map(q => `<li>${{q}}</li>`).join('')}}</ul>
        </div>`;
      }}

      html += `<div class="jd-section">
        <div class="jd-subtitle">🌟 郑大建筑专硕专属竞争优势与人设</div>
        <p style="font-size: 13.5px; color: #334155; line-height: 1.6;">${{adv}}</p>
      </div>`;

      if (ats.length > 0) {{
        html += `<div class="jd-section">
          <div class="jd-subtitle">🔑 ATS 简历高命中关键词 (投递必填)</div>
          <div class="tag-cloud">${{ats.map(k => `<span class="ats-chip">${{k}}</span>`).join('')}}</div>
        </div>`;
      }}

            html += `<div class="jd-section" style="background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%); border: 1.5px solid #a7f3d0; border-radius: 10px; padding: 14px;">
        <div class="jd-subtitle" style="color: #065f46; display: flex; align-items: center; justify-content: space-between;">
          <span>🦞 牛客 AI 专项求职助手能力联动</span>
          <span style="font-size: 11px; background: #10b981; color: white; padding: 2px 8px; border-radius: 12px;">已装载 v1.1.2</span>
        </div>
        <p style="font-size: 12.5px; color: #047857; margin-bottom: 10px; line-height: 1.5;">针对当前【${{job.company}}】与岗位，一键生成 AI 提问指令，随时在对话中调起牛客专属技能：</p>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button class="btn btn-secondary" style="font-size: 12px; padding: 6px 12px; background: white; border: 1px solid #10b981; color: #065f46;" onclick="copyNowClawPrompt('brief')">🏢 一键复制【面试前公司速查】指令</button>
          <button class="btn btn-secondary" style="font-size: 12px; padding: 6px 12px; background: white; border: 1px solid #10b981; color: #065f46;" onclick="copyNowClawPrompt('interview')">🎙️ 一键复制【岗前模拟面试】指令</button>
          <button class="btn btn-secondary" style="font-size: 12px; padding: 6px 12px; background: white; border: 1px solid #10b981; color: #065f46;" onclick="copyNowClawPrompt('tailor')">📝 一键复制【定向简历改写】指令</button>
        </div>
      </div>`;

      document.getElementById('modalJdContent').innerHTML = html;
      document.getElementById('jdModal').style.display = 'flex';
    }}

    function copyJdPrompt() {{
      if (!currentViewingJob) return;
      const j = currentViewingJob;
      const text = `我正在应聘【${{j.company}}】的【${{j.positions.join('、')}}】岗位。\\n企业背景：${{j.scale_badge}}\\n要求与避坑：${{j.tips_and_pitfalls}}\\n请根据我的背景（郑州大学建筑专硕、国奖前2%、有京东零售商家采销运营与新东方私域活动实战）为我定制一份专属简历核心STAR经历与面试自述。`;
      navigator.clipboard.writeText(text).then(() => {{
        alert('✅ 针对该岗位的定制 Prompt 已复制到剪贴板！');
      }}).catch(() => {{
        prompt('请手动复制以下 Prompt：', text);
      }});
    }}

    function openAddModal() {{ document.getElementById('addModal').style.display = 'flex'; }}
    function openTrashModal() {{ renderTrashList(); document.getElementById('trashModal').style.display = 'flex'; }}
    function renderTrashList() {{
      const removed = getRemovedSet();
      const listEl = document.getElementById('trashList');
      if (removed.size === 0) {{
        listEl.innerHTML = '<p style=\"color:#94a3b8; font-size:13px; text-align:center; padding:20px;\">回收站为空</p>';
        return;
      }}
      let html = '';
      removed.forEach(id => {{
        const j = ALL_JOBS.find(x => x.id === id);
        const name = j ? `${{j.company}} - ${{j.positions.join('、')}}` : id;
        html += `
          <div style=\"display:flex; justify-content:space-between; align-items:center; padding:10px 12px; border-bottom:1px solid #f1f5f9;\">
            <span style=\"font-size:13px; font-weight:600;\">${{name}}</span>
            <button class=\"btn btn-secondary\" style=\"padding:4px 10px; font-size:12px; color:#1e3a8a; background:#eff6ff;\" onclick=\"restoreRemoved('${{id}}')\">恢复显示</button>
          </div>
        `;
      }});
      listEl.innerHTML = html;
    }}

    function handleJobSubmit(e) {{
      e.preventDefault();
      const comp = document.getElementById('addCompany').value.trim();
      const ind = document.getElementById('addIndustry').value;
      const pos = document.getElementById('addPositions').value.trim().split(/[,，]/).map(s => s.trim()).filter(Boolean);
      const loc = document.getElementById('addLocations').value.trim().split(/[,，]/).map(s => s.trim()).filter(Boolean);
      const sal = document.getElementById('addSalary').value.trim() || '💰 15w - 25w + 绩效年终';
      const tier = document.getElementById('addTier').value;
      const dline = document.getElementById('addDeadline').value || '招满即止';
      const url = document.getElementById('addApplyUrl').value.trim();
      const desc = document.getElementById('addJdDesc').value.trim();

      let mod = '全品类头部大厂';
      if (ind === '央国企') mod = '央国企龙头';
      else if (ind === '互联网') mod = '互联网大厂';
      else if (ind === '外企(中国)' || ind === '外企（中国）') mod = '外企（中国）';
      else if (ind === '管培生计划') mod = '管培生计划';
      const isMt = (ind === '管培生计划') || pos.some(p => /管培|培训生|储备|gmt|uflp/i.test(p));
      const isForeign = (mod === '外企（中国）');

      const newId = `${{comp}}_${{pos.join('_')}}_自建批`.replace(/\\s+/g, '');
      const newJob = {{
        id: newId,
        company: comp,
        industry: ind,
        module: mod,
        is_mt: isMt,
        is_foreign: isForeign,
        positions: pos,
        locations: loc.length > 0 ? loc : ['全国'],
        salary_range: sal,
        tier: tier,
        deadline: dline,
        apply_url: url,
        is_custom: true,
        is_featured: false,
        status: '待投递',
        scale_badge: '🏢 自主录入重点目标企业',
        interview_process: '🎯 简历投递 ➔ 综合面试 ➔ 录用意向',
        tips_and_pitfalls: '【自主录入】发挥复合专业优势，做好针对性准备。',
        reason: desc || '用户自主录入的高契合重点目标岗位',
        jd: {{
          responsibilities: [desc || '负责相关业务板块推进与经营目标达成。'],
          qualifications: ['本硕应届毕业生，具备出色综合素质与执行力。'],
          candidate_advantage: '郑大建筑专硕工科底盘，严谨度与结构化能力突出。',
          ats_keywords: [comp, tier + '级', '自主录入']
        }}
      }};

      ALL_JOBS.unshift(newJob);
      const customList = getCustomJobs();
      customList.unshift(newJob);
      localStorage.setItem('custom_jobs_extra', JSON.stringify(customList));

      closeModal('addModal');
      document.getElementById('addJobForm').reset();
      updateAllStatsAndRenders();
      showToast(`✅ 成功录入岗位：${{comp}}`);
    }}

    function closeModal(id) {{ document.getElementById(id).style.display = 'none'; }}

    function exportData() {{
      const data = {{
        statuses: getStoredStatuses(),
        custom_jobs: getCustomJobs(),
        inbox_decisions: getInboxDecisions(),
        removed_ids: Array.from(getRemovedSet())
      }};
      const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `秋招投递作战室备份_${{new Date().toISOString().slice(0,10)}}.json`;
      a.click();
    }}

    function initExtraCustomJobs() {{
      const extras = getCustomJobs();
      extras.forEach(ej => {{
        if (!ALL_JOBS.some(x => x.id === ej.id)) {{
          ALL_JOBS.unshift(ej);
        }}
      }});
    }}

    // 未投递模块筛选按钮绑定
    document.querySelectorAll('[data-disc-mod]').forEach(btn => {{
      btn.addEventListener('click', (e) => {{
        document.querySelectorAll('[data-disc-mod]').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        currentDiscoveryModule = e.target.getAttribute('data-disc-mod');
        renderDiscoveryJobs();
      }});
    }});

    // 待审仓筛选按钮绑定 (支持点击子元素 tab-badge 正常冒泡触发)
    document.querySelectorAll('[data-inbox-filter]').forEach(btn => {{
      btn.addEventListener('click', (e) => {{
        const targetBtn = e.target.closest('[data-inbox-filter]');
        if (!targetBtn) return;
        document.querySelectorAll('[data-inbox-filter]').forEach(b => b.classList.remove('active'));
        targetBtn.classList.add('active');
        currentInboxFilter = targetBtn.getAttribute('data-inbox-filter');
        renderInboxJobs();
      }});
    }});

    // 实战投递过滤按钮绑定
    document.querySelectorAll('[data-track-filter]').forEach(btn => {{
      btn.addEventListener('click', (e) => {{
        document.querySelectorAll('[data-track-filter]').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        currentTrackingFilter = e.target.getAttribute('data-track-filter');
        renderTrackingJobs();
      }});
    }});

    document.getElementById('discoverySearchInput').addEventListener('input', (e) => {{
      currentDiscoverySearch = e.target.value.trim();
      renderDiscoveryJobs();
    }});

    document.getElementById('inboxSearchInput').addEventListener('input', (e) => {{
      currentInboxSearch = e.target.value.trim();
      renderInboxJobs();
    }});

    document.getElementById('trackingSearchInput').addEventListener('input', (e) => {{
      currentTrackingSearch = e.target.value.trim();
      renderTrackingJobs();
    }});

    sanitizeStorage();
    initExtraCustomJobs();
    syncInboxDecisionsToJobs();
    updateAllStats();
    renderEmergencyCallouts();
    renderDiscoveryJobs();
    renderInboxJobs();
  </script>
</body>
</html>
"""
    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_code)
    print(f"[+] 3.6 三主视图（含每日精选待审仓）HTML 看板已生成: {OUTPUT_HTML_PATH}")

    # 本地协同：若父目录存在工作区，同步复制一份为 秋招雷达与进度看板.html
    try:
        parent_html = REPO_ROOT.parent / "秋招雷达与进度看板.html"
        if REPO_ROOT.parent.exists():
            with open(parent_html, "w", encoding="utf-8") as f:
                f.write(html_code)
            print(f"[+] 本地工作区同步已更新: {parent_html}")
    except Exception:
        pass




def main():
    parser = argparse.ArgumentParser(description="秋招全景情报雷达 4.0")
    parser.add_argument("--industry", help="指定筛选行业，逗号分隔，如: 央国企,互联网")
    parser.add_argument("--keyword", help="指定公司或岗位关键词过滤")
    parser.add_argument("--no-toast", action="store_true", help="不发送 Windows 桌面 Toast 通知")
    parser.add_argument("--web-crawl", "--web-search", action="store_true", help="在生成前先执行全网实时网络检索与真链收集")
    args = parser.parse_args()

    if args.web_crawl:
        try:
            from daily_web_recruitment_collector import run_collection_and_update
            run_collection_and_update()
        except Exception as e:
            print(f"[!] 自动网络检索组件执行异常: {e}")

    daily_inbox_path = DATA_DIR / "daily_inbox_jobs.json"
    daily_inbox_jobs = load_json(daily_inbox_path, default=[])

    tracking_db = load_json(TRACKING_DB_PATH, default={})
    custom_jobs = load_json(CUSTOM_JOBS_PATH, default=[])
    removed_ids = set(load_json(REMOVED_JOBS_PATH, default=[]))
    builtin_jobs = load_json(BUILTIN_JOBS_PATH, default=[])
    mega_sources = load_json(MEGA_SOURCES_PATH, default=[])
    portals_map = load_json(OFFICIAL_PORTALS_PATH, default={})

    # 1. 多源汇聚
    all_raw_jobs = []

    # 注入用户自定义岗位 (第一优先级)
    for cj in custom_jobs:
        all_raw_jobs.append(cj)

    # 注入全行业名企精选大底池 (含完整薪酬、规模、避坑)
    for mj in mega_sources:
        mj_copy = dict(mj)
        mj_copy["id"] = make_job_id(mj["company"], "_".join(mj.get("positions", [])), mj.get("batch", "正式批"))
        all_raw_jobs.append(mj_copy)

    # 注入内置高含金量专库 (带完整JD)
    for bj in builtin_jobs:
        bj_copy = dict(bj)
        bj_copy["id"] = make_job_id(bj["company"], "_".join(bj["positions"]), bj.get("batch", ""))
        all_raw_jobs.append(bj_copy)

    # 动态拉取远程数据源 1
    feed1 = fetch_primary_jobs()
    for j in feed1:
        all_raw_jobs.append(j)

    # 动态拉取远程数据源 2
    feed2 = fetch_secondary_jobs()
    for j in feed2:
        all_raw_jobs.append(j)

    print(f"[*] 全源汇聚原始岗位总数: {len(all_raw_jobs)} 条")

    # 2. 去重、分级与多维情报补齐
    seen_ids = set()
    ranked_jobs = []

    for j in all_raw_jobs:
        company = j.get("company", "").strip()
        positions = j.get("positions") or []
        pos_str = "_".join(positions)
        jid = j.get("id") or make_job_id(company, pos_str, j.get("batch", ""))

        if jid in seen_ids:
            continue
        seen_ids.add(jid)

        # 补全投递链接
        current_url = j.get("apply_url")
        enriched_url = enrich_with_portal(company, current_url, portals_map)
        j["apply_url"] = enriched_url or current_url

        if args.industry:
            allowed = {i.strip() for i in args.industry.split(",")}
            if (j.get("industry") or "其他") not in allowed:
                continue

        if args.keyword:
            kw = args.keyword.lower()
            text = f"{company} {' '.join(positions)}".lower()
            if kw not in text:
                continue

        # 评估等级
        tier, reason, tags = evaluate_job(j)
        if j.get("tier") in ["S", "A", "B"]:
            tier = j["tier"]
            reason = j.get("reason", reason)
            tags = j.get("tags", tags)

        if tier not in ["S", "A", "B"]:
            continue

        job_item = dict(j)
        job_item["id"] = jid
        job_item["tier"] = tier
        job_item["reason"] = reason
        job_item["tags"] = tags

        # 补齐薪资预估与企业规模背景
        if not job_item.get("salary_range") or not job_item.get("scale_badge"):
            scale, salary, process, tips = infer_salary_and_scale(company, job_item.get("industry", "其他"), positions, tags)
            job_item.setdefault("scale_badge", scale)
            job_item.setdefault("salary_range", salary)
            job_item.setdefault("interview_process", process)
            job_item.setdefault("tips_and_pitfalls", tips)

        # 补齐 JD
        if not job_item.get("jd"):
            job_item["jd"] = generate_synthesized_jd(company, job_item.get("industry", "其他"), positions, tier, tags)

        ranked_jobs.append(job_item)

    # 3. 算法精选：每天早上 8:00 置顶精选 30-50 个“通识核心业务池”岗位
    featured_candidates = []
    for rj in ranked_jobs:
        if rj["id"] in removed_ids:
            continue
        # 优先将带有成熟薪资福利、企业规模背书、且属于S/A级的通识业务岗作为精选
        is_priority_company = any(k in rj["company"] for k in [
            "中建", "华润", "建研院", "铁建", "保利", "中海", "交建", "电网", "电信", "移动",
            "阿里", "腾讯", "美团", "字节", "京东", "快手", "拼多多", "小红书", "DeepSeek",
            "vivo", "OPPO", "比亚迪", "宁德时代", "理想", "京东方", "深信服", "帆软", "宝洁", "招商银行", "中国银行",
            "海尔", "美的", "顺丰", "得物", "金风科技", "联想", "中国外运", "招商蛇口", "超聚变", "卫龙", "小米", "青岛啤酒", "中国平安"
        ])
        if is_priority_company or rj.get("tier") == "S" or (rj.get("tier") == "A" and rj.get("is_custom")):
            featured_candidates.append(rj)

    # 每日早8点动态轮换机制：引入日期伪随机因子进行种子打乱，确保每天早8点刷新的精选未投岗位具备新鲜度与动态轮换特性！
    today_seed = int(datetime.now().strftime("%Y%m%d"))
    import random
    rng = random.Random(today_seed)
    # 按Tier分层，确保S级天选岗位优先，在同层内以每日种子稳定随机轮换
    s_cands = [j for j in featured_candidates if j.get("tier") == "S"]
    a_cands = [j for j in featured_candidates if j.get("tier") != "S"]
    rng.shuffle(s_cands)
    rng.shuffle(a_cands)
    featured_jobs = (s_cands + a_cands)[:40]

    # 排序：S级优先 -> A级 -> B级
    tier_order = {"S": 0, "A": 1, "B": 2}
    ranked_jobs.sort(key=lambda x: (tier_order.get(x.get("tier", "B"), 3), x.get("deadline") or "9999"))

    print(f"[+] 经过全网智能筛选，入库有效通识与对口岗位总数: {len(ranked_jobs)} 个")
    print(f"    - 🌟 今日早8点算法精选推荐: {len(featured_jobs)} 个")
    print(f"    - 🌟 S 级 (天选对口): {len([x for x in ranked_jobs if x.get('tier') == 'S' and x['id'] not in removed_ids])} 个")
    print(f"    - 🔥 A 级 (重点攻坚): {len([x for x in ranked_jobs if x.get('tier') == 'A' and x['id'] not in removed_ids])} 个")
    print(f"    - 🛡️ B 级 (稳健保底): {len([x for x in ranked_jobs if x.get('tier') == 'B' and x['id'] not in removed_ids])} 个")

    # 4. 生成报告与看板
    generate_markdown_report(ranked_jobs, tracking_db, removed_ids, featured_jobs, daily_inbox_jobs)
    generate_html_dashboard(ranked_jobs, tracking_db, removed_ids, featured_jobs, daily_inbox_jobs)

    # 5. Windows 原生 Toast 桌面通知
    if not args.no_toast:
        send_windows_toast(
            "🎯 秋招雷达已完成早8点自动更新！",
            f"已为你精选出 {len(featured_jobs)} 个高薪通识岗位，累计纳管 {len(ranked_jobs)} 岗，点击打开作战看板。"
        )

    print(f"[+] 3.0 全流程调度完成！Markdown 全景台账与作战室看板已全面更新。")


if __name__ == "__main__":
    main()
