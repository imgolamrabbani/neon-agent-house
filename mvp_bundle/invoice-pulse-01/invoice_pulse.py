#!/usr/bin/env python3
"""InvoicePulse v3 — Zero-subscription local invoice audit, escalation drafter & interactive HTML dashboard.

100% Python standard library ($0 fixed cost, zero external installs, zero hardcoded secrets, local-first privacy).
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
class InvoiceAudit:
    invoice_id: str
    client_name: str
    client_email: str
    amount_usd: float
    due_date: str
    days_overdue: int
    stage: str
    late_fee_usd: float
    total_due_usd: float
    payment_url: str
    email_subject: str
    email_body: str
    mailto_href: str


def classify_stage(days_overdue: int) -> str:
    if days_overdue <= 0:
        return "CURRENT"
    if days_overdue <= 6:
        return "DAY_3_NUDGE"
    if days_overdue <= 13:
        return "DAY_7_FOLLOWUP"
    if days_overdue <= 29:
        return "DAY_14_LATE_FEE"
    return "DAY_30_ESCALATION"


def build_email_parts(
    *,
    invoice_id: str,
    client_name: str,
    amount_usd: float,
    due_date: str,
    days_overdue: int,
    stage: str,
    late_fee_usd: float,
    total_due_usd: float,
    payment_url: str,
    sender_name: str = "[Your Name]",
) -> tuple[str, str]:
    if stage == "CURRENT":
        return (
            f"Invoice #{invoice_id} upcoming reminder (${amount_usd:,.2f})",
            f"Hi {client_name},\n\nFriendly reminder that Invoice #{invoice_id} for ${amount_usd:,.2f} is due on {due_date}.\nPayment link: {payment_url}\n\nThanks,\n{sender_name}",
        )
    if stage == "DAY_3_NUDGE":
        subject = f"Quick check-in: Invoice #{invoice_id} (${amount_usd:,.2f})"
        body = (
            f"Hi {client_name},\n\n"
            f"Hope your week is going well. Quick heads-up that Invoice #{invoice_id} "
            f"for ${amount_usd:,.2f} (due {due_date}) is now {days_overdue} day(s) past due.\n"
            f"If it was already scheduled with AP, feel free to ignore—otherwise you can settle it directly here: {payment_url}\n\n"
            f"Thanks,\n{sender_name}"
        )
    elif stage == "DAY_7_FOLLOWUP":
        subject = f"Follow-up: Invoice #{invoice_id} — {days_overdue} days overdue"
        body = (
            f"Hi {client_name},\n\n"
            f"Following up on Invoice #{invoice_id} (${amount_usd:,.2f}, due {due_date}), "
            f"which is now {days_overdue} days overdue.\n"
            f"Could you confirm the expected payment date with accounts payable? Payment link: {payment_url}\n\n"
            f"Best,\n{sender_name}"
        )
    elif stage == "DAY_14_LATE_FEE":
        subject = f"Action needed: Overdue Invoice #{invoice_id} (${total_due_usd:,.2f})"
        body = (
            f"Hi {client_name},\n\n"
            f"Invoice #{invoice_id} (due {due_date}) is now {days_overdue} days past due. "
            f"Per our agreement, a prorated late fee of ${late_fee_usd:,.2f} applies, bringing the total due to ${total_due_usd:,.2f}.\n"
            f"Please process payment within 3 business days to keep project deliverables on schedule: {payment_url}\n\n"
            f"Regards,\n{sender_name}"
        )
    else:
        subject = f"URGENT: 30+ Days Overdue — Invoice #{invoice_id} (${total_due_usd:,.2f})"
        body = (
            f"Hi {client_name},\n\n"
            f"Invoice #{invoice_id} (due {due_date}) is now {days_overdue} days overdue "
            f"(original ${amount_usd:,.2f} + late fee ${late_fee_usd:,.2f} = ${total_due_usd:,.2f}).\n"
            f"Work and handoffs are paused until payment clears via {payment_url}. "
            f"Please reply today with payment confirmation.\n\n"
            f"Regards,\n{sender_name}"
        )
    return subject, body


def audit_invoices(
    csv_path: Path,
    *,
    as_of: date,
    monthly_late_rate: float = 0.015,
    sender_name: str = "[Your Name]",
    outbox_dir: Path | None = None,
) -> list[InvoiceAudit]:
    results: list[InvoiceAudit] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("status", "").strip().lower() == "paid":
                continue
            due = date.fromisoformat(row["due_date"].strip())
            days_overdue = (as_of - due).days
            stage = classify_stage(days_overdue)
            amount = round(float(row["amount_usd"]), 2)
            late_fee = (
                round(amount * monthly_late_rate * (days_overdue / 30.0), 2)
                if days_overdue >= 14
                else 0.0
            )
            total_due = round(amount + late_fee, 2)
            client_email = row["client_email"].strip()
            payment_url = row.get("payment_url", "https://example.com/pay").strip()
            subject, body = build_email_parts(
                invoice_id=row["invoice_id"].strip(),
                client_name=row["client_name"].strip(),
                amount_usd=amount,
                due_date=due.isoformat(),
                days_overdue=days_overdue,
                stage=stage,
                late_fee_usd=late_fee,
                total_due_usd=total_due,
                payment_url=payment_url,
                sender_name=sender_name,
            )
            mailto_href = (
                f"mailto:{urllib.parse.quote(client_email)}"
                f"?subject={urllib.parse.quote(subject)}"
                f"&body={urllib.parse.quote(body)}"
            )
            audit = InvoiceAudit(
                invoice_id=row["invoice_id"].strip(),
                client_name=row["client_name"].strip(),
                client_email=client_email,
                amount_usd=amount,
                due_date=due.isoformat(),
                days_overdue=days_overdue,
                stage=stage,
                late_fee_usd=late_fee,
                total_due_usd=total_due,
                payment_url=payment_url,
                email_subject=subject,
                email_body=body,
                mailto_href=mailto_href,
            )
            results.append(audit)
            if outbox_dir is not None and days_overdue > 0:
                outbox_dir.mkdir(parents=True, exist_ok=True)
                draft_file = outbox_dir / f"{audit.invoice_id}_{audit.stage.lower()}.txt"
                draft_file.write_text(
                    f"To: {audit.client_email}\nSubject: {audit.email_subject}\n\n{audit.email_body}\n",
                    encoding="utf-8",
                )
    results.sort(key=lambda a: a.days_overdue, reverse=True)
    return results


def render_markdown_report(audits: list[InvoiceAudit], as_of: str) -> str:
    overdue = [a for a in audits if a.days_overdue > 0]
    total_principal = sum(a.amount_usd for a in overdue)
    total_fees = sum(a.late_fee_usd for a in overdue)
    total_due = sum(a.total_due_usd for a in overdue)
    lines = [
        f"# InvoicePulse Overdue Ledger ({as_of})",
        "",
        f"- **Overdue Invoices:** {len(overdue)}",
        f"- **Principal Overdue:** ${total_principal:,.2f}",
        f"- **Accrued Late Fees:** ${total_fees:,.2f}",
        f"- **Total Cash at Risk:** **${total_due:,.2f}**",
        "",
        "| Invoice | Client | Due Date | Days Overdue | Stage | Principal | Late Fee | Total Due |",
        "| :--- | :--- | :--- | :---: | :--- | ---: | ---: | ---: |",
    ]
    for a in audits:
        lines.append(
            f"| `{a.invoice_id}` | {a.client_name} | {a.due_date} | {max(a.days_overdue, 0)}d | `{a.stage}` | "
            f"${a.amount_usd:,.2f} | ${a.late_fee_usd:,.2f} | **${a.total_due_usd:,.2f}** |"
        )
    return "\n".join(lines) + "\n"


def render_html_dashboard(audits: list[InvoiceAudit], as_of: str) -> str:
    overdue = [a for a in audits if a.days_overdue > 0]
    total_due = round(sum(a.total_due_usd for a in overdue), 2)
    total_fees = round(sum(a.late_fee_usd for a in overdue), 2)
    critical_count = sum(1 for a in overdue if a.days_overdue >= 30)
    data_json = json.dumps([asdict(a) for a in audits]).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>InvoicePulse — Local Cashflow & Follow-Up Dashboard ({html.escape(as_of)})</title>
<style>
  :root {{
    --bg: #0b1020;
    --panel: #131a2e;
    --panel-2: #1a233d;
    --border: #273355;
    --text: #e6ecf8;
    --muted: #93a3c7;
    --cyan: #38bdf8;
    --emerald: #34d399;
    --amber: #fbbf24;
    --rose: #fb7185;
    --violet: #a78bfa;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    background: radial-gradient(circle at top right, #162244 0%, var(--bg) 55%);
    color: var(--text);
    line-height: 1.5;
  }}
  .wrap {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px 64px; }}
  header {{
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
    gap: 16px; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 18px;
  }}
  .brand h1 {{ margin: 0; font-size: 26px; letter-spacing: -0.02em; }}
  .brand p {{ margin: 4px 0 0; color: var(--muted); font-size: 14px; }}
  .pill {{
    background: rgba(52, 211, 153, 0.14); color: var(--emerald);
    border: 1px solid rgba(52, 211, 153, 0.35); padding: 6px 12px;
    border-radius: 999px; font-size: 12px; font-weight: 600;
  }}
  .kpis {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 14px; margin-bottom: 24px;
  }}
  .kpi {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 18px;
  }}
  .kpi .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }}
  .kpi .value {{ font-size: 28px; font-weight: 700; margin-top: 6px; }}
  .kpi.risk .value {{ color: var(--rose); }}
  .kpi.fees .value {{ color: var(--amber); }}
  .kpi.count .value {{ color: var(--cyan); }}
  .kpi.crit .value {{ color: var(--violet); }}
  .controls {{
    display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 18px;
  }}
  .search {{
    flex: 1; min-width: 220px; background: var(--panel); border: 1px solid var(--border);
    color: var(--text); padding: 10px 14px; border-radius: 10px; font-size: 14px;
  }}
  .filter-btn {{
    background: var(--panel); color: var(--muted); border: 1px solid var(--border);
    padding: 8px 14px; border-radius: 10px; cursor: pointer; font-size: 13px; font-weight: 600;
  }}
  .filter-btn.active {{ background: var(--cyan); color: #061325; border-color: var(--cyan); }}
  .cards {{ display: flex; flex-direction: column; gap: 14px; }}
  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 18px 20px;
    transition: opacity 0.2s ease, border-color 0.2s ease;
  }}
  .card.paid {{ opacity: 0.45; border-style: dashed; }}
  .card-top {{
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;
  }}
  .meta {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }}
  .inv-id {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 700; color: var(--cyan); }}
  .client {{ font-size: 17px; font-weight: 700; }}
  .email {{ color: var(--muted); font-size: 13px; }}
  .badge {{
    padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: 0.04em;
  }}
  .DAY_30_ESCALATION {{ background: rgba(251, 113, 133, 0.18); color: var(--rose); border: 1px solid rgba(251, 113, 133, 0.4); }}
  .DAY_14_LATE_FEE {{ background: rgba(251, 191, 36, 0.16); color: var(--amber); border: 1px solid rgba(251, 191, 36, 0.4); }}
  .DAY_7_FOLLOWUP {{ background: rgba(167, 139, 250, 0.16); color: var(--violet); border: 1px solid rgba(167, 139, 250, 0.4); }}
  .DAY_3_NUDGE {{ background: rgba(56, 189, 248, 0.16); color: var(--cyan); border: 1px solid rgba(56, 189, 248, 0.4); }}
  .CURRENT {{ background: rgba(52, 211, 153, 0.16); color: var(--emerald); border: 1px solid rgba(52, 211, 153, 0.4); }}
  .amounts {{ text-align: right; }}
  .total {{ font-size: 22px; font-weight: 700; }}
  .sub {{ font-size: 12px; color: var(--muted); }}
  .actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
  .btn {{
    display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; border-radius: 9px;
    font-size: 13px; font-weight: 600; text-decoration: none; cursor: pointer;
    border: 1px solid var(--border); background: var(--panel-2); color: var(--text);
  }}
  .btn.primary {{ background: var(--cyan); color: #061325; border-color: var(--cyan); }}
  .btn.success {{ background: rgba(52, 211, 153, 0.15); color: var(--emerald); border-color: rgba(52, 211, 153, 0.4); }}
  details {{ margin-top: 12px; background: #0d1324; border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; }}
  summary {{ cursor: pointer; font-size: 13px; color: var(--muted); font-weight: 600; }}
  pre {{ white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12.5px; color: #cbd5e1; margin: 10px 0 0; }}
  .toast {{
    position: fixed; bottom: 20px; right: 20px; background: var(--emerald); color: #062118;
    padding: 10px 16px; border-radius: 10px; font-weight: 700; font-size: 13px; display: none;
  }}
  footer {{ margin-top: 32px; text-align: center; color: var(--muted); font-size: 12px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <h1>InvoicePulse — Overdue Cashflow Command</h1>
      <p>Audit Date: {html.escape(as_of)} &bull; 100% Local &amp; Private &bull; $0/mo Subscription</p>
    </div>
    <div class="pill">Zero SaaS Fees &bull; Stdlib Only</div>
  </header>

  <section class="kpis">
    <div class="kpi risk"><div class="label">Total Cash At Risk</div><div class="value" id="kpiRisk">${total_due:,.2f}</div></div>
    <div class="kpi fees"><div class="label">Accrued Late Fees</div><div class="value" id="kpiFees">${total_fees:,.2f}</div></div>
    <div class="kpi count"><div class="label">Overdue Invoices</div><div class="value" id="kpiCount">{len(overdue)}</div></div>
    <div class="kpi crit"><div class="label">30+ Day Escalations</div><div class="value" id="kpiCrit">{critical_count}</div></div>
  </section>

  <div class="controls">
    <input class="search" id="searchBox" type="search" placeholder="Filter by client, invoice ID, or email..." />
    <button class="filter-btn active" data-stage="ALL">All Unpaid</button>
    <button class="filter-btn" data-stage="OVERDUE">Overdue Only</button>
    <button class="filter-btn" data-stage="DAY_30_ESCALATION">30d+ Urgent</button>
    <button class="filter-btn" data-stage="DAY_14_LATE_FEE">14d+ Late Fee</button>
    <button class="filter-btn" data-stage="DAY_3_NUDGE">Day 3 Nudge</button>
  </div>

  <div class="cards" id="cards"></div>
  <footer>Generated locally by InvoicePulse v3 &mdash; your invoice CSV never leaves your computer.</footer>
</div>
<div class="toast" id="toast">Copied email draft to clipboard!</div>

<script>
const ITEMS = {data_json};
const PAID_KEY = "invoicepulse_paid_ids_v3";
let activeStage = "ALL";
let paidSet = new Set(JSON.parse(localStorage.getItem(PAID_KEY) || "[]"));

function showToast(msg) {{
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.style.display = "block";
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => {{ t.style.display = "none"; }}, 2200);
}}

function money(n) {{
  return "$" + Number(n).toLocaleString("en-US", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
}}

function togglePaid(id) {{
  if (paidSet.has(id)) paidSet.delete(id); else paidSet.add(id);
  localStorage.setItem(PAID_KEY, JSON.stringify([...paidSet]));
  render();
}}

function copyDraft(id) {{
  const item = ITEMS.find(x => x.invoice_id === id);
  if (!item) return;
  const full = `To: ${{item.client_email}}\\nSubject: ${{item.email_subject}}\\n\\n${{item.email_body}}`;
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(full).then(() => showToast("Copied draft for #" + id));
  }} else {{
    showToast("Draft ready in preview for #" + id);
  }}
}}

function render() {{
  const q = document.getElementById("searchBox").value.trim().toLowerCase();
  const activeOverdue = ITEMS.filter(x => x.days_overdue > 0 && !paidSet.has(x.invoice_id));
  document.getElementById("kpiRisk").textContent = money(activeOverdue.reduce((s, x) => s + x.total_due_usd, 0));
  document.getElementById("kpiFees").textContent = money(activeOverdue.reduce((s, x) => s + x.late_fee_usd, 0));
  document.getElementById("kpiCount").textContent = String(activeOverdue.length);
  document.getElementById("kpiCrit").textContent = String(activeOverdue.filter(x => x.days_overdue >= 30).length);

  const filtered = ITEMS.filter(x => {{
    if (activeStage === "OVERDUE" && x.days_overdue <= 0) return false;
    if (activeStage !== "ALL" && activeStage !== "OVERDUE" && x.stage !== activeStage) return false;
    if (!q) return true;
    return `${{x.invoice_id}} ${{x.client_name}} ${{x.client_email}} ${{x.stage}}`.toLowerCase().includes(q);
  }});

  const root = document.getElementById("cards");
  root.innerHTML = filtered.map(item => {{
    const isPaid = paidSet.has(item.invoice_id);
    const overdueTxt = item.days_overdue > 0 ? `${{item.days_overdue}} days overdue` : `Due in ${{Math.abs(item.days_overdue)}} days`;
    return `
      <article class="card ${{isPaid ? "paid" : ""}}">
        <div class="card-top">
          <div>
            <div class="meta">
              <span class="inv-id">#${{item.invoice_id}}</span>
              <span class="client">${{item.client_name}}</span>
              <span class="badge ${{item.stage}}">${{item.stage.replaceAll("_", " ")}}</span>
            </div>
            <div class="email">${{item.client_email}} &bull; Due ${{item.due_date}} &bull; ${{overdueTxt}}</div>
          </div>
          <div class="amounts">
            <div class="total">${{money(item.total_due_usd)}}</div>
            <div class="sub">Principal ${{money(item.amount_usd)}} + Late Fee ${{money(item.late_fee_usd)}}</div>
          </div>
        </div>
        <div class="actions">
          <a class="btn primary" href="${{item.mailto_href}}">Open Email Draft</a>
          <button class="btn" onclick="copyDraft('${{item.invoice_id}}')">Copy Follow-Up Text</button>
          <a class="btn" href="${{item.payment_url}}" target="_blank" rel="noopener">Payment Link</a>
          <button class="btn success" onclick="togglePaid('${{item.invoice_id}}')">${{isPaid ? "Undo Paid" : "Mark Paid"}}</button>
        </div>
        <details>
          <summary>Preview Follow-Up Email (${{item.email_subject}})</summary>
          <pre>To: ${{item.client_email}}
Subject: ${{item.email_subject}}

${{item.email_body}}</pre>
        </details>
      </article>
    `;
  }}).join("");
}}

document.getElementById("searchBox").addEventListener("input", render);
document.querySelectorAll(".filter-btn").forEach(btn => {{
  btn.addEventListener("click", () => {{
    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeStage = btn.dataset.stage;
    render();
  }});
}});
render();
</script>
</body>
</html>
"""


