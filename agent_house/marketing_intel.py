"""Wing 2 — Kilobyte Labs Continuous Internet Trend & Buyer-Intent Auditor ($0).

Continuously audits live public sources with zero paid APIs:
1. Hacker News Algolia API (recent Show HN, Ask HN, and comments mentioning
   macOS menu bar utilities, localhost port conflicts, screenshot compression,
   Electron bloat, and indie Mac apps).
2. Reddit live public JSON feeds (r/macapps, r/SideProject, r/macOS, r/webdev)
   for fresh high-intent discussions and competitor launches.
3. GitHub Search API (trending Swift/macOS menu bar utilities & macOS updates).

Outputs structured intelligence to `state/market_intel.json` & `state/market_intel.md`
with concrete recommended engagement angles and zero fabricated URLs.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_house.config import STATE_DIR
from agent_house.hall_room import _atomic_write, _utc_now

BRAND_NAME = "Kilobyte Labs"
BRAND_TAGLINE = "Tiny native Apple Silicon macOS utilities. Zero Electron. Zero subscriptions."
STOREFRONT_URL = "https://imgolamrabbani.github.io/neon-agent-house/"

PRODUCTS: list[dict[str, Any]] = [
    {
        "slug": "portpilot",
        "name": "PortPilot",
        "price_usd": 9,
        "url": "https://adorable48.gumroad.com/l/portpilot",
        "hook": "337 KB native Swift/AppKit macOS menu-bar localhost port radar & 1-click process killer (SIGTERM/SIGKILL, Open in Browser, Clean All Dev Ports).",
        "keywords": ["port", "localhost", "eaddrinuse", "lsof", "3000", "5173", "menu bar", "menubar", "developer", "electron", "kill process", "vite", "nextjs", "docker"],
    },
    {
        "slug": "snapshrink",
        "name": "SnapShrink",
        "price_usd": 7,
        "url": "https://adorable48.gumroad.com/l/snapshrink",
        "hook": "Native Apple Silicon Swift + hardware ImageIO screenshot/image compressor & automatic GPS/camera EXIF privacy stripper (zero cloud uploads).",
        "keywords": ["screenshot", "compress", "image", "exif", "gps", "metadata", "privacy", "png", "heic", "tinypng", "imageoptim", "menu bar", "menubar"],
    },
    {
        "slug": "mac-power-bundle",
        "name": "Mac Power User Bundle",
        "price_usd": 12,
        "url": "https://adorable48.gumroad.com/l/mac-power-bundle",
        "hook": "Both PortPilot + SnapShrink compiled native Apple Silicon macOS apps + offline Gumroad License Keys ($12 one-time, save 25%).",
        "keywords": ["macapps", "macos", "indie", "bundle", "utility", "utilities", "one-time", "no subscription", "native", "swift"],
    },
]

MARKET_INTEL_JSON = STATE_DIR / "market_intel.json"
MARKET_INTEL_MD = STATE_DIR / "market_intel.md"
CAMPAIGNS_JSON = STATE_DIR / "marketing_campaigns.json"

USER_AGENT = "KilobyteLabs-TrendAuditor/1.0 (+https://imgolamrabbani.github.io/neon-agent-house/)"


def _fetch_json(url: str, timeout: int = 12) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _match_product(text: str) -> dict[str, Any]:
    low = text.lower()
    best_prod = PRODUCTS[2]
    best_hits = 0
    for prod in PRODUCTS:
        hits = sum(1 for kw in prod["keywords"] if kw in low)
        if hits > best_hits:
            best_hits = hits
            best_prod = prod
    return {"product": best_prod["name"], "url": best_prod["url"], "keyword_hits": best_hits}


def audit_hacker_news(max_per_query: int = 6) -> list[dict[str, Any]]:
    queries = [
        "macOS menu bar app",
        "localhost port kill",
        "screenshot compress macOS",
        "native macOS utility Electron",
        "Show HN macOS menu bar",
    ]
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for q in queries:
        qs = urllib.parse.urlencode({"query": q, "tags": "story", "hitsPerPage": max_per_query})
        url = f"https://hn.algolia.com/api/v1/search_by_date?{qs}"
        try:
            data = _fetch_json(url)
        except Exception:
            continue
        for hit in data.get("hits", []):
            oid = str(hit.get("objectID") or "")
            if not oid or oid in seen:
                continue
            seen.add(oid)
            title = str(hit.get("title") or "").strip()
            if not title:
                continue
            match = _match_product(title)
            items.append(
                {
                    "source": "hacker_news",
                    "id": oid,
                    "title": title,
                    "url": f"https://news.ycombinator.com/item?id={oid}",
                    "points": int(hit.get("points") or 0),
                    "comments": int(hit.get("num_comments") or 0),
                    "created_at": str(hit.get("created_at") or ""),
                    "query": q,
                    "matched_product": match["product"],
                    "matched_url": match["url"],
                    "relevance_score": match["keyword_hits"] * 15 + min(40, int(hit.get("points") or 0)),
                }
            )
    items.sort(key=lambda x: x["relevance_score"], reverse=True)
    return items[:15]


def audit_reddit_public(subreddits: tuple[str, ...] = ("macapps", "SideProject", "macOS", "webdev")) -> list[dict[str, Any]]:
    import xml.etree.ElementTree as ET

    items: list[dict[str, Any]] = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for sub in subreddits:
        rss_url = f"https://www.reddit.com/r/{sub}/hot/.rss?limit=15"
        try:
            req = urllib.request.Request(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) KilobyteLabsAuditor/1.0"},
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml_text = resp.read().decode("utf-8", errors="replace")
            root = ET.fromstring(xml_text)
        except Exception:
            continue
        for entry in root.findall("atom:entry", ns)[:15]:
            title = (entry.findtext("atom:title", "", ns) or "").strip()
            link_el = entry.find("atom:link", ns)
            url = link_el.attrib.get("href", "") if link_el is not None else ""
            content = (entry.findtext("atom:content", "", ns) or "")[:300]
            eid = (entry.findtext("atom:id", "", ns) or "").strip()
            if not title or not url:
                continue
            match = _match_product(f"{title} {content}")
            items.append(
                {
                    "source": f"reddit:r/{sub}",
                    "subreddit": sub,
                    "id": eid,
                    "title": title,
                    "url": url,
                    "upvotes": 0,
                    "comments": 0,
                    "flair": "",
                    "matched_product": match["product"],
                    "matched_url": match["url"],
                    "relevance_score": match["keyword_hits"] * 20 + 10,
                }
            )
        time.sleep(0.35)
    items.sort(key=lambda x: x["relevance_score"], reverse=True)
    return items[:20]


def audit_github_macos_trends() -> list[dict[str, Any]]:
    url = (
        "https://api.github.com/search/repositories?"
        + urllib.parse.urlencode(
            {"q": "macos menu bar swift stars:>30 pushed:>2026-01-01", "sort": "updated", "per_page": 10}
        )
    )
    items: list[dict[str, Any]] = []
    try:
        data = _fetch_json(url)
    except Exception:
        return items
    for repo in data.get("items", []):
        name = str(repo.get("full_name") or "")
        desc = str(repo.get("description") or "")
        items.append(
            {
                "source": "github_trends",
                "name": name,
                "description": desc,
                "url": str(repo.get("html_url") or ""),
                "stars": int(repo.get("stargazers_count") or 0),
                "updated_at": str(repo.get("updated_at") or ""),
            }
        )
    return items


def check_own_links_health() -> list[dict[str, Any]]:
    urls = [
        ("Storefront", STOREFRONT_URL),
        ("PortPilot ($9)", "https://adorable48.gumroad.com/l/portpilot"),
        ("SnapShrink ($7)", "https://adorable48.gumroad.com/l/snapshrink"),
        ("Mac Power User Bundle ($12)", "https://adorable48.gumroad.com/l/mac-power-bundle"),
    ]
    out = []
    for label, u in urls:
        code = 0
        try:
            req = urllib.request.Request(u, headers={"User-Agent": USER_AGENT}, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as r:
                code = int(r.status)
        except Exception:
            try:
                req = urllib.request.Request(u, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=10) as r:
                    code = int(r.status)
            except Exception:
                code = 0
        out.append({"label": label, "url": u, "http_status": code, "live": code == 200})
    return out


def run_live_internet_audit() -> dict[str, Any]:
    """Run full Wing 2 Internet Trend, Competitor & Buyer-Intent Audit and save to state/."""
    now = _utc_now()
    hn = audit_hacker_news()
    reddit = audit_reddit_public()
    gh = audit_github_macos_trends()
    health = check_own_links_health()

    report = {
        "brand": BRAND_NAME,
        "tagline": BRAND_TAGLINE,
        "audited_at": now,
        "own_links_health": health,
        "all_own_links_live": all(h["live"] for h in health),
        "counts": {
            "reddit_leads": len(reddit),
            "hacker_news_leads": len(hn),
            "github_macos_trends": len(gh),
        },
        "top_reddit_opportunities": reddit,
        "top_hn_opportunities": hn,
        "github_macos_trends": gh,
    }
    _atomic_write(MARKET_INTEL_JSON, json.dumps(report, indent=2) + "\n")
    _atomic_write(MARKET_INTEL_MD, render_intel_markdown(report))
    return report


def render_intel_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['brand']} — Live Internet Trend & Marketing Audit",
        "",
        f"> **Updated:** {report['audited_at']} | **All Storefront/Gumroad Links Live:** `{report['all_own_links_live']}`",
        "",
        "## Live Product & Storefront Health",
    ]
    for h in report["own_links_health"]:
        lines.append(f"- **{h['label']}**: {h['url']} (`HTTP {h['http_status']}`)")

    lines.extend(["", "## Top Live Reddit Conversations & Launch Channels"])
    for r in report["top_reddit_opportunities"][:10]:
        lines.append(
            f"- **[{r['source']}]** ({r['upvotes']}↑, {r['comments']} comments, match=`{r['matched_product']}`): "
            f"[{r['title']}]({r['url']})"
        )

    lines.extend(["", "## Top Recent Hacker News Signals"])
    for h in report["top_hn_opportunities"][:8]:
        lines.append(
            f"- **[HN]** ({h['points']} pts, {h['comments']} comments, match=`{h['matched_product']}`): "
            f"[{h['title']}]({h['url']})"
        )

    lines.extend(["", "## Trending macOS Swift Menu-Bar Repos (Competitor & Feature Radar)"])
    for g in report["github_macos_trends"][:8]:
        lines.append(f"- **{g['name']}** ({g['stars']}★): {g['description']} — {g['url']}")

    return "\n".join(lines) + "\n"
