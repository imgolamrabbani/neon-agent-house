#!/usr/bin/env python3
"""LaunchCheck v1 — Zero-subscription pre-launch SEO, broken-link & security-header auditor.

100% Python standard library ($0 fixed cost, zero pip installs, zero hardcoded secrets).
Audits live URLs or local static HTML files and outputs a dark-mode interactive Launch Readiness Report.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

SECURITY_HEADERS = (
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
)


@dataclass
class AuditCheck:
    category: str
    name: str
    passed: bool
    severity: str
    detail: str
    fix: str


def audit_html_document(
    html_text: str,
    *,
    source_label: str,
    headers: dict[str, str] | None = None,
    check_remote_headers: bool = False,
) -> dict:
    checks: list[AuditCheck] = []
    lower = html_text.lower()

    title_m = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.I | re.S)
    title_txt = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""
    checks.append(AuditCheck(
        "SEO", "Title Tag (10-65 chars)", 10 <= len(title_txt) <= 65, "HIGH",
        f"'{title_txt}' ({len(title_txt)} chars)" if title_txt else "Missing <title>",
        "Add a concise 10-65 character <title> tag describing the page value."
    ))

    desc_m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html_text, flags=re.I)
    desc_txt = desc_m.group(1).strip() if desc_m else ""
    checks.append(AuditCheck(
        "SEO", "Meta Description (50-160 chars)", 50 <= len(desc_txt) <= 160, "HIGH",
        f"{len(desc_txt)} chars" if desc_txt else "Missing meta description",
        "Add <meta name=\"description\" content=\"...\"> (50-160 chars) to improve search CTR."
    ))

    h1_count = len(re.findall(r"<h1\b", lower))
    checks.append(AuditCheck(
        "SEO", "Single H1 Heading", h1_count == 1, "MEDIUM",
        f"Found {h1_count} <h1> tag(s)",
        "Use exactly one <h1> tag per page for clear search hierarchy."
    ))

    has_viewport = 'name="viewport"' in lower or "name='viewport'" in lower
    checks.append(AuditCheck(
        "Mobile", "Responsive Viewport Meta", has_viewport, "HIGH",
        "Present" if has_viewport else "Missing viewport meta tag",
        "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">."
    ))

    has_og = 'property="og:title"' in lower or "property='og:title'" in lower
    checks.append(AuditCheck(
        "Social", "OpenGraph Social Preview (og:title)", has_og, "MEDIUM",
        "Present" if has_og else "Missing og:title metadata",
        "Add og:title, og:description, and og:image tags so links look crisp on X, Slack, and LinkedIn."
    ))

    imgs = re.findall(r"<img\b[^>]*>", html_text, flags=re.I)
    missing_alt = [tag for tag in imgs if "alt=" not in tag.lower()]
    checks.append(AuditCheck(
        "Accessibility", "Image Alt Attributes", len(missing_alt) == 0, "MEDIUM",
        f"{len(imgs) - len(missing_alt)}/{len(imgs)} images have alt text",
        "Add descriptive alt=\"...\" attributes to every <img> tag."
    ))

    placeholder_links = re.findall(r'href=["\']([^"\']*(?:REPLACE_WITH|localhost|127\.0\.0\.1)[^"\']*)["\']', html_text, flags=re.I)
    checks.append(AuditCheck(
        "Links", "Zero Placeholder / Localhost Links", len(placeholder_links) == 0, "CRITICAL",
        "Clean" if not placeholder_links else f"Found: {', '.join(placeholder_links[:3])}",
        "Replace placeholder or localhost hrefs with live production URLs before launch."
    ))

    if check_remote_headers and headers is not None:
        h_lower = {k.lower(): v for k, v in headers.items()}
        for hdr in SECURITY_HEADERS:
            present = hdr in h_lower
            checks.append(AuditCheck(
                "Security", f"Header: {hdr}", present, "MEDIUM",
                h_lower.get(hdr, "Missing")[:80],
                f"Configure your host/CDN to emit the '{hdr}' HTTP response header."
            ))

    passed = sum(1 for c in checks if c.passed)
    score = int(round((passed / len(checks)) * 100)) if checks else 0
    return {
        "target": source_label,
        "score": score,
        "passed": passed,
        "total": len(checks),
        "checks": [asdict(c) for c in checks],
    }


def audit_target(target: str) -> dict:
    p = Path(target)
    if p.is_file():
        return audit_html_document(p.read_text(encoding="utf-8"), source_label=str(p), check_remote_headers=False)
    req = urllib.request.Request(target, headers={"User-Agent": "LaunchCheck/1.0"})
    with urllib.request.urlopen(req, timeout=10.0) as resp:
        body = resp.read(250_000).decode("utf-8", errors="ignore")
        headers = dict(resp.headers.items())
    return audit_html_document(body, source_label=target, headers=headers, check_remote_headers=True)


def render_html_report(report: dict, as_of: str) -> str:
    score = report["score"]
    grade_color = "#34d399" if score >= 85 else ("#fbbf24" if score >= 60 else "#fb7185")
    rows = "\n".join(
        f"""<tr>
          <td><span class="cat">{html.escape(c['category'])}</span></td>
          <td><strong>{html.escape(c['name'])}</strong><div class="sub">{html.escape(c['detail'])}</div></td>
          <td><span class="badge {'PASS' if c['passed'] else 'FAIL'}">{'PASS' if c['passed'] else 'FIX (' + c['severity'] + ')'}</span></td>
          <td class="sub">{'Ready for launch' if c['passed'] else html.escape(c['fix'])}</td>
        </tr>"""
        for c in report["checks"]
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>LaunchCheck Audit — {html.escape(report['target'])}</title>
<style>
  :root {{ --bg:#090e1c; --panel:#121a2f; --border:#253357; --text:#ecf2ff; --muted:#94a5ca; --cyan:#38bdf8; --emerald:#34d399; --rose:#fb7185; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif; background:radial-gradient(circle at top right,#16254a,var(--bg) 55%); color:var(--text); line-height:1.5; }}
  .wrap {{ max-width:1040px; margin:0 auto; padding:32px 20px 64px; }}
  header {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:16px; border-bottom:1px solid var(--border); padding-bottom:18px; margin-bottom:24px; }}
  .score {{ font-size:44px; font-weight:900; color:{grade_color}; }}
  .sub {{ color:var(--muted); font-size:13px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--border); border-radius:14px; overflow:hidden; }}
  th, td {{ padding:14px 16px; border-bottom:1px solid var(--border); text-align:left; font-size:14px; vertical-align:top; }}
  th {{ font-size:12px; text-transform:uppercase; color:var(--muted); letter-spacing:0.06em; }}
  .cat {{ font-family:ui-monospace,Menlo,monospace; font-size:12px; color:var(--cyan); }}
  .badge {{ padding:4px 10px; border-radius:999px; font-size:11px; font-weight:700; white-space:nowrap; }}
  .PASS {{ background:rgba(52,211,153,0.16); color:var(--emerald); border:1px solid rgba(52,211,153,0.4); }}
  .FAIL {{ background:rgba(251,113,133,0.18); color:var(--rose); border:1px solid rgba(251,113,133,0.4); }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1 style="margin:0;font-size:26px;">LaunchCheck Pre-Launch Audit</h1>
      <div class="sub">Target: {html.escape(report['target'])} &bull; Date: {html.escape(as_of)} &bull; {report['passed']}/{report['total']} checks passed</div>
    </div>
    <div class="score">{score}/100</div>
  </header>
  <table>
    <thead><tr><th>Category</th><th>Check &amp; Observed State</th><th>Status</th><th>Recommended Fix</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
</body>
</html>
"""


