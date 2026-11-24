# Neon Agent House — Shared Hall Room

> **Write Authority:** Exclusively `hall-room-verifier` | **Last Updated:** 2026-11-24T20:48:39Z

## invoice-pulse-01 — InvoicePulse v3 — Zero-Subscription Overdue Invoice Command Center
- **Status:** `READY_FOR_MONETIZATION` | **Research Score:** 100/100 | **MVP Score:** 100
- **Buyer Persona:** Solo freelance developers, designers, and boutique consultants
- **Recurring Pain:** Losing hours weekly writing awkward unpaid-invoice follow-up emails and watching AP quietly overlook invoices, while resenting $25-$59/mo CRM suites and 4%-6.9% SaaS fee markups.
- **Recommended Offer:** $9 Starter Fast-Win / $29 Pro Lifetime (one-time) | **Fixed Stack Cost:** $0/mo
- **Unit Economics:** Conservative: 15 buyers/mo = $121.5/mo net | Base: 50 buyers/mo = $405.0/mo net
- **Top Risk:** Organic distribution without ad spend relies on authentic Show HN / r/SideProject launch engagement while founder is awake to answer replies.
- **Verified Primary Evidence:**
  - "I kept losing hours every week writing 'just checking in' emails for unpaid invoices — and I knew every other freelancer was doing the same." — https://news.ycombinator.com/item?id=47243082 (Hacker News, 2026-03-04)
  - "The invoicing SaaS I was using to bill my clients raised its credit card processing fee to 6.9% for free accounts (4% on top of Stripe's 2.9% + 30c fee), so I decided to build my own to fit my minimal needs." — https://news.ycombinator.com/item?id=48920389 (Hacker News, 2026-07-15)
  - "I thought I had a good relationship with one client and that invoices were being paid on time, but then I found that around £10k had been overlooked by AP over the course of a few years." — https://news.ycombinator.com/item?id=18129101 (Hacker News, 2018-10-03)
  - "The idea came from repeatedly watching freelancers (and honestly, myself) lose time to admin just to get paid." — https://news.ycombinator.com/item?id=46771990 (Hacker News, 2026-01-26)
- **Verified Competitors:**
  - **HoneyBook**: Starter $36/mo ($29/mo annual), Essentials $59/mo ($49/mo annual), Premium $129/mo (https://www.honeybook.com/pricing) — Gap: High monthly recurring fee and heavy CRM bloat for solo freelancers who only need clean payment follow-ups.
  - **Dubsado**: Starter $35/mo ($335/yr), Premier $55/mo ($525/yr) (https://www.dubsado.com/pricing) — Gap: Requires $55/mo Premier tier for automated workflows and steep initial configuration.
  - **HelloBonsai**: Basic $15/user/mo (no full invoicing), Essentials $25/user/mo, Premium $39/user/mo (https://www.hellobonsai.com/pricing) — Gap: Per-seat recurring billing and basic tier omits full invoicing workflows.
  - **Moxie**: Starter $12/mo ($10/mo annual), Pro $25/mo, Teams $40/mo (https://www.withmoxie.com/pricing) — Gap: Still requires ongoing SaaS subscription and cloud lock-in for client billing data.
- **Verified MVP Artifact:**
  - Spec: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/invoice-pulse-01/build_spec.md`
  - Runnable Artifact: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/invoice-pulse-01/invoice_pulse.py`
  - Test Command: `{python} invoice_pulse.py --self-test && {python} invoice_pulse.py --csv sample_invoices.csv --as-of 2026-11-25 --html dashboard.html --report overdue_report.md --outbox outbox` (exit=0)
