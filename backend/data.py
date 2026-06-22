HERO = {
    "title_prefix": "洋洋 · ",
    "title_highlight": "CODE",

    "subtitle": "逆向爬虫 · 全栈自动化 · 风控对抗",
    "description": (
        "不接「演示型 Demo」，只做能上线、能跑量、能省人的交付。"
        "覆盖 TikTok 公会运营、电商跨境采集、社媒矩阵、企业 RPA 等真实业务场景。"
    ),
    "cta_text": "查看项目成果",
}

PROCESS = {
    "label": "合作流程",
    "title_before": "从想法到落地，",
    "title_highlight": "只需四步",
    "note": "支持按阶段报价 · MVP 验证通常 1–3 天出方案 · 可签合同",
    "steps": [
        {
            "step": "01",
            "title": "需求沟通",
            "description": "明确业务目标、数据口径、交付形式与时间节点，评估技术可行性与风险点。",
        },
        {
            "step": "02",
            "title": "MVP 验证",
            "description": "快速打通核心链路（抓取 / 逆向 / 自动化），用小成本验证方案能否跑通、是否值得投入。",
        },
        {
            "step": "03",
            "title": "交付上线",
            "description": "完善稳定性、风控对抗、数据清洗与入库，交付可运行脚本、接口或桌面工具，并附使用说明。",
        },
        {
            "step": "04",
            "title": "运维支持",
            "description": "上线后协助排查异常、适配平台变更，按需提供迭代优化与长期维护。",
        },
    ],
}

STATS = [
    {"value": "1000万+", "label": "日级数据抓取量", "desc": "国际航班 / 电商接口"},
    {"value": "100+", "label": "交付外包项目", "desc": "To B / To C 真实需求"},
    {"value": "30TB+", "label": "游戏资源采集", "desc": "3 个月完成突破"},
    {"value": "1000+", "label": "矩阵账号运维", "desc": "Facebook 稳定运行 3 个月"},
]

SKILLS = [
    {
        "category": "爬虫 & 自动化",
        "icon": "🕷",
        "items": [
            "Python / Scrapy / aiohttp",
            "Playwright / Selenium / Puppeteer",
            "AutoUI2 手机自动化",
            "指纹浏览器 AdsPower 对接",
            "curl_cffi TLS/JA3 指纹突破",
        ],
    },
    {
        "category": "逆向 & 风控对抗",
        "icon": "🔓",
        "items": [
            "JS 混淆还原 / Hook 调试",
            "Sign 纯算协议破解",
            "滑动 / 旋转验证码绕过",
            "Canvas / WebRTC 指纹对抗",
            "Chrome DevTools + AI 协作逆向",
        ],
    },
    {
        "category": "后端 & 工程化",
        "icon": "⚙",
        "items": [
            "FastAPI / Flask 接口服务",
            "MySQL Redis数据清洗入库",
            "Node.js 浏览器插件后端",
            "Qt5 桌面 UI 开发",
            "LangChain AI 智能体",
        ],
    },
    {
        "category": "系统 & 安全",
        "icon": "🛡",
        "items": [
            "Windows 进程注入 / DLL Hook",
            "MinHook 内存参数修改",
            "Fiddler / Charles 抓包分析",
            "微信小程序 / App 协议逆向",
            "代理池 / Socks5 会话保持",
        ],
    },
]

