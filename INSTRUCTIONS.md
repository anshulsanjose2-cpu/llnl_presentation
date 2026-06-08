# LLNL Presentation — Project Instructions

Internal reference for building, editing, and rebuilding the deck, video, PDF, and subtitles.
This is a Reveal.js slide deck (`index.html`) plus a generated video, PDF, and subtitle track.

**Production URL:** https://anshulsanjose2-cpu.github.io/llnl_presentation/
Hosted on GitHub Pages from the `main` branch (repo `anshulsanjose2-cpu/llnl_presentation`).
Pushing to `main` deploys automatically — give Pages a minute, then hard-reload. Because it's
served over HTTPS, the video overlay and subtitles work in production (subtitles need HTTP(S),
not `file://`).

---

## Project layout

The project is modularized into folders. `index.html` stays at the repo root (it's the
web entry point); everything else is grouped by role. **All commands run from the repo root.**

```
/ (repo root)
├── index.html            Deck — single self-contained file (slides + CSS + JS inline). Source of truth for slide content.
├── INSTRUCTIONS.md       This file.
├── package.json          npm deps (playwright, pdfkit).
├── src/                  Page config (loaded by index.html via <script src="src/...">)
│   ├── config.js           Runtime config: content lock (countdown).
│   └── config.local.js     Local-dev overrides for config.js (gitignored, optional).
├── assets/               All media (served to the browser)
│   ├── video/    LLNL_Presentation.mp4                       Final video (~15:43, 1280×960).
│   ├── pdf/      LLNL_AI_Solutions_Engineer_Presentation.pdf  Exported PDF, 1 slide/page.
│   ├── subtitles/ subtitles.vtt                              WebVTT subs (transcribed from audio).
│   ├── audio/    LLNL_Speech_andrew.mp3, LLNL_Speech.m4a, sample_*.mp3   Narration + samples.
│   └── slides/
│       ├── images/   PNG screenshot per slide (build input for video AND pdf). [gitignored]
│       └── clips/    Per-slide mp4 (image baked for its narration duration). [gitignored]
├── content/             Narration text & talk track
│   ├── LLNL_Speech.txt        Narration script, in order, with [SLIDE X — ...] markers. Ground truth.
│   ├── LLNL_Speech_clean.txt  Cleaned narration text.
│   ├── LLNL_Talk_Track.md     Human-readable talk track / speaker notes.
│   └── LLNL_Speech_andrew.vtt DO NOT USE for subtitles — two transcripts interleaved, bad timestamps. [gitignored]
├── scripts/             Build pipeline (see below)
└── build/              Generated intermediates (ffmpeg_concat.txt). [gitignored]
```

### Scripts (all in `scripts/`, run from repo root)
| Script | What it does |
|---|---|
| `scripts/capture_slides.js` | Playwright (system Chrome) screenshots each slide/fragment state → `assets/slides/images/`. Handles flip-card back faces. |
| `scripts/make_video.py` | Full pipeline: capture slides → bake clips → concat + add audio → `assets/video/LLNL_Presentation.mp4`. |
| `scripts/rebuild_close.py` | Targeted rebuild of **only** the closing slide (recapture `07_close.png`, rebake clip, recombine). Use when only the close changed. |
| `scripts/sync_video.py` | Generates per-section audio to get exact slide timestamps, then rebuilds. (Heavier; for re-syncing audio to slides.) |
| `scripts/build_pdf.js` | **Preferred PDF builder** — assembles `assets/slides/images/*.png` into the PDF with PDFKit (clean 10 pages). |
| `scripts/generate_subtitles.py` | Regenerate `assets/subtitles/subtitles.vtt` by transcribing the video audio (mlx-whisper). |
| `scripts/export_pdf.js` | Reveal `?print-pdf` export. **Deprecated — produces duplicate pages.** Use `build_pdf.js` instead. |

All Python scripts derive the repo root as the parent of `scripts/`, so they work regardless of cwd; still run them from the repo root for the server-rooted capture step.

### Tooling / environment
- **Node**: `/opt/homebrew/bin/node`. **ffmpeg/ffprobe**: `/opt/homebrew/bin/ffmpeg`.
- **Chrome** (for Playwright): `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
- npm dev deps include `playwright` and `pdfkit`.
- `.venv-whisper/` — Python venv with `mlx-whisper` for subtitle transcription (gitignored).
- Local HTTP server for testing: run **from the repo root** — `python3 -m http.server 8765 --bind 127.0.0.1`, then open `http://127.0.0.1:8765`. (Subtitles only load over HTTP, not `file://`.)

---

## Slide order (10 slides)
`00_title` · `01_intro` · `02a_naive` · `02b_production` · `03_retrieval` · `04a_casestudy` · `04b_arch` · `05_impact` · `06_tooling` · `07_close`

