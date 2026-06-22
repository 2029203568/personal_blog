import csv
import json
import math
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

import cv2
import numpy as np
import requests
from playwright.sync_api import BrowserContext, Frame, Locator, Page, sync_playwright


BASE_URL = "http://localhost:50213"
SHOP_LIST_API = f"{BASE_URL}/api/v2/userapi/user/shopseriallist"
BROWSER_START_API = f"{BASE_URL}/api/v2/browser/start"

DOUYIN_HOME = "https://www.douyin.com/"
DEFAULT_SEARCH_KEYWORD = "日本"
DEFAULT_VIDEO_COUNT = 1
DEFAULT_MAX_EXPAND_CLICKS = 50
DEFAULT_MAX_VISITS_PER_VIDEO = 10
DEFAULT_AUTO_VISIT = True
DEFAULT_DM_TEMPLATE = "你好我们有产品请联系我们"
DM_HOURLY_LIMIT = 35
DM_RECORDS_FILENAME = "私信记录.json"
EXPAND_BATCH_SIZE = 5
CAPTCHA_MAX_RETRIES = 5
CAPTCHA_DISTANCE_RETRY_OFFSETS = (-6, -4, -2, 0, 2, 4, 6)
SKIP_COMMENT_TEXTS = frozenset({"作者赞过", "作者回复过"})


def _normalize_comment_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lines = [line for line in lines if line not in SKIP_COMMENT_TEXTS]
    return "\n".join(lines)

CSV_COLUMNS = [
    "视频标题",
    "发布作者",
    "发布时间",
    "评论人昵称",
    "评论内容",
    "命中关键词",
    "是否私信",
    "处理结果",
]


class PostInfo(TypedDict):
    title: str
    author: str
    publish_time: str


class CommentRecord(TypedDict):
    video_title: str
    video_author: str
    video_publish_time: str
    comment_nickname: str
    comment_content: str
    matched_keyword: str
    replied: str
    reply_content: str


def human_pause(page: Page, min_ms: int = 300, max_ms: int = 900) -> None:
    page.wait_for_timeout(random.randint(min_ms, max_ms))


def human_reading_pause(page: Page, min_ms: int = 1200, max_ms: int = 2800) -> None:
    page.wait_for_timeout(random.randint(min_ms, max_ms))


def human_move_to(page: Page, locator: Locator) -> None:
    try:
        box = locator.bounding_box()
        if not box:
            locator.hover(timeout=3000)
            return
        x = box["x"] + box["width"] * random.uniform(0.25, 0.75)
        y = box["y"] + box["height"] * random.uniform(0.25, 0.75)
        page.mouse.move(x, y, steps=random.randint(10, 22))
        human_pause(page, 80, 220)
    except Exception:
        try:
            locator.hover(timeout=2000)
        except Exception:
            pass


def human_click(page: Page, locator: Locator, timeout: int = 5000) -> None:
    click_with_fallback(page, locator, timeout=timeout)


def dismiss_douyin_home_interruptions(page: Page) -> None:
    """关闭首页可能遮挡搜索框的弹窗/提示。"""
    close_selectors = [
        '[data-e2e="login-close"]',
        '[data-e2e="modal-close-inner-button"]',
        "div.semi-modal-close",
        '[aria-label="关闭"]',
        'button:has-text("我知道了")',
        'button:has-text("以后再说")',
        'span:has-text("我知道了")',
    ]
    for selector in close_selectors:
        btn = page.locator(selector).first
        if btn.count() == 0:
            continue
        try:
            if btn.is_visible():
                click_with_fallback(page, btn, timeout=2000)
                human_pause(page, 300, 600)
        except Exception:
            continue


def human_fill_input(page: Page, locator: Locator, text: str) -> None:
    locator.wait_for(state="visible", timeout=30000)
    locator.scroll_into_view_if_needed(timeout=30000)
    try:
        click_with_fallback(page, locator, timeout=8000)
    except Exception:
        try:
            locator.focus(timeout=3000)
        except Exception:
            locator.evaluate("el => el.focus()")
    human_pause(page, 100, 280)
    try:
        locator.fill("")
    except Exception:
        locator.press("Control+A")
        human_pause(page, 100, 280)
        locator.press("Backspace")
    human_pause(page, 180, 450)
    human_type_text(page, text)


def click_with_fallback(
    page: Page, locator: Locator, timeout: int = 8000, *, fast: bool = False
) -> None:
    """普通点击被视频层遮挡时，依次尝试 force 点击和 JS 点击。"""
    locator.wait_for(state="visible", timeout=timeout)
    locator.scroll_into_view_if_needed(timeout=timeout)
    if fast:
        human_pause(page, 50, 120)
    else:
        human_pause(page, 250, 700)
    try:
        if not fast:
            human_move_to(page, locator)
        delay = random.randint(20, 60) if fast else random.randint(70, 200)
        locator.click(delay=delay, timeout=3000)
    except Exception:
        try:
            locator.click(force=True, timeout=3000)
        except Exception:
            locator.evaluate(
                """(el) => {
                    el.dispatchEvent(new MouseEvent('click', {
                        bubbles: true, cancelable: true, view: window
                    }));
                }"""
            )
    if fast:
        human_pause(page, 80, 200)
    else:
        human_pause(page, 350, 900)


def human_type_text(page: Page, text: str, *, fast: bool = False) -> None:
    delay_range = (15, 45) if fast else (55, 170)
    for char in text:
        page.keyboard.type(char, delay=random.randint(*delay_range))
        if not fast and random.random() < 0.1:
            human_pause(page, 150, 400)


def human_scroll_element(
    page: Page,
    locator: Locator,
    step: int | None = None,
    min_pause: int = 400,
    max_pause: int = 1000,
) -> None:
    if step is None:
        step = random.randint(320, 580)
    chunks = random.randint(2, 4)
    for chunk_index in range(chunks):
        distance = step // chunks + random.randint(-35, 35)
        locator.evaluate(
            "(el, d) => { el.scrollTop = Math.min(el.scrollTop + d, el.scrollHeight); }",
            distance,
        )
        human_pause(page, 120, 300)
        if chunk_index == chunks - 1 and random.random() < 0.25:
            human_pause(page, 200, 500)
    human_pause(page, min_pause, max_pause)


DEFAULT_KEYWORDS = [
    # 询价
    "多少钱", "价格多少", "报价", "费用", "贵吗", "划算吗", "怎么收费",
    # 求购/求推荐
    "求推荐", "哪里有", "想买", "想要", "求带", "求资源", "求介绍",
    # 联系方式
    "怎么联系", "有微信吗", "私我", "加我", "联系方式", "留个电话",
    # 对比/决策
    "怎么样", "靠谱吗", "好不好", "效果如何", "值得买吗", "有坑吗",
    # 抱怨/痛点
    "太难了", "不会选", "踩雷", "被坑了", "后悔", "来不及了", "急需",
    # 行动暗示
    "已私信", "已关注", "求带路", "拉我", "报名", "想了解",
]


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError(f"接口返回不是 JSON 对象: {url}")
    return data


def fetch_env_list() -> list[dict[str, Any]]:
    payload = {"groupId": "", "accountName": ""}
    result = post_json(SHOP_LIST_API, payload)
    if result.get("code") != 0:
        raise RuntimeError(f"获取环境列表失败: code={result.get('code')} msg={result.get('msg')}")
    env_list = ((result.get("data") or {}).get("list")) or []
    if not isinstance(env_list, list):
        return []
    return [x for x in env_list if isinstance(x, dict)]


def choose_env(env_list: list[dict[str, Any]]) -> dict[str, Any]:
    if not env_list:
        raise RuntimeError("环境列表为空，请先在本地客户端创建环境。")

    print("\n可用环境列表:")
    for idx, item in enumerate(env_list, start=1):
        serial = item.get("serial", "")
        account_name = item.get("accountName", "")
        shop_id = item.get("shopId", "")
        group_id = item.get("groupId", "")
        print(f"{idx:>2}. serial={serial} | 名称={account_name} | shopId={shop_id} | groupId={group_id}")

    while True:
        raw = input("\n请输入要启动的环境序号(如 1): ").strip()
        if not raw.isdigit():
            print("输入无效，请输入数字。")
            continue
        n = int(raw)
        if 1 <= n <= len(env_list):
            return env_list[n - 1]
        print(f"超出范围，请输入 1 ~ {len(env_list)}。")


def start_browser(account_id: str) -> dict[str, Any]:
    payload = {
        "account_id": account_id,
        "append_cmd": "",
        "headless": "0",
    }
    result = post_json(BROWSER_START_API, payload)
    if result.get("code") != 0:
        raise RuntimeError(f"启动环境失败: code={result.get('code')} msg={result.get('msg')}")
    data = result.get("data") or {}
    if not isinstance(data, dict):
        raise RuntimeError("启动环境返回 data 格式错误。")
    return data


def ask_search_keyword() -> str:
    raw = input(f"\n请输入搜索关键词(直接回车使用默认「{DEFAULT_SEARCH_KEYWORD}」): ").strip()
    return raw or DEFAULT_SEARCH_KEYWORD


def ask_video_count() -> int:
    while True:
        raw = input(
            f"\n请输入要处理评论的视频个数(直接回车使用默认 {DEFAULT_VIDEO_COUNT} 个): "
        ).strip()
        if not raw:
            return DEFAULT_VIDEO_COUNT
        if raw.isdigit() and int(raw) >= 1:
            return int(raw)
        print("输入无效，请输入大于等于 1 的整数。")


