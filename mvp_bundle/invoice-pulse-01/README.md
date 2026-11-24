# InvoicePulse v3 — Zero-Subscription Overdue Invoice Command Center

Stop paying **$25–$59/month** for bloated freelance CRM suites (or **4%–6.9%** invoicing fee markups) just to spot overdue invoices and send polite follow-up emails.

**InvoicePulse** runs 100% locally on your own computer using built-in Python 3 (zero `pip install`, zero cloud lock-in, zero recurring fees).

## Quickstart (3 Steps — Under 60 Seconds)

1. **Edit `sample_invoices.csv`** (or copy it to `my_invoices.csv`) with your client invoices and Stripe/PayPal payment links.
2. **Run the auditor & generate your interactive dashboard:**
   ```bash
   python3 invoice_pulse.py --csv sample_invoices.csv --sender "Alex Rivera" --html dashboard.html --report overdue_report.md
   ```
3. **Open `dashboard.html` in any browser:**
   - See your exact **Total Cash at Risk** and **Accrued Late Fees** instantly.
   - Click **Open Email Draft** (`mailto:`) or **Copy Follow-Up Text** to send tone-calibrated Day-3, Day-7, Day-14 (late fee), or Day-30 escalation emails in 2 seconds.
   - Click **Mark Paid** to track cleared invoices locally in your browser.

## Verify Your Install Anytime
```bash
python3 invoice_pulse.py --self-test
```
