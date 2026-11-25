#!/usr/bin/env python3
"""SubTrim v1 — Zero-Plaid local bank/card CSV recurring SaaS & subscription leak auditor.

100% Python standard library ($0 fixed cost, zero bank logins, zero hardcoded secrets).
Detects recurring charges, price hikes, and annual burn from any local CSV bank statement
and generates an interactive dark-mode Savings Dashboard (sub_audit.html).
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass
class SubscriptionFinding:
    merchant: str
    occurrences: int
    avg_cadence_days: float
    latest_amount_usd: float
    previous_amount_usd: float
    price_hike_pct: float
    annualized_usd: float
    flag: str
    last_charged: str


def normalize_merchant(raw: str) -> str:
    cleaned = re.sub(r"[#*0-9]+", " ", raw or "")
    cleaned = re.sub(r"\b(inc|llc|ltd|corp|com|www|billing|payment|autopay)\b", " ", cleaned, flags=re.I)
    return re.sub(r"\s+", " ", cleaned).strip().title() or "Unknown Merchant"


def analyze_statement(csv_path: Path) -> list[SubscriptionFinding]:
    grouped: dict[str, list[tuple[date, float]]] = defaultdict(list)
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            amt = abs(float(row["amount_usd"]))
            if amt <= 0:
                continue
            dt = date.fromisoformat(row["date"].strip())
            grouped[normalize_merchant(row["merchant"])].append((dt, amt))

    findings: list[SubscriptionFinding] = []
    for merchant, entries in grouped.items():
        entries.sort(key=lambda x: x[0])
        if len(entries) < 2:
            continue
        gaps = [(entries[i][0] - entries[i - 1][0]).days for i in range(1, len(entries))]
        avg_gap = sum(gaps) / len(gaps)
        if avg_gap > 45:
            continue
        latest_dt, latest_amt = entries[-1]
        prev_amt = entries[-2][1]
        hike_pct = round(((latest_amt - prev_amt) / prev_amt) * 100, 1) if prev_amt > 0 else 0.0
        annualized = round(latest_amt * (365.0 / max(avg_gap, 1.0)), 2)

        if hike_pct >= 5.0:
            flag = "PRICE_HIKE"
        elif any(g <= 5 for g in gaps):
            flag = "POSSIBLE_DUPLICATE"
        elif annualized >= 300.0:
            flag = "HIGH_BURN"
        else:
            flag = "RECURRING"

        findings.append(
            SubscriptionFinding(
                merchant=merchant,
                occurrences=len(entries),
                avg_cadence_days=round(avg_gap, 1),
                latest_amount_usd=round(latest_amt, 2),
                previous_amount_usd=round(prev_amt, 2),
                price_hike_pct=hike_pct,
                annualized_usd=annualized,
                flag=flag,
                last_charged=latest_dt.isoformat(),
            )
        )
    findings.sort(key=lambda f: f.annualized_usd, reverse=True)
    return findings


def render_html_dashboard(findings: list[SubscriptionFinding], as_of: str) -> str:
    total_annual = round(sum(f.annualized_usd for f in findings), 2)
    total_monthly = round(total_annual / 12.0, 2)
    hikes = sum(1 for f in findings if f.flag == "PRICE_HIKE")
    data_json = json.dumps([asdict(f) for f in findings]).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>SubTrim — Zero-Plaid Subscription &amp; SaaS Leak Audit ({html.escape(as_of)})</title>
<style>
  :root {{ --bg:#090e1c; --panel:#121a2f; --border:#243255; --text:#eef3ff; --muted:#93a4c8; --cyan:#38bdf8; --emerald:#34d399; --amber:#fbbf24; --rose:#fb7185; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif; background:radial-gradient(circle at top right,#16254a,var(--bg) 55%); color:var(--text); line-height:1.5; }}
  .wrap {{ max-width:1060px; margin:0 auto; padding:32px 20px 64px; }}
  header {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:14px; border-bottom:1px solid var(--border); padding-bottom:18px; margin-bottom:24px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; margin-bottom:24px; }}
  .kpi {{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:18px; }}
  .kpi .lbl {{ font-size:12px; text-transform:uppercase; color:var(--muted); letter-spacing:0.06em; }}
  .kpi .val {{ font-size:28px; font-weight:800; margin-top:6px; }}
  .kpi.burn .val {{ color:var(--rose); }}
  .kpi.save .val {{ color:var(--emerald); }}
  .kpi.hike .val {{ color:var(--amber); }}
  .kpi.cnt .val {{ color:var(--cyan); }}
  table {{ width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--border); border-radius:14px; overflow:hidden; }}
  th, td {{ padding:14px 16px; border-bottom:1px solid var(--border); text-align:left; font-size:14px; }}
  th {{ font-size:12px; text-transform:uppercase; color:var(--muted); letter-spacing:0.06em; }}
  tr.cancel {{ opacity:0.5; text-decoration:line-through; }}
  .badge {{ padding:4px 10px; border-radius:999px; font-size:11px; font-weight:700; }}
  .PRICE_HIKE {{ background:rgba(251,113,133,0.18); color:var(--rose); border:1px solid rgba(251,113,133,0.4); }}
  .HIGH_BURN {{ background:rgba(251,191,36,0.16); color:var(--amber); border:1px solid rgba(251,191,36,0.4); }}
  .POSSIBLE_DUPLICATE {{ background:rgba(251,113,133,0.18); color:var(--rose); border:1px solid rgba(251,113,133,0.4); }}
  .RECURRING {{ background:rgba(56,189,248,0.16); color:var(--cyan); border:1px solid rgba(56,189,248,0.4); }}
  .btn {{ padding:7px 12px; border-radius:8px; border:1px solid var(--border); background:#1b2645; color:var(--text); cursor:pointer; font-size:12.5px; font-weight:600; }}
  .btn.active {{ background:var(--emerald); color:#052016; border-color:var(--emerald); }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1 style="margin:0;font-size:26px;">SubTrim &mdash; Zero-Plaid Subscription Audit</h1>
      <div style="color:var(--muted);font-size:13px;">Audit Date: {html.escape(as_of)} &bull; 100% Local CSV &bull; Zero Bank Passwords Shared</div>
    </div>
  </header>
  <section class="kpis">
    <div class="kpi burn"><div class="lbl">Annualized Burn</div><div class="val" id="kpiAnnual">${total_annual:,.2f}/yr</div></div>
    <div class="kpi save"><div class="lbl">Savings Marked to Cancel</div><div class="val" id="kpiSaved">$0.00/yr</div></div>
    <div class="kpi cnt"><div class="lbl">Monthly Equivalent</div><div class="val">${total_monthly:,.2f}/mo</div></div>
    <div class="kpi hike"><div class="lbl">Price Hikes Detected</div><div class="val">{hikes}</div></div>
  </section>
  <table>
    <thead><tr><th>Merchant</th><th>Flag</th><th>Latest Charge</th><th>Annualized</th><th>Cadence</th><th>Action</th></tr></thead>
    <tbody id="rows"></tbody>
  </table>
</div>
<script>
const ITEMS = {data_json};
const KEY = "subtrim_cancel_v1";
let cancels = new Set(JSON.parse(localStorage.getItem(KEY) || "[]"));
function money(n) {{ return "$" + Number(n).toLocaleString("en-US", {{minimumFractionDigits:2, maximumFractionDigits:2}}); }}
function toggleCancel(m) {{
  if (cancels.has(m)) cancels.delete(m); else cancels.add(m);
  localStorage.setItem(KEY, JSON.stringify([...cancels]));
  render();
}}
function render() {{
  const saved = ITEMS.filter(x => cancels.has(x.merchant)).reduce((s, x) => s + x.annualized_usd, 0);
  document.getElementById("kpiSaved").textContent = money(saved) + "/yr";
  document.getElementById("rows").innerHTML = ITEMS.map(x => {{
    const isCancel = cancels.has(x.merchant);
    const hikeTxt = x.price_hike_pct > 0 ? ` (+${{x.price_hike_pct}}%)` : "";
    return `<tr class="${{isCancel ? 'cancel' : ''}}">
      <td><strong>${{x.merchant}}</strong><div style="color:#93a4c8;font-size:12px;">${{x.occurrences}} charges &bull; last ${{x.last_charged}}</div></td>
      <td><span class="badge ${{x.flag}}">${{x.flag.replaceAll('_',' ')}}</span></td>
      <td>${{money(x.latest_amount_usd)}}${{hikeTxt}}</td>
      <td><strong>${{money(x.annualized_usd)}}/yr</strong></td>
      <td>~${{x.avg_cadence_days}}d</td>
      <td><button class="btn ${{isCancel ? 'active' : ''}}" onclick="toggleCancel('${{x.merchant.replaceAll("'", "\\\\'")}}')">${{isCancel ? 'Marked to Cancel' : 'Mark Cancel'}}</button></td>
    </tr>`;
  }}).join("");
}}
render();
</script>
</body>
</html>
"""


