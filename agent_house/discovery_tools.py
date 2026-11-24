"""Zero-cost ($0) live discovery tools for Pain-Point Scout & Market Analyst.

Uses only free, unauthenticated public endpoints (HN Algolia, GitHub Search API)
plus a pre-flight URL liveness filter so rooms avoid 403/404 links on Round 0.
"""

from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

USER_AGENT = "NeonAgentHouse/2.0"


def _clean_html(raw: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw or ""))
    return re.sub(r"\s+", " ", text).strip()


def fetch_url_text(url: str, timeout: float = 8.0, max_bytes: int = 120_000) -> tuple[bool, int, str]:
    """Fetch a URL and return (is_ok, status_code, cleaned_text_or_error)."""
    if not url or not url.startswith(("http://", "https://")):
        return False, 0, "invalid URL scheme"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = int(getattr(resp, "status", 200))
            raw = resp.read(max_bytes).decode("utf-8", errors="ignore")
            return (200 <= status < 400), status, _clean_html(raw)
    except urllib.error.HTTPError as exc:
        return False, int(exc.code), f"HTTP {exc.code}"
    except Exception as exc:
        return False, 0, f"{type(exc).__name__}: {exc}"


def preflight_filter_urls(urls: list[str], timeout: float = 6.0) -> dict[str, Any]:
    """Pre-check URLs before submitting to Hall Room Verifier to hit 100% first-pass rate."""
    live: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for url in urls:
        ok, status, detail = fetch_url_text(url, timeout=timeout, max_bytes=16_000)
        if ok:
            live.append({"url": url, "status": status})
        else:
            rejected.append({"url": url, "status": status, "reason": detail})
    return {"live": live, "rejected": rejected}


def search_hn_buyer_pain(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Query free Hacker News Algolia API for real primary-source buyer complaints."""
    qs = urllib.parse.urlencode({"query": query, "tags": "comment", "hitsPerPage": limit})
    url = f"https://hn.algolia.com/api/v1/search_by_date?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=8.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    results: list[dict[str, Any]] = []
    for hit in data.get("hits", []):
        obj_id = hit.get("objectID")
        text = _clean_html(hit.get("comment_text") or "")
        if obj_id and len(text) >= 40:
            results.append(
                {
                    "source_url": f"https://news.ycombinator.com/item?id={obj_id}",
                    "verbatim_quote": text[:280],
                    "source_context": f"Hacker News, {(hit.get('created_at') or '')[:10]}",
                }
            )
    return results


def search_github_issues_pain(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Query public GitHub Issues Search API ($0) for real user feature/pain complaints."""
    qs = urllib.parse.urlencode({"q": f"{query} is:issue", "per_page": limit})
    url = f"https://api.github.com/search/issues?{qs}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=8.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    results: list[dict[str, Any]] = []
    for item in data.get("items", []):
        html_url = item.get("html_url")
        title = (item.get("title") or "").strip()
        if html_url and title:
            results.append(
                {
                    "source_url": html_url,
                    "verbatim_quote": title[:240],
                    "source_context": f"GitHub Issue, {(item.get('created_at') or '')[:10]}",
                }
            )
    return results
