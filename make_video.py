#!/usr/bin/env python3
"""
make_video.py — combines slide screenshots + audio into LLNL_Presentation.mp4
Run from the project directory: python3 make_video.py
"""
import subprocess, threading, http.server, os, re, sys, time

PROJECT   = os.path.dirname(os.path.abspath(__file__))
AUDIO     = os.path.join(PROJECT, 'LLNL_Speech_andrew.mp3')
SPEECH    = os.path.join(PROJECT, 'LLNL_Speech.txt')
OUTPUT    = os.path.join(PROJECT, 'LLNL_Presentation.mp4')
SLIDES_DIR = os.path.join(PROJECT, 'slide_images')
CAPTURE_JS = os.path.join(PROJECT, 'capture_slides.js')
FFMPEG    = '/opt/homebrew/bin/ffmpeg'
PORT      = 8765
TOTAL_AUDIO = 526.008  # seconds from ffprobe

# ── 1. Parse speech into sections ────────────────────────────────────────────
with open(SPEECH) as f:
    raw = f.read()

# Split on [SLIDE X — ...] markers; section 0 = intro before first marker
parts = re.split(r'\[SLIDE [^\]]+\]', raw)

def wc(s): return len(s.split())

total_words = sum(wc(p) for p in parts)
spw = TOTAL_AUDIO / total_words  # seconds per word

# Ordered list: (slide_image_filename, speech_part_index)
SLIDE_MAP = [
    ('00_title.png',      0),   # intro narration → title card
    ('01_intro.png',      1),   # SLIDE 1
    ('02a_naive.png',     2),   # SLIDE 2a
    ('02b_production.png',3),   # SLIDE 2b
    ('03_retrieval.png',  4),   # SLIDE 3
    ('04a_casestudy.png', 5),   # SLIDE 4a
    ('04b_arch.png',      6),   # SLIDE 4b
    ('05_impact.png',     7),   # SLIDE 4c
    ('06_tooling.png',    8),   # SLIDE 5
    ('07_close.png',      9),   # SLIDE 6
]

durations = {}
for img, idx in SLIDE_MAP:
    if idx < len(parts):
        durations[img] = max(2.0, wc(parts[idx]) * spw)
    else:
        durations[img] = 5.0

print("Slide durations (seconds):")
for img, _ in SLIDE_MAP:
    print(f"  {img}: {durations[img]:.1f}s")
print(f"  Total: {sum(durations.values()):.1f}s  (audio: {TOTAL_AUDIO:.1f}s)")

# ── 2. Start HTTP server ──────────────────────────────────────────────────────
os.chdir(PROJECT)
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

httpd = http.server.HTTPServer(('127.0.0.1', PORT), QuietHandler)
thread = threading.Thread(target=httpd.serve_forever, daemon=True)
thread.start()
print(f"\nHTTP server started on port {PORT}")
time.sleep(0.5)

# ── 3. Install playwright (first-time only) & capture slides ──────────────────
os.makedirs(SLIDES_DIR, exist_ok=True)

print("Installing playwright (first run may take a moment)...")
subprocess.run(
    ['npm', 'install', '--save-dev', 'playwright'],
    cwd=PROJECT, capture_output=True
)

print("Capturing slides…")
result = subprocess.run(
    ['node', CAPTURE_JS, str(PORT), SLIDES_DIR],
    cwd=PROJECT, capture_output=False, text=True
)
httpd.shutdown()

if result.returncode != 0:
    print("Slide capture failed — aborting.")
    sys.exit(1)

# ── 4. Verify all screenshots exist ──────────────────────────────────────────
missing = [img for img, _ in SLIDE_MAP if not os.path.exists(os.path.join(SLIDES_DIR, img))]
if missing:
    print("Missing screenshots:", missing)
    sys.exit(1)

# ── 5. Bake each image into a proper video clip ───────────────────────────────
clips_dir = os.path.join(PROJECT, 'slide_clips')
os.makedirs(clips_dir, exist_ok=True)
clip_paths = []

print("\nBaking slide clips…")
for img, _ in SLIDE_MAP:
    src  = os.path.join(SLIDES_DIR, img)
    clip = os.path.join(clips_dir, img.replace('.png', '.mp4'))
    clip_paths.append(clip)
    dur  = durations[img]
    subprocess.run([
        FFMPEG, '-y',
        '-loop', '1', '-i', src,
        '-t', str(dur),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-vf', 'scale=1280:960:flags=lanczos,format=yuv420p',
        '-r', '25',
        '-an',
        clip
    ], check=True, capture_output=True)
    print(f"  {img} → {dur:.1f}s")

# ── 6. Concatenate clips + add audio ─────────────────────────────────────────
concat = os.path.join(PROJECT, 'ffmpeg_concat.txt')
with open(concat, 'w') as f:
    for clip in clip_paths:
        f.write(f"file '{clip}'\n")

print("\nRendering final video…")
cmd = [
    FFMPEG, '-y',
    '-f', 'concat', '-safe', '0', '-i', concat,
    '-i', AUDIO,
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '192k',
    '-shortest',
    OUTPUT
]
subprocess.run(cmd, cwd=PROJECT, check=True)
print(f"\nDone → {OUTPUT}")
