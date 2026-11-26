#!/usr/bin/env node
/**
 * Deterministic 1080x1920 30fps HTML5/CSS3/SVG/Canvas -> MP4 renderer via Chrome CDP.
 * Zero npm dependencies: drives local Google Chrome + FFmpeg directly over native WebSocket.
 *
 * Usage:
 *   node chrome_frame_renderer.mjs --html scene.html --audio master.wav --out video.mp4 --duration 42.5 --fps 30
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    if (argv[i].startsWith("--")) {
      const k = argv[i].slice(2);
      const v = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : "true";
      args[k] = v;
    }
  }
  return args;
}

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.id = 0;
    this.pending = new Map();
  }
  async connect() {
    await new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.addEventListener("open", () => resolve());
      this.ws.addEventListener("error", (e) => reject(e));
      this.ws.addEventListener("message", (ev) => {
        const msg = JSON.parse(ev.data.toString());
        if (msg.id && this.pending.has(msg.id)) {
          const { resolve: res, reject: rej } = this.pending.get(msg.id);
          this.pending.delete(msg.id);
          if (msg.error) rej(new Error(msg.error.message || JSON.stringify(msg.error)));
          else res(msg.result);
        }
      });
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  close() {
    try { this.ws.close(); } catch {}
  }
}

async function waitForDevTools(port, timeoutMs = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/json/list`);
      if (r.ok) {
        const list = await r.json();
        const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
        if (page) return page.webSocketDebuggerUrl;
      }
    } catch {}
    await new Promise((r) => setTimeout(r, 120));
  }
  throw new Error("Timed out waiting for Chrome DevTools endpoint");
}

async function main() {
  const args = parseArgs(process.argv);
  const htmlPath = path.resolve(args.html);
  const audioPath = args.audio ? path.resolve(args.audio) : null;
  const outPath = path.resolve(args.out);
  const duration = parseFloat(args.duration || "35");
  const fps = parseInt(args.fps || "30", 10);
  const width = parseInt(args.width || "1080", 10);
  const height = parseInt(args.height || "1920", 10);
  const totalFrames = Math.max(1, Math.ceil(duration * fps));
  const port = 19222 + Math.floor(Math.random() * 2000);
  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), "chrome-render-"));

  const chromeBin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const chrome = spawn(chromeBin, [
    "--headless=new",
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profileDir}`,
    `--window-size=${width},${height}`,
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--allow-file-access-from-files",
    "--no-first-run",
    "--no-default-browser-check",
    "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });

  let cdp;
  try {
    const wsUrl = await waitForDevTools(port);
    cdp = new CDPClient(wsUrl);
    await cdp.connect();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: false,
    });

    const fileUrl = `file://${encodeURI(htmlPath)}`;
    await cdp.send("Page.navigate", { url: fileUrl });

    // Wait for page + images + fonts + window.renderFrame to be ready
    for (let i = 0; i < 120; i++) {
      const evalRes = await cdp.send("Runtime.evaluate", {
        expression: `Boolean(document.readyState === 'complete' && typeof window.renderFrame === 'function' && window.__RENDER_READY__ !== false)`,
        returnByValue: true,
      });
      if (evalRes?.result?.value === true) break;
      await new Promise((r) => setTimeout(r, 100));
    }

    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    const ffArgs = [
      "-y", "-v", "error",
      "-f", "image2pipe", "-vcodec", "mjpeg", "-r", String(fps), "-i", "-",
    ];
    if (audioPath) {
      ffArgs.push("-i", audioPath);
    }
    ffArgs.push(
      "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
      "-pix_fmt", "yuv420p",
    );
    if (audioPath) {
      ffArgs.push("-c:a", "aac", "-b:a", "192k", "-shortest");
    }
    ffArgs.push("-movflags", "+faststart", outPath);

    const ff = spawn("ffmpeg", ffArgs, { stdio: ["pipe", "inherit", "inherit"] });
    const ffDone = new Promise((resolve, reject) => {
      ff.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exit ${code}`))));
    });

    const t0 = Date.now();
    for (let f = 0; f < totalFrames; f++) {
      const t = f / fps;
      await cdp.send("Runtime.evaluate", {
        expression: `window.renderFrame(${t.toFixed(5)}, ${f});`,
        awaitPromise: false,
      });
      const shot = await cdp.send("Page.captureScreenshot", {
        format: "jpeg",
        quality: 92,
        fromSurface: true,
      });
      const buf = Buffer.from(shot.data, "base64");
      if (!ff.stdin.write(buf)) {
        await new Promise((r) => ff.stdin.once("drain", r));
      }
      if ((f + 1) % 150 === 0 || f + 1 === totalFrames) {
        const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
        console.log(`[render] ${f + 1}/${totalFrames} frames (${elapsed}s)`);
      }
    }
    ff.stdin.end();
    await ffDone;
    console.log(`[render] DONE -> ${outPath}`);
  } finally {
    if (cdp) cdp.close();
    chrome.kill("SIGKILL");
    try { fs.rmSync(profileDir, { recursive: true, force: true }); } catch {}
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
