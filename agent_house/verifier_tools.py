"""Deterministic adversarial verification primitives for Hall Room Verifier (v2+).

Independently validates:
- Live HTTP 200 reachability AND quote-keyword grounding inside fetched pages
- Live competitor pricing URL reachability AND pricing signals on page
- $0 fixed stack cost and exact unit-economics arithmetic
- MVP spec, zero TODO stubs, zero hardcoded secrets, live CLI execution, and optional self-test/HTML UI checks
"""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from agent_house.config import MIN_PASS_SCORE
from agent_house.discovery_tools import fetch_url_text

SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z\-_]{30,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(api_key|secret_key|password)\s*=\s*['\"][^'\"]{8,}['\"]"),
]

FLUFF_TERMS = (
    "dropshipping",
    "get rich quick",
    "make money while you sleep",
    "passive income hack",
)

STOPWORDS = {
    "about", "after", "again", "being", "could", "every", "first", "found",
    "from", "have", "just", "more", "other", "over", "some", "that", "their",
    "them", "then", "there", "these", "they", "this", "what", "when", "where",
    "which", "while", "with", "would", "your",
}


def _quote_grounded_in_page(quote: str, page_text: str) -> tuple[bool, float]:
    """Verify substantive keywords from quote actually appear on the fetched page."""
    tokens = [
        tok
        for tok in re.findall(r"[a-z0-9]{4,}", quote.lower())
        if tok not in STOPWORDS
    ]
    unique_tokens = list(dict.fromkeys(tokens))
    if not unique_tokens:
        return False, 0.0
    page_lower = page_text.lower()
    hits = sum(1 for tok in unique_tokens if tok in page_lower)
    ratio = hits / len(unique_tokens)
    return ratio >= 0.45, round(ratio, 2)


def check_url_live(url: str, timeout: float = 8.0) -> tuple[bool, str]:
    """Return (is_live, detail) via HTTP GET check."""
    ok, status, detail = fetch_url_text(url, timeout=timeout, max_bytes=16_000)
    return ok, (f"HTTP {status}" if ok else detail)


