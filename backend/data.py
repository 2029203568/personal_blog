HERO = {
    "title_prefix": "于洋洋 · ",
    "title_highlight": "CODE",
    "subtitle": "逆向爬虫 · 全栈自动化 · 风控对抗",
    "description": (
        "专注 Web/App 逆向、大规模数据采集与 RPA 自动化落地。"
        "从 JS 混淆破解到千万级日抓取，从指纹浏览器矩阵到 AI 智能体全流程，"
        "为电商、社媒、游戏资源、企业办公等场景提供定制化技术方案。"
    ),
    "cta_text": "查看项目成果",
}

STATS = [
    {"value": "1000万+", "label": "日级数据抓取量", "desc": "国际航班 / 电商接口"},
    {"value": "50+", "label": "交付外包项目", "desc": "To B / To C 真实需求"},
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
            "MySQL 数据清洗入库",
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
        "title": "Facebook 养号矩阵",
        "period": "2026.02 – 2026.05",
        "description": "AdsPower 环境隔离 + Meta 定时发布，500–1000 账号，日发视频 10000+ 次，稳定运行 3 个月。",
        "tags": ["AdsPower", "多线程", "Meta API"],
        "highlight": "10000+ 次/日",
    },
    {
        "title": "小红书 LangChain 智能体",
        "period": "2026.04 – 2026.05",
        "description": "采集-生成-发布全流程自动化，三种 AI 模型协同，Qt5 UI + 定时发布，零人工介入。",
        "tags": ["LangChain", "Playwright", "Qt5"],
        "highlight": "全自动",
    },
    {
        "title": "1688 竞品上架自动化",
        "period": "外包交付",
        "description": "突破滑动验证码与挑战页，自动爬取供应商联系方式，表格输入输出一体化。",
        "tags": ["1688", "验证码", "RPA"],
        "highlight": "1300+ SKU",
    },
    {
        "title": "国际航班千万级抓取",
        "period": "2026.04 – 至今",
        "description": "突破 Akamai 风控，日抓取千万级航班数据，Git 定时部署 + MySQL 清洗入库。",
        "tags": ["Akamai", "千万级", "FastAPI"],
        "highlight": "1000万+/日",
    },
    {
        "title": "游戏 3D 资源采集",
        "period": "2025.10 – 2026.03",
        "description": "3 个月抓取 30TB 游戏模型资源，浏览器插件提速，UE 解包与 TA 技术美术处理。",
        "tags": ["Scrapy", "浏览器插件", "UE 解包"],
        "highlight": "30TB+",
    },
    {
        "title": "网页自动化抢票插件",
        "period": "外包交付",
        "description": "Chrome 扩展 + 放票监听程序，Injected Runner 注入，毫秒级响应抢票操作。",
        "tags": ["Chrome 扩展", "监听", "Inject"],
        "highlight": "毫秒级",
    },
    {
        "title": "IMAP 邮件预警系统",
        "period": "2026.04 – 2026.05",
        "description": "FastAPI 后端 + 163 邮箱 IMAP 监控，关键词规则清洗，钉钉机器人 @负责人通知。",
        "tags": ["FastAPI", "IMAP", "钉钉"],
        "highlight": "实时预警",
    },
    {
        "title": "Sign 纯算协议破解",
        "period": "逆向工程",
        "description": "谷歌翻译 Acs-Token、闲鱼/淘宝 Sign、云片滑动验证码纯算模拟，无浏览器依赖。",
        "tags": ["JS 逆向", "纯算", "协议"],
        "highlight": "3+ 平台",
    },
]

CONTACT = {
    "email": "2029203568@qq.com",
    "location": "上海",
    "github": "",
    "wechat_qr": "/assets/wechat-qr.jpg",
}

SITE = {
    "brand": "于洋洋",
    "logo": "",
    "copyright": "© 2026 于洋洋 · 技术博客. All rights reserved.",
}

SIDE_NAV = [
    {"id": "hero", "label": "首页"},
    {"id": "stats", "label": "数据"},
    {"id": "skills", "label": "技能"},
    {"id": "domain-1", "label": "领域"},
    {"id": "projects", "label": "项目"},
]
