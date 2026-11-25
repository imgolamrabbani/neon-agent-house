"""Outstanding YouTube Shorts SEO Engine & 100-Point SEO Scorer.

Engineers high-CTR titles, semantic search descriptions, timestamped chapters,
competitor-alternative keyword tags (strictly <=500 chars per YouTube API rules),
and pinned-comment CTAs to maximize both YouTube Shorts Shelf & Search reach.
"""

from __future__ import annotations

from typing import Any

YOUTUBE_CATEGORY_SCIENCE_TECH = "28"
MAX_TAG_CHARS = 480  # Safe margin below YouTube Data API v3's 500-char hard limit

SEO_PROFILES: dict[str, dict[str, Any]] = {
    "invoice-pulse-01": {
        "title": "STOP Paying $59/mo for Invoice Reminders (1-File Python Fix) #Shorts",
        "primary_keyword": "freelance invoice tracker",
        "competitor_alts": [
            "HoneyBook alternative",
            "Dubsado alternative",
            "HelloBonsai alternative",
            "free invoice follow up automation",
        ],
        "semantic_summary": (
            "Tired of paying $36-$59/month for HoneyBook, Dubsado, or Bonsai just to track overdue invoices "
            "and chase late client payments? InvoicePulse is a 100% local, zero-dependency Python 3 script "
            "that audits your invoice CSV, calculates prorated late fees, generates Day-3 to Day-30 polite "
            "escalation emails, and builds a dark-mode interactive cashflow dashboard with zero monthly fees."
        ),
        "chapters": [
            ("0:00", "The $708/yr freelance invoicing SaaS trap"),
            ("0:06", "Why hidden 6.9% fees & silent AP leaks drain solo builders"),
            ("0:14", "1-file local Python replacement (zero pip installs)"),
            ("0:22", "Dark-mode dashboard + automatic late fees & mailto drafts"),
            ("0:32", "$708/yr SaaS rent vs. $9 once forever"),
        ],
        "hashtags": ["#Shorts", "#Python", "#Freelance", "#SoloBuilder", "#Automation"],
        "extra_tags": [
            "invoice automation python",
            "late invoice email template",
            "overdue invoice tracker",
            "freelance tools no subscription",
            "python project ideas",
            "solo developer tools",
            "indie hacker tools",
            "stop paying monthly subscriptions",
            "micro saas tools",
            "local first software",
        ],
    },
    "saas-sub-trimmer-01": {
        "title": "STOP Giving Apps Your Bank Password (Local CSV Audit Fix) #Shorts",
        "primary_keyword": "Plaid alternative subscription tracker",
        "competitor_alts": [
            "YNAB alternative",
            "Monarch Money alternative",
            "Rocket Money alternative",
            "offline subscription tracker CSV",
        ],
        "semantic_summary": (
            "Why pay $14.99/month for YNAB, Monarch Money, or Rocket Money AND hand over your bank username, "
            "password, and MFA to Plaid? SubTrim is a 100% offline Python 3 CSV statement auditor that detects "
            "forgotten recurring SaaS renewals, flags silent price hikes in red, and calculates your instant "
            "annual savings in a dark-mode local HTML dashboard—without ever sharing a single bank login."
        ),
        "chapters": [
            ("0:00", "Why sharing bank passwords with budget apps is broken"),
            ("0:07", "How forgotten SaaS trials & price hikes drain $1,700+/yr"),
            ("0:15", "Zero-Plaid local CSV audit in 1 Python command"),
            ("0:23", "Dark-mode savings dashboard + instant price-hike alerts"),
            ("0:33", "Own it for $9 once instead of renting $180/yr"),
        ],
        "hashtags": ["#Shorts", "#Privacy", "#Python", "#PersonalFinance", "#NoSubscription"],
        "extra_tags": [
            "cancel forgotten subscriptions",
            "bank csv analyzer python",
            "plaid privacy alternative",
            "saas spend tracker",
            "personal finance python script",
            "offline budget tool",
            "indie hacker finance",
            "stop subscription creep",
            "local first finance",
            "solo founder tools",
        ],
    },
    "scope-shield-01": {
        "title": "Client Asked for a 'Quick Tweak'? Send THIS Change Order #Shorts",
        "primary_keyword": "freelance scope creep change order",
        "competitor_alts": [
            "Proposify alternative",
            "Qwilr alternative",
            "Bonsai contract alternative",
            "freelance change order generator",
        ],
        "semantic_summary": (
            "Stop losing 20%-40% of your freelance project margin to casual Slack DMs asking for 'one quick tweak.' "
            "ScopeShield is a local Python 3 tool that turns your baseline SOW and out-of-scope requests into a "
            "priced, print-to-PDF HTML Change Order with automatic extra-hours, schedule-shift math, and a polite "
            "1-click approval email—without paying $49-$65/month for Proposify or Qwilr."
        ),
        "chapters": [
            ("0:00", "How 'one quick tweak' kills freelance profit margins"),
            ("0:08", "Turning baseline SOW + client requests into exact pricing"),
            ("0:18", "Printable Change Order + 1-click polite approval email"),
            ("0:28", "$9 one-time vs $588/yr proposal SaaS"),
        ],
        "hashtags": ["#Shorts", "#Freelance", "#WebDev", "#Agency", "#Python"],
        "extra_tags": [
            "stop scope creep freelance",
            "change order template freelance",
            "freelance pricing tips",
            "client management tools",
            "fixed price freelance tips",
            "solo agency automation",
            "python productivity script",
            "no subscription freelance tools",
        ],
    },
    "launch-check-01": {
        "title": "Audit Any Site's SEO & Security in 5 Seconds (No $139/mo Tool) #Shorts",
        "primary_keyword": "local SEO and security header auditor",
        "competitor_alts": [
            "Ahrefs alternative",
            "Semrush alternative",
            "Moz Pro alternative",
            "Screaming Frog alternative python",
        ],
        "semantic_summary": (
            "Stop shipping day-one launch bugs like broken placeholder links, missing OpenGraph tags, or missing "
            "HTTP security headers—without paying $49-$139/month for Ahrefs, Semrush, or Moz. LaunchCheck audits "
            "any live URL or local HTML file in 5 seconds using Python 3 stdlib and outputs a 0-100 Launch Readiness "
            "dark-mode dashboard with prioritized fixes."
        ),
        "chapters": [
            ("0:00", "Day-one launch bugs that silently kill traffic"),
            ("0:09", "Auditing SEO, OG tags, links & 6 security headers in 5s"),
            ("0:20", "0-100 dark-mode Launch Readiness report"),
            ("0:30", "$9 once vs $139/mo SEO suites"),
        ],
        "hashtags": ["#Shorts", "#SEO", "#WebDev", "#IndieHackers", "#Python"],
        "extra_tags": [
            "pre launch website checklist",
            "python seo audit script",
            "http security headers checker",
            "broken link checker python",
            "indie hacker launch checklist",
            "technical seo tool",
            "local website auditor",
        ],
    },
    "git-changelog-kit-01": {
        "title": "Turn Git Commits Into a Public Changelog Page in 2 Seconds #Shorts",
        "primary_keyword": "git log to HTML changelog generator",
        "competitor_alts": [
            "Beamer changelog alternative",
            "Canny changelog alternative",
            "LaunchNotes alternative",
            "static HTML release notes generator",
        ],
        "semantic_summary": (
            "Stop paying $49-$99/month for Beamer or Canny just to show users what you shipped. ChangelogKit turns "
            "any local Git commit history into a categorized CHANGELOG.md and a searchable dark-mode static HTML "
            "release notes page in 2 seconds—ready to drop straight onto GitHub Pages for $0 hosting."
        ),
        "chapters": [
            ("0:00", "Why skipping changelogs makes your product look dead"),
            ("0:09", "1 Python command turns Git log into dark-mode release notes"),
            ("0:20", "Auto-categorized features, fixes & breaking changes"),
            ("0:30", "$9 once vs $588/yr changelog SaaS"),
        ],
        "hashtags": ["#Shorts", "#Git", "#Python", "#IndieHackers", "#DevTools"],
        "extra_tags": [
            "automated changelog generator",
            "git release notes script",
            "conventional commits html",
            "github pages changelog",
            "solo saas tools",
            "developer productivity python",
            "zero subscription dev tools",
        ],
    },
}