def run_self_test() -> int:
    """Built-in verification suite ensuring zero broken logic before delivery."""
    assert classify_stage(-2) == "CURRENT"
    assert classify_stage(4) == "DAY_3_NUDGE"
    assert classify_stage(10) == "DAY_7_FOLLOWUP"
    assert classify_stage(17) == "DAY_14_LATE_FEE"
    assert classify_stage(36) == "DAY_30_ESCALATION"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        csv_file = tmp_dir / "test.csv"
        csv_file.write_text(
            "invoice_id,client_name,client_email,amount_usd,due_date,status,payment_url\n"
            "T-1,Acme,ap@acme.example,2000,2026-10-20,unpaid,https://pay.example.com/t1\n"
            "T-2,PaidCo,ap@paid.example,500,2026-10-01,paid,https://pay.example.com/t2\n",
            encoding="utf-8",
        )
        audits = audit_invoices(csv_file, as_of=date(2026, 11, 25), outbox_dir=tmp_dir / "out")
        assert len(audits) == 1
        assert audits[0].stage == "DAY_30_ESCALATION"
        assert audits[0].late_fee_usd == 36.0
        assert audits[0].total_due_usd == 2036.0
        assert (tmp_dir / "out" / "T-1_day_30_escalation.txt").is_file()
        html_doc = render_html_dashboard(audits, "2026-11-25")
        assert "InvoicePulse" in html_doc and "mailto:" in html_doc
    print("SELF-TEST PASSED: InvoicePulse v3 core logic, late fees, drafts, and HTML dashboard verified.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="InvoicePulse v3 — Local overdue invoice auditor, email drafter & HTML dashboard."
    )
    parser.add_argument("--csv", type=Path, default=Path("sample_invoices.csv"))
    parser.add_argument("--as-of", default=date.today().isoformat(), help="Audit date (YYYY-MM-DD).")
    parser.add_argument("--sender", default="[Your Name]", help="Your name for email signatures.")
    parser.add_argument("--late-rate", type=float, default=0.015, help="Monthly late fee rate (default 0.015 = 1.5%%).")
    parser.add_argument("--outbox", type=Path, default=Path("outbox"))
    parser.add_argument("--html", type=Path, default=None, help="Output path for standalone interactive HTML dashboard.")
    parser.add_argument("--report", type=Path, default=None, help="Output path for Markdown summary report.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--self-test", action="store_true", help="Run built-in verification tests and exit.")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    audits = audit_invoices(
        args.csv,
        as_of=date.fromisoformat(args.as_of),
        monthly_late_rate=args.late_rate,
        sender_name=args.sender,
        outbox_dir=args.outbox,
    )
    overdue = [a for a in audits if a.days_overdue > 0]
    total_overdue = round(sum(a.total_due_usd for a in overdue), 2)

    if args.html is not None:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html_dashboard(audits, args.as_of), encoding="utf-8")

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_markdown_report(audits, args.as_of), encoding="utf-8")

    if args.as_json:
        print(
            json.dumps(
                {
                    "as_of": args.as_of,
                    "overdue_count": len(overdue),
                    "total_overdue_usd": total_overdue,
                    "items": [asdict(a) for a in audits],
                },
                indent=2,
            )
        )
    else:
        print(
            f"InvoicePulse v3 Audit ({args.as_of}) — {len(overdue)} overdue invoice(s) totaling ${total_overdue:,.2f}"
        )
        for a in overdue:
            print(
                f"  - #{a.invoice_id} | {a.client_name} | {a.days_overdue}d overdue | {a.stage} | total=${a.total_due_usd:,.2f}"
            )
        if args.html is not None:
            print(f"Interactive dashboard written to: {args.html.resolve()}")
        if args.report is not None:
            print(f"Markdown report written to: {args.report.resolve()}")
        print(f"Follow-up drafts written to: {args.outbox.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
