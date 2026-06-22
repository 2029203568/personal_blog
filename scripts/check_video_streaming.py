#!/usr/bin/env python3
"""检查视频 URL 是否支持 Range（Accept-Ranges + 206）。"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from typing import Dict, Optional, Tuple

DEFAULT_URL = "http://127.0.0.1:8000/assets/videos/facebook-yanghao.mp4"


def fetch_headers(url: str, range_header: Optional[str] = None) -> Tuple[Dict[str, str], int]:
    req = urllib.request.Request(url, method="HEAD")
    if range_header:
        req.add_header("Range", range_header)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return {k.lower(): v for k, v in resp.headers.items()}, resp.status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args()
    url = args.url

    print(f"HEAD {url}")
    try:
        h1, s1 = fetch_headers(url)
    except Exception as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  状态: {s1}")
    print(f"  Accept-Ranges: {h1.get('accept-ranges', '(无)')}")
    print(f"  Content-Length: {h1.get('content-length', '(无)')}")
    print(f"  Content-Type: {h1.get('content-type', '(无)')}")

    print(f"\nHEAD + Range bytes=0-1023")
    try:
        h2, s2 = fetch_headers(url, "bytes=0-1023")
    except urllib.error.HTTPError as e:
        h2 = {k.lower(): v for k, v in e.headers.items()}
        s2 = e.code
    print(f"  状态: {s2} (期望 206)")
    print(f"  Content-Range: {h2.get('content-range', '(无)')}")

    ok_range = h1.get("accept-ranges") == "bytes"
    ok_206 = s2 == 206
    if ok_range and ok_206:
        print("\n✓ Range 流媒体配置正常，浏览器应可拖拽进度。")
    else:
        print("\n✗ 未通过。请检查：")
        if not ok_range:
            print("  - 响应缺少 Accept-Ranges: bytes（后端路由或 Nginx）")
        if not ok_206:
            print("  - Range 请求未返回 206（代理可能吞掉 Range 头）")
        print("  - MP4 需 faststart: python3 scripts/faststart_mp4.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