DOMAINS = [
    {
        "id": "domain-1",
        "badge": "电商 & 跨境",
        "title": "突破反爬，<br>批量采集商品数据",
        "description": (
            "覆盖京东、淘宝、天猫、抖音、小红书、亚马逊、Shopee、Ozon 等主流平台。"
            "解决滑动验证码、JS 环境监测、IP 代理、请求头签名等<strong>多层反爬机制</strong>，"
            "实现商品监听、评论采集、竞品上架自动化，输出 Excel / JSON 一体化交付。"
        ),
        "image": "",
        "image_alt": "电商数据采集",
        "tags": ["1688 竞品上架", "Shopee 监听", "评论情感分析", "供应商联系方式"],
        "reverse": False,
    },
    {
        "id": "domain-2",
        "badge": "社媒 & 矩阵运营",
        "title": "多账号环境隔离，<br>规模化自动化运营",
        "description": (
            "基于 AdsPower 指纹浏览器实现<strong>500–1000 账号矩阵</strong>，"
            "Facebook 每日发布视频超万次，稳定运行 3 个月。"
            "涵盖小红书批量点赞、TikTok 直播数据抓取、微博帖子采集、"
            "抖音协议点赞收藏等全流程自动化。"
        ),
        "image": "",
        "image_alt": "社交媒体自动化",
        "tags": ["Facebook 矩阵", "小红书智能体", "TikTok 直播", "批量点赞"],
        "reverse": True,
    },
    {
        "id": "domain-3",
        "badge": "企业 & 办公效率",
        "title": "RPA 流程自动化，<br>零人工介入",
        "description": (
            "为旅游、游戏、教育等行业客户搭建<strong>采集 → 清洗 → 入库 → 预警</strong>全链路。"
            "Akamai 风控突破、Git 定时部署、IMAP 邮件预警钉钉通知、"
            "办公平台 API 中间脚本，大幅提升团队办公效率。"
        ),
        "image": "",
        "image_alt": "企业自动化",
        "tags": ["Akamai 突破", "邮件预警", "浏览器插件", "定时任务"],
        "reverse": False,
    },
    {
        "id": "domain-4",
        "badge": "AI & 智能体",
        "title": "LangChain 驱动，<br>内容生产全自动",
        "description": (
            "构建小红书 AI 智能体：Playwright 采集 → LLM 生成标题/正文 → "
            "AI 图片/视频生成 → 定时发布，<strong>全程无需人工介入</strong>。"
            "支持图文/视频双模式，Qt5 桌面 UI 交互，三种 AI 模型协同。"
        ),
        "image": "",
        "image_alt": "AI 智能体",
        "tags": ["LangChain", "Prompt 模板", "定时发布", "微信小程序"],
        "reverse": True,
    },
]

PROJECTS = [
    {
        "title": "TikTok PC 直播间数据采集",
        "period": "公会运营 · 外包交付",
        "client": "直播公会 / MCN",
        "result": "结构化主播库 · 支持分层运营与拉帮入会",
        "description": "合法接口获取 PC 端直播间关键数据，清洗整合后用于定向挖猎优质主播。",
        "tags": ["TikTok", "数据清洗", "公会运营"],
        "highlight": "主播信息库",
    },
    {
        "title": "Facebook 养号矩阵",
        "period": "2026.02 – 2026.05",
        "client": "出海营销团队",
        "result": "1000 账号矩阵 · 日发 10000+ 视频 · 稳定 3 个月",
        "description": "AdsPower 环境隔离 + Meta 定时发布，替代人工上传，降低封号与人力成本。",
        "tags": ["AdsPower", "多线程", "Meta API"],
        "highlight": "10000+ 次/日",
        "demo_video": "/assets/videos/facebook-yanghao.mp4",
        "demo_anchor": "facebook-matrix",
    },
    {
        "title": "抖音获客自动化",
        "period": "社媒运营 · 外包交付",
        "client": "本地生活 / 电商引流团队",
        "result": "评论区回复 + 私信触达 · 关键词匹配 · CSV 导出",
        "description": (
            "同一套指纹浏览器 + Playwright 抖音网页自动化，提供两种获客方式："
            "① 评论区模式——按关键词搜索视频，展开评论区匹配询价/求购等意向词并自动回复；"
            "② 私信模式——命中评论后进入用户主页发送私信模板，支持每小时频率限制与 JSON 记录。"
        ),
        "tags": ["Playwright", "抖音", "评论区", "私信获客", "关键词筛选"],
        "highlight": "双模式获客",
        "demo_video": "/assets/videos/douyin-pinglun-huoke.mp4",
        "demo_anchor": "douyin-comment-leads",
    },
    {
        "title": "小红书 LangChain 智能体",
        "period": "2026.04 – 2026.05",
        "client": "内容运营团队",
        "result": "采集-生成-发布全自动 · 0 人工值守",
        "description": "三种 AI 模型协同产出图文/视频，Qt5 定时发布，内容产能提升数倍。",
        "tags": ["LangChain", "Playwright", "Qt5"],
        "highlight": "全自动",
    },
    {
        "title": "1688 竞品上架自动化",
        "period": "跨境电商 · Kilimall 卖家",
        "client": "跨境 / 国内卖家",
        "result": "Kilimall 热销 → 1688 货源 → 自动上架 · 1300+ SKU",
        "description": (
            "指纹浏览器 + Playwright 串联全流程：Kilimall 竞品采集 → 豆包 AI 生成 1688 选品词 → "
            "1688 销量 TOP 货源与图文下载 → HS 海关归类/英文标题 → 按成本规则自动定价，"
            "批量填入 Kilimall 卖家中心，支持定时上架与断点续传。"
        ),
        "tags": ["Kilimall", "1688", "Playwright", "豆包 AI"],
        "highlight": "全链路 RPA",
        "demo_anchor": "1688-pick",
    },
    {
        "title": "国际航班千万级抓取",
        "period": "2026.04 – 至今",
        "client": "旅游数据公司",
        "result": "日抓取 1000 万+ · Akamai 风控突破",
        "description": "航班数据清洗入库，Git 定时部署，支撑比价与航线分析业务。",
        "tags": ["Akamai", "千万级", "FastAPI"],
        "highlight": "1000万+/日",
    },
    {
        "title": "游戏 3D 资源采集",
        "period": "2025.10 – 2026.03",
        "client": "游戏资源平台",
        "result": "3 个月 30TB 资源 · 插件提速采集",
        "description": "外网模型站批量抓取 + UE 解包，缩短内容储备周期。",
        "tags": ["Scrapy", "浏览器插件", "UE 解包"],
        "highlight": "30TB+",
    },
    {
        "title": "网页自动化抢票插件",
        "period": "活动运营 · 外包交付",
        "client": "票务 / 活动方",
        "result": "毫秒级响应放票 · 监听自动触发",
        "description": "Chrome 扩展 + 放票监听，Injected Runner 注入，提升抢票成功率。",
        "tags": ["Chrome 扩展", "监听", "Inject"],
        "highlight": "毫秒级",
    },
    {
        "title": "IMAP 邮件预警系统",
        "period": "2026.04 – 2026.05",
        "client": "企业内部运营",
        "result": "异常邮件实时钉钉 @负责人",
        "description": "163 邮箱 IMAP 监控 + 规则清洗，替代人工刷邮件。",
        "tags": ["FastAPI", "IMAP", "钉钉"],
        "highlight": "实时预警",
    },
    {
        "title": "Sign 纯算协议破解",
        "period": "逆向工程 · 多平台",
        "client": "数据采集 / 自动化客户",
        "result": "无浏览器依赖 · 3+ 平台协议复用",
        "description": "谷歌翻译、闲鱼/淘宝 Sign、云片验证码纯算，降低资源占用与封号率。",
        "tags": ["JS 逆向", "纯算", "协议"],
        "highlight": "3+ 平台",
    },
]