def verify_pain_report(
    pain_report: dict[str, Any],
    *,
    check_live_urls: bool = True,
) -> dict[str, Any]:
    """Score Pain-Point Scout output against v2 DONE WELL rubric (URL + quote content grounding)."""
    checks: list[dict[str, Any]] = []
    fixes: list[str] = []

    candidates = pain_report.get("candidates", [])
    has_candidates = isinstance(candidates, list) and len(candidates) >= 1
    checks.append(
        {
            "name": "has_candidate_micro_niches",
            "pass": has_candidates,
            "evidence": f"{len(candidates)} candidate(s) provided",
        }
    )
    if not has_candidates:
        fixes.append("Provide at least 1 concrete micro-niche candidate in candidates[].")

    top = candidates[0] if has_candidates else {}
    evidence = top.get("evidence", [])
    has_three_quotes = isinstance(evidence, list) and len(evidence) >= 3
    checks.append(
        {
            "name": "min_three_primary_quotes",
            "pass": has_three_quotes,
            "evidence": f"{len(evidence)} primary-source quote(s) on top candidate",
        }
    )
    if not has_three_quotes:
        fixes.append("Include at least 3 verbatim primary-source buyer quotes with live URLs.")

    url_failures: list[str] = []
    grounding_failures: list[str] = []
    verified_urls = 0
    grounded_quotes = 0
    for idx, item in enumerate(evidence):
        quote = (item.get("verbatim_quote") or "").strip()
        url = (item.get("source_url") or "").strip()
        if len(quote) < 20:
            url_failures.append(f"quote[{idx}] too short or empty")
            continue
        if check_live_urls:
            ok, status, page_text = fetch_url_text(url)
            if ok:
                verified_urls += 1
                grounded, ratio = _quote_grounded_in_page(quote, page_text)
                if grounded:
                    grounded_quotes += 1
                else:
                    grounding_failures.append(f"{url} (keyword_match={ratio})")
            else:
                url_failures.append(f"{url} (HTTP {status} / {page_text})")
        else:
            if url.startswith("https://"):
                verified_urls += 1
                grounded_quotes += 1
            else:
                url_failures.append(f"invalid url: {url}")

    urls_pass = has_three_quotes and not url_failures and verified_urls >= 3
    checks.append(
        {
            "name": "all_primary_urls_verified",
            "pass": urls_pass,
            "evidence": (
                f"{verified_urls}/{len(evidence)} URLs verified live"
                if not url_failures
                else f"Failed URLs: {', '.join(url_failures)}"
            ),
        }
    )
    if not urls_pass:
        fixes.append(
            f"Replace unverified/unreachable URLs: {'; '.join(url_failures) or 'need >=3 live URLs'}."
        )

    grounding_pass = urls_pass and not grounding_failures and grounded_quotes >= 3
    checks.append(
        {
            "name": "quotes_grounded_in_live_pages",
            "pass": grounding_pass,
            "evidence": (
                f"{grounded_quotes}/{len(evidence)} quotes verified against live page content"
                if not grounding_failures
                else f"Unmatched quote content: {', '.join(grounding_failures)}"
            ),
        }
    )
    if not grounding_pass and urls_pass:
        fixes.append(
            f"Quote text did not match fetched page content: {'; '.join(grounding_failures)}. Use exact verbatim quotes."
        )

    persona_ok = bool((top.get("buyer_persona") or "").strip()) and bool(
        (top.get("recurring_pain") or "").strip()
    )
    checks.append(
        {
            "name": "concrete_persona_and_workflow",
            "pass": persona_ok,
            "evidence": f"persona='{top.get('buyer_persona', '')[:60]}'",
        }
    )
    if not persona_ok:
        fixes.append("Specify a concrete buyer_persona and recurring_pain workflow.")

    blob = str(pain_report).lower()
    fluff_hits = [term for term in FLUFF_TERMS if term in blob]
    no_fluff = not fluff_hits
    checks.append(
        {
            "name": "zero_vague_mmo_fluff",
            "pass": no_fluff,
            "evidence": "clean" if no_fluff else f"flagged terms: {fluff_hits}",
        }
    )
    if not no_fluff:
        fixes.append(f"Remove generic/fluff angles: {', '.join(fluff_hits)}.")

    passed_count = sum(1 for c in checks if c["pass"])
    score = int(round((passed_count / len(checks)) * 100))
    mandatory_pass = all(c["pass"] for c in checks) and score >= MIN_PASS_SCORE
    return {
        "agent": "pain_point_scout",
        "score": score,
        "pass": mandatory_pass,
        "checks": checks,
        "exact_fixes": fixes,
    }


