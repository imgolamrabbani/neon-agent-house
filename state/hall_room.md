# Neon Agent House — Shared Hall Room

> **Write Authority:** Exclusively `hall-room-verifier` | **Last Updated:** 2026-11-25T10:06:45Z

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

## saas-sub-trimmer-01 — SubTrim — Zero-Plaid Local CSV Subscription & SaaS Leak Auditor
- **Status:** `READY_FOR_MONETIZATION` | **Research Score:** 100/100 | **MVP Score:** 100
- **Buyer Persona:** Privacy-conscious solo founders, developers, and freelancers
- **Recurring Pain:** Refusing to hand over bank usernames/passwords/MFA to Plaid-connected budgeting apps ($14.99/mo YNAB/Monarch) while silently bleeding cash to forgotten recurring SaaS renewals and price hikes.
- **Recommended Offer:** $9 one-time Starter Fast-Win | **Fixed Stack Cost:** $0/mo
- **Unit Economics:** Conservative: 15 buyers/mo = $121.5/mo net | Base: 50 buyers/mo = $405.0/mo net
- **Top Risk:** Bank CSV column headers vary across banks; clear 3-column mapping instructions reduce buyer friction.
- **Verified Primary Evidence:**
  - "Plaid needing you to enter your username, password, and MFA for your bank is like genuine lunacy." — https://news.ycombinator.com/item?id=50526710 (Hacker News, 2026-11-17)
  - "Plaid requires your bank username and password, so they have full read-write access to your account. They can do anything you can do when logged in to the bank's website" — https://news.ycombinator.com/item?id=48152652 (Hacker News, 2026-05-15)
  - "unexpected charges and difficult-to-cancel billing is the game. The best customer is always the one that pays but never uses the service" — https://news.ycombinator.com/item?id=45998546 (Hacker News, 2025-11-20)