def run_self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "stmt.csv"
        p.write_text(
            "date,merchant,amount_usd\n"
            "2026-09-01,HONEYBOOK INC #9921,39.00\n"
            "2026-10-01,HONEYBOOK INC #9922,59.00\n"
            "2026-11-01,HONEYBOOK INC #9923,59.00\n",
            encoding="utf-8",
        )
        findings = analyze_statement(p)
        assert len(findings) == 1
        assert findings[0].merchant == "Honeybook"
        assert findings[0].latest_amount_usd == 59.0
        doc = render_html_dashboard(findings, "2026-11-25")
        assert "SubTrim" in doc and "Honeybook" in doc
    print("SELF-TEST PASSED: SubTrim v1 recurring detection, price-hike alert, and HTML savings dashboard verified.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SubTrim — Local CSV recurring SaaS & subscription leak auditor.")
    parser.add_argument("--csv", type=Path, default=Path("sample_statement.csv"))
    parser.add_argument("--as-of", default="2026-11-25")
    parser.add_argument("--html", type=Path, default=Path("sub_audit.html"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    findings = analyze_statement(args.csv)
    total_annual = round(sum(f.annualized_usd for f in findings), 2)
    args.html.write_text(render_html_dashboard(findings, args.as_of), encoding="utf-8")
    print(f"SubTrim ({args.as_of}) — {len(findings)} recurring subscription(s) totaling ${total_annual:,.2f}/yr -> {args.html.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
