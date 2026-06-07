#!/usr/bin/env python3
"""
sync_video.py — generates per-section audio to get exact slide timestamps,
then concatenates into final MP3 and rebuilds the video.
"""
import re, os, subprocess, tempfile, shutil

PROJECT    = os.path.dirname(os.path.abspath(__file__))
SPEECH     = os.path.join(PROJECT, 'LLNL_Speech.txt')
AUDIO_OUT  = os.path.join(PROJECT, 'LLNL_Speech_andrew.mp3')
SLIDES_DIR = os.path.join(PROJECT, 'slide_images')
CLIPS_DIR  = os.path.join(PROJECT, 'slide_clips')
OUTPUT     = os.path.join(PROJECT, 'LLNL_Presentation.mp4')
FFMPEG     = '/opt/homebrew/bin/ffmpeg'
FFPROBE    = '/opt/homebrew/bin/ffprobe'
RATE       = '-5%'

SLIDE_MAP = [
    ('00_title.png',       0),
    ('01_intro.png',       1),
    ('02a_naive.png',      2),
    ('02b_production.png', 3),
    ('03_retrieval.png',   4),
    ('04a_casestudy.png',  5),
    ('04b_arch.png',       6),
    ('05_impact.png',      7),
    ('06_tooling.png',     8),
    ('07_close.png',       9),
]

# ── Split speech into sections ────────────────────────────────────────────────
with open(SPEECH, encoding='utf-8') as f:
    raw = f.read()

parts = re.split(r'\[SLIDE [^\]]+\]', raw)
parts = [p.strip() for p in parts]
print(f"Found {len(parts)} sections")

# ── Generate audio per section, measure duration ──────────────────────────────
tmp_dir = tempfile.mkdtemp()
section_durations = []
section_files = []

print("\nGenerating per-section audio…")
for i, text in enumerate(parts):
    txt_file = os.path.join(tmp_dir, f'section_{i:02d}.txt')
    mp3_file = os.path.join(tmp_dir, f'section_{i:02d}.mp3')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(text)

    subprocess.run(
        ['edge-tts', '--voice', 'en-US-AndrewNeural',
         '--rate', RATE, '--file', txt_file, '--write-media', mp3_file],
        check=True, capture_output=True
    )

    result = subprocess.run(
        [FFPROBE, '-v', 'quiet', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', mp3_file],
        capture_output=True, text=True, check=True
    )
    dur = float(result.stdout.strip())
    section_durations.append(dur)
    section_files.append(mp3_file)
    print(f"  section {i}: {dur:.2f}s")

# ── Concatenate section audio files into final MP3 ────────────────────────────
concat_audio = os.path.join(tmp_dir, 'concat_audio.txt')
with open(concat_audio, 'w') as f:
    for mp3 in section_files:
        f.write(f"file '{mp3}'\n")

print(f"\nConcatenating audio → {AUDIO_OUT}")
subprocess.run([
    FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', concat_audio,
    '-c', 'copy', AUDIO_OUT
], check=True, capture_output=True)

total = sum(section_durations)
print(f"Total audio: {total:.1f}s ({total/60:.1f} min)")

# ── Calculate exact slide timestamps ─────────────────────────────────────────
cumulative = 0.0
timestamps = []
for img, idx in SLIDE_MAP:
    timestamps.append(cumulative)
    cumulative += section_durations[idx]

print("\nExact slide timings:")
for (img, idx), ts, dur in zip(SLIDE_MAP, timestamps, section_durations):
    print(f"  {img}: starts {ts:.2f}s, duration {dur:.2f}s")

# ── Bake slide clips ──────────────────────────────────────────────────────────
os.makedirs(CLIPS_DIR, exist_ok=True)
clip_paths = []

print("\nBaking clips…")
for (img, idx), dur in zip(SLIDE_MAP, section_durations):
    src  = os.path.join(SLIDES_DIR, img)
    clip = os.path.join(CLIPS_DIR, img.replace('.png', '.mp4'))
    clip_paths.append(clip)
    subprocess.run([
        FFMPEG, '-y',
        '-loop', '1', '-i', src,
        '-t', f'{dur:.3f}',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-vf', 'scale=1280:960:flags=lanczos,format=yuv420p',
        '-r', '25', '-an', clip
    ], check=True, capture_output=True)
    print(f"  {img} → {dur:.1f}s")

# ── Concatenate clips + add audio ─────────────────────────────────────────────
concat_video = os.path.join(PROJECT, 'ffmpeg_concat.txt')
with open(concat_video, 'w') as f:
    for clip in clip_paths:
        f.write(f"file '{clip}'\n")

print("\nRendering final video…")
subprocess.run([
    FFMPEG, '-y',
    '-f', 'concat', '-safe', '0', '-i', concat_video,
    '-i', AUDIO_OUT,
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '192k',
    '-shortest',
    OUTPUT
], check=True, cwd=PROJECT)

shutil.rmtree(tmp_dir)
print(f"\nDone → {OUTPUT}  ({total/60:.1f} min)")