# 案例页分区：演示视频（按项目） + 交付截图（统一归档）
CASE_SECTIONS = [
    {
        "id": "demo-videos",
        "type": "videos",
        "name": "项目演示视频",
        "description": "代表项目的实操录屏，与首页「项目成果」对应；先看怎么跑，再往下看交付截图。",
    },
    {
        "id": "delivery-screenshots",
        "type": "screenshots",
        "name": "项目交付截图",
        "description": (
            "真实运行界面、脚本输出与数据产出，统一归档。"
            "涵盖电商跨境、社媒矩阵、数据采集逆向、企业 RPA 等场景，均为已上线交付记录。"
        ),
    },
]

DEMO_VIDEOS = [
    {
        "id": "facebook-matrix",
        "title": "Facebook 养号矩阵",
        "project_title": "Facebook 养号矩阵",
        "description": "AdsPower 多账号环境隔离 + Meta 定时发布，矩阵养号与批量发视频实操录屏。",
        "result": "1000 账号 · 日发 10000+ 视频 · 稳定 3 个月",
        "video": "/assets/videos/facebook-yanghao.mp4",
        "video_hls": "/assets/videos/facebook-yanghao/master.m3u8",
    },
    {
        "id": "1688-pick",
        "title": "1688 竞品上架 · 竞品挑选",
        "project_title": "1688 竞品上架自动化",
        "description": (
            "Kilimall 按关键词分页采集热销商品，去重后取 reviews TOP；豆包分析批次标题生成 1688 搜索词；"
            "1688 按销量筛选货源并下载详情图文，HS编码网检索 + 豆包输出海关品名、HS 编码与英文标题，写入 CSV。"
        ),
        "result": "热销 TOP · 豆包选词 · 1688 货源 + 海关归类",
        "video": "/assets/videos/1688-jingpin-tiaoxuan.mp4",
        "video_hls": "/assets/videos/1688-jingpin-tiaoxuan/master.m3u8",
    },
    {
        "id": "1688-upload",
        "title": "1688 竞品上架 · 自动上架",
        "project_title": "1688 竞品上架自动化",
        "description": (
            "读取 1688 商品资料，Playwright 驱动 Kilimall 卖家中心：自动选类目、上传主图、"
            "填写 HS/中英标题与包装信息，按成本+运费+佣金+利润率算价，批量设置 SKU 库存；"
            "支持立即、延迟或指定时间上架，可从任意序号断点续传。"
        ),
        "result": "1300+ SKU 批量上架 · 自动定价 · 定时发布",
        "video": "/assets/videos/1688-zidong-shangjia.mp4",
        "video_hls": "/assets/videos/1688-zidong-shangjia/master.m3u8",
    },
    {
        "id": "douyin-comment-leads",
        "title": "抖音获客 · 评论区回复",
        "project_title": "抖音获客自动化",
        "description": (
            "指纹浏览器启动抖音环境，Playwright 按关键词搜索视频并打开评论区；"
            "批量展开回复、滚动加载评论，匹配询价/求购/联系方式等默认关键词，"
            "命中后立即回复模板话术，并将视频信息与评论明细导出 CSV。"
        ),
        "result": "关键词匹配 · 评论区自动回复 · CSV 导出",
        "video": "/assets/videos/douyin-pinglun-huoke.mp4",
        "video_hls": "/assets/videos/douyin-pinglun-huoke/master.m3u8",
    },
    {
        "id": "douyin-dm-leads",
        "title": "抖音获客 · 私信触达",
        "project_title": "抖音获客自动化",
        "description": (
            "与评论区模式共用搜索与关键词筛选流程；命中意向评论后自动进入评论者主页，"
            "点击私信按钮发送模板话术，支持每视频私信上限、1 小时 35 条频率控制，"
            "私信记录实时写入 JSON，评论明细同步导出 CSV。"
        ),
        "result": "点头像私信 · 频率限制 · JSON/CSV 导出",
        "video": "/assets/videos/douyin-sixin-huoke.mp4",
        "video_hls": "/assets/videos/douyin-sixin-huoke/master.m3u8",
    },
]