def verify_economics_report(
    economics_report: dict[str, Any],
    *,
    check_live_urls: bool = True,
) -> dict[str, Any]:
    """Score Market & ROI Analyst output against v2 DONE WELL rubric."""
    checks: list[dict[str, Any]] = []
    fixes: list[str] = []

    competitors = economics_report.get("competitors", [])
    comp_count_ok = isinstance(competitors, list) and len(competitors) >= 3
    url_failures: list[str] = []
    price_failures: list[str] = []
    for comp in competitors:
        url = (comp.get("live_pricing_url") or "").strip()
        tiers = (comp.get("verified_price_tiers") or "").strip()
        if "$" not in tiers:
            price_failures.append(f"{comp.get('name', 'unknown')} missing USD price")
        if check_live_urls:
            ok, status, page_text = fetch_url_text(url)
            if not ok:
                url_failures.append(f"{url} (HTTP {status})")
            elif not any(tok in page_text.lower() for tok in ("$", "pricing", "plan", "month", "year")):
                price_failures.append(f"{url} missing pricing signals on page")
        elif not url.startswith("https://"):
            url_failures.append(f"invalid url: {url}")

    comps_ok = comp_count_ok and not url_failures and not price_failures
    checks.append(
        {
            "name": "min_three_verified_competitors",
            "pass": comps_ok,
            "evidence": (
                f"{len(competitors)} competitors with verified live pricing pages and USD tiers"
                if comps_ok
                else f"count={len(competitors)}, url_errs={url_failures}, price_errs={price_failures}"
            ),
        }
    )
    if not comps_ok:
        fixes.append(
            f"Provide >=3 real competitors with live HTTPS pricing URLs and exact USD tiers (issues: {url_failures + price_failures})."
        )

    fixed_cost = economics_report.get("fixed_monthly_cost_usd")
    zero_cost_ok = fixed_cost == 0 or fixed_cost == 0.0
    checks.append(
        {
            "name": "zero_dollar_fixed_stack_cost",
            "pass": zero_cost_ok,
            "evidence": f"fixed_monthly_cost_usd={fixed_cost!r}",
        }
    )
    if not zero_cost_ok:
        fixes.append("Eliminate paid SaaS/API dependencies so fixed_monthly_cost_usd is 0.")

    ue = economics_report.get("unit_economics", {})
    price = ue.get("price_usd", 0)
    fee_rate = ue.get("platform_fee_rate", 0.10)
    cons_buyers = ue.get("conservative_monthly_buyers", 0)
    base_buyers = ue.get("base_monthly_buyers", 0)
    expected_cons = round(price * (1 - fee_rate) * cons_buyers, 2)
    expected_base = round(price * (1 - fee_rate) * base_buyers, 2)
    reported_cons = ue.get("conservative_monthly_net_usd")
    reported_base = ue.get("base_monthly_net_usd")
    math_ok = (
        price > 0
        and cons_buyers > 0
        and base_buyers >= cons_buyers
        and reported_cons is not None
        and reported_base is not None
        and abs(float(reported_cons) - expected_cons) <= 0.5
        and abs(float(reported_base) - expected_base) <= 0.5
    )
    checks.append(
        {
            "name": "verified_unit_economics_arithmetic",
            "pass": math_ok,
            "evidence": (
                f"conservative=${reported_cons} (expected ${expected_cons}), base=${reported_base} (expected ${expected_base})"
            ),
        }
    )
    if not math_ok:
        fixes.append(
            f"Fix unit_economics arithmetic: price*(1-fee_rate)*buyers should equal conservative={expected_cons}, base={expected_base}."
        )

    risk_ok = len((economics_report.get("top_distribution_risk") or "").strip()) >= 15
    checks.append(
        {
            "name": "honest_distribution_risk",
            "pass": risk_ok,
            "evidence": (economics_report.get("top_distribution_risk") or "")[:80],
        }
    )
    if not risk_ok:
        fixes.append("State the #1 concrete customer-acquisition or distribution risk.")

    passed_count = sum(1 for c in checks if c["pass"])
    score = int(round((passed_count / len(checks)) * 100))
    mandatory_pass = all(c["pass"] for c in checks) and score >= MIN_PASS_SCORE
    return {
        "agent": "market_roi_analyst",
        "score": score,
        "pass": mandatory_pass,
        "checks": checks,
        "exact_fixes": fixes,
    }


