# Non-Spammy Organic Launch Posts — InvoicePulse v3

> **Important:** Post these **only while you are awake** so you can reply authentically to comments (especially on Show HN, where active founder replies drive 90% of traction and prevent spam flags).

---

## 1. Hacker News (`Show HN`)
**Submit URL:** `https://news.ycombinator.com/submit` (use your GitHub Pages / GitHub repo URL, NOT a raw Gumroad checkout link!)

**Title:**
`Show HN: InvoicePulse – Zero-dependency local Python overdue invoice auditor & HTML dashboard`

**First Comment (paste immediately after submitting):**
```text
Hi HN,

I kept seeing solo freelancers complain about paying $35–$59/mo for bloated CRM suites (or getting hit with 4%–6.9% invoicing fee markups) just to track overdue invoices and send polite "just checking in" emails.

So I built InvoicePulse: a single-file, Python stdlib-only local tool (zero pip installs, zero cloud accounts, zero subscriptions).

How it works:
1. Keep your invoices in a plain local CSV with your own Stripe/PayPal payment links.
2. Run `python3 invoice_pulse.py --csv sample_invoices.csv --html dashboard.html`.
3. It calculates days overdue + optional prorated late fees (after day 14), generates 4 tone-calibrated follow-up stages (Day 3, Day 7, Day 14, Day 30), writes `.txt` drafts to `outbox/`, and generates a standalone dark-mode HTML dashboard with 1-click `mailto:` links and localStorage "Mark Paid" state.

Your client/revenue data never leaves your machine.

Happy to hear feedback on edge cases (multi-currency, custom grace periods, or net-15/net-45 terms) you'd want added next!
```

---

## 2. Reddit (`r/SideProject` or `r/freelance` — check weekly promo thread rules first!)
**Title:**
`I built a $0/mo local tool that turns an invoice CSV into an overdue cashflow dashboard + 1-click follow-up drafts (no more $40/mo CRM subscriptions)`

**Body:**
```text
Every time I looked at HoneyBook ($36–$59/mo), Dubsado ($35–$55/mo), or Bonsai ($25+/mo), I realized most solo freelancers only actually use 10% of the suite: knowing which invoices are slipping past AP and sending awkward follow-up emails without sounding rude.

So I built InvoicePulse using pure Python standard library (zero installs, works offline on Mac/Windows/Linux):
- Reads a simple local `invoices.csv`
- Flags Day-3, Day-7, Day-14 (with prorated late-fee math), and Day-30+ overdue invoices
- Builds a clean dark-mode local HTML dashboard with Total Cash at Risk KPIs, 1-click `mailto:` buttons, and Copy Draft buttons

Link to the live demo & toolkit ($9 one-time if you want the packaged bundle, or happy to share the exact email templates right here in the comments): https://adorable48.gumroad.com/l/zcnhpu

Would love honest feedback from fellow solo freelancers: what's the #1 late-invoice headache you still deal with?
```

---

## 3. X / Twitter Thread (3 Short Posts)
**Post 1:**
```text
Solo freelancers are paying $36–$59/mo for bloated CRMs just to do one job:

Spot overdue invoices and send polite follow-up emails.

I built InvoicePulse: a 100% local, zero-dependency tool that turns a plain CSV into an overdue cashflow dashboard + 1-click follow-up drafts.

$9 once. $0/month forever. 🧵👇
```

**Post 2:**
```text
How it works in 60 seconds:
1. Drop unpaid invoices + your own Stripe/PayPal links into a local CSV
2. Run 1 Python command (stdlib only—zero pip installs)
3. Open dashboard.html:
   - Total Cash at Risk + Accrued Late Fees
   - Day 3 / Day 7 / Day 14 / Day 30 escalation emails
   - 1-click mailto: & Copy Draft
```

**Post 3:**
```text
No monthly subscription. No extra 4% fee rake. Your client CSV never leaves your laptop.

Grab the Starter Fast-Win pack ($9 one-time) here: https://adorable48.gumroad.com/l/zcnhpu

Replies open—tell me what billing headache you want automated next.
```
