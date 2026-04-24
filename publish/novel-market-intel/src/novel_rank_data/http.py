from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    text: str
    error: str | None = None


def fetch_url(url: str, timeout: int = 20) -> FetchResult:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or sniff_charset(raw) or "utf-8"
            text = raw.decode(charset, errors="replace")
            return FetchResult(
                url=url,
                final_url=response.geturl(),
                status_code=response.status,
                headers=dict(response.headers.items()),
                text=text,
            )
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return FetchResult(
            url=url,
            final_url=url,
            status_code=exc.code,
            headers=dict(exc.headers.items()),
            text=body,
            error=str(exc),
        )
    except URLError as exc:
        return FetchResult(
            url=url,
            final_url=url,
            status_code=0,
            headers={},
            text="",
            error=str(exc),
        )


def sniff_charset(raw: bytes) -> str | None:
    head = raw[:4096].decode("ascii", errors="ignore").lower()
    patterns = (
        r'charset=["\']?([a-z0-9_\-]+)',
        r'content=["\'][^"\']*charset=([a-z0-9_\-]+)',
    )
    for pattern in patterns:
        match = re.search(pattern, head)
        if match:
            return match.group(1)
    return None