CONTACT = {
    "email": "2029203568@qq.com",
    "location": "上海",
    "github": "",
    "wechat_qr": "/assets/wechat-qr.jpg",
}

SITE = {
    "brand": "洋洋",
    "logo": "",
    "copyright": "© 2026 洋洋 · 技术博客. All rights reserved.",
}

CASES = {
    "hero": {
        "label": "REAL CASES",
        "title_prefix": "帮您实现 ",
        "title_highlight": "MVP",
        "title_suffix": " 可行性验证",
        "tagline": "您有想法，我们给结果",
        "description": "自 2024 年至今，已服务 100+ 真实案例，均来自市场真实需求。从想法到落地，专注可交付的技术结果。",
    },
    "stats": [
        {"value": "100+", "label": "真实交付案例"},
        {"value": "2024—", "label": "持续服务至今"},
        {"value": "100%", "label": "来自市场需求"},
    ],
    "pillars": [
        {
            "icon": "🚀",
            "title": "MVP 快速验证",
            "description": "用最小成本验证想法是否可行，快速出原型、跑通核心流程，避免盲目投入。",
        },
        {
            "icon": "🛡",
            "title": "可靠交付与安防",
            "description": "风控对抗、环境隔离、稳定运维，保障自动化方案长期可用、账号与数据安全。",
        },
        {
            "icon": "📈",
            "title": "市场需求驱动",
            "description": "每一个案例均来自 To B / To C 真实外包需求，解决实际问题，而非演示 Demo。",
        },
    ],
    "gallery": {
        "label": "交付记录",
        "title_before": "演示视频与",
        "title_highlight": "交付",
        "title_after": "截图",
        "description": "演示视频按项目展示实操过程；交付截图统一归档，与首页项目成果相互印证。",
    },
    "cta": {
        "title": "有想法，就能落地",
        "description": "从 MVP 验证到完整交付，告诉我您的需求，我来给出可执行的技术方案。",
        "button": "实现您的需求",
    },
}

SIDE_NAV = [
    {"id": "hero", "label": "首页"},
    {"id": "stats", "label": "数据"},
    {"id": "skills", "label": "技能"},
    {"id": "domain-1", "label": "领域"},
    {"id": "projects", "label": "项目"},
    {"id": "process", "label": "流程"},
]

PROJECTS_SECTION = {
    "intro": "以下均为真实外包交付，标注服务对象与可量化结果，而非仅罗列技术栈。",
}