def verify_mvp_bundle(
    mvp_bundle: dict[str, Any],
    *,
    execute_test: bool = True,
) -> dict[str, Any]:
    """Score MVP Builder artifact: spec, zero stubs, zero secrets, execution & optional UI/ZIP checks."""
    checks: list[dict[str, Any]] = []
    fixes: list[str] = []

    spec_path = Path(mvp_bundle.get("spec_path", ""))
    artifact_path = Path(mvp_bundle.get("artifact_path", ""))

    spec_ok = spec_path.is_file() and spec_path.stat().st_size > 200
    checks.append(
        {
            "name": "build_spec_present",
            "pass": spec_ok,
            "evidence": f"{spec_path} ({spec_path.stat().st_size if spec_path.is_file() else 0} bytes)",
        }
    )
    if not spec_ok:
        fixes.append("Write a complete build_spec.md (>200 bytes) covering architecture, $0 stack, and weekend polish steps.")

    artifact_ok = artifact_path.is_file() and artifact_path.stat().st_size > 200
    artifact_text = artifact_path.read_text(encoding="utf-8") if artifact_ok else ""
    no_stubs = artifact_ok and ("TODO" not in artifact_text and "NotImplementedError" not in artifact_text)
    checks.append(
        {
            "name": "runnable_artifact_no_stubs",
            "pass": no_stubs,
            "evidence": f"{artifact_path} ({len(artifact_text)} chars, stubs={'no' if no_stubs else 'yes'})",
        }
    )
    if not no_stubs:
        fixes.append("Ship a complete runnable MVP artifact with zero TODO stubs or NotImplementedError placeholders.")

    secret_hits = [pat.pattern for pat in SECRET_PATTERNS if pat.search(artifact_text)]
    secrets_ok = artifact_ok and not secret_hits
    checks.append(
        {
            "name": "zero_hardcoded_secrets",
            "pass": secrets_ok,
            "evidence": "clean" if secrets_ok else f"matched patterns: {secret_hits}",
        }
    )
    if not secrets_ok:
        fixes.append("Remove any hardcoded secrets/API keys; read credentials exclusively from environment variables.")

    test_cmd = mvp_bundle.get("test_command", "")
    test_ok = False
    test_evidence = "not executed"
    if execute_test and artifact_ok and test_cmd:
        cmd = test_cmd.replace("{python}", shlex.quote(sys.executable))
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(artifact_path.parent),
            capture_output=True,
            text=True,
            timeout=20,
        )
        test_ok = proc.returncode == 0 and len(proc.stdout.strip()) > 0
        test_evidence = f"exit={proc.returncode}, stdout_preview={proc.stdout.strip()[:140]!r}"
        if proc.returncode != 0:
            test_evidence += f", stderr={proc.stderr.strip()[:120]!r}"
    elif not execute_test:
        test_ok = mvp_bundle.get("test_exit_code") == 0
        test_evidence = f"declared exit_code={mvp_bundle.get('test_exit_code')}"

    checks.append(
        {
            "name": "live_execution_test_passed",
            "pass": test_ok,
            "evidence": test_evidence,
        }
    )
    if not test_ok:
        fixes.append(f"Fix MVP runtime error so test_command succeeds cleanly ({test_evidence}).")

    # Optional v3 buyer-readiness checks when declared in bundle
    dashboard_path_str = mvp_bundle.get("dashboard_path")
    if dashboard_path_str:
        dp = Path(dashboard_path_str)
        dash_ok = dp.is_file() and dp.stat().st_size > 1500 and "<html" in dp.read_text(encoding="utf-8").lower()
        checks.append(
            {
                "name": "interactive_html_dashboard_generated",
                "pass": dash_ok,
                "evidence": f"{dp} ({dp.stat().st_size if dp.is_file() else 0} bytes)",
            }
        )
        if not dash_ok:
            fixes.append("Generate a complete standalone HTML dashboard (>1500 bytes).")

    zip_path_str = mvp_bundle.get("zip_path")
    if zip_path_str:
        zp = Path(zip_path_str)
        zip_ok = zp.is_file() and zp.stat().st_size > 1000
        checks.append(
            {
                "name": "sellable_zip_package_ready",
                "pass": zip_ok,
                "evidence": f"{zp} ({zp.stat().st_size if zp.is_file() else 0} bytes)",
            }
        )
        if not zip_ok:
            fixes.append("Build the buyer-ready ZIP package before submitting.")

    passed_count = sum(1 for c in checks if c["pass"])
    score = int(round((passed_count / len(checks)) * 100))
    mandatory_pass = all(c["pass"] for c in checks) and score >= MIN_PASS_SCORE
    return {
        "agent": "mvp_builder",
        "score": score,
        "pass": mandatory_pass,
        "checks": checks,
        "exact_fixes": fixes,
    }