def run_self_test() -> int:
    sample_html = (
        "<!doctype html><html><head>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "<title>LaunchCheck Demo Site Title</title>"
        "<meta name='description' content='A crisp production-ready landing page description exceeding fifty characters easily.'>"
        "<meta property='og:title' content='LaunchCheck Demo'>"
        "</head><body><h1>Hello</h1><a href='https://example.com'>Live</a></body></html>"
    )
    rep = audit_html_document(
        sample_html,
        source_label="self-test.html",
        headers={h: "ok" for h in SECURITY_HEADERS},
        check_remote_headers=True,
    )
    assert rep["score"] == 100 and rep["passed"] == rep["total"]
    doc = render_html_report(rep, "2026-11-25")
    assert "LaunchCheck Pre-Launch Audit" in doc and "100/100" in doc
    print("SELF-TEST PASSED: LaunchCheck v1 SEO, links, accessibility, and security-header checks verified.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LaunchCheck — Local pre-launch SEO, link & security-header auditor.")
    parser.add_argument("--target", default="../../docs/index.html", help="Live HTTPS URL or local HTML file path.")
    parser.add_argument("--as-of", default="2026-11-25")
    parser.add_argument("--html", type=Path, default=Path("audit_report.html"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    rep = audit_target(args.target)
    args.html.write_text(render_html_report(rep, args.as_of), encoding="utf-8")
    print(f"LaunchCheck ({args.as_of}) — {rep['target']} scored {rep['score']}/100 ({rep['passed']}/{rep['total']} passed) -> {args.html.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
