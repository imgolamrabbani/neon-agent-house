# ChangelogKit — Zero-Subscription Local Git to HTML Release Notes Generator

Turn your local Git commit history into a searchable dark-mode public Release Notes page + `CHANGELOG.md` in 2 seconds—without paying $49–$99/month for Beamer or Canny.

## Quickstart (3 Steps)
1. Point ChangelogKit at any local Git repo:
   ```bash
   python3 changelog_kit.py --repo /path/to/your/repo --name "MyProduct" --md CHANGELOG.md --html changelog.html
   ```
2. Drop `changelog.html` onto GitHub Pages, Netlify, or Vercel ($0 hosting).
3. Verify anytime: `python3 changelog_kit.py --self-test`
