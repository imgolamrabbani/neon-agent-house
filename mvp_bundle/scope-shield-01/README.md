# ScopeShield — Zero-Subscription Freelance Change-Order Generator

Turn casual "can we just add one quick thing?" client DMs into a clean, priced Change Order PDF/HTML + polite approval email in 30 seconds—without paying $49–$65/month for Proposify or Qwilr.

## Quickstart (3 Steps)
1. Edit `sample_sow.json` (your baseline budget & hourly rate) and `sample_changes.csv` (new client requests).
2. Run:
   ```bash
   python3 scope_shield.py --sow sample_sow.json --changes sample_changes.csv --html change_order.html
   ```
3. Open `change_order.html` in your browser, click **Print / Save PDF**, and click **Open Approval Email**.

Verify anytime: `python3 scope_shield.py --self-test`