def ask_keywords() -> list[str]:
    print("\n默认关键词类别:")
    print("  询价: 多少钱、价格多少、报价、费用、贵吗、划算吗、怎么收费")
    print("  求购: 求推荐、哪里有、想买、想要、求带、求资源、求介绍")
    print("  联系: 怎么联系、有微信吗、私我、加我、联系方式、留个电话")
    print("  决策: 怎么样、靠谱吗、好不好、效果如何、值得买吗、有坑吗")
    print("  痛点: 太难了、不会选、踩雷、被坑了、后悔、来不及了、急需")
    print("  行动: 已私信、已关注、求带路、拉我、报名、想了解")
    raw = input(
        "\n请输入自定义关键词(多个用逗号分隔，直接回车使用默认关键词): "
    ).strip()
    if not raw:
        return list(DEFAULT_KEYWORDS)
    keywords = [k.strip() for k in re.split(r"[,，、\s]+", raw) if k.strip()]
    return keywords or list(DEFAULT_KEYWORDS)


def ask_max_expand_clicks() -> int:
    while True:
        raw = input(
            f"\n请输入每个视频评论区展开按钮总点击次数"
            f"(直接回车使用默认 {DEFAULT_MAX_EXPAND_CLICKS} 次): "
        ).strip()
        if not raw:
            return DEFAULT_MAX_EXPAND_CLICKS
        if raw.isdigit() and int(raw) >= 0:
            return int(raw)
        print("输入无效，请输入大于等于 0 的整数。")


def ask_dm_template() -> str:
    raw = input(
        f"\n请输入私信模板(直接回车使用默认「{DEFAULT_DM_TEMPLATE}」): "
    ).strip()
    return raw or DEFAULT_DM_TEMPLATE


def ask_max_visits_per_video() -> int:
    while True:
        raw = input(
            f"\n请输入每个视频最多私信次数"
            f"(直接回车使用默认 {DEFAULT_MAX_VISITS_PER_VIDEO} 次，输入 0 表示不限制): "
        ).strip()
        if not raw:
            return DEFAULT_MAX_VISITS_PER_VIDEO
        if raw.isdigit() and int(raw) >= 0:
            return int(raw)
        print("输入无效，请输入大于等于 0 的整数。")


def get_active_page(context: BrowserContext) -> Page:
    for pg in reversed(context.pages):
        try:
            if not pg.is_closed():
                pg.bring_to_front()
                return pg
        except Exception:
            continue
    page = context.new_page()
    page.bring_to_front()
    return page


def ensure_page_ready(page: Page, context: BrowserContext) -> Page:
    try:
        if page.is_closed():
            raise RuntimeError("page closed")
        return page
    except Exception:
        new_page = get_active_page(context)
        print("原标签页不可用，已切换到可用标签页")
        return new_page


def connect_douyin_browser(p, ws_endpoint: str) -> tuple[Any, BrowserContext, Page]:
    last_exc: Exception | None = None
    for attempt in range(1, 6):
        try:
            browser = p.chromium.connect_over_cdp(ws_endpoint, timeout=30000)
            contexts = browser.contexts
            context = contexts[0] if contexts else browser.new_context()
            page = get_active_page(context)
            current_url = ""
            try:
                current_url = page.url
            except Exception:
                pass
            print(f"已连接浏览器(第 {attempt} 次)，当前标签页: {current_url or '新标签页'}")
            return browser, context, page
        except Exception as exc:
            last_exc = exc
            print(f"连接浏览器失败({attempt}/5): {exc}")
            time.sleep(2)
    raise RuntimeError(f"无法连接浏览器环境: {last_exc}") from last_exc


def safe_goto(page: Page, url: str, context: BrowserContext, *, timeout: int = 60000) -> Page:
    page = ensure_page_ready(page, context)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        return page
    except Exception as exc:
        if "closed" not in str(exc).lower():
            raise
        print(f"导航时标签页已关闭，正在重试: {exc}")
        page = get_active_page(context)
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        return page


def search_on_douyin(page: Page, keyword: str, context: BrowserContext) -> Page:
    print(f"正在打开抖音首页: {DOUYIN_HOME}")
    page = safe_goto(page, DOUYIN_HOME, context)
    human_reading_pause(page, 1800, 3200)
    dismiss_douyin_home_interruptions(page)

    search_input = page.locator('[data-e2e="searchbar-input"]')
    search_input.wait_for(state="visible", timeout=30000)
    human_fill_input(page, search_input, keyword)
    human_pause(page, 400, 900)

    search_button = page.locator('[data-e2e="searchbar-button"]')
    human_click(page, search_button)
    print(f"已搜索关键词: {keyword}")

    page.locator("#search-result-container, #search-content-area").first.wait_for(
        state="visible", timeout=30000
    )
    human_reading_pause(page, 1500, 2800)
    wait_for_search_videos(page)
    return page


def _read_locator_text(locator: Locator, timeout: int = 2000) -> str:
    if locator.count() == 0:
        return ""
    try:
        return locator.inner_text(timeout=timeout).strip()
    except Exception:
        return ""


def is_scroll_list_layout(page: Page) -> bool:
    scroll_list = page.locator('ul[data-e2e="scroll-list"]')
    if scroll_list.count() == 0:
        return False
    try:
        return scroll_list.first.is_visible()
    except Exception:
        return False


def _normalize_publish_time(text: str) -> str:
    return re.sub(r"^[·\s]+", "", text).strip()


def extract_post_info_from_waterfall_item(item: Locator) -> PostInfo:
    title = _read_locator_text(
        item.locator(
            ".X8RuTw0W .RBpYLmIg, .g_CC0Sp2 .RBpYLmIg, .RBpYLmIg, "
            "div.BjLsdJMi, .K4Ja9W9H div.BjLsdJMi, .vrPRtA6U div.BjLsdJMi"
        ).first
    )
    meta_el = item.locator(".AgRax2gG, div.RY_wFBXl, .K4Ja9W9H div.RY_wFBXl").first
    author = _read_locator_text(
        meta_el.locator("span.lGzJpEad, .L_NECGJi .lGzJpEad, span.WldPmwm5").first
    )
    author = author.lstrip("@").strip()
    publish_time = _normalize_publish_time(
        _read_locator_text(meta_el.locator("span.Yftofmx6, span.dO8W7uoF").first)
    )
    return PostInfo(title=title, author=author, publish_time=publish_time)


def extract_post_info_from_scroll_list_item(item: Locator) -> PostInfo:
    title = _read_locator_text(
        item.locator(
            ".YOd74VnT .KYUFliur, .TG7OZENa .KYUFliur, "
            ".DFsxdHs2 .F1Jesh1w, .DFsxdHs2 span.cWFktkUR"
        ).first
    )
    meta_el = item.locator(".ycfEUnvt, .bUvqLwJV, .UUu6dldY").first
    author = _read_locator_text(
        meta_el.locator(
            "a.gpzfpvmu .KYUFliur, .YPGZWw4P .KYUFliur, "
            "p.Buidgdt4, a.jwmvCVIo.t9UjRDmM p.Buidgdt4"
        ).first
    )
    publish_time = _normalize_publish_time(
        _read_locator_text(meta_el.locator("p.IhQeg9vr, p.qJ5BPfxR").first)
    )
    return PostInfo(title=title, author=author, publish_time=publish_time)


def extract_post_info_from_search_item(
    item: Locator, *, scroll_list: bool = False
) -> PostInfo:
    if scroll_list:
        return extract_post_info_from_scroll_list_item(item)
    return extract_post_info_from_waterfall_item(item)


def extract_post_info_from_active_video(page: Page) -> PostInfo:
    active_video = get_active_video(page)
    title = _read_locator_text(
        active_video.locator('[data-e2e="video-desc"], .title[data-e2e="video-desc"]').first
    )
    author = _read_locator_text(
        active_video.locator(
            '[data-e2e="feed-video-nickname"], .account-name-text'
        ).first
    )
    author = author.lstrip("@").strip()
    publish_time = _normalize_publish_time(
        _read_locator_text(
            active_video.locator(".video-create-time .time, .account .time").first
        )
    )
    return PostInfo(title=title, author=author, publish_time=publish_time)


def merge_post_info(primary: PostInfo, fallback: PostInfo) -> PostInfo:
    return PostInfo(
        title=primary["title"] or fallback["title"],
        author=primary["author"] or fallback["author"],
        publish_time=primary["publish_time"] or fallback["publish_time"],
    )


SEARCH_RESULT_VIDEO_SELECTOR = (
    '[data-e2e="feed-video"], [data-e2e="feed-active-video"], #sliderVideo'
)
SEARCH_RESULT_CLICK_SELECTOR = (
    f"{SEARCH_RESULT_VIDEO_SELECTOR}, "
    ".douyin-player, .playerContainer, .tWwml1jQ, .nbExF2ih, "
    ".jGwTAgpj .PV2JPzEx, .jGwTAgpj, "
    ".FrfjJSkC .videoImage, .yb3knZ7b.videoImage, .FrfjJSkC, "
    ".LFQCShEn.videoImage, .videoImage, .search-result-card"
)
LEGACY_WATERFALL_VIDEO_SELECTOR = (
    ".FrfjJSkC, .videoImage, .yb3knZ7b.videoImage, .LFQCShEn"
)


