# Neon Agent House — Shared Hall Room

> **Write Authority:** Exclusively `hall-room-verifier` | **Last Updated:** 2026-11-24T21:04:43Z

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

## scope-shield-01 — ScopeShield — Zero-Subscription Freelance Change-Order & Scope-Creep Generator
- **Status:** `READY_FOR_MONETIZATION` | **Research Score:** 100/100 | **MVP Score:** 100
- **Buyer Persona:** Fixed-price freelance developers, designers, and boutique agencies
- **Recurring Pain:** Losing 20%-40% of project margin to casual client 'quick tweak' DMs because drafting formal change orders feels confrontational and proposal suites cost $39-$65/user/mo.
- **Recommended Offer:** $9 one-time Starter Fast-Win | **Fixed Stack Cost:** $0/mo
- **Unit Economics:** Conservative: 12 buyers/mo = $97.2/mo net | Base: 40 buyers/mo = $324.0/mo net
- **Top Risk:** Standing out among freelance contract templates requires leading with instant dollar-impact HTML/PDF change orders.
- **Verified Primary Evidence:**
  - "One pro habit you need is dealing with change orders and part of that has to do with whether you have an easier or more difficult client to please. For example, a difficult client will ask for 'tweak' but if you're a pro, you don't bite." — https://news.ycombinator.com/item?id=48830015 (Hacker News, 2026-07-08)
  - "On the flip side I've seen many projects go way over budget when a client is actively involved and introduces scope creep that turns into launch blockers." — https://news.ycombinator.com/item?id=46490660 (Hacker News, 2026-01-04)
  - "This is so true, scope creep is real when the client actively gets involved And when that happens it's better to move the contract to hourly rather having it fixed price" — https://news.ycombinator.com/item?id=46491586 (Hacker News, 2026-01-04)
- **Verified Competitors:**
  - **Proposify**: Build $49/mo ($39/user/mo annual), Grow $65/user/mo annual (https://www.proposify.com/pricing) — Gap: Heavy enterprise proposal SaaS priced per seat.
  - **Qwilr**: Starter $49/mo ($35/user/mo annual), Growth $55/user/mo (5-user min) (https://www.qwilr.com/pricing/) — Gap: High recurring cost and 5-seat minimums on growth plans.
  - **HelloBonsai**: Essentials $25/user/mo, Premium $39/user/mo (https://www.hellobonsai.com/pricing) — Gap: Recurring monthly suite lock-in for simple change-order pricing.
- **Verified MVP Artifact:**
  - Spec: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/scope-shield-01/build_spec.md`
  - Runnable Artifact: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/scope-shield-01/scope_shield.py`
  - Test Command: `{python} scope_shield.py --self-test && {python} scope_shield.py --sow sample_sow.json --changes sample_changes.csv --html change_order.html` (exit=0)

## launch-check-01 — LaunchCheck — Zero-Subscription Pre-Launch SEO, Link & Security-Header Auditor
- **Status:** `READY_FOR_MONETIZATION` | **Research Score:** 100/100 | **MVP Score:** 100
- **Buyer Persona:** Indie hackers, solo SaaS founders, and small web agencies shipping landing pages
- **Recurring Pain:** Shipping day-one launch bugs (broken links, missing OG/SEO tags, missing security headers) because enterprise SEO audit suites cost $49-$249/month.
- **Recommended Offer:** $9 one-time Starter Fast-Win | **Fixed Stack Cost:** $0/mo
- **Unit Economics:** Conservative: 15 buyers/mo = $121.5/mo net | Base: 55 buyers/mo = $445.5/mo net
- **Top Risk:** Competing with free browser extensions requires emphasizing single-command CI/local HTML audit reports.
- **Verified Primary Evidence:**
  - "I built Shipcheck after seeing too many launches where small technical issues caused real problems on day one — broken links, slow pages, misconfigured SSL, missing security headers, DNS/email setup mistakes, etc." — https://news.ycombinator.com/item?id=47229745 (Hacker News, 2026-03-03)
  - "I've been building CheckSitePulse, a website auditing tool that crawls sites and reports issues like broken links, spelling mistakes, accessibility problems, SEO issues, missing security headers, and content policy violations." — https://news.ycombinator.com/item?id=49242309 (Hacker News, 2026-08-10)
  - "The main difference is it bundles a bunch of launch checks in one place like SEO metadata, sitemap/robots, security headers" — https://news.ycombinator.com/item?id=47242949 (Hacker News, 2026-03-04)
- **Verified Competitors:**
  - **Ahrefs**: Starter $29/mo, Lite $129/mo, Standard $249/mo (https://ahrefs.com/pricing) — Gap: Expensive monthly subscription overkill for quick pre-launch site checks.
  - **Semrush**: Pro $139-$199/mo, Guru $249.95-$299/mo (https://www.semrush.com/pricing/) — Gap: High monthly enterprise pricing for indie founders launching micro-sites.
  - **Moz Pro**: Starter $49/mo, Standard $99/mo ($79/mo annual) (https://moz.com/products/pro/pricing) — Gap: Recurring monthly cost with cloud-only crawls.
- **Verified MVP Artifact:**
  - Spec: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/launch-check-01/build_spec.md`
  - Runnable Artifact: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/launch-check-01/launch_check.py`
  - Test Command: `{python} launch_check.py --self-test && {python} launch_check.py --target ../../docs/index.html --html audit_report.html` (exit=0)