def _pack_tags_within_limit(candidates: list[str], max_chars: int = MAX_TAG_CHARS) -> list[str]:
    """Deduplicate and pack YouTube API tags strictly within the 500-char total limit."""
    seen: set[str] = set()
    packed: list[str] = []
    total_len = 0
    for raw in candidates:
        tag = " ".join(raw.replace("#", "").strip().split())
        if not tag or len(tag) < 2 or len(tag) > 60:
            continue
        key = tag.lower()
        if key in seen:
            continue
        # YouTube counts comma + quotes overhead for multi-word tags
        projected = total_len + len(tag) + (3 if " " in tag else 1)
        if projected > max_chars:
            break
        seen.add(key)
        packed.append(tag)
        total_len = projected
    return packed


def build_outstanding_seo(
    *,
    niche_id: str,
    cta_url: str,
    bundle_url: str,
    storefront_url: str,
    fallback_title: str = "",
) -> dict[str, Any]:
    """Build a complete, high-reach YouTube Shorts SEO package."""
    prof = SEO_PROFILES.get(niche_id)
    if prof is None:
        prof = {
            "title": (fallback_title or f"STOP Paying Monthly SaaS — {niche_id} Local Python Tool #Shorts")[:95],
            "primary_keyword": "zero subscription python automation tool",
            "competitor_alts": ["no subscription SaaS alternative", "local python productivity tool"],
            "semantic_summary": (
                "Replace overpriced monthly SaaS subscriptions with a 100% local, zero-dependency Python 3 script "
                "and dark-mode HTML dashboard. Pay once, own the source code forever."
            ),
            "chapters": [
                ("0:00", "The monthly SaaS subscription trap"),
                ("0:12", "1-file local Python replacement"),
                ("0:28", "$9 one-time vs recurring SaaS"),
            ],
            "hashtags": ["#Shorts", "#Python", "#Automation", "#IndieHackers", "#SoloBuilder"],
            "extra_tags": ["python automation", "indie hacker tools", "solo developer", "no subscription software"],
        }

    chapters_block = "\n".join(f"{ts} {label}" for ts, label in prof["chapters"])
    hashtags_line = " ".join(prof["hashtags"][:5])

    description = (
        f"Get this local tool ($9 once, $0/month forever): {cta_url}\n"
        f"SAVE 58% — All 5 Solo-Builder Tools ($19 Bundle): {bundle_url}\n"
        f"Full Storefront & Open-Source Agent House: {storefront_url}\n\n"
        f"{prof['semantic_summary']}\n\n"
        f"Chapters:\n{chapters_block}\n\n"
        "Why solo builders switch:\n"
        "- 100% Python 3 standard library (zero pip installs)\n"
        "- Runs completely offline on macOS, Windows, and Linux\n"
        "- Built-in --self-test verification + full source code\n\n"
        f"{hashtags_line}"
    )

    pinned_comment = (
        f"Grab this tool ($9 once, $0/mo forever): {cta_url}\n"
        f"Or get ALL 5 zero-subscription local Python tools for $19 (save 58%): {bundle_url}\n"
        "Which monthly subscription do you want replaced with a 1-file local tool next? Drop it below!"
    )

    tags = _pack_tags_within_limit(
        [
            "Shorts",
            prof["primary_keyword"],
            *prof["competitor_alts"],
            *prof["extra_tags"],
            "Python",
            "Automation",
        ]
    )

    seo_pack = {
        "title": prof["title"],
        "description": description,
        "pinned_comment": pinned_comment,
        "tags": tags,
        "hashtags": prof["hashtags"][:5],
        "category_id": YOUTUBE_CATEGORY_SCIENCE_TECH,
        "default_language": "en",
        "default_audio_language": "en",
        "made_for_kids": False,
        "primary_keyword": prof["primary_keyword"],
    }
    seo_pack["seo_audit"] = score_youtube_seo(seo_pack)
    return seo_pack