def get_search_waterfall_items(page: Page) -> Locator:
    items = page.locator(
        '#search-result-container div[id^="waterfall_item_"], '
        "#search-result-container div.oWmZEHuF[id^='waterfall_item_'], "
        "#search-result-container .AMqhOzPC"
    )
    items = items.filter(
        has=page.locator(
            f"{SEARCH_RESULT_VIDEO_SELECTOR}, {LEGACY_WATERFALL_VIDEO_SELECTOR}"
        )
    )
    if items.count() > 0:
        return items

    cards = page.locator("#search-result-container .search-result-card").filter(
        has=page.locator(
            f"{SEARCH_RESULT_VIDEO_SELECTOR}, {LEGACY_WATERFALL_VIDEO_SELECTOR}"
        )
    )
    if cards.count() > 0:
        return cards

    return page.locator("#search-result-container li").filter(
        has=page.locator(SEARCH_RESULT_VIDEO_SELECTOR)
    )


def get_search_scroll_list_items(page: Page) -> Locator:
    return page.locator('ul[data-e2e="scroll-list"] > li').filter(
        has=page.locator(SEARCH_RESULT_VIDEO_SELECTOR)
    )


def get_search_result_items(page: Page) -> Locator:
    if is_scroll_list_layout(page):
        items = get_search_scroll_list_items(page)
        if items.count() > 0:
            return items
    items = get_search_waterfall_items(page)
    if items.count() > 0:
        return items
    return page.locator("#search-result-container li").filter(
        has=page.locator(SEARCH_RESULT_VIDEO_SELECTOR)
    )


def wait_for_search_videos(page: Page, timeout_ms: int = 30000) -> None:
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if get_search_result_items(page).count() > 0:
            return
        human_pause(page, 600, 1200)
        scroll_search_results(page, step=400)
    raise RuntimeError("搜索结果页未加载出可点击的视频，请检查关键词或页面布局是否变化")


def scroll_search_results(page: Page, step: int | None = None) -> None:
    scroll_step = step or random.randint(650, 950)
    if is_scroll_list_layout(page):
        scroll_list = page.locator('ul[data-e2e="scroll-list"]').first
        if scroll_list.count() > 0:
            human_scroll_element(page, scroll_list, step=scroll_step)
            return
    container = page.locator("#search-result-container, #search-content-area").first
    human_scroll_element(page, container, step=scroll_step)


def ensure_search_result_item(page: Page, index: int) -> tuple[Locator, bool]:
    attempts = 0
    while attempts < 20:
        scroll_items = get_search_scroll_list_items(page)
        if scroll_items.count() > index:
            item = scroll_items.nth(index)
            item.wait_for(state="visible", timeout=20000)
            item.scroll_into_view_if_needed()
            human_pause(page, 400, 900)
            return item, True

        waterfall_items = get_search_waterfall_items(page)
        if waterfall_items.count() > index:
            item = waterfall_items.nth(index)
            item.wait_for(state="visible", timeout=20000)
            item.scroll_into_view_if_needed()
            human_pause(page, 400, 900)
            return item, False

        scroll_search_results(page)
        attempts += 1

    total = max(
        get_search_scroll_list_items(page).count(),
        get_search_waterfall_items(page).count(),
    )
    raise RuntimeError(
        f"搜索结果不足，需要第 {index + 1} 个视频，当前仅找到 {total} 个。"
    )


def get_active_video(page: Page) -> Locator:
    modal_video = page.locator(
        '[data-e2e="modal-video-container"] [data-e2e="feed-active-video"]'
    )
    if modal_video.count() > 0:
        try:
            if modal_video.first.is_visible():
                return modal_video.first
        except Exception:
            pass

    active_video = page.locator('[data-e2e="feed-active-video"]').first
    active_video.wait_for(state="visible", timeout=30000)
    return active_video


def get_pause_button(active_video: Locator) -> Locator | None:
    pause_selectors = [
        'xg-icon.xgplayer-play[data-state="play"]',
        'xg-icon.xgplayer-play:has(.xg-icon-pause)',
        ".xgplayer-play[data-state='play']",
        ".douyin-player-icon.douyin-player-play",
        ".douyin-player-play",
    ]
    for selector in pause_selectors:
        btn = active_video.locator(selector).first
        if btn.count() == 0:
            continue
        try:
            if btn.is_visible():
                return btn
        except Exception:
            continue
    return None


def is_video_paused(active_video: Locator) -> bool:
    paused_selectors = [
        'xg-icon.xgplayer-play[data-state="pause"]',
        ".xgplayer-play[data-state='pause']",
        ".douyin-player.douyin-player-pause",
        ".douyin-player-pause",
    ]
    for selector in paused_selectors:
        indicator = active_video.locator(selector).first
        if indicator.count() == 0:
            continue
        try:
            if indicator.is_visible():
                return True
        except Exception:
            continue
    return False


def pause_active_video(page: Page) -> bool:
    active_video = get_active_video(page)
    player_area = active_video.locator(
        ".xgplayer, .douyin-player, .playerContainer, .basePlayerContainer, video"
    ).first
    if player_area.count() > 0:
        try:
            human_move_to(page, player_area)
            human_pause(page, 300, 700)
        except Exception:
            pass

    if is_video_paused(active_video):
        print("视频已处于暂停状态")
        return True

    pause_button = get_pause_button(active_video)
    if pause_button is not None:
        click_with_fallback(page, pause_button)
        human_pause(page, 400, 900)
        print("已暂停当前视频")
        return True

    print("未找到暂停按钮，跳过暂停步骤")
    return False


def wake_video_interaction_area(page: Page) -> None:
    active_video = get_active_video(page)
    interaction_area = active_video.locator(
        ".sfF_Ujit, .hOcDRkbZ, .hlPyF0rE.positionBox, .positionBox"
    ).first
    if interaction_area.count() == 0:
        return
    try:
        human_move_to(page, interaction_area)
        human_pause(page, 200, 500)
    except Exception:
        pass


def get_comment_button(page: Page) -> Locator:
    modal = page.locator('[data-e2e="modal-video-container"]')
    if modal.count() > 0:
        try:
            if modal.first.is_visible():
                btn = modal.locator(
                    '[data-e2e="feed-active-video"] .sfF_Ujit [data-e2e="feed-comment-icon"], '
                    '[data-e2e="feed-active-video"] .hOcDRkbZ [data-e2e="feed-comment-icon"], '
                    '[data-e2e="feed-active-video"] [data-e2e="feed-comment-icon"]'
                ).first
                if btn.count() > 0:
                    return btn
        except Exception:
            pass

    active_video = get_active_video(page)
    selectors = [
        ".sfF_Ujit [data-e2e='feed-comment-icon']",
        ".hOcDRkbZ [data-e2e='feed-comment-icon']",
        ".hlPyF0rE [data-e2e='feed-comment-icon']",
        ".positionBox [data-e2e='feed-comment-icon']",
        '[data-e2e="feed-comment-icon"]',
    ]
    for selector in selectors:
        btn = active_video.locator(selector).first
        if btn.count() == 0:
            continue
        try:
            if btn.is_visible():
                return btn
        except Exception:
            continue
    return active_video.locator('[data-e2e="feed-comment-icon"]').first


def collect_and_open_search_result(page: Page, index: int) -> PostInfo:
    item, scroll_list = ensure_search_result_item(page, index)
    post_info = extract_post_info_from_search_item(item, scroll_list=scroll_list)
    layout_name = "单列列表" if scroll_list else "瀑布流"
    print(f"已在搜索结果页({layout_name})采集第 {index + 1} 个帖子信息:")
    print(f"  标题: {post_info['title'] or '(未获取)'}")
    print(f"  作者: {post_info['author'] or '(未获取)'}")
    print(f"  时间: {post_info['publish_time'] or '(未获取)'}")

    click_target = item.locator(SEARCH_RESULT_CLICK_SELECTOR).first
    human_reading_pause(page, 800, 1600)
    human_click(page, click_target)
    print(f"已点击第 {index + 1} 个搜索结果")

    human_reading_pause(page, 2200, 3800)
    get_active_video(page)

    if not any(post_info.values()):
        fallback = extract_post_info_from_active_video(page)
        post_info = merge_post_info(post_info, fallback)
        print("搜索结果页信息不完整，已从视频页补充:")
        print(f"  标题: {post_info['title'] or '(未获取)'}")
        print(f"  作者: {post_info['author'] or '(未获取)'}")
        print(f"  时间: {post_info['publish_time'] or '(未获取)'}")

    return post_info


def open_comment_panel(page: Page) -> None:
    get_active_video(page)
    pause_active_video(page)
    wake_video_interaction_area(page)
    comment_button = get_comment_button(page)
    comment_button.wait_for(state="visible", timeout=30000)
    human_pause(page, 500, 1200)
    click_with_fallback(page, comment_button)
    print("已打开当前视频的评论区")

    page.locator(
        '#videoSideCard [data-e2e="comment-list"], '
        '[data-e2e="comment-list"], #merge-all-comment-container'
    ).first.wait_for(state="visible", timeout=30000)
    human_reading_pause(page, 1000, 2000)


COMMENT_AUTHOR_SELECTOR = (
    ".comment-item-info-wrap .Sw1iq0tk a.jwmvCVIo [data-click-from='title'], "
    ".comment-item-info-wrap .Sw1iq0tk a.jwmvCVIo, "
    ".comment-item-info-wrap a.jwmvCVIo, "
    ".comment-item-info-wrap a.Z3VQe4ky, "
    ".jyqk68aK a.Z3VQe4ky, "
    ".bTHWOB9x a.Z3VQe4ky, "
    "a.hY8lWHgA"
)
COMMENT_TEXT_SELECTOR = (
    "div.Pmn4RZdg, div.Sbe6bqNb, div.hVlA20pu div.Sbe6bqNb, div.LvAtyU_f"
)
COMMENT_AVATAR_SELECTORS = [
    ".comment-item-avatar .xOf24BBw[data-click-from='click_icon'] a.jwmvCVIo",
    ".comment-item-avatar .xOf24BBw a.jwmvCVIo",
    ".comment-item-avatar .Eu_DN4Bp[data-click-from='click_icon'] a.Z3VQe4ky",
    ".comment-item-avatar .Eu_DN4Bp a.Z3VQe4ky",
    ".r3xWtndX.comment-item-avatar a.Z3VQe4ky",
    '.comment-item-avatar a.jwmvCVIo:has([data-e2e="live-avatar"])',
    '.comment-item-avatar a.Z3VQe4ky:has([data-e2e="live-avatar"])',
    ".comment-item-avatar a.jwmvCVIo",
    ".comment-item-avatar a.Z3VQe4ky",
]


