#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novel_rank_data.browser import browser_runtime_available, fetch_url_in_browser
from novel_rank_data.extractors import extract_records_for_platform
from novel_rank_data.http import fetch_url
from novel_rank_data.platforms import resolve_platforms
from novel_rank_data.storage import ensure_dir, write_json, write_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch ranking/discovery pages from major novel platforms.")
    parser.add_argument("--platforms", nargs="*", help="Platform slugs such as qidian jjwxc fanqie qimao zongheng")
    parser.add_argument("--output-root", default=str(ROOT / "data" / "raw"), help="Root directory for raw snapshots")
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout in seconds")
    parser.add_argument(
        "--fetch-mode",
        choices=("auto", "http", "browser"),
        default="auto",
        help="Force plain HTTP, browser automation, or auto mode.",
    )
    return parser.parse_args()


def fetch_endpoint(endpoint, args):
    if args.fetch_mode == "http":
        result = fetch_url(endpoint.url, timeout=args.timeout)
        return {
            "url": result.url,
            "final_url": result.final_url,
            "status_code": result.status_code,
            "headers": result.headers,
            "text": result.text,
            "error": result.error,
            "fetch_method": "http",
        }

    should_try_browser = args.fetch_mode == "browser" or (
        args.fetch_mode == "auto" and endpoint.preferred_fetch == "browser"
    )
    if should_try_browser and browser_runtime_available():
        browser_result = fetch_url_in_browser(
            endpoint.url,
            timeout=args.timeout,
            wait_for_selector=endpoint.wait_for_selector,
            post_wait_ms=endpoint.post_wait_ms,
        )
        if browser_result.ok and browser_result.html:
            return {
                "url": endpoint.url,
                "final_url": browser_result.final_url,
                "status_code": browser_result.status_code,
                "headers": {},
                "text": browser_result.html,
                "error": browser_result.error,
                "fetch_method": "browser",
            }
        if args.fetch_mode == "browser":
            return {
                "url": endpoint.url,
                "final_url": browser_result.final_url,
                "status_code": browser_result.status_code,
                "headers": {},
                "text": browser_result.html,
                "error": browser_result.error or browser_result.stderr,
                "fetch_method": "browser",
            }

    result = fetch_url(endpoint.url, timeout=args.timeout)
    fetch_method = "http"
    if (
        args.fetch_mode == "auto"
        and browser_runtime_available()
        and (result.status_code in (0, 202, 403) or not result.text.strip())
    ):
        browser_result = fetch_url_in_browser(
            endpoint.url,
            timeout=args.timeout,
            wait_for_selector=endpoint.wait_for_selector,
            post_wait_ms=endpoint.post_wait_ms,
        )
        if browser_result.ok and browser_result.html:
            return {
                "url": endpoint.url,
                "final_url": browser_result.final_url,
                "status_code": browser_result.status_code,
                "headers": {},
                "text": browser_result.html,
                "error": browser_result.error,
                "fetch_method": "browser_fallback",
            }

    return {
        "url": result.url,
        "final_url": result.final_url,
        "status_code": result.status_code,
        "headers": result.headers,
        "text": result.text,
        "error": result.error,
        "fetch_method": fetch_method,
    }


def main() -> int:
    args = parse_args()
    captured_at = datetime.now(UTC)
    capture_day = captured_at.strftime("%Y-%m-%d")
    capture_stamp = captured_at.strftime("%H%M%S")
    output_root = Path(args.output_root).expanduser().resolve()
    platforms = resolve_platforms(args.platforms)

    for platform in platforms:
        platform_dir = ensure_dir(output_root / capture_day / platform.slug / capture_stamp)
        for endpoint in platform.endpoints:
            result = fetch_endpoint(endpoint, args)
            document = None
            records = []
            extraction_method = None
            if result["text"]:
                document, records, extraction_method = extract_records_for_platform(
                    platform.slug,
                    result["text"],
                    endpoint_name=endpoint.name,
                )

            payload = {
                "platform": platform.slug,
                "platform_display_name": platform.display_name,
                "audience": platform.audience,
                "monetization": platform.monetization,
                "captured_at": captured_at.isoformat(),
                "endpoint": {
                    "name": endpoint.name,
                    "chart": endpoint.chart,
                    "url": endpoint.url,
                    "notes": endpoint.notes,
                },
                "request": {
                    "url": result["url"],
                    "final_url": result["final_url"],
                    "status_code": result["status_code"],
                    "headers": result["headers"],
                    "error": result["error"],
                    "fetch_method": result["fetch_method"],
                },
                "page": {
                    "title": document.title if document else "",
                    "visible_text_excerpt": (document.visible_text[:1000] if document else ""),
                    "record_count": len(records),
                    "extraction_method": extraction_method,
                },
                "records": records,
            }
            base_name = endpoint.name
            write_json(platform_dir / f"{base_name}.json", payload)
            write_text(platform_dir / f"{base_name}.html", result["text"])
            print(
                f"[{platform.slug}:{endpoint.name}] status={result['status_code']} fetch={result['fetch_method']} "
                f"records={len(records)} "
                f"saved={platform_dir / f'{base_name}.json'}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
