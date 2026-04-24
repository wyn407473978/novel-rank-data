from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BROWSER_SCRIPT = ROOT / "scripts" / "browser_fetch.mjs"
DEFAULT_CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


@dataclass
class BrowserFetchResult:
    ok: bool
    final_url: str
    status_code: int
    html: str
    title: str
    stderr: str | None = None
    error: str | None = None


def browser_runtime_available() -> bool:
    return shutil.which("node") is not None and BROWSER_SCRIPT.exists() and resolve_browser_executable() is not None


def resolve_browser_executable() -> str | None:
    for path in DEFAULT_CHROME_PATHS:
        if Path(path).exists():
            return path
    return None


def fetch_url_in_browser(
    url: str,
    timeout: int = 25,
    wait_for_selector: str | None = None,
    post_wait_ms: int = 0,
) -> BrowserFetchResult:
    executable_path = resolve_browser_executable()
    if executable_path is None:
        return BrowserFetchResult(
            ok=False,
            final_url=url,
            status_code=0,
            html="",
            title="",
            error="No supported Chrome-family browser executable found.",
        )

    payload = {
        "url": url,
        "timeoutMs": timeout * 1000,
        "waitUntil": "domcontentloaded",
        "waitForSelector": wait_for_selector,
        "postWaitMs": post_wait_ms,
        "executablePath": executable_path,
    }
    command = ["node", str(BROWSER_SCRIPT), json.dumps(payload, ensure_ascii=False)]
    completed = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
    if completed.returncode != 0:
        return BrowserFetchResult(
            ok=False,
            final_url=url,
            status_code=0,
            html="",
            title="",
            stderr=completed.stderr.strip() or None,
            error=f"Browser fetch failed with code {completed.returncode}",
        )
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return BrowserFetchResult(
            ok=False,
            final_url=url,
            status_code=0,
            html="",
            title="",
            stderr=completed.stdout[:1000],
            error=f"Invalid browser JSON output: {exc}",
        )
    return BrowserFetchResult(
        ok=data.get("ok", False),
        final_url=data.get("finalUrl") or url,
        status_code=data.get("status", 0),
        html=data.get("html", ""),
        title=data.get("title", ""),
        stderr=data.get("stderr"),
        error=data.get("error"),
    )