def get_comment_scroll_container(page: Page) -> Locator:
    selectors = [
        "#videoSideCard [data-e2e='comment-list']",
        '[data-e2e="comment-list"]',
        "#merge-all-comment-container",
        "#videoSideCard #merge-all-comment-container",
        ".comment-mainContent",
    ]
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count() > 0:
            return locator
    return page.locator("body")


def scroll_comment_panel(page: Page, step: int | None = None) -> None:
    container = get_comment_scroll_container(page)
    human_scroll_element(page, container, step=step or random.randint(500, 820))


def load_more_comments_by_scrolling(page: Page, steps: int = 4) -> int:
    """连续向下滚动评论区，触发虚拟列表加载更多评论。"""
    before_count = get_comment_items(page).count()
    for step_index in range(steps):
        scroll_comment_panel(page)
        if step_index < steps - 1:
            human_pause(page, 400, 900)
    after_count = get_comment_items(page).count()
    if after_count > before_count:
        print(f"  滚动加载: 可见评论 {before_count} -> {after_count} 条")
    return after_count - before_count


def has_no_more_comments(page: Page) -> bool:
    end_marker = page.locator("div.fanRMYie").filter(has_text="暂时没有更多评论")
    try:
        return end_marker.count() > 0 and end_marker.first.is_visible()
    except Exception:
        return False


def _expand_reply_button_locator(page: Page) -> Locator:
    return page.locator(
        'button.comment-reply-expand-btn:visible, '
        'button.lEo_65ZO:visible, '
        'button:has-text("展开"):has-text("回复"):visible, '
        'button:has(.VZWu521O):visible, '
        'button:has(.Q0y_i6F4):visible, '
        'button:has(.YJKsQai6):visible'
    )


def click_one_expand_reply_button(page: Page) -> bool:
    expand_buttons = _expand_reply_button_locator(page)
    count = expand_buttons.count()
    for index in range(count):
        button = expand_buttons.nth(index)
        try:
            text = button.inner_text(timeout=1000)
        except Exception:
            continue
        if not re.search(r"展开\d+条回复", text):
            continue
        try:
            human_click(page, button, timeout=3000)
            human_pause(page, 500, 1100)
            return True
        except Exception:
            continue
    return False


def click_comment_more_buttons(page: Page) -> int:
    """点击评论区内「展开/查看更多」类按钮（不含三点菜单）。"""
    more_buttons = page.locator(
        'button:visible:has-text("查看更多"), '
        'span:visible:has-text("查看更多"), '
        'button:visible:has-text("展开"), '
        'span:visible:has-text("展开")'
    )
    clicked = 0
    count = more_buttons.count()
    for index in range(count):
        button = more_buttons.nth(index)
        try:
            text = button.inner_text(timeout=1000).strip()
        except Exception:
            continue
        if re.search(r"展开\d+条回复", text):
            continue
        try:
            human_click(page, button, timeout=2000)
            clicked += 1
            human_pause(page, 350, 800)
        except Exception:
            continue
    return clicked


def get_comment_items(page: Page) -> Locator:
    container = get_comment_scroll_container(page)
    items = container.locator('[data-e2e="comment-item"]')
    if items.count() > 0:
        return items
    items = container.locator("div.IJfG7ymB")
    if items.count() > 0:
        return items
    items = container.locator("div.F89wJ3x4")
    if items.count() > 0:
        return items
    return container.locator("div.F7ubq_7y.HfWacTUC")


def extract_visible_comments_batch(page: Page) -> list[tuple[int, str, str]]:
    """一次性批量读取可见评论，避免逐条 Locator 往返。"""
    try:
        raw = page.evaluate(
            """
            () => {
                const skipTexts = new Set(["作者赞过", "作者回复过"]);
                const normalizeCommentText = (text) =>
                    text
                        .split(/\\n+/)
                        .map((line) => line.trim())
                        .filter((line) => line && !skipTexts.has(line))
                        .join("\\n");

                const container =
                    document.querySelector("#videoSideCard [data-e2e='comment-list']") ||
                    document.querySelector('[data-e2e="comment-list"]') ||
                    document.querySelector('#merge-all-comment-container') ||
                    document.querySelector('.comment-mainContent') ||
                    document.body;
                const items = container.querySelectorAll('[data-e2e="comment-item"], div.IJfG7ymB');
                const results = [];
                items.forEach((item, index) => {
                    const rect = item.getBoundingClientRect();
                    if (rect.width <= 0 || rect.height <= 0) return;
                    const style = window.getComputedStyle(item);
                    if (style.visibility === 'hidden' || style.display === 'none') return;

                    const authorEl =
                        item.querySelector(".comment-item-info-wrap .Sw1iq0tk a.jwmvCVIo [data-click-from='title']") ||
                        item.querySelector('.comment-item-info-wrap .Sw1iq0tk a.jwmvCVIo') ||
                        item.querySelector('.comment-item-info-wrap a.jwmvCVIo') ||
                        item.querySelector('.comment-item-info-wrap a.Z3VQe4ky') ||
                        item.querySelector('.jyqk68aK a.Z3VQe4ky') ||
                        item.querySelector('.bTHWOB9x a.Z3VQe4ky') ||
                        item.querySelector('a.hY8lWHgA');
                    const textEl =
                        item.querySelector('div.Pmn4RZdg') ||
                        item.querySelector('div.Sbe6bqNb') ||
                        item.querySelector('div.LvAtyU_f');
                    let author = authorEl
                        ? authorEl.innerText.replace(/^@+/, '').replace(/作者/g, '').trim()
                        : '';
                    if (!author) {
                        const avatarImg = item.querySelector('.comment-item-avatar img[alt]');
                        if (avatarImg) {
                            author = avatarImg.getAttribute('alt').replace(/头像$/, '').trim();
                        }
                    }
                    const text = textEl
                        ? normalizeCommentText(textEl.innerText.trim())
                        : '';
                    if (!text) return;
                    results.push({ index, author, text });
                });
                return results;
            }
            """
        )
    except Exception:
        return []

    return [(item["index"], item["author"], item["text"]) for item in raw]


def extract_comment_text(item: Locator) -> str:
    return _normalize_comment_text(
        _read_locator_text(item.locator(COMMENT_TEXT_SELECTOR).first)
    )


def extract_comment_author(item: Locator) -> str:
    author = _read_locator_text(item.locator(COMMENT_AUTHOR_SELECTOR).first)
    author = author.replace("作者", "").lstrip("@").strip()
    if author:
        return author
    avatar_alt = _read_locator_text(
        item.locator(".comment-item-avatar img[alt]").first
    )
    return re.sub(r"头像$", "", avatar_alt).strip()


def comment_fingerprint(author: str, text: str) -> str:
    return f"{author}::{text}"


def matches_keyword(text: str, keywords: list[str]) -> str | None:
    if not text:
        return None
    for keyword in keywords:
        if keyword and keyword in text:
            return keyword
    return None


def get_comment_avatar(item: Locator) -> Locator:
    for selector in COMMENT_AVATAR_SELECTORS:
        avatar = item.locator(selector).first
        if avatar.count() == 0:
            continue
        try:
            if avatar.is_visible():
                return avatar
        except Exception:
            return avatar
    return item.locator(".comment-item-avatar a").first


def get_comment_item_at(page: Page, index: int) -> Locator:
    return get_comment_items(page).nth(index)


def _decode_image_bytes(data: bytes) -> np.ndarray | None:
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    return image