`02b` and `04b` are **flip-card back faces** of `02a`/`04a` (revealed via fragments). Capture scripts force the back face for those screenshots; PDF export hides back faces.

---

## Common tasks

### Full end-to-end rebuild (video + PDF + subtitles)
One command does everything — capture slides, render video, build PDF, regenerate subtitles:
```bash
./build.sh                 # full rebuild        (or: npm run build)
./build.sh --no-subtitles  # skip subtitle step
./build.sh --pdf-only      # just rebuild the PDF from existing slide images
```
Use this after any slide edit. The individual steps below are for when you only need one artifact.

### Edit slide text
Edit `index.html` directly. Then run `./build.sh` (or rebuild just the artifact the change touches).

### Rebuild the video
- **Whole deck changed:** `python3 scripts/make_video.py`
- **Only the closing slide changed:** `python3 scripts/rebuild_close.py`
- Slide durations are derived from word counts in `content/LLNL_Speech.txt` against the audio length. The narration audio (`assets/audio/LLNL_Speech_andrew.mp3`) is **not** regenerated by these — only the visuals + timing. If you change spoken content, the audio must be regenerated separately (TTS).

### Rebuild the PDF — use build_pdf.js, NOT export_pdf.js
Just run:
```bash
node scripts/build_pdf.js     # → assets/pdf/LLNL_AI_Solutions_Engineer_Presentation.pdf (clean 10 pages)
```
It assembles `assets/slides/images/*.png` with PDFKit. **Always recapture the relevant slide(s) first** so screenshots are current. Avoid `scripts/export_pdf.js` (Reveal `?print-pdf`) — it produces **36 pages instead of 10** because `pdfSeparateFragments:false` set after load doesn't retrigger the print layout, and `Reveal.sync()` doesn't fix it.

### Rebuild subtitles — transcribe the AUDIO, don't reuse the old VTT
Just run:
```bash
.venv-whisper/bin/python scripts/generate_subtitles.py   # → assets/subtitles/subtitles.vtt
```
It extracts the audio from `assets/video/LLNL_Presentation.mp4` and transcribes it with mlx-whisper, so timing is always in sync. Re-run whenever the video/audio is rebuilt.

**Do not use `content/LLNL_Speech_andrew.vtt`** — it contains two complete transcripts interleaved with unreliable/overlapping timestamps (e.g. two unrelated lines show at 0:02). No scaling or reordering fixes it.

---

## Video overlay (title slide)
The title slide has three buttons: **Watch Video** (opens a fullscreen overlay playing `assets/video/LLNL_Presentation.mp4` with subtitles on by default), **View Slides** (advances into the normal deck), and **Download PDF** (an `<a download>` to `assets/pdf/...pdf`). Overlay closes via the × button, Escape, or clicking outside. While open, Reveal keyboard nav is disabled. Relevant IDs in `index.html`: `#video-overlay`, `#video-player`, `#btn-video`, `#btn-slides`, `#btn-pdf`, `#video-close`. Subtitle size is controlled by the `::cue` CSS rule (currently `font-size:.7em`).

## Content lock
Controlled by `src/config.js`:
- **Content lock** (`contentLock`): hides the deck behind a countdown until `showAtUTC`. Set `enabled:false` to disable. Times are **UTC** (`...Z`). Go-live: 2026-06-10 16:00 UTC = 9:00 AM Pacific.
Headless capture/export disables it via `addInitScript` so the deck renders.

### Quickly flip the flag (and deploy)
`scripts/toggle_flags.sh` flips `contentLock.enabled: true <-> false` and commits + pushes to `main`
(which redeploys GitHub Pages). "Go live" = set it to false.
```bash
./scripts/toggle_flags.sh            # flip contentLock.enabled, commit, push   (or: npm run toggle)
./scripts/toggle_flags.sh --dry-run  # preview the change, write nothing
./scripts/toggle_flags.sh --no-push  # commit but don't push
```

## Key durations / specs
- Slide size / video resolution: **1280×960**.
- Video: ~**15:43** (943.1s). Raw TTS audio: 963.4s.
- Subtitles: ~156 cues (from base.en transcription).

## Gotchas (learned the hard way)
1. **PDF dupes** → use PDFKit from screenshots, never Reveal print-pdf.
2. **Subtitle desync / double lines** → the bundled `_andrew.vtt` is broken; always re-transcribe the video audio.
3. **Subtitles don't load** → must be served over HTTP, not opened as `file://`.
4. **Local server shows home-dir listing** → you launched it from the wrong cwd; run it from the project dir.
5. Capture/export scripts depend on the exact Chrome path above and on Playwright being installed.
