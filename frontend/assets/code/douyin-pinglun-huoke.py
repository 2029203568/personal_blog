import csv
import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

import requests
from playwright.sync_api import Locator, Page, sync_playwright


BASE_URL = "http://localhost:50213"
SHOP_LIST_API = f"{BASE_URL}/api/v2/userapi/user/shopseriallist"
BROWSER_START_API = f"{BASE_URL}/api/v2/browser/start"

DOUYIN_HOME = "https://www.douyin.com/"
DEFAULT_SEARCH_KEYWORD = "日本"
DEFAULT_VIDEO_COUNT = 1
DEFAULT_MAX_EXPAND_CLICKS = 50
DEFAULT_MAX_REPLIES_PER_VIDEO = 10
DEFAULT_AUTO_REPLY = True
EXPAND_BATCH_SIZE = 5
DEFAULT_REPLY_TEMPLATE = "你好我们有产品请联系我们"
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
    "是否回复",
    "回复内容",
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


def human_type_in_editor(
    page: Page, editor: Locator, text: str, *, fast: bool = False
) -> None:
    click_with_fallback(page, editor, timeout=5000, fast=fast)
    human_pause(page, 80, 180) if fast else human_pause(page, 250, 600)
    human_type_text(page, text, fast=fast)
    human_pause(page, 150, 350) if fast else human_pause(page, 500, 1100)


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


def ask_reply_template() -> str:
    raw = input(
        f"\n请输入回复模板(直接回车使用默认「{DEFAULT_REPLY_TEMPLATE}」): "
    ).strip()
    return raw or DEFAULT_REPLY_TEMPLATE


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


def ask_max_replies_per_video() -> int:
    while True:
        raw = input(
            f"\n请输入每个视频最多回复次数"
            f"(直接回车使用默认 {DEFAULT_MAX_REPLIES_PER_VIDEO} 次，输入 0 表示不限制): "
        ).strip()
        if not raw:
            return DEFAULT_MAX_REPLIES_PER_VIDEO
        if raw.isdigit() and int(raw) >= 0:
            return int(raw)
        print("输入无效，请输入大于等于 0 的整数。")