def calc_slide_offset(bg_bytes: bytes, slide_bytes: bytes) -> int | None:
    bg = _decode_image_bytes(bg_bytes)
    slide = _decode_image_bytes(slide_bytes)
    if bg is None or slide is None:
        return None

    if slide.ndim == 3 and slide.shape[2] == 4:
        alpha = slide[:, :, 3]
        slide_rgb = slide[:, :, :3]
        mask = alpha > 120
        slide_gray = cv2.cvtColor(slide_rgb, cv2.COLOR_BGR2GRAY)
        slide_gray = cv2.bitwise_and(slide_gray, slide_gray, mask=mask.astype(np.uint8))
    else:
        slide_gray = cv2.cvtColor(slide, cv2.COLOR_BGR2GRAY)

    bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    bg_edge = cv2.Canny(bg_gray, 80, 180)
    slide_edge = cv2.Canny(slide_gray, 80, 180)

    if slide_edge.shape[0] >= bg_edge.shape[0] or slide_edge.shape[1] >= bg_edge.shape[1]:
        return None

    result = cv2.matchTemplate(bg_edge, slide_edge, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < 0.2:
        return None
    return int(max_loc[0])


def get_captcha_host(page: Page) -> tuple[Frame | Page, Locator | None] | None:
    iframe = page.locator('iframe[src*="verifycenter/captcha"], iframe[src*="verifycenter"]').first
    if iframe.count() > 0:
        try:
            if iframe.is_visible():
                frame = iframe.content_frame()
                if frame and frame.locator("#captcha_verify_image").count() > 0:
                    return frame, iframe
        except Exception:
            pass
    captcha_img = page.locator("#captcha_verify_image").first
    if captcha_img.count() > 0:
        try:
            if captcha_img.is_visible():
                return page, None
        except Exception:
            return page, None
    return None


def is_captcha_visible(page: Page) -> bool:
    return get_captcha_host(page) is not None


def _human_drag_progress(progress: float) -> float:
    """先慢后快再慢的非对称拖动曲线。"""
    progress = max(0.0, min(1.0, progress))
    if progress < 0.18:
        return (progress / 0.18) ** 2 * 0.14
    if progress < 0.78:
        mid = (progress - 0.18) / 0.6
        return 0.14 + mid * 0.76
    tail = (progress - 0.78) / 0.22
    return 0.9 + (1 - (1 - tail) ** 2) * 0.1


def build_human_drag_track(
    start_x: float,
    start_y: float,
    distance: float,
) -> list[tuple[float, float, int]]:
    """生成带接近、波动、过冲回正、终点微抖的拖动轨迹。"""
    points: list[tuple[float, float, int]] = []
    approach_x = start_x + random.uniform(-3, 3)
    approach_y = start_y + random.uniform(-2, 2)
    points.append((approach_x, approach_y, random.randint(70, 150)))

    overshoot_px = random.uniform(2.5, 7.0) if random.random() < 0.7 else 0.0
    drag_target = distance + overshoot_px if overshoot_px else distance
    main_steps = random.randint(30, 48)
    y_wave_amp = random.uniform(0.8, 2.2)
    y_wave_freq = random.uniform(2.2, 5.0)

    for step in range(1, main_steps + 1):
        progress = step / main_steps
        ratio = _human_drag_progress(progress)
        x = start_x + drag_target * ratio
        x += random.uniform(-1.4, 1.4)
        if progress > 0.5:
            x += random.uniform(-0.8, 0.8)
        y = start_y + math.sin(progress * math.pi * y_wave_freq) * y_wave_amp
        y += random.uniform(-1.2, 1.2)
        wait_ms = random.randint(8, 28)
        if random.random() < 0.1:
            wait_ms += random.randint(50, 140)
        points.append((x, y, wait_ms))

    if overshoot_px > 0:
        correction_steps = random.randint(5, 10)
        for step in range(1, correction_steps + 1):
            progress = step / correction_steps
            eased = progress * progress * (3 - 2 * progress)
            x = start_x + drag_target + (distance - drag_target) * eased
            x += random.uniform(-0.6, 0.6)
            y = start_y + random.uniform(-1.0, 1.0)
            points.append((x, y, random.randint(14, 38)))

    for _ in range(random.randint(2, 5)):
        jitter_x = start_x + distance + random.uniform(-2.0, 2.0)
        jitter_y = start_y + random.uniform(-1.2, 1.2)
        points.append((jitter_x, jitter_y, random.randint(18, 55)))

    points.append(
        (
            start_x + distance + random.uniform(-0.8, 0.8),
            start_y + random.uniform(-0.6, 0.6),
            random.randint(70, 160),
        )
    )
    return points


def human_drag_slider(page: Page, start_x: float, start_y: float, distance: float) -> None:
    track = build_human_drag_track(start_x, start_y, distance)
    approach_x, approach_y, approach_wait = track[0]
    page.mouse.move(approach_x, approach_y, steps=random.randint(8, 14))
    page.wait_for_timeout(approach_wait)

    press_x = start_x + random.uniform(-1.2, 1.2)
    press_y = start_y + random.uniform(-0.8, 0.8)
    page.mouse.move(press_x, press_y, steps=random.randint(4, 9))
    human_pause(page, 90, 180)
    page.mouse.down()
    human_pause(page, random.randint(100, 220), random.randint(200, 360))

    for x, y, wait_ms in track[1:]:
        page.mouse.move(x, y, steps=random.randint(2, 6))
        page.wait_for_timeout(wait_ms)

    human_pause(page, 90, 200)
    page.mouse.up()


def refresh_captcha(page: Page) -> bool:
    captcha_ctx = get_captcha_host(page)
    if captcha_ctx is None:
        return False
    host, _iframe = captcha_ctx
    refresh_btn = host.locator(".vc-captcha-refresh").first
    try:
        if refresh_btn.count() > 0 and refresh_btn.is_visible():
            click_with_fallback(page, refresh_btn, timeout=3000, fast=True)
            human_pause(page, 1000, 1800)
            return True
    except Exception:
        pass
    return False


def solve_slide_captcha(page: Page, *, distance_offset: float = 0.0) -> bool:
    captcha_ctx = get_captcha_host(page)
    if captcha_ctx is None:
        return True
    host, _iframe = captcha_ctx
    if host.locator("#captcha_verify_image").count() == 0:
        return True

    bg_loc = host.locator("#captcha_verify_image").first
    slide_loc = host.locator(
        "#captcha-verify_img_slide, #captcha_verify_img_slide"
    ).first
    slider_loc = host.locator(".captcha-slider-btn").first
    if slide_loc.count() == 0 or slider_loc.count() == 0:
        print("  验证码: 未找到滑块元素")
        return False

    try:
        bg_bytes = bg_loc.screenshot()
        slide_bytes = slide_loc.screenshot()
    except Exception as exc:
        print(f"  验证码: 截图失败 ({exc})")
        return False

    offset = calc_slide_offset(bg_bytes, slide_bytes)
    if offset is None:
        print("  验证码: OpenCV 未能识别缺口位置")
        return False

    try:
        bg_box = bg_loc.bounding_box()
        slider_box = slider_loc.bounding_box()
        natural_width = host.evaluate(
            '() => document.querySelector("#captcha_verify_image")?.naturalWidth || 0'
        )
    except Exception as exc:
        print(f"  验证码: 读取元素尺寸失败 ({exc})")
        return False

    if not bg_box or not slider_box or not natural_width:
        print("  验证码: 元素尺寸无效")
        return False

    scale = bg_box["width"] / natural_width
    drag_distance = max(0.0, offset * scale + distance_offset)

    start_x = slider_box["x"] + slider_box["width"] / 2
    start_y = slider_box["y"] + slider_box["height"] / 2

    print(
        f"  验证码: 识别缺口 offset={offset}px, 拖动 {drag_distance:.1f}px"
        + (f" (微调 {distance_offset:+.1f}px)" if distance_offset else "")
    )
    human_drag_slider(page, start_x, start_y, drag_distance)
    human_pause(page, 1200, 2200)
    return True


def wait_captcha_gone(page: Page, timeout_ms: int = 15000) -> bool:
    elapsed = 0
    step = 500
    while elapsed < timeout_ms:
        if not is_captcha_visible(page):
            return True
        page.wait_for_timeout(step)
        elapsed += step
    return not is_captcha_visible(page)


def handle_captcha_if_present(page: Page) -> bool:
    if not is_captcha_visible(page):
        return True

    print("  检测到滑块验证码，开始自动处理...")
    used_offsets: list[float] = []
    for attempt in range(1, CAPTCHA_MAX_RETRIES + 1):
        if attempt > 1:
            refresh_captcha(page)

        if attempt == 1:
            distance_offset = random.uniform(-1.5, 1.5)
        else:
            candidates = [
                off for off in CAPTCHA_DISTANCE_RETRY_OFFSETS if off not in used_offsets
            ]
            distance_offset = float(
                random.choice(candidates or CAPTCHA_DISTANCE_RETRY_OFFSETS)
            )
        used_offsets.append(distance_offset)

        print(
            f"  验证码尝试 {attempt}/{CAPTCHA_MAX_RETRIES}"
            f"，距离微调 {distance_offset:+.1f}px"
        )
        if not solve_slide_captcha(page, distance_offset=distance_offset):
            human_pause(page, 800, 1500)
            continue
        if wait_captcha_gone(page):
            print("  验证码已通过")
            return True
        print("  验证码未通过，准备刷新后重试...")
        human_pause(page, 600, 1200)

    print("  验证码自动处理失败，请手动完成验证")
    return False


def get_private_message_button(page: Page) -> Locator:
    selectors = [
        ".nfXJTPCl .Lwq5O0r5 button:has(span.semi-button-content:text-is('私信'))",
        ".yqH0VJK5 button.semi-button-secondary:has(span.semi-button-content:text-is('私信'))",
        "button.semi-button-secondary:has(span.semi-button-content:text-is('私信'))",
        "button:has(span.semi-button-content:text-is('私信'))",
    ]
    for selector in selectors:
        buttons = page.locator(selector)
        for idx in range(buttons.count()):
            btn = buttons.nth(idx)
            try:
                if btn.is_visible():
                    return btn
            except Exception:
                continue
    return page.get_by_role("button", name="私信").first


def wait_im_dialog_appear(page: Page, min_ms: int = 5000, max_ms: int = 7000) -> bool:
    """点击私信按钮后，等待浮框出现；超时时间为 5-7 秒（随机）。"""
    timeout_ms = random.randint(min_ms, max_ms)
    try:
        page.locator('[data-e2e="im-dialog"]').first.wait_for(
            state="visible", timeout=timeout_ms
        )
        return True
    except Exception:
        return False


class DmRateLimiter:
    """1 小时内最多私信 DM_HOURLY_LIMIT 条，记录持久化到 JSON 文件。"""

    def __init__(self, path: Path | None = None) -> None:
        self.path = (path or (get_app_dir() / DM_RECORDS_FILENAME)).resolve()
        ensure_writable_data_dir(self.path)
        self.records: list[dict[str, Any]] = self._load()
        print(f"私信记录文件: {self.path}")

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                records = data.get("records")
                if isinstance(records, list):
                    return records
        except Exception:
            pass
        return []

    def _save(self) -> None:
        payload = {"records": self.records, "updated_at": datetime.now().isoformat()}
        ensure_writable_data_dir(self.path)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self.path)

    @staticmethod
    def _record_timestamp(record: dict[str, Any]) -> float | None:
        raw = record.get("timestamp") or record.get("私信时间")
        if not raw:
            return None
        raw_str = str(raw)
        for fmt in (None, "%Y-%m-%d %H:%M:%S"):
            try:
                if fmt is None:
                    return datetime.fromisoformat(raw_str).timestamp()
                return datetime.strptime(raw_str, fmt).timestamp()
            except Exception:
                continue
        return None

    def count_in_last_hour(self) -> int:
        cutoff = time.time() - 3600
        count = 0
        for record in self.records:
            ts = self._record_timestamp(record)
            if ts is not None and ts > cutoff:
                count += 1
        return count

    def remaining_quota(self) -> int:
        return max(0, DM_HOURLY_LIMIT - self.count_in_last_hour())

    def can_start(self) -> bool:
        return self.count_in_last_hour() < DM_HOURLY_LIMIT

    def is_limit_reached(self) -> bool:
        return self.count_in_last_hour() >= DM_HOURLY_LIMIT

    def record_send(
        self,
        *,
        nickname: str,
        profile_url: str,
        message: str,
        video_title: str = "",
        comment_content: str = "",
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "私信时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nickname": nickname,
            "profile_url": profile_url,
            "message": message,
            "video_title": video_title,
            "comment_content": comment_content,
        }
        self.records.append(entry)
        self._save()
        hourly_count = self.count_in_last_hour()
        print(
            f"  私信记录已实时保存至 {self.path.name}"
            f" (近1小时 {hourly_count}/{DM_HOURLY_LIMIT} 条)"
        )


