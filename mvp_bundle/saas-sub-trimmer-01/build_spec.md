# Build Spec — SubTrim v1 (`saas-sub-trimmer-01`)

## 1. Verified Buyer Problem
Developers and solo founders hate handing over their bank username/password/MFA to Plaid-connected budgeting subscriptions (YNAB $14.99/mo, Monarch Money $14.99/mo, Tiller $79–$99/yr) just to spot forgotten recurring SaaS charges and silent price hikes on a card statement.

## 2. Architecture (100% Free Stack — $0/mo Fixed Cost)
- **Runtime:** Python 3.10+ stdlib only (`csv`, `re`, `html`, `json`, `datetime`, `argparse`). Zero Plaid, zero bank logins, zero cloud sync.
- **Outputs:** Interactive dark-mode HTML Savings Dashboard (`sub_audit.html`) flagging recurring subscriptions, price hikes (`PRICE_HIKE`), duplicate charges, and interactive Mark-to-Cancel Annual Savings calculator.
- **Pricing:** `$9` one-time Starter Fast-Win.
