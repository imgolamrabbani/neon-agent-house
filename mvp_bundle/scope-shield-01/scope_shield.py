#!/usr/bin/env python3
"""ScopeShield v1 — Zero-subscription freelance scope-creep & change-order generator.

100% Python standard library ($0 fixed cost, zero external installs, zero hardcoded secrets).
Turns a baseline SOW + incoming client tweak requests into a priced Change Order HTML dashboard
and 1-click polite client approval email drafts.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import tempfile
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass
class ChangeItem:
    request_id: str
    title: str
    requested_by: str
    channel: str
    baseline_clause: str
    estimated_hours: float
    hourly_rate_usd: float
    cost_impact_usd: float
    schedule_shift_days: int
    severity: str


def classify_severity(hours: float, shift_days: int) -> str:
    if hours >= 10 or shift_days >= 5:
        return "MAJOR_SCOPE_CHANGE"
    if hours >= 4 or shift_days >= 2:
        return "MODERATE_CHANGE_ORDER"
    return "MINOR_ADDON"


def load_changes(sow_path: Path, changes_csv: Path) -> tuple[dict, list[ChangeItem]]:
    sow = json.loads(sow_path.read_text(encoding="utf-8"))
    rate = float(sow.get("hourly_rate_usd", 125.0))
    items: list[ChangeItem] = []
    with changes_csv.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("status", "").strip().lower() == "approved":
                continue
            hrs = float(row["estimated_hours"])
            shift = int(row["schedule_shift_days"])
            items.append(
                ChangeItem(
                    request_id=row["request_id"].strip(),
                    title=row["title"].strip(),
                    requested_by=row["requested_by"].strip(),
                    channel=row["channel"].strip(),
                    baseline_clause=row["baseline_clause"].strip(),
                    estimated_hours=round(hrs, 2),
                    hourly_rate_usd=rate,
                    cost_impact_usd=round(hrs * rate, 2),
                    schedule_shift_days=shift,
                    severity=classify_severity(hrs, shift),
                )
            )
    return sow, items


def build_approval_email(sow: dict, items: list[ChangeItem], as_of: str) -> tuple[str, str, str]:
    total_hrs = round(sum(i.estimated_hours for i in items), 2)
    total_cost = round(sum(i.cost_impact_usd for i in items), 2)
    total_days = sum(i.schedule_shift_days for i in items)
    subject = f"Change Order Approval: {sow['project_name']} (+${total_cost:,.2f} / +{total_days}d)"
    bullet_lines = "\n".join(
        f"- [{i.request_id}] {i.title}: +{i.estimated_hours}h (${i.cost_impact_usd:,.2f}, +{i.schedule_shift_days}d) — outside '{i.baseline_clause}'"
        for i in items
    )
    body = (
        f"Hi {sow['client_contact']},\n\n"
        f"Thanks for the great ideas on {sow['project_name']}. I'd love to include the additions below. "
        f"Because they sit outside our signed baseline scope (${float(sow['baseline_budget_usd']):,.2f}), "
        f"here is the formal Change Order summary ({as_of}):\n\n"
        f"{bullet_lines}\n\n"
        f"Total Additional Scope: +{total_hrs} hours | +${total_cost:,.2f} | +{total_days} business day(s)\n"
        f"Revised Project Total: ${float(sow['baseline_budget_usd']) + total_cost:,.2f}\n\n"
        "Please reply 'APPROVED' to lock these into the sprint—otherwise we'll stay 100% on the original scope & deadline.\n\n"
        f"Best,\n{sow.get('freelancer_name', '[Your Name]')}"
    )
    mailto = (
        f"mailto:{urllib.parse.quote(sow['client_email'])}"
        f"?subject={urllib.parse.quote(subject)}"
        f"&body={urllib.parse.quote(body)}"
    )
    return subject, body, mailto


def render_html(sow: dict, items: list[ChangeItem], as_of: str) -> str:
    baseline = float(sow["baseline_budget_usd"])
    total_hrs = round(sum(i.estimated_hours for i in items), 2)
    total_cost = round(sum(i.cost_impact_usd for i in items), 2)
    total_days = sum(i.schedule_shift_days for i in items)
    revised = baseline + total_cost
    subject, body, mailto = build_approval_email(sow, items, as_of)
    rows_html = "\n".join(
        f"""<tr>
          <td><code>{html.escape(i.request_id)}</code></td>
          <td><strong>{html.escape(i.title)}</strong><div class="sub">Via {html.escape(i.channel)} ({html.escape(i.requested_by)}) &bull; Outside: {html.escape(i.baseline_clause)}</div></td>
          <td><span class="badge {i.severity}">{i.severity.replace('_', ' ')}</span></td>
          <td>+{i.estimated_hours:g}h</td>
          <td>+{i.schedule_shift_days}d</td>
          <td class="cost">+${i.cost_impact_usd:,.2f}</td>
        </tr>"""
        for i in items
    )
    full_email = f"To: {sow['client_email']}\nSubject: {subject}\n\n{body}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>ScopeShield Change Order — {html.escape(sow['project_name'])}</title>
<style>
  :root {{ --bg:#0a0f1e; --panel:#131b31; --border:#263459; --text:#edf2ff; --muted:#95a6cb; --cyan:#38bdf8; --amber:#fbbf24; --rose:#fb7185; --emerald:#34d399; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif; background:radial-gradient(circle at top left,#18274c,var(--bg) 55%); color:var(--text); line-height:1.5; }}
  .wrap {{ max-width:1040px; margin:0 auto; padding:32px 20px 64px; }}
  header {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:14px; border-bottom:1px solid var(--border); padding-bottom:18px; margin-bottom:24px; }}
  h1 {{ margin:0; font-size:26px; }}
  .sub {{ color:var(--muted); font-size:13px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:14px; margin-bottom:24px; }}
  .kpi {{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:18px; }}
  .kpi .lbl {{ font-size:12px; text-transform:uppercase; color:var(--muted); letter-spacing:0.06em; }}
  .kpi .val {{ font-size:26px; font-weight:800; margin-top:6px; }}
  .kpi.add .val {{ color:var(--amber); }}
  .kpi.rev .val {{ color:var(--emerald); }}
  .kpi.hrs .val {{ color:var(--cyan); }}
  table {{ width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--border); border-radius:14px; overflow:hidden; margin-bottom:24px; }}
  th, td {{ padding:14px 16px; border-bottom:1px solid var(--border); text-align:left; font-size:14px; vertical-align:top; }}
  th {{ font-size:12px; text-transform:uppercase; color:var(--muted); letter-spacing:0.06em; }}
  .cost {{ font-weight:700; color:var(--emerald); white-space:nowrap; }}
  .badge {{ padding:4px 10px; border-radius:999px; font-size:11px; font-weight:700; white-space:nowrap; }}
  .MAJOR_SCOPE_CHANGE {{ background:rgba(251,113,133,0.18); color:var(--rose); border:1px solid rgba(251,113,133,0.4); }}
  .MODERATE_CHANGE_ORDER {{ background:rgba(251,191,36,0.16); color:var(--amber); border:1px solid rgba(251,191,36,0.4); }}
  .MINOR_ADDON {{ background:rgba(56,189,248,0.16); color:var(--cyan); border:1px solid rgba(56,189,248,0.4); }}
  .panel {{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:20px; }}
  .actions {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:14px; }}
  .btn {{ display:inline-flex; align-items:center; padding:10px 16px; border-radius:10px; font-weight:700; font-size:13px; text-decoration:none; cursor:pointer; border:1px solid var(--border); background:#1c2745; color:var(--text); }}
  .btn.primary {{ background:var(--cyan); color:#051120; border-color:var(--cyan); }}
  pre {{ white-space:pre-wrap; background:#0b1121; border:1px solid var(--border); border-radius:10px; padding:14px; font-size:12.5px; color:#cbd5e1; margin:0; }}
  @media print {{ .actions {{ display:none; }} body {{ background:#fff; color:#111; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>ScopeShield Change Order &mdash; {html.escape(sow['project_name'])}</h1>
      <div class="sub">Client: {html.escape(sow['client_company'])} ({html.escape(sow['client_contact'])}) &bull; Issued {html.escape(as_of)} &bull; Rate: ${float(sow['hourly_rate_usd']):,.2f}/hr</div>
    </div>
    <button class="btn" onclick="window.print()">Print / Save PDF</button>
  </header>

  <section class="kpis">
    <div class="kpi"><div class="lbl">Signed Baseline SOW</div><div class="val">${baseline:,.2f}</div></div>
    <div class="kpi add"><div class="lbl">Unbilled Creep Captured</div><div class="val">+${total_cost:,.2f}</div></div>
    <div class="kpi rev"><div class="lbl">Revised Project Total</div><div class="val">${revised:,.2f}</div></div>
    <div class="kpi hrs"><div class="lbl">Extra Effort / Delay</div><div class="val">+{total_hrs:g}h / +{total_days}d</div></div>
  </section>

  <table>
    <thead><tr><th>ID</th><th>Out-of-Scope Request</th><th>Severity</th><th>Hours</th><th>Shift</th><th>Price Impact</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>

  <section class="panel">
    <div class="actions">
      <a class="btn primary" href="{mailto}">Open Approval Email (mailto:)</a>
      <button class="btn" onclick="navigator.clipboard && navigator.clipboard.writeText(document.getElementById('emailDraft').textContent)">Copy Approval Email</button>
    </div>
    <pre id="emailDraft">{html.escape(full_email)}</pre>
  </section>
</div>
</body>
</html>
"""