def get_dm_input(page: Page) -> Locator:
    selectors = [
        '[data-e2e="msg-input"] .messageEditorinputArea[contenteditable="true"]',
        '[data-e2e="msg-input"] [data-slate-editor="true"][contenteditable="true"]',
        ".messageEditorinputArea[contenteditable='true']",
        '[data-e2e="msg-input"] [contenteditable="true"]',
    ]
    for selector in selectors:
        editor = page.locator(selector).first
        if editor.count() > 0:
            return editor
    return page.locator('[data-e2e="msg-input"] [contenteditable="true"]').first


def get_dm_send_button(page: Page) -> Locator:
    selectors = [
        '[data-e2e="msg-input"] .e2e-send-msg-btn',
        ".messageMsgInputpublishRedBtn.e2e-send-msg-btn",
        ".messageMsgInputpublishBtn.e2e-send-msg-btn",
        ".e2e-send-msg-btn",
    ]
    for selector in selectors:
        btn = page.locator(selector).first
        if btn.count() > 0:
            return btn
    return page.locator(".e2e-send-msg-btn").first


def send_dm_on_profile_page(page: Page, template: str) -> tuple[bool, str]:
    dialog_opened = False
    last_error = "私信浮框未出现"

    for attempt in range(2):
        pm_btn = get_private_message_button(page)
        if pm_btn.count() == 0:
            return False, "未找到私信按钮"

        try:
            pm_btn.wait_for(state="visible", timeout=10000)
            click_with_fallback(page, pm_btn, timeout=5000, fast=True)
        except Exception as exc:
            return False, f"点击私信按钮失败 ({exc})"

        if wait_im_dialog_appear(page):
            dialog_opened = True
            break

        last_error = "私信浮框未出现"
        if attempt == 0:
            print("  私信浮框未出现，重试一次...")
            human_pause(page, 800, 1500)
        else:
            return False, last_error

    if not dialog_opened:
        return False, last_error

    editor = get_dm_input(page)
    try:
        editor.wait_for(state="visible", timeout=8000)
        click_with_fallback(page, editor, timeout=5000, fast=True)
        human_pause(page, 150, 300)
        human_type_text(page, template, fast=True)
        human_pause(page, 200, 400)
    except Exception as exc:
        return False, f"输入私信内容失败 ({exc})"

    send_btn = get_dm_send_button(page)
    try:
        send_btn.wait_for(state="visible", timeout=5000)
        click_with_fallback(page, send_btn, timeout=5000, fast=True)
        human_pause(page, 600, 1200)
    except Exception as exc:
        return False, f"点击发送按钮失败 ({exc})"

    return True, "私信已发送"


def visit_user_and_send_dm(
    page: Page,
    item: Locator,
    author: str,
    template: str,
    *,
    dm_limiter: DmRateLimiter | None = None,
    video_title: str = "",
    comment_content: str = "",
) -> tuple[bool, str]:
    if dm_limiter is not None and dm_limiter.is_limit_reached():
        return False, f"已达1小时私信上限 {DM_HOURLY_LIMIT} 条"

    try:
        item.scroll_into_view_if_needed(timeout=5000)
    except Exception as exc:
        return False, f"评论未滚动到可见区域 ({exc})"

    avatar = get_comment_avatar(item)
    if avatar.count() == 0:
        return False, "未找到用户头像"

    context = page.context
    existing_pages = set(context.pages)
    profile_page: Page | None = None

    try:
        with context.expect_page(timeout=15000) as page_info:
            click_with_fallback(page, avatar, timeout=5000, fast=True)
        profile_page = page_info.value
    except Exception:
        new_pages = [p for p in context.pages if p not in existing_pages]
        if new_pages:
            profile_page = new_pages[-1]

    if profile_page is None:
        return False, "点击头像后未打开新标签页"

    try:
        profile_page.wait_for_load_state("domcontentloaded", timeout=30000)
    except Exception:
        pass

    if is_captcha_visible(profile_page):
        if not handle_captcha_if_present(profile_page):
            try:
                profile_page.close()
            except Exception:
                pass
            page.bring_to_front()
            return False, "验证码处理失败"

    try:
        profile_page.locator('[data-e2e="user-info"]').first.wait_for(
            state="visible", timeout=10000
        )
    except Exception:
        pass

    human_pause(profile_page, 2000, 4000)

    ok, dm_result = send_dm_on_profile_page(profile_page, template)
    profile_url = profile_page.url

    try:
        profile_page.close()
    except Exception:
        pass
    page.bring_to_front()
    human_pause(page, 400, 800)

    nickname = author or "用户"
    if ok:
        if dm_limiter is not None:
            dm_limiter.record_send(
                nickname=nickname,
                profile_url=profile_url,
                message=template,
                video_title=video_title,
                comment_content=comment_content,
            )
        return True, f"已私信 {nickname} ({profile_url}) - {dm_result}"
    return False, dm_result


def make_comment_record(
    post_info: PostInfo,
    nickname: str,
    content: str,
    matched_keyword: str = "",
    visited: bool = False,
    visit_result: str = "",
) -> CommentRecord:
    return CommentRecord(
        video_title=post_info["title"],
        video_author=post_info["author"],
        video_publish_time=post_info["publish_time"],
        comment_nickname=nickname,
        comment_content=content,
        matched_keyword=matched_keyword,
        replied="是" if visited else "否",
        reply_content=visit_result,
    )


def process_visible_comments(
    page: Page,
    post_info: PostInfo,
    keywords: list[str],
    dm_template: str,
    processed: set[str],
    records: list[CommentRecord],
    auto_visit: bool = DEFAULT_AUTO_VISIT,
    visits_so_far: int = 0,
    max_visits: int = 0,
    dm_limiter: DmRateLimiter | None = None,
) -> tuple[int, int, bool]:
    batch = extract_visible_comments_batch(page)
    matched = 0
    visited_count = 0
    visit_limit_reached = False

    for index, author, text in batch:
        if visit_limit_reached:
            break
        if dm_limiter is not None and dm_limiter.is_limit_reached():
            visit_limit_reached = True
            print(f"  已达1小时私信上限 {DM_HOURLY_LIMIT} 条，强制停止")
            break
        if text in SKIP_COMMENT_TEXTS:
            continue

        fp = comment_fingerprint(author, text)
        if fp in processed:
            continue
        processed.add(fp)

        keyword_hit = matches_keyword(text, keywords) or ""
        did_visit = False
        visit_result = ""

        if keyword_hit:
            matched += 1
            print(f"  命中关键词「{keyword_hit}」: {author or '未知用户'} - {text[:40]}")
            if auto_visit:
                if dm_limiter is not None and dm_limiter.is_limit_reached():
                    visit_limit_reached = True
                    print(f"  已达1小时私信上限 {DM_HOURLY_LIMIT} 条，强制停止")
                elif max_visits > 0 and visits_so_far + visited_count >= max_visits:
                    visit_limit_reached = True
                    print(
                        f"  已达本视频私信上限 {max_visits} 次，"
                        "停止继续私信"
                    )
                else:
                    print(f"  正在点击头像并私信: {author or '未知用户'}")
                    item = get_comment_item_at(page, index)
                    ok, visit_result = visit_user_and_send_dm(
                        page,
                        item,
                        author,
                        dm_template,
                        dm_limiter=dm_limiter,
                        video_title=post_info["title"],
                        comment_content=text,
                    )
                    if ok:
                        did_visit = True
                        visited_count += 1
                        print(f"  私信成功: {author or '未知用户'} - {visit_result}")
                        if dm_limiter is not None and dm_limiter.is_limit_reached():
                            visit_limit_reached = True
                            print(
                                f"  已达1小时私信上限 {DM_HOURLY_LIMIT} 条，强制停止"
                            )
                        elif max_visits > 0 and visits_so_far + visited_count >= max_visits:
                            visit_limit_reached = True
                            print(
                                f"  已达本视频私信上限 {max_visits} 次，"
                                "停止继续私信"
                            )
                    else:
                        print(f"  私信失败: {author or '未知用户'} - {visit_result}")
                        if (
                            dm_limiter is not None
                            and "已达1小时私信上限" in visit_result
                        ):
                            visit_limit_reached = True

        records.append(
            make_comment_record(
                post_info,
                author or "未知用户",
                text,
                matched_keyword=keyword_hit,
                visited=did_visit,
                visit_result=visit_result,
            )
        )

    return matched, visited_count, visit_limit_reached


