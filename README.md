# Neon Agent House — Autonomous 5-Agent Micro-Niche & MVP Engine

An autonomous 5-agent **Agent House** built on **Google ADK 2.x** (`google-adk>=2.15.0`) and **Gemini 4 Neon** (`gemini-4-neon`), with Antigravity skills, parallel fan-out/join discovery, an adversarial **Hall Room Verifier** (max 2 retry rounds + live quote-in-page verification), exclusive write-locked Hall Room (`state/hall_room.json` & `state/hall_room.md`), and a weekly self-improvement loop.

## What It Solves
Eliminates manual one-by-one niche research and hallucinated "make money online" ideas. Given one broad directive, the House runs specialized rooms in parallel, rejects unverified claims/URLs/math automatically, builds and tests a runnable `$0`-stack digital product MVP, and promotes only 100%-verified packages into your shared Hall Room.

## Install & Run in 3 Steps

1. **Create a virtual environment and install dependencies:**
   ```bash
   uv venv --python 3.12 .venv
   uv pip install --python .venv/bin/python -e ".[dev]"
   ```
2. **Set your Gemini API key in your shell (for standalone live runs outside Antigravity):**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```
3. **Run your Agent House with one command:**
   ```bash
   ./run_house.sh run "Find an urgent $0-stack workflow pain for solo freelancers solvable with a $9-$29 automation"
   ```
   *(Or run the weekly self-improvement audit: `./run_house.sh weekly`, or run tests: `.venv/bin/pytest -v`.)*

## Architecture
- **5 Antigravity Skills (Single Source of Truth):** `.agent/skills/{house-lead,pain-point-scout,market-roi-analyst,mvp-builder,hall-room-verifier}/SKILL.md`
- **Google ADK 2.x Graph (`agent_house/graph.py`):** Native `Workflow`, `JoinNode`, conditional `EventActions(route=...)`, max-2-round Verifier loops, and `RequestInput` external-release approval gate (zero deprecated `SequentialAgent`/`ParallelAgent`/`LoopAgent`).
- **Shipped Product v3 (`mvp_bundle/invoice-pulse-01/` & `dist/InvoicePulse_v3.zip`):** **InvoicePulse v3** — zero-dependency local Python overdue invoice auditor, late-fee calculator, and interactive dark-mode HTML dashboard + full launch kit in `outputs/launch_kit/`.
