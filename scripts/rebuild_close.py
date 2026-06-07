#!/usr/bin/env python3
"""Rebuilds only the closing slide clip and final video."""
import subprocess, threading, http.server, os, re, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT    = os.path.dirname(SCRIPT_DIR)  # repo root (scripts/ lives one level down)
AUDIO      = os.path.join(PROJECT, 'assets', 'audio', 'LLNL_Speech_andrew.mp3')
SPEECH     = os.path.join(PROJECT, 'content', 'LLNL_Speech.txt')
OUTPUT     = os.path.join(PROJECT, 'assets', 'video', 'LLNL_Presentation.mp4')
SLIDES_DIR = os.path.join(PROJECT, 'assets', 'slides', 'images')
CLIPS_DIR  = os.path.join(PROJECT, 'assets', 'slides', 'clips')
CAPTURE_JS = os.path.join(SCRIPT_DIR, 'capture_slides.js')
FFMPEG     = '/opt/homebrew/bin/ffmpeg'
PORT       = 8765
TOTAL_AUDIO = 526.008

with open(SPEECH) as f:
    raw = f.read()

parts = re.split(r'\[SLIDE [^\]]+\]', raw)

def wc(s): return len(s.split())
total_words = sum(wc(p) for p in parts)
spw = TOTAL_AUDIO / total_words

# Closing slide is parts[9]
close_duration = max(2.0, wc(parts[9]) * spw)
print(f"07_close.png duration: {close_duration:.1f}s")

# Start HTTP server
os.chdir(PROJECT)
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

httpd = http.server.HTTPServer(('127.0.0.1', PORT), QuietHandler)
thread = threading.Thread(target=httpd.serve_forever, daemon=True)
thread.start()
print(f"HTTP server on port {PORT}")
time.sleep(0.5)

# Capture only the closing slide via inline Node script
capture_script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch({{
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: ['--no-sandbox', '--disable-gpu']
  }});
  const page = await browser.newPage();
  await page.setViewportSize({{ width: 1280, height: 960 }});
  await page.goto('http://localhost:{PORT}/index.html', {{ waitUntil: 'networkidle', timeout: 30000 }});
  await new Promise(r => setTimeout(r, 2000));
  await page.evaluate(() => Reveal.slide(7, 0, -1));
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({{ path: '{SLIDES_DIR}/07_close.png', type: 'png' }});
  console.log('captured 07_close.png');
  await browser.close();
}})().catch(e => {{ console.error(e); process.exit(1); }});
"""

tmp_js = os.path.join(PROJECT, '_capture_close.js')
with open(tmp_js, 'w') as f:
    f.write(capture_script)

print("Capturing 07_close.png…")
result = subprocess.run(['node', tmp_js], cwd=PROJECT, text=True)
httpd.shutdown()
os.remove(tmp_js)

if result.returncode != 0:
    print("Capture failed.")
    raise SystemExit(1)

# Rebake 07_close.mp4
close_clip = os.path.join(CLIPS_DIR, '07_close.mp4')
close_img  = os.path.join(SLIDES_DIR, '07_close.png')
print(f"Baking 07_close.mp4 ({close_duration:.1f}s)…")
subprocess.run([
    FFMPEG, '-y',
    '-loop', '1', '-i', close_img,
    '-t', str(close_duration),
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-vf', 'scale=1280:960:flags=lanczos,format=yuv420p',
    '-r', '25', '-an',
    close_clip
], check=True, capture_output=True)
print("  done.")

# Recombine all clips + audio
SLIDE_ORDER = [
    '00_title.mp4', '01_intro.mp4', '02a_naive.mp4', '02b_production.mp4',
    '03_retrieval.mp4', '04a_casestudy.mp4', '04b_arch.mp4', '05_impact.mp4',
    '06_tooling.mp4', '07_close.mp4',
]
concat = os.path.join(PROJECT, 'build', 'ffmpeg_concat.txt')
os.makedirs(os.path.dirname(concat), exist_ok=True)
with open(concat, 'w') as f:
    for clip in SLIDE_ORDER:
        f.write(f"file '{os.path.join(CLIPS_DIR, clip)}'\n")

print("Rendering final video…")
subprocess.run([
    FFMPEG, '-y',
    '-f', 'concat', '-safe', '0', '-i', concat,
    '-i', AUDIO,
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '192k',
    '-shortest',
    OUTPUT
], cwd=PROJECT, check=True)
print(f"\nDone → {OUTPUT}")