def get_app_dir() -> Path:
    """获取程序数据目录：开发时为脚本目录，打包后为 exe 所在目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def ensure_writable_data_dir(path: Path) -> Path:
    """确保数据目录存在且可写，返回绝对路径。"""
    directory = path.resolve().parent if path.suffix else path.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    probe = directory / ".write_probe"
    try:
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        raise RuntimeError(f"数据目录不可写: {directory} ({exc})") from exc
    return directory


def save_comments_to_csv(records: list[CommentRecord], search_keyword: str) -> Path:
    output_dir = ensure_writable_data_dir(get_app_dir())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = re.sub(r'[\\/:*?"<>|]', "_", search_keyword) or "douyin"
    output_path = output_dir / f"评论采集_{safe_keyword}_{timestamp}.csv"

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "视频标题": record["video_title"],
                    "发布作者": record["video_author"],
                    "发布时间": record["video_publish_time"],
                    "评论人昵称": record["comment_nickname"],
                    "评论内容": record["comment_content"],
                    "命中关键词": record["matched_keyword"],
                    "是否私信": record["replied"],
                    "处理结果": record["reply_content"],
                }
            )

    return output_path


def close_video_panel(page: Page) -> None:
    close_selectors = [
        "div.A79YNGgR.isDark",
        "div.A79YNGgR",
        '[data-e2e="modal-video-container"] div.A79YNGgR',
        "div.pGZF8lyn.isDark",
        "div.pGZF8lyn",
        ".search-horizontal-new-layout div.pGZF8lyn",
        '[class*="searchModal"] div.pGZF8lyn',
    ]
    for selector in close_selectors:
        close_btn = page.locator(selector).first
        if close_btn.count() == 0:
            continue
        try:
            if close_btn.is_visible():
                human_pause(page, 400, 900)
                click_with_fallback(page, close_btn, timeout=5000)
                human_reading_pause(page, 1000, 2000)
                print("已关闭当前视频")
                return
        except Exception:
            continue

    try:
        page.keyboard.press("Escape")
        human_pause(page, 800, 1500)
        if page.locator("#search-result-container").first.is_visible():
            print("已通过 Esc 返回搜索结果页")
            return
    except Exception:
        pass

    print("关闭视频失败: 未找到关闭按钮，请手动关闭后继续")


def effective_max_visits(
    max_visits_per_video: int, dm_limiter: DmRateLimiter | None
) -> int:
    """结合每视频上限与1小时全局上限，取较小有效值。"""
    if dm_limiter is None:
        return max_visits_per_video
    remaining = dm_limiter.remaining_quota()
    if remaining <= 0:
        return 0
    if max_visits_per_video <= 0:
        return remaining
    return min(max_visits_per_video, remaining)


def browse_comments(
    page: Page,
    post_info: PostInfo,
    keywords: list[str],
    dm_template: str,
    max_expand_clicks: int = DEFAULT_MAX_EXPAND_CLICKS,
    expand_batch_size: int = EXPAND_BATCH_SIZE,
    max_rounds: int = 200,
    auto_visit: bool = DEFAULT_AUTO_VISIT,
    max_visits_per_video: int = DEFAULT_MAX_VISITS_PER_VIDEO,
    dm_limiter: DmRateLimiter | None = None,
) -> list[CommentRecord]:
    effective_max = effective_max_visits(max_visits_per_video, dm_limiter)
    visit_limit_text = ""
    if auto_visit:
        if dm_limiter is not None:
            hourly_used = dm_limiter.count_in_last_hour()
            visit_limit_text = (
                f", 1小时私信上限 {DM_HOURLY_LIMIT} 条"
                f"(已用 {hourly_used} 条, 剩余 {dm_limiter.remaining_quota()} 条)"
            )
        if effective_max > 0:
            visit_limit_text += f", 本视频最多私信 {effective_max} 次"
        elif dm_limiter is not None and dm_limiter.is_limit_reached():
            visit_limit_text += ", 已达1小时私信上限"
    print(
        f"开始在评论区滚动、展开回复并处理关键词评论..."
        f"展开上限 {max_expand_clicks} 次, 每 {expand_batch_size} 次展开后滚动加载"
        + (", 命中后立即点击头像并私信" if auto_visit else ", 仅采集不自动私信")
        + visit_limit_text
    )
    if auto_visit and dm_limiter is not None and dm_limiter.is_limit_reached():
        print(f"已达1小时私信上限 {DM_HOURLY_LIMIT} 条，跳过本视频私信")
        close_video_panel(page)
        return []
    processed: set[str] = set()
    records: list[CommentRecord] = []
    total_matched = 0
    total_visited = 0
    total_expanded = 0
    batch_expanded = 0
    expand_limit_reached = max_expand_clicks <= 0
    expand_exhausted = False
    visit_limit_reached = False
    stagnant_rounds = 0
    prev_processed_count = 0

    def finalize_partial_expand_batch() -> bool:
        nonlocal batch_expanded, total_matched, total_visited
        if batch_expanded <= 0:
            return False
        print(f"处理剩余批内 {batch_expanded} 次展开后的关键词评论...")
        load_more_comments_by_scrolling(page, steps=2)
        return drain_keyword_comments()

    def stop_expand_phase(*, exhausted: bool) -> None:
        nonlocal expand_limit_reached, expand_exhausted, just_reached_expand_limit
        expand_limit_reached = True
        expand_exhausted = exhausted
        just_reached_expand_limit = True
        if exhausted:
            print(
                f"评论区已无更多展开按钮(累计展开 {total_expanded}/{max_expand_clicks} 次)，"
                "提前终止展开"
            )
        else:
            print(f"已达展开按钮点击上限 {max_expand_clicks} 次，停止展开")

    def process_matches_now() -> tuple[int, int, bool]:
        nonlocal total_matched, total_visited, visit_limit_reached
        matched, visited, limit_hit = process_visible_comments(
            page,
            post_info,
            keywords,
            dm_template,
            processed,
            records,
            auto_visit=auto_visit,
            visits_so_far=total_visited,
            max_visits=effective_max,
            dm_limiter=dm_limiter,
        )
        total_matched += matched
        total_visited += visited
        if limit_hit:
            visit_limit_reached = True
            if dm_limiter is not None and dm_limiter.is_limit_reached():
                print(
                    f"已达1小时私信上限 {DM_HOURLY_LIMIT} 条"
                    f"(累计成功私信 {total_visited} 次)，关闭当前视频"
                )
            elif effective_max > 0:
                print(
                    f"已达本视频私信上限 {effective_max} 次"
                    f"(累计成功私信 {total_visited} 次)，关闭当前视频"
                )
        return matched, visited, limit_hit

    def drain_keyword_comments() -> bool:
        while True:
            matched, visited, limit_hit = process_matches_now()
            if matched == 0 or limit_hit:
                return limit_hit

    def finish_expand_batch() -> bool:
        nonlocal batch_expanded
        if batch_expanded < expand_batch_size:
            return False
        print(f"已完成 {expand_batch_size} 次展开，向下滚动加载更多评论...")
        load_more_comments_by_scrolling(page, steps=3)
        matched, visited, limit_hit = process_matches_now()
        print(
            f"本批滚动后处理完成: 命中 {matched} 条, 私信 {visited} 条"
            + ("，当前无更多可处理的关键词评论" if matched == 0 else "")
        )
        batch_expanded = 0
        return limit_hit

    if drain_keyword_comments():
        print(
            f"评论区处理完成: 共展开 {total_expanded} 次, 扫描 {len(processed)} 条评论, "
            f"命中关键词 {total_matched} 条, 成功私信 {total_visited} 条"
        )
        close_video_panel(page)
        return records

    prev_comment_count = get_comment_items(page).count()
    just_reached_expand_limit = False

    for round_index in range(1, max_rounds + 1):
        expanded_this_round = 0
        just_reached_expand_limit = False

        if not expand_limit_reached:
            while (
                batch_expanded < expand_batch_size
                and total_expanded < max_expand_clicks
            ):
                if click_one_expand_reply_button(page):
                    total_expanded += 1
                    batch_expanded += 1
                    expanded_this_round += 1
                    _, _, limit_hit = process_matches_now()
                    if limit_hit:
                        visit_limit_reached = True
                        break
                    if batch_expanded >= expand_batch_size:
                        if finish_expand_batch():
                            visit_limit_reached = True
                            break
                    if total_expanded >= max_expand_clicks:
                        stop_expand_phase(exhausted=False)
                        break
                    continue

                scroll_comment_panel(page)
                if click_one_expand_reply_button(page):
                    total_expanded += 1
                    batch_expanded += 1
                    expanded_this_round += 1
                    _, _, limit_hit = process_matches_now()
                    if limit_hit:
                        visit_limit_reached = True
                        break
                    if batch_expanded >= expand_batch_size:
                        if finish_expand_batch():
                            visit_limit_reached = True
                            break
                    if total_expanded >= max_expand_clicks:
                        stop_expand_phase(exhausted=False)
                    continue

                stop_expand_phase(exhausted=True)
                break

        if visit_limit_reached:
            break

        if just_reached_expand_limit:
            print("展开阶段结束，开始向下滚动加载更多评论...")
            load_more_comments_by_scrolling(page, steps=6)
            if finalize_partial_expand_batch():
                break
        elif expand_limit_reached:
            load_more_comments_by_scrolling(page, steps=4)
        else:
            scroll_comment_panel(page)

        more_clicked = click_comment_more_buttons(page)

        matched, visited, limit_hit = process_matches_now()
        if limit_hit:
            break

        if random.random() < 0.2:
            human_reading_pause(page, 800, 1800)

        comment_count = get_comment_items(page).count()
        if expand_limit_reached:
            if (
                comment_count <= prev_comment_count
                and len(processed) == prev_processed_count
                and expanded_this_round == 0
            ):
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
            prev_comment_count = comment_count
        elif len(processed) == prev_processed_count and expanded_this_round == 0:
            stagnant_rounds += 1
        else:
            stagnant_rounds = 0
        prev_processed_count = len(processed)

        no_more = has_no_more_comments(page)
        print(
            f"第 {round_index} 轮: 展开 {expanded_this_round} 次"
            f"(累计 {total_expanded}/{max_expand_clicks}), "
            f"批内 {batch_expanded}/{expand_batch_size}, "
            f"更多 {more_clicked} 次, 命中 {matched} 条, 私信 {visited} 条, "
            f"累计处理 {len(processed)} 条, 可见评论 {comment_count} 条, "
            f"累计私信 {total_visited}"
            + (f"/{max_visits_per_video}" if max_visits_per_video > 0 else "")
            + ("，已无更多评论" if no_more else "")
            + ("，展开按钮已用尽(提前终止)" if expand_exhausted else "")
            + ("，已停止展开" if expand_limit_reached and not expand_exhausted else "")
            + ("，已达私信上限" if visit_limit_reached else "")
        )

        if expand_exhausted:
            if drain_keyword_comments():
                break
            print("展开按钮已用尽，提前结束评论区处理。")
            break

        if no_more:
            print("检测到「暂时没有更多评论」，收尾处理剩余可见评论...")
            if batch_expanded > 0:
                if finish_expand_batch():
                    break
            if drain_keyword_comments():
                break
            break

        if expand_limit_reached and stagnant_rounds >= 8:
            print("已达展开上限且连续多轮滚动无新评论，停止处理。")
            if batch_expanded > 0:
                if finish_expand_batch():
                    break
            if drain_keyword_comments():
                break
            break

        if stagnant_rounds >= 8:
            print("连续多轮无新评论，停止滚动。")
            if batch_expanded > 0:
                if finish_expand_batch():
                    break
            if drain_keyword_comments():
                break
            break

    print(
        f"评论区处理完成: 共展开 {total_expanded} 次, 扫描 {len(processed)} 条评论, "
        f"命中关键词 {total_matched} 条, 成功私信 {total_visited} 条"
    )
    close_video_panel(page)
    return records


def process_single_video(
    page: Page,
    video_index: int,
    video_count: int,
    keywords: list[str],
    dm_template: str,
    max_expand_clicks: int,
    auto_visit: bool = DEFAULT_AUTO_VISIT,
    max_visits_per_video: int = DEFAULT_MAX_VISITS_PER_VIDEO,
    dm_limiter: DmRateLimiter | None = None,
) -> list[CommentRecord]:
    print(f"\n========== 处理第 {video_index + 1}/{video_count} 个视频 ==========")
    if video_index > 0:
        human_reading_pause(page, 1500, 3000)
    post_info = collect_and_open_search_result(page, video_index)
    open_comment_panel(page)
    return browse_comments(
        page,
        post_info,
        keywords,
        dm_template,
        max_expand_clicks=max_expand_clicks,
        auto_visit=auto_visit,
        max_visits_per_video=max_visits_per_video,
        dm_limiter=dm_limiter,
    )


def run_douyin_flow(
    page: Page,
    context: BrowserContext,
    keyword: str,
    video_count: int,
    keywords: list[str],
    dm_template: str,
    max_expand_clicks: int,
    auto_visit: bool = DEFAULT_AUTO_VISIT,
    max_visits_per_video: int = DEFAULT_MAX_VISITS_PER_VIDEO,
    dm_limiter: DmRateLimiter | None = None,
) -> Path | None:
    page = search_on_douyin(page, keyword, context)
    all_records: list[CommentRecord] = []

    for video_index in range(video_count):
        if dm_limiter is not None and dm_limiter.is_limit_reached():
            print(
                f"\n已达1小时私信上限 {DM_HOURLY_LIMIT} 条，"
                f"停止处理剩余 {video_count - video_index} 个视频"
            )
            break
        try:
            records = process_single_video(
                page,
                video_index,
                video_count,
                keywords,
                dm_template,
                max_expand_clicks,
                auto_visit=auto_visit,
                max_visits_per_video=max_visits_per_video,
                dm_limiter=dm_limiter,
            )
            all_records.extend(records)
        except Exception as exc:
            print(f"第 {video_index + 1} 个视频处理失败: {exc}")
            close_video_panel(page)
            continue
        if dm_limiter is not None and dm_limiter.is_limit_reached():
            print(f"\n已达1小时私信上限 {DM_HOURLY_LIMIT} 条，强制停止全部流程")
            break

    if all_records:
        output_path = save_comments_to_csv(all_records, keyword)
        print(f"\n共处理 {video_count} 个视频, 采集 {len(all_records)} 条评论")
        print(f"评论数据已保存至: {output_path}")
    else:
        print("未采集到评论数据，跳过 CSV 保存。")
        output_path = None

    print("抖音搜索、评论区浏览与自动私信流程已完成。")
    return output_path


def run_playwright(
    ws_endpoint: str,
    keyword: str,
    video_count: int,
    keywords: list[str],
    dm_template: str,
    max_expand_clicks: int,
    auto_visit: bool = DEFAULT_AUTO_VISIT,
    max_visits_per_video: int = DEFAULT_MAX_VISITS_PER_VIDEO,
    dm_limiter: DmRateLimiter | None = None,
) -> None:
    with sync_playwright() as p:
        browser, context, page = connect_douyin_browser(p, ws_endpoint)

        run_douyin_flow(
            page,
            context,
            keyword,
            video_count,
            keywords,
            dm_template,
            max_expand_clicks,
            auto_visit=auto_visit,
            max_visits_per_video=max_visits_per_video,
            dm_limiter=dm_limiter,
        )

        input("流程结束，按回车断开连接...")


def main() -> None:
    print("正在获取环境列表...")
    env_list = fetch_env_list()
    selected = choose_env(env_list)

    account_id = str(selected.get("shopId") or "").strip()
    if not account_id:
        raise RuntimeError("所选环境缺少 shopId，无法启动。")

    print(f"\n正在启动环境: {selected.get('accountName', '')} ({account_id})")
    start_data = start_browser(account_id)
    ws = (start_data.get("ws") or {}).get("puppeteer", "")
    if not ws:
        raise RuntimeError(f"未获取到 ws.puppeteer，返回数据: {json.dumps(start_data, ensure_ascii=False)}")

    keyword = ask_search_keyword()
    video_count = ask_video_count()
    keywords = ask_keywords()
    dm_template = ask_dm_template()
    auto_visit = DEFAULT_AUTO_VISIT
    max_expand_clicks = ask_max_expand_clicks()
    max_visits_per_video = ask_max_visits_per_video()

    dm_limiter = DmRateLimiter()
    if auto_visit:
        hourly_used = dm_limiter.count_in_last_hour()
        if not dm_limiter.can_start():
            raise RuntimeError(
                f"近1小时内已私信 {hourly_used} 条，已达上限 {DM_HOURLY_LIMIT} 条，"
                "拒绝运行，请1小时后再试"
            )
        remaining = dm_limiter.remaining_quota()
        effective_total = effective_max_visits(max_visits_per_video, dm_limiter)
        print(
            f"\n1小时私信限制: 已用 {hourly_used}/{DM_HOURLY_LIMIT} 条，"
            f"本次最多可私信 {effective_total} 条"
        )
        if max_visits_per_video > remaining:
            print(
                f"提示: 每视频设置 {max_visits_per_video} 次，"
                f"但1小时内剩余额度仅 {remaining} 条，将按 {remaining} 条执行"
            )

    visit_limit_desc = (
        f"每视频最多私信 {max_visits_per_video} 次"
        if max_visits_per_video > 0
        else "每视频私信次数不限制"
    )
    print(
        f"\n将搜索「{keyword}」, 处理 {video_count} 个视频, "
        f"使用 {len(keywords)} 个关键词, 私信模板: {dm_template}, "
        f"自动私信: {'是' if auto_visit else '否'}, "
        f"每个视频展开上限: {max_expand_clicks} 次(每 {EXPAND_BATCH_SIZE} 次展开后处理关键词评论), "
        f"{visit_limit_desc}, "
        f"1小时私信上限 {DM_HOURLY_LIMIT} 条"
    )
    print("环境启动成功，正在通过 Playwright 连接...")
    time.sleep(2)
    run_playwright(
        ws,
        keyword,
        video_count,
        keywords,
        dm_template,
        max_expand_clicks,
        auto_visit=auto_visit,
        max_visits_per_video=max_visits_per_video,
        dm_limiter=dm_limiter if auto_visit else None,
    )


if __name__ == "__main__":
    main()