def search_on_douyin(page: Page, keyword: str) -> None:
    print(f"正在打开抖音首页: {DOUYIN_HOME}")
    page.goto(DOUYIN_HOME, wait_until="domcontentloaded", timeout=60000)
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
        item.locator(".YOd74VnT .KYUFliur, .TG7OZENa .KYUFliur").first
    )
    meta_el = item.locator(".ycfEUnvt").first
    author = _read_locator_text(
        meta_el.locator("a.gpzfpvmu .KYUFliur, .YPGZWw4P .KYUFliur").first
    )
    publish_time = _normalize_publish_time(
        _read_locator_text(meta_el.locator("p.IhQeg9vr").first)
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


def get_search_waterfall_items(page: Page) -> Locator:
    items = page.locator(
        '#search-result-container div[id^="waterfall_item_"], '
        "#search-result-container div.oWmZEHuF[id^='waterfall_item_'], "
        "#search-result-container .AMqhOzPC"
    )
    items = items.filter(
        has=page.locator(
            ".search-result-card .FrfjJSkC, "
            ".search-result-card .videoImage, "
            ".search-result-card .yb3knZ7b.videoImage, "
            ".search-result-card .LFQCShEn"
        )
    )
    if items.count() > 0:
        return items

    return page.locator("#search-result-container .search-result-card").filter(
        has=page.locator(".FrfjJSkC, .videoImage, .yb3knZ7b.videoImage, .LFQCShEn")
    )


def get_search_scroll_list_items(page: Page) -> Locator:
    return page.locator('ul[data-e2e="scroll-list"] > li.Pva1pk_i').filter(
        has=page.locator(
            '[data-e2e="feed-video"], [data-e2e="feed-active-video"], .jGwTAgpj'
        )
    )


def get_search_result_items(page: Page) -> Locator:
    if is_scroll_list_layout(page):
        items = get_search_scroll_list_items(page)
        if items.count() > 0:
            return items
    return get_search_waterfall_items(page)


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
    scroll_list = is_scroll_list_layout(page)
    attempts = 0
    while attempts < 20:
        items = get_search_result_items(page)
        if items.count() > index:
            item = items.nth(index)
            item.wait_for(state="visible", timeout=20000)
            item.scroll_into_view_if_needed()
            human_pause(page, 400, 900)
            return item, scroll_list
        scroll_search_results(page)
        attempts += 1

    items = get_search_result_items(page)
    raise RuntimeError(
        f"搜索结果不足，需要第 {index + 1} 个视频，当前仅找到 {items.count()} 个。"
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

    if scroll_list:
        click_target = item.locator(
            '[data-e2e="feed-video"], [data-e2e="feed-active-video"], '
            ".jGwTAgpj .PV2JPzEx, .jGwTAgpj"
        ).first
    else:
        click_target = item.locator(
            ".FrfjJSkC .videoImage, .yb3knZ7b.videoImage, .FrfjJSkC, "
            ".LFQCShEn.videoImage, .videoImage, .search-result-card"
        ).first
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

    page.locator('[data-e2e="comment-list"], #merge-all-comment-container').first.wait_for(
        state="visible", timeout=30000
    )
    human_reading_pause(page, 1000, 2000)


def get_comment_scroll_container(page: Page) -> Locator:
    selectors = [
        '[data-e2e="comment-list"]',
        "#merge-all-comment-container",
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
        'button:has-text("展开"):has-text("回复"):visible, '
        'button:has(.VZWu521O):visible, '
        'button:has(.Q0y_i6F4):visible'
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
                    document.querySelector('[data-e2e="comment-list"]') ||
                    document.querySelector('#merge-all-comment-container') ||
                    document.querySelector('.comment-mainContent') ||
                    document.body;
                const items = container.querySelectorAll('[data-e2e="comment-item"]');
                const results = [];
                items.forEach((item, index) => {
                    const rect = item.getBoundingClientRect();
                    if (rect.width <= 0 || rect.height <= 0) return;
                    const style = window.getComputedStyle(item);
                    if (style.visibility === 'hidden' || style.display === 'none') return;

                    const authorEl =
                        item.querySelector('.comment-item-info-wrap a.Z3VQe4ky') ||
                        item.querySelector('.jyqk68aK a.Z3VQe4ky') ||
                        item.querySelector('.bTHWOB9x a.Z3VQe4ky') ||
                        item.querySelector('a.hY8lWHgA');
                    const textEl =
                        item.querySelector('div.Sbe6bqNb') ||
                        item.querySelector('div.LvAtyU_f');
                    const author = authorEl
                        ? authorEl.innerText.replace(/^@+/, '').trim()
                        : '';
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
        _read_locator_text(
            item.locator(
                "div.Sbe6bqNb, div.hVlA20pu div.Sbe6bqNb, div.LvAtyU_f"
            ).first
        )
    )


def extract_comment_author(item: Locator) -> str:
    author = _read_locator_text(
        item.locator(
            ".comment-item-info-wrap a.Z3VQe4ky, "
            ".jyqk68aK a.Z3VQe4ky, "
            ".bTHWOB9x a.Z3VQe4ky, "
            "a.hY8lWHgA"
        ).first
    )
    return author.lstrip("@").strip()


def comment_fingerprint(author: str, text: str) -> str:
    return f"{author}::{text}"


def matches_keyword(text: str, keywords: list[str]) -> str | None:
    if not text:
        return None
    for keyword in keywords:
        if keyword and keyword in text:
            return keyword
    return None


def submit_comment_reply(page: Page, *, fast: bool = False) -> None:
    send_selectors = [
        ".comment-input-container .FbVIhLlK",
        ".comment-input-container .oXIqR6qH",
        ".comment-input-container span.oXIqR6qH",
        '[data-e2e="comment-post"]',
        ".comment-input-right-ct .FbVIhLlK",
    ]
    for selector in send_selectors:
        btn = page.locator(selector).first
        if btn.count() == 0:
            continue
        try:
            if btn.is_visible():
                click_with_fallback(page, btn, timeout=3000, fast=fast)
                return
        except Exception:
            continue
    human_pause(page, 80, 150) if fast else human_pause(page, 200, 500)
    page.keyboard.press("Enter")
    human_pause(page, 250, 500) if fast else human_pause(page, 600, 1200)


def get_comment_body(item: Locator) -> Locator:
    body = item.locator(".bTHWOB9x .hVlA20pu.bthXBGo2, .bTHWOB9x .hVlA20pu").first
    if body.count() > 0:
        return body
    return item.locator(".hVlA20pu.bthXBGo2, .hVlA20pu").first


def get_comment_reply_button(item: Locator) -> Locator:
    body = get_comment_body(item)
    search_root = body if body.count() > 0 else item
    candidate_selectors = [
        ".RC2G0Sa3 .riDGlQZm",
        ".comment-item-stats-container .riDGlQZm",
        ".aNdOM6ya .riDGlQZm",
        ".riDGlQZm .ZkLSMYW2.mOaznmCV",
        ".riDGlQZm .ZkLSMYW2",
        ".riDGlQZm",
    ]
    for selector in candidate_selectors:
        buttons = search_root.locator(selector)
        count = buttons.count()
        for idx in range(count):
            btn = buttons.nth(idx)
            try:
                if btn.is_visible():
                    return btn
            except Exception:
                continue
    reply_text = search_root.get_by_text("回复", exact=True)
    if reply_text.count() > 0:
        for idx in range(reply_text.count()):
            btn = reply_text.nth(idx)
            try:
                if btn.is_visible():
                    return btn
            except Exception:
                continue
        return reply_text.first
    return search_root.locator(".riDGlQZm").first


def get_comment_item_at(page: Page, index: int) -> Locator:
    return get_comment_scroll_container(page).locator('[data-e2e="comment-item"]').nth(
        index
    )


def wake_comment_item(item: Locator) -> None:
    body = get_comment_body(item)
    target = body if body.count() > 0 else item
    try:
        target.hover(timeout=3000)
    except Exception:
        try:
            item.hover(timeout=2000)
        except Exception:
            pass


def get_comment_editor(page: Page) -> Locator:
    selectors = [
        ".comment-input-container .public-DraftEditor-content[contenteditable='true']",
        ".comment-input-container [contenteditable='true']",
        ".comment-input-inner-container [contenteditable='true']",
        ".comment-input-container textarea",
        '[data-e2e="comment-input"]',
        ".gL8GFAmM .public-DraftEditor-content[contenteditable='true']",
    ]
    for selector in selectors:
        editor = page.locator(selector).first
        if editor.count() == 0:
            continue
        try:
            if editor.is_visible():
                return editor
        except Exception:
            continue
    return page.locator(".comment-input-container [contenteditable='true']").first


def activate_comment_editor(page: Page, *, fast: bool = False) -> None:
    placeholders = [
        ".comment-input-container .LpZjb4Yg",
        ".comment-input-container .j_kd_P_l",
        ".comment-input-inner-container",
        ".comment-input-container",
    ]
    for selector in placeholders:
        el = page.locator(selector).first
        if el.count() == 0:
            continue
        try:
            if el.is_visible():
                click_with_fallback(page, el, timeout=3000, fast=fast)
                human_pause(page, 120, 250) if fast else human_pause(page, 300, 600)
                return
        except Exception:
            continue


def is_xigua_reply_only(page: Page) -> bool:
    tooltip = page.locator(
        '.semi-tooltip-content:has-text("前往西瓜视频回复"), '
        '.semi-tooltip-content:has-text("西瓜视频")'
    )
    try:
        return tooltip.count() > 0 and tooltip.first.is_visible()
    except Exception:
        return False


def reply_to_comment(page: Page, item: Locator, template: str) -> bool:
    try:
        item.scroll_into_view_if_needed(timeout=5000)
    except Exception as exc:
        print(f"  回复失败: 评论未滚动到可见区域 ({exc})")
        return False

    wake_comment_item(item)
    human_pause(page, 150, 350)

    reply_btn = get_comment_reply_button(item)
    if reply_btn.count() == 0:
        print("  回复失败: 未找到回复按钮")
        return False

    try:
        if not reply_btn.is_visible():
            wake_comment_item(item)
            human_pause(page, 150, 300)
    except Exception:
        pass

    clicked = False
    for target in (reply_btn, reply_btn.locator("xpath=..").first):
        if target.count() == 0:
            continue
        try:
            click_with_fallback(page, target, timeout=5000, fast=True)
            clicked = True
            break
        except Exception:
            continue
    if not clicked:
        print("  回复失败: 点击回复按钮失败")
        return False

    human_pause(page, 200, 400)

    if is_xigua_reply_only(page):
        print("  回复失败: 当前视频仅支持前往西瓜视频回复，无法在网页评论区直接回复")
        return False

    editor = get_comment_editor(page)
    try:
        editor.wait_for(state="visible", timeout=5000)
    except Exception:
        activate_comment_editor(page, fast=True)
        try:
            editor.wait_for(state="visible", timeout=4000)
        except Exception:
            print("  回复失败: 评论输入框未出现，请确认已登录且该视频允许网页回复")
            return False

    try:
        human_type_in_editor(page, editor, template, fast=True)
        submit_comment_reply(page, fast=True)
        return True
    except Exception as exc:
        print(f"  回复失败: 输入或发送评论失败 ({exc})")
        return False


def make_comment_record(
    post_info: PostInfo,
    nickname: str,
    content: str,
    matched_keyword: str = "",
    replied: bool = False,
    reply_content: str = "",
) -> CommentRecord:
    return CommentRecord(
        video_title=post_info["title"],
        video_author=post_info["author"],
        video_publish_time=post_info["publish_time"],
        comment_nickname=nickname,
        comment_content=content,
        matched_keyword=matched_keyword,
        replied="是" if replied else "否",
        reply_content=reply_content,
    )


def process_visible_comments(
    page: Page,
    post_info: PostInfo,
    keywords: list[str],
    template: str,
    processed: set[str],
    records: list[CommentRecord],
    auto_reply: bool = DEFAULT_AUTO_REPLY,
    replies_so_far: int = 0,
    max_replies: int = 0,
) -> tuple[int, int, bool]:
    batch = extract_visible_comments_batch(page)
    matched = 0
    replied = 0
    reply_limit_reached = False

    for index, author, text in batch:
        if reply_limit_reached:
            break
        if text in SKIP_COMMENT_TEXTS:
            continue

        fp = comment_fingerprint(author, text)
        if fp in processed:
            continue
        processed.add(fp)

        keyword_hit = matches_keyword(text, keywords) or ""
        did_reply = False
        reply_content = ""

        if keyword_hit:
            matched += 1
            print(f"  命中关键词「{keyword_hit}」: {author or '未知用户'} - {text[:40]}")
            if auto_reply and template:
                if max_replies > 0 and replies_so_far + replied >= max_replies:
                    reply_limit_reached = True
                    print(
                        f"  已达本视频回复上限 {max_replies} 次，"
                        "停止继续回复"
                    )
                else:
                    print(f"  正在立即回复: {author or '未知用户'}")
                    item = get_comment_item_at(page, index)
                    if reply_to_comment(page, item, template):
                        did_reply = True
                        reply_content = template
                        replied += 1
                        print(f"  已回复: {author or '未知用户'}")
                        if max_replies > 0 and replies_so_far + replied >= max_replies:
                            reply_limit_reached = True
                            print(
                                f"  已达本视频回复上限 {max_replies} 次，"
                                "停止继续回复"
                            )
                    else:
                        print(f"  未回复: {author or '未知用户'}（见上方失败原因）")

        records.append(
            make_comment_record(
                post_info,
                author or "未知用户",
                text,
                matched_keyword=keyword_hit,
                replied=did_reply,
                reply_content=reply_content,
            )
        )

    return matched, replied, reply_limit_reached


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def save_comments_to_csv(records: list[CommentRecord], search_keyword: str) -> Path:
    output_dir = get_app_dir()
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
                    "是否回复": record["replied"],
                    "回复内容": record["reply_content"],
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


def browse_comments(
    page: Page,
    post_info: PostInfo,
    keywords: list[str],
    reply_template: str,
    max_expand_clicks: int = DEFAULT_MAX_EXPAND_CLICKS,
    expand_batch_size: int = EXPAND_BATCH_SIZE,
    max_rounds: int = 200,
    auto_reply: bool = DEFAULT_AUTO_REPLY,
    max_replies_per_video: int = DEFAULT_MAX_REPLIES_PER_VIDEO,
) -> list[CommentRecord]:
    reply_limit_text = (
        f", 每视频最多回复 {max_replies_per_video} 次"
        if max_replies_per_video > 0
        else ""
    )
    print(
        f"开始在评论区滚动、展开回复并处理关键词评论..."
        f"展开上限 {max_expand_clicks} 次, 每 {expand_batch_size} 次展开后滚动加载"
        + (", 命中后立即回复" if auto_reply else ", 仅采集不自动回复")
        + reply_limit_text
    )
    processed: set[str] = set()
    records: list[CommentRecord] = []
    total_matched = 0
    total_replied = 0
    total_expanded = 0
    batch_expanded = 0
    expand_limit_reached = max_expand_clicks <= 0
    expand_exhausted = False
    reply_limit_reached = False
    stagnant_rounds = 0
    prev_processed_count = 0

    def finalize_partial_expand_batch() -> bool:
        nonlocal batch_expanded, total_matched, total_replied
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
        nonlocal total_matched, total_replied, reply_limit_reached
        matched, replied, limit_hit = process_visible_comments(
            page,
            post_info,
            keywords,
            reply_template,
            processed,
            records,
            auto_reply=auto_reply,
            replies_so_far=total_replied,
            max_replies=max_replies_per_video,
        )
        total_matched += matched
        total_replied += replied
        if limit_hit:
            reply_limit_reached = True
            print(
                f"已达本视频回复上限 {max_replies_per_video} 次"
                f"(累计成功回复 {total_replied} 次)，关闭当前视频"
            )
        return matched, replied, limit_hit

    def drain_keyword_comments() -> bool:
        while True:
            matched, replied, limit_hit = process_matches_now()
            if matched == 0 or limit_hit:
                return limit_hit

    def finish_expand_batch() -> bool:
        nonlocal batch_expanded
        if batch_expanded < expand_batch_size:
            return False
        print(f"已完成 {expand_batch_size} 次展开，向下滚动加载更多评论...")
        load_more_comments_by_scrolling(page, steps=3)
        matched, replied, limit_hit = process_matches_now()
        print(
            f"本批滚动后处理完成: 命中 {matched} 条, 回复 {replied} 条"
            + ("，当前无更多可处理的关键词评论" if matched == 0 else "")
        )
        batch_expanded = 0
        return limit_hit

    if drain_keyword_comments():
        print(
            f"评论区处理完成: 共展开 {total_expanded} 次, 扫描 {len(processed)} 条评论, "
            f"命中关键词 {total_matched} 条, 成功回复 {total_replied} 条"
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
                        reply_limit_reached = True
                        break
                    if batch_expanded >= expand_batch_size:
                        if finish_expand_batch():
                            reply_limit_reached = True
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
                        reply_limit_reached = True
                        break
                    if batch_expanded >= expand_batch_size:
                        if finish_expand_batch():
                            reply_limit_reached = True
                            break
                    if total_expanded >= max_expand_clicks:
                        stop_expand_phase(exhausted=False)
                    continue

                stop_expand_phase(exhausted=True)
                break

        if reply_limit_reached:
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

        matched, replied, limit_hit = process_matches_now()
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
            f"更多 {more_clicked} 次, 命中 {matched} 条, 回复 {replied} 条, "
            f"累计处理 {len(processed)} 条, 可见评论 {comment_count} 条, "
            f"累计回复 {total_replied}"
            + (f"/{max_replies_per_video}" if max_replies_per_video > 0 else "")
            + ("，已无更多评论" if no_more else "")
            + ("，展开按钮已用尽(提前终止)" if expand_exhausted else "")
            + ("，已停止展开" if expand_limit_reached and not expand_exhausted else "")
            + ("，已达回复上限" if reply_limit_reached else "")
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
        f"命中关键词 {total_matched} 条, 成功回复 {total_replied} 条"
    )
    close_video_panel(page)
    return records


def process_single_video(
    page: Page,
    video_index: int,
    video_count: int,
    keywords: list[str],
    reply_template: str,
    max_expand_clicks: int,
    auto_reply: bool = DEFAULT_AUTO_REPLY,
    max_replies_per_video: int = DEFAULT_MAX_REPLIES_PER_VIDEO,
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
        reply_template,
        max_expand_clicks=max_expand_clicks,
        auto_reply=auto_reply,
        max_replies_per_video=max_replies_per_video,
    )


def run_douyin_flow(
    page: Page,
    keyword: str,
    video_count: int,
    keywords: list[str],
    reply_template: str,
    max_expand_clicks: int,
    auto_reply: bool = DEFAULT_AUTO_REPLY,
    max_replies_per_video: int = DEFAULT_MAX_REPLIES_PER_VIDEO,
) -> Path | None:
    search_on_douyin(page, keyword)
    all_records: list[CommentRecord] = []

    for video_index in range(video_count):
        try:
            records = process_single_video(
                page,
                video_index,
                video_count,
                keywords,
                reply_template,
                max_expand_clicks,
                auto_reply=auto_reply,
                max_replies_per_video=max_replies_per_video,
            )
            all_records.extend(records)
        except Exception as exc:
            print(f"第 {video_index + 1} 个视频处理失败: {exc}")
            close_video_panel(page)
            continue

    if all_records:
        output_path = save_comments_to_csv(all_records, keyword)
        print(f"\n共处理 {video_count} 个视频, 采集 {len(all_records)} 条评论")
        print(f"评论数据已保存至: {output_path}")
    else:
        print("未采集到评论数据，跳过 CSV 保存。")
        output_path = None

    print("抖音搜索、评论区浏览与自动回复流程已完成。")
    return output_path


def run_playwright(
    ws_endpoint: str,
    keyword: str,
    video_count: int,
    keywords: list[str],
    reply_template: str,
    max_expand_clicks: int,
    auto_reply: bool = DEFAULT_AUTO_REPLY,
    max_replies_per_video: int = DEFAULT_MAX_REPLIES_PER_VIDEO,
) -> None:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_endpoint)
        contexts = browser.contexts
        context = contexts[0] if contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()

        run_douyin_flow(
            page,
            keyword,
            video_count,
            keywords,
            reply_template,
            max_expand_clicks,
            auto_reply=auto_reply,
            max_replies_per_video=max_replies_per_video,
        )

        input("流程结束，按回车断开连接...")
        browser.close()


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
    reply_template = ask_reply_template()
    auto_reply = DEFAULT_AUTO_REPLY
    max_expand_clicks = ask_max_expand_clicks()
    max_replies_per_video = ask_max_replies_per_video()

    reply_limit_desc = (
        f"每视频最多回复 {max_replies_per_video} 次"
        if max_replies_per_video > 0
        else "每视频回复次数不限制"
    )
    print(
        f"\n将搜索「{keyword}」, 处理 {video_count} 个视频, "
        f"使用 {len(keywords)} 个关键词, 回复模板: {reply_template}, "
        f"自动回复: {'是' if auto_reply else '否'}, "
        f"每个视频展开上限: {max_expand_clicks} 次(每 {EXPAND_BATCH_SIZE} 次展开后处理关键词评论), "
        f"{reply_limit_desc}"
    )
    print("环境启动成功，正在通过 Playwright 连接...")
    run_playwright(
        ws,
        keyword,
        video_count,
        keywords,
        reply_template,
        max_expand_clicks,
        auto_reply=auto_reply,
        max_replies_per_video=max_replies_per_video,
    )


if __name__ == "__main__":
    main()