- **Verified Competitors:**
  - **YNAB**: $14.99/mo or $109/yr (https://www.ynab.com/pricing) — Gap: Requires recurring subscription and cloud bank syncing.
  - **Monarch Money**: $14.99/mo or $99.99/yr (Plus $199.99/yr) (https://www.monarchmoney.com/pricing) — Gap: No free tier and relies on third-party bank credential aggregators.
  - **Tiller**: $79-$99/yr flat annual subscription (https://www.tillerhq.com/pricing/) — Gap: Requires annual renewal and cloud bank-feed connection.
- **Verified MVP Artifact:**
  - Spec: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/saas-sub-trimmer-01/build_spec.md`
  - Runnable Artifact: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/saas-sub-trimmer-01/sub_trim.py`
  - Test Command: `{python} sub_trim.py --self-test && {python} sub_trim.py --csv sample_statement.csv --html sub_audit.html` (exit=0)

## git-changelog-kit-01 — ChangelogKit — Zero-Subscription Git to HTML Release Notes Generator
- **Status:** `READY_FOR_MONETIZATION` | **Research Score:** 100/100 | **MVP Score:** 100
- **Buyer Persona:** Indie hackers, solo SaaS builders, and open-source maintainers
- **Recurring Pain:** Skipping customer release notes because manual writing is tedious and hosted changelog widgets (Canny $79-$99/mo, Beamer $49-$119/mo) charge recurring subscriptions.
- **Recommended Offer:** $9 one-time Starter Fast-Win | **Fixed Stack Cost:** $0/mo
- **Unit Economics:** Conservative: 12 buyers/mo = $97.2/mo net | Base: 45 buyers/mo = $364.5/mo net
- **Top Risk:** Devs have free CLI tools like git-cliff; positioning focuses on instant zero-config static dark-mode HTML release pages ready for GitHub Pages.
- **Verified Primary Evidence:**
  - "Writing changelogs is tedious and usually skipped. I built changelogai.to: connect your GitHub account, select a repo, and AI generates customer-friendly changelogs directly from your commit history." — https://news.ycombinator.com/item?id=46283350 (Hacker News, 2025-12-16)
  - "Well, to be fair writing documentation is tedious (as are changelogs, and writing code)." — https://news.ycombinator.com/item?id=44569605 (Hacker News, 2025-07-15)
  - "I'm building a changelog system at the moment. It's basically the github_changelog_generator gem, but without overwriting old changelog entries." — https://news.ycombinator.com/item?id=28427023 (Hacker News, 2021-09-05)
- **Verified Competitors:**
  - **Canny**: Pro $79/mo annual ($99/mo monthly), scales to $279-$529/mo (https://canny.io/pricing) — Gap: Expensive per-tracked-user SaaS pricing for solo founders.
  - **Beamer**: Starter $49/mo annual ($59/mo monthly), Pro $99/mo, Scale $249/mo (https://www.getbeamer.com/pricing) — Gap: MAU-metered recurring subscription and paid branding removal.
  - **LaunchNotes**: Entry ~$249/mo+ / Enterprise custom annual contracts (https://www.launchnotes.com/pricing) — Gap: Enterprise product-ops pricing unreachable for indie builders.
- **Verified MVP Artifact:**
  - Spec: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/git-changelog-kit-01/build_spec.md`
  - Runnable Artifact: `/Volumes/MAC EXTRA/Vibe/Neon/mvp_bundle/git-changelog-kit-01/changelog_kit.py`
  - Test Command: `{python} changelog_kit.py --self-test && {python} changelog_kit.py --repo ../.. --name 'Neon Agent House' --md CHANGELOG.md --html changelog.html` (exit=0)

---

# Wing 2 — Verified YouTube Shorts (`yt-video-verifier`)

## yt-short-01 — STOP Paying $59/mo Just to Chase Late Invoices #Shorts
- **Status:** `QA_PASSED_READY_FOR_UPLOAD` | **QA Score:** 100/100 | **Resolution:** 1080x1920 | **Duration:** 40.73s
- **Linked Wing 1 Product:** `invoice-pulse-01` (https://adorable48.gumroad.com/l/zcnhpu)
- **MP4 File:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/yt-short-01/yt-short-01.mp4`
- **Thumbnail:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/yt-short-01/thumbnail.png`
- **YouTube URL:** ready_for_upload

## yt-short-02 — Why Giving Plaid Your Bank Password Is Insane (Local CSV Fix) #Shorts
- **Status:** `QA_PASSED_READY_FOR_UPLOAD` | **QA Score:** 100/100 | **Resolution:** 1080x1920 | **Duration:** 40.3s
- **Linked Wing 1 Product:** `saas-sub-trimmer-01` (https://adorable48.gumroad.com/l/ijrfzn)
- **MP4 File:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/yt-short-02/yt-short-02.mp4`
- **Thumbnail:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/yt-short-02/thumbnail.png`
- **YouTube URL:** ready_for_upload

## ep-01-mariana-pov — POV: Your Submersible Loses Power at 11,000 Meters Deep #Shorts
- **Status:** `PUBLISHED_YOUTUBE` | **QA Score:** 100/100 | **Resolution:** 1080x1920 | **Duration:** 54.07s
- **Linked Wing 1 Product:** `the-deep-chronicle` (https://www.youtube.com/@TheDeepChronicle)
- **MP4 File:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/ep-01-mariana-pov/ep-01-mariana-pov.mp4`
- **Thumbnail:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/ep-01-mariana-pov/thumbnail.png`
- **YouTube URL:** https://youtube.com/shorts/TAup6L0vRgE

## ep-02-apollo11-silence — The 30 Seconds Apollo 11 Almost Crashed on the Moon #Shorts
- **Status:** `SCHEDULED_YOUTUBE` | **QA Score:** 100/100 | **Resolution:** 1080x1920 | **Duration:** 53.63s
- **Linked Wing 1 Product:** `the-deep-chronicle` (https://www.youtube.com/@TheDeepChronicle)
- **MP4 File:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/ep-02-apollo11-silence/ep-02-apollo11-silence.mp4`
- **Thumbnail:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/ep-02-apollo11-silence/thumbnail.png`
- **YouTube URL:** https://youtube.com/shorts/cOAg6vplzzk

## ep-03-voyager-edge — Voyager 1 Is Still Calling Home From 15 Billion Miles Away #Shorts
- **Status:** `SCHEDULED_YOUTUBE` | **QA Score:** 100/100 | **Resolution:** 1080x1920 | **Duration:** 56.27s
- **Linked Wing 1 Product:** `the-deep-chronicle` (https://www.youtube.com/@TheDeepChronicle)
- **MP4 File:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/ep-03-voyager-edge/ep-03-voyager-edge.mp4`
- **Thumbnail:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/ep-03-voyager-edge/thumbnail.png`
- **YouTube URL:** https://youtube.com/shorts/EIkBUDbWLI8

## ep-04-blackhole-pov — What Happens 1 Second After You Fall Into a Black Hole #Shorts
- **Status:** `PUBLISHED_YOUTUBE` | **QA Score:** 100/100 | **Resolution:** 1080x1920 | **Duration:** 50.5s
- **Linked Wing 1 Product:** `the-deep-chronicle` (https://www.youtube.com/@TheDeepChronicle)
- **MP4 File:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/ep-04-blackhole-pov/ep-04-blackhole-pov.mp4`
- **Thumbnail:** `/Volumes/MAC EXTRA/Vibe/Neon/outputs/youtube_shorts/ep-04-blackhole-pov/thumbnail.png`
- **YouTube URL:** https://youtube.com/shorts/tzQoXANXVTw
