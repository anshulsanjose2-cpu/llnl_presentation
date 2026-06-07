#!/usr/bin/env python3
"""
generate_subtitles.py — regenerate assets/subtitles/subtitles.vtt by transcribing
the actual video audio, so subtitle timing is always in sync with the audio.

DO NOT reuse content/LLNL_Speech_andrew.vtt — it has two transcripts interleaved
with bad timestamps (unfixable by scaling).

Requires the mlx-whisper venv at .venv-whisper/ (see INSTRUCTIONS.md). Run with:
    .venv-whisper/bin/python scripts/generate_subtitles.py
"""
import os, subprocess, tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT    = os.path.dirname(SCRIPT_DIR)
VIDEO      = os.path.join(PROJECT, 'assets', 'video', 'LLNL_Presentation.mp4')
OUT        = os.path.join(PROJECT, 'assets', 'subtitles', 'subtitles.vtt')
FFMPEG     = '/opt/homebrew/bin/ffmpeg'
MODEL      = 'mlx-community/whisper-base.en-mlx'


def fmt(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); ms = int(round(t % 1 * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def main():
    import mlx_whisper  # imported here so the helpful error only fires when actually run

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        wav = tmp.name
    try:
        print("Extracting audio from video…")
        subprocess.run([FFMPEG, '-y', '-i', VIDEO, '-vn', '-ac', '1', '-ar', '16000', wav],
                       check=True, capture_output=True)
        print("Transcribing (downloads model on first run)…")
        result = mlx_whisper.transcribe(wav, path_or_hf_repo=MODEL)
    finally:
        if os.path.exists(wav):
            os.remove(wav)

    segs = result["segments"]
    lines = ["WEBVTT", ""]
    for i, s in enumerate(segs, 1):
        lines += [str(i), f"{fmt(s['start'])} --> {fmt(s['end'])}", s['text'].strip(), ""]
    with open(OUT, 'w') as f:
        f.write("\n".join(lines))
    print(f"Done — {len(segs)} cues → {OUT}")


if __name__ == '__main__':
    main()