def score_youtube_seo(seo: dict[str, Any]) -> dict[str, Any]:
    """Score a YouTube Shorts SEO package out of 100 across 6 reach-critical checks."""
    title = seo.get("title", "")
    desc = seo.get("description", "")
    tags = seo.get("tags", [])
    hashtags = seo.get("hashtags", [])

    total_tag_chars = sum(len(t) + (3 if " " in t else 1) for t in tags)
    checks = [
        {
            "name": "high_ctr_mobile_title",
            "pass": 25 <= len(title) <= 85 and "#Shorts" in title,
            "evidence": f"len={len(title)}, has_Shorts={'#Shorts' in title}",
        },
        {
            "name": "above_the_fold_cta_link",
            "pass": "https://" in "\n".join(desc.splitlines()[:3]),
            "evidence": "live URL present in top 3 lines",
        },
        {
            "name": "semantic_description_and_chapters",
            "pass": len(desc) >= 350 and "0:00" in desc,
            "evidence": f"desc_len={len(desc)}, has_chapters={'0:00' in desc}",
        },
        {
            "name": "focused_hashtag_count_3_to_5",
            "pass": 3 <= len(hashtags) <= 5,
            "evidence": f"hashtags={len(hashtags)}",
        },
        {
            "name": "rich_tags_within_500_char_api_limit",
            "pass": len(tags) >= 8 and total_tag_chars <= 500,
            "evidence": f"tag_count={len(tags)}, api_chars={total_tag_chars}/500",
        },
        {
            "name": "engagement_pinned_comment_ready",
            "pass": "https://" in seo.get("pinned_comment", "") and "?" in seo.get("pinned_comment", ""),
            "evidence": "CTA link + engagement question present",
        },
    ]
    passed = sum(1 for c in checks if c["pass"])
    score = int(round((passed / len(checks)) * 100))
    return {"score": score, "pass": all(c["pass"] for c in checks), "checks": checks}
