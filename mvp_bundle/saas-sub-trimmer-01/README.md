# SubTrim — Zero-Plaid Local CSV Subscription & SaaS Leak Auditor

Spot forgotten recurring charges and silent price hikes in 10 seconds—without handing your bank password to Plaid or paying $14.99/month for YNAB or Monarch Money.

## Quickstart (3 Steps)
1. Export any bank/card CSV with columns `date,merchant,amount_usd` (or test with `sample_statement.csv`).
2. Run:
   ```bash
   python3 sub_trim.py --csv sample_statement.csv --html sub_audit.html
   ```
3. Open `sub_audit.html` in your browser and click **Mark Cancel** to tally your instant annual savings.

Verify anytime: `python3 sub_trim.py --self-test`
