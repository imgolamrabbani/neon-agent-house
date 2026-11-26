# Kilobyte Labs — Multi-Platform Launch Campaign Kit

## [Reddit — r/macapps] I built two tiny (<400 KB) native Swift/AppKit macOS menu-bar tools — PortPilot (localhost port killer) & SnapShrink (offline image compressor + GPS/EXIF stripper)
- **Campaign ID:** `reddit-macapps-launch` | **QA Score:** `100/100` | **Status:** `READY_TO_PUBLISH`

Hey r/macapps — developer here from **Kilobyte Labs**.

I got tired of installing 250 MB Electron wrappers or paying $10/mo subscriptions for basic macOS utilities, so I compiled two pure Swift/AppKit Apple Silicon menu-bar apps (zero Electron, zero Python, zero cloud uploads):

**1. PortPilot ($9 one-time)** — *337 KB native ARM64 menu-bar localhost port manager*
- Live radar of listening TCP ports (`:3000` Next.js, `:5173` Vite, `:5432` Postgres, `:8000` FastAPI, `:6379` Redis, etc.) with PID & RAM usage
- 1-click **Open in Browser**, **Copy URL**, **Pin Favorites**, **Stop (`SIGTERM`) / Force Kill (`SIGKILL`)**, and **Clean All Dev Ports**
- Free view-only radar works right out of the box; Gumroad license key unlocks 1-click kill & works 100% offline afterward.
- Link: https://adorable48.gumroad.com/l/portpilot

**2. SnapShrink ($7 one-time)** — *Native Apple ImageIO screenshot compressor & privacy stripper*
- Shrinks bloated macOS screenshots & photos (PNG/JPG/HEIC) up to 80% smaller locally using Apple's hardware `ImageIO`
- Automatically strips hidden GPS location, camera serial, TIFF, and EXIF metadata
- Optional Auto-Shrink Desktop Screenshots watcher mode
- Link: https://adorable48.gumroad.com/l/snapshrink

**Mac Power User Bundle ($12 for both — 25% off):** https://adorable48.gumroad.com/l/mac-power-bundle
**Overview & specs:** https://imgolamrabbani.github.io/neon-agent-house/

*Full transparency:* Both require macOS 14+ (Apple Silicon) and are currently ad-hoc signed indie builds (no $99/yr Apple Developer notarization yet), so first launch uses Right-Click -> Open once. Happy to answer any Swift/AppKit questions or hear what lightweight Mac menu-bar utility you wish existed next!

---

## [Reddit — r/SideProject] Built Kilobyte Labs: two tiny native macOS menu-bar utilities (<400 KB Swift binaries, zero Electron, one-time $7-$9)
- **Campaign ID:** `reddit-sideproject-launch` | **QA Score:** `100/100` | **Status:** `READY_TO_PUBLISH`

After getting frustrated with bloated Electron apps eating hundreds of MB of RAM just to sit in the macOS menu bar, I built two ultra-light native Swift/AppKit Apple Silicon utilities under **Kilobyte Labs**:

1. **PortPilot ($9 once)** — Live menu-bar radar for every listening localhost port (`:3000`, `:5173`, `:5432`, `:8000`, etc.) with 1-click Open in Browser, Copy URL, SIGTERM/SIGKILL, and Clean All Dev Ports. The entire compiled ARM64 binary is **337 KB**.
2. **SnapShrink ($7 once)** — Menu-bar image & screenshot compressor built on Apple's native `ImageIO` that shrinks files up to 80% and strips all GPS/camera EXIF metadata completely offline.

Both ship as drag-and-drop macOS `.dmg` installers with offline hardware-bound Gumroad License Key activation (plus a $12 bundle for both).

Storefront: https://imgolamrabbani.github.io/neon-agent-house/
Bundle ($12): https://adorable48.gumroad.com/l/mac-power-bundle

Would love brutal feedback on the positioning, pricing, and what annoying Mac/dev friction I should build as tool #3!

---

## [Hacker News — Show HN] Show HN: PortPilot – A 337 KB native Swift macOS menu-bar localhost port killer
- **Campaign ID:** `hn-show-portpilot` | **QA Score:** `100/100` | **Status:** `READY_TO_PUBLISH`

I built PortPilot because I was typing `lsof -nP -iTCP -sTCP:LISTEN` and `kill -9` ten times a day when Next.js, Vite, and FastAPI dev servers wedged ports.

Instead of wrapping a web view in 200MB of Electron, it's a pure Swift/AppKit/SwiftUI ARM64 binary (337 KB) that lives in the macOS menu bar, parses `lsof -F`, tags common dev runtimes, and gives 1-click Open, Copy URL, SIGTERM/SIGKILL, and Clean All Dev Ports.

Landing page & details: https://imgolamrabbani.github.io/neon-agent-house/
Direct Gumroad page ($9 one-time): https://adorable48.gumroad.com/l/portpilot

Note: It's currently ad-hoc signed while bootstrapping at $0 fixed cost (Right-Click -> Open on first run). Feedback welcome!

---

## [Dev.to — Dev.to (#macos #swift #indiedev #webdev)] Why I Built a 337 KB Native Swift Port Manager Instead of Another 200 MB Electron App
- **Campaign ID:** `devto-engineering-post` | **QA Score:** `100/100` | **Status:** `READY_TO_PUBLISH`

Every full-stack developer hits `Error: listen EADDRINUSE: address already in use :::3000` at least once a day.

This week I launched **Kilobyte Labs** with two compiled Apple Silicon macOS utilities built in pure Swift/AppKit/CoreGraphics with zero Electron dependencies:
- **PortPilot** (`337 KB` binary) — menu-bar localhost port monitor + 1-click process killer: https://adorable48.gumroad.com/l/portpilot
- **SnapShrink** — offline Apple `ImageIO` screenshot compressor + GPS/EXIF privacy stripper: https://adorable48.gumroad.com/l/snapshrink

Full showcase: https://imgolamrabbani.github.io/neon-agent-house/

---

## [Indie Hackers — Indie Hackers (Mac / Solo Founders)] Launching Kilobyte Labs: $0/mo fixed-cost studio shipping <400 KB native macOS utilities
- **Campaign ID:** `indiehackers-launch` | **QA Score:** `100/100` | **Status:** `READY_TO_PUBLISH`

Stopped selling raw code templates and pivoted to shipping compiled, stripped native Apple Silicon macOS utilities with Gumroad License Keys.

Just shipped our first two apps (**PortPilot** $9 + **SnapShrink** $7, or **$12 Mac Power User Bundle**):
https://imgolamrabbani.github.io/neon-agent-house/

---
