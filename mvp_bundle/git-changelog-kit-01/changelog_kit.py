#!/usr/bin/env python3
"""ChangelogKit v1 — Zero-subscription local Git log to HTML & Markdown release notes generator.

100% Python standard library ($0 fixed cost, zero pip installs, zero hardcoded secrets).
Turns any local git repository commit history into a categorized CHANGELOG.md and a
standalone dark-mode customer-facing HTML release notes page (changelog.html).
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

CATEGORY_RULES = [
    ("Breaking Changes", re.compile(r"(?i)(breaking|!:)")),
    ("New Features", re.compile(r"(?i)^(feat|add|launch|upgrade|build|ship)\b")),
    ("Bug Fixes", re.compile(r"(?i)^(fix|patch|resolve|repair|hotfix)\b")),
    ("Performance & Security", re.compile(r"(?i)^(perf|sec|harden|optimi)")),
]


@dataclass
class CommitEntry:
    sha: str
    date: str
    subject: str
    category: str


def categorize_subject(subject: str) -> str:
    cleaned = subject.strip()
    for label, pattern in CATEGORY_RULES:
        if pattern.search(cleaned):
            return label
    return "Improvements & Maintenance"


def clean_subject(subject: str) -> str:
    return re.sub(r"^(feat|fix|perf|docs|chore|refactor|test)(\([^)]+\))?!?:\s*", "", subject.strip(), flags=re.I)


def read_git_commits(repo_dir: Path, limit: int = 50) -> list[CommitEntry]:
    proc = subprocess.run(
        ["git", "log", f"-n{limit}", "--pretty=format:%h|%cs|%s"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        check=True,
    )
    entries: list[CommitEntry] = []
    for line in proc.stdout.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        sha, dt, subj = parts
        entries.append(
            CommitEntry(
                sha=sha.strip(),
                date=dt.strip(),
                subject=clean_subject(subj),
                category=categorize_subject(subj),
            )
        )
    return entries


def render_markdown(entries: list[CommitEntry], project_name: str) -> str:
    lines = [f"# {project_name} — Changelog", ""]
    by_date: dict[str, list[CommitEntry]] = {}
    for e in entries:
        by_date.setdefault(e.date, []).append(e)
    for dt, items in by_date.items():
        lines.append(f"## Release {dt}")
        for e in items:
            lines.append(f"- **[{e.category}]** {e.subject} (`{e.sha}`)")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_html(entries: list[CommitEntry], project_name: str) -> str:
    data_json = json.dumps([asdict(e) for e in entries]).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html.escape(project_name)} — Release Notes</title>
<style>
  :root {{ --bg:#080d1a; --panel:#11192e; --border:#233155; --text:#eef3ff; --muted:#96a7cb; --cyan:#38bdf8; --emerald:#34d399; --amber:#fbbf24; --rose:#fb7185; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",sans-serif; background:radial-gradient(circle at top left,#16254a,var(--bg) 55%); color:var(--text); line-height:1.55; }}
  .wrap {{ max-width:920px; margin:0 auto; padding:36px 20px 64px; }}
  header {{ border-bottom:1px solid var(--border); padding-bottom:18px; margin-bottom:24px; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:20px; }}
  input {{ flex:1; min-width:220px; background:var(--panel); border:1px solid var(--border); color:var(--text); padding:10px 14px; border-radius:10px; }}
  .pill {{ background:var(--panel); color:var(--muted); border:1px solid var(--border); padding:8px 14px; border-radius:999px; cursor:pointer; font-size:12.5px; font-weight:600; }}
  .pill.active {{ background:var(--cyan); color:#051120; border-color:var(--cyan); }}
  .card {{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:16px 20px; margin-bottom:12px; }}
  .meta {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; font-size:12px; color:var(--muted); margin-bottom:6px; }}
  .tag {{ padding:3px 9px; border-radius:999px; font-weight:700; font-size:11px; background:rgba(56,189,248,0.16); color:var(--cyan); }}
  .sha {{ font-family:ui-monospace,Menlo,monospace; color:var(--emerald); }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1 style="margin:0;font-size:28px;">{html.escape(project_name)} &mdash; Product Changelog</h1>
    <div style="color:var(--muted);font-size:14px;">Generated locally by ChangelogKit v1 &bull; Zero-Subscription Release Notes</div>
  </header>
  <div class="controls">
    <input id="q" type="search" placeholder="Search release notes..." />
    <button class="pill active" data-cat="ALL">All Updates</button>
    <button class="pill" data-cat="New Features">New Features</button>
    <button class="pill" data-cat="Bug Fixes">Bug Fixes</button>
    <button class="pill" data-cat="Improvements & Maintenance">Maintenance</button>
  </div>
  <div id="list"></div>
</div>
<script>
const ITEMS = {data_json};
let cat = "ALL";
function render() {{
  const q = document.getElementById("q").value.trim().toLowerCase();
  const filtered = ITEMS.filter(x => (cat === "ALL" || x.category === cat) && (!q || `${{x.subject}} ${{x.sha}} ${{x.date}}`.toLowerCase().includes(q)));
  document.getElementById("list").innerHTML = filtered.map(x => `
    <article class="card">
      <div class="meta"><span class="tag">${{x.category}}</span><span>${{x.date}}</span><span class="sha">${{x.sha}}</span></div>
      <div style="font-size:15px;font-weight:600;">${{x.subject}}</div>
    </article>
  `).join("") || "<p style='color:#96a7cb'>No matching commits.</p>";
}}
document.getElementById("q").addEventListener("input", render);
document.querySelectorAll(".pill").forEach(b => b.addEventListener("click", () => {{
  document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
  b.classList.add("active"); cat = b.dataset.cat; render();
}}));
render();
</script>
</body>
</html>
"""


def run_self_test() -> int:
    assert categorize_subject("feat(ui): add dark mode") == "New Features"
    assert categorize_subject("fix: handle empty csv") == "Bug Fixes"
    assert categorize_subject("feat!: drop v1 schema") == "Breaking Changes"
    sample = [
        CommitEntry("a1b2c3d", "2026-11-25", "Add interactive HTML dashboard", "New Features"),
        CommitEntry("e4f5g6h", "2026-11-24", "Handle quoted CSV paths", "Bug Fixes"),
    ]
    md = render_markdown(sample, "DemoApp")
    doc = render_html(sample, "DemoApp")
    assert "DemoApp" in md and "a1b2c3d" in md
    assert "Product Changelog" in doc and "interactive HTML dashboard" in doc
    print("SELF-TEST PASSED: ChangelogKit v1 categorization, Markdown, and interactive HTML changelog verified.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ChangelogKit — Local Git log to HTML & Markdown changelog generator.")
    parser.add_argument("--repo", type=Path, default=Path("../.."))
    parser.add_argument("--name", default="Neon Agent House")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--md", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--html", type=Path, default=Path("changelog.html"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    entries = read_git_commits(args.repo, limit=args.limit)
    args.md.write_text(render_markdown(entries, args.name), encoding="utf-8")
    args.html.write_text(render_html(entries, args.name), encoding="utf-8")
    print(f"ChangelogKit — Processed {len(entries)} git commit(s) -> {args.md.name} & {args.html.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