def run_self_test() -> int:
    assert classify_severity(12, 6) == "MAJOR_SCOPE_CHANGE"
    assert classify_severity(5, 2) == "MODERATE_CHANGE_ORDER"
    assert classify_severity(2, 1) == "MINOR_ADDON"
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        sow_p = d / "sow.json"
        csv_p = d / "changes.csv"
        sow_p.write_text(json.dumps({
            "project_name": "Acme Redesign",
            "client_company": "Acme Corp",
            "client_contact": "Jordan",
            "client_email": "jordan@acme.example",
            "freelancer_name": "Alex",
            "baseline_budget_usd": 5000,
            "hourly_rate_usd": 125,
        }), encoding="utf-8")
        csv_p.write_text(
            "request_id,title,requested_by,channel,baseline_clause,estimated_hours,schedule_shift_days,status\n"
            "CR-1,Multi-language i18n,Jordan,Slack,English-only MVP,12,5,pending\n",
            encoding="utf-8",
        )
        sow, items = load_changes(sow_p, csv_p)
        assert len(items) == 1 and items[0].cost_impact_usd == 1500.0
        doc = render_html(sow, items, "2026-11-25")
        assert "ScopeShield Change Order" in doc and "$1,500.00" in doc
    print("SELF-TEST PASSED: ScopeShield v1 scope-impact math, HTML Change Order, and approval email verified.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ScopeShield — Local freelance change-order & scope-creep calculator.")
    parser.add_argument("--sow", type=Path, default=Path("sample_sow.json"))
    parser.add_argument("--changes", type=Path, default=Path("sample_changes.csv"))
    parser.add_argument("--as-of", default="2026-11-25")
    parser.add_argument("--html", type=Path, default=Path("change_order.html"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    sow, items = load_changes(args.sow, args.changes)
    total_cost = round(sum(i.cost_impact_usd for i in items), 2)
    args.html.write_text(render_html(sow, items, args.as_of), encoding="utf-8")
    print(f"ScopeShield ({args.as_of}) — {len(items)} out-of-scope item(s) totaling +${total_cost:,.2f} -> {args.html.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
