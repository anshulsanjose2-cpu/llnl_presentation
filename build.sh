#!/usr/bin/env bash
#
# build.sh — end-to-end rebuild of the LLNL presentation.
#
# Runs the full pipeline so the video and PDF (and subtitles) are ready:
#   1. Render video  — capture slide screenshots, bake clips, mux with audio
#                      → assets/video/LLNL_Presentation.mp4
#                      (also refreshes assets/slides/images used by the PDF)
#   2. Build PDF     — assemble slide screenshots with PDFKit (clean 10 pages)
#                      → assets/pdf/LLNL_AI_Solutions_Engineer_Presentation.pdf
#   3. Subtitles     — transcribe the rendered video's audio with mlx-whisper
#                      → assets/subtitles/subtitles.vtt
#                      (skipped automatically if the .venv-whisper/ venv is absent)
#
# Usage:
#   ./build.sh                 # full rebuild (video + pdf + subtitles)
#   ./build.sh --no-subtitles  # skip the subtitle step
#   ./build.sh --pdf-only       # only rebuild the PDF from existing slide images
#
# Safe to run from anywhere — it cd's to the repo root (its own directory).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

WHISPER_PY="$ROOT/.venv-whisper/bin/python"
DO_SUBTITLES=1
PDF_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --no-subtitles) DO_SUBTITLES=0 ;;
    --pdf-only)     PDF_ONLY=1 ;;
    -h|--help)
      sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }

if [[ "$PDF_ONLY" -eq 1 ]]; then
  step "PDF only — building from existing slide images"
  node scripts/build_pdf.js
  echo -e "\n\033[1;32m✓ PDF rebuilt.\033[0m"
  exit 0
fi

# 1. Video (also regenerates the slide screenshots the PDF needs)
step "1/3  Rendering video (capture slides → bake clips → mux audio)"
python3 scripts/make_video.py

# 2. PDF (from the freshly captured slide screenshots)
step "2/3  Building PDF from slide screenshots"
node scripts/build_pdf.js

# 3. Subtitles (transcribe the freshly rendered video audio)
if [[ "$DO_SUBTITLES" -eq 1 ]]; then
  if [[ -x "$WHISPER_PY" ]]; then
    step "3/3  Regenerating subtitles (transcribing video audio)"
    "$WHISPER_PY" scripts/generate_subtitles.py
  else
    step "3/3  Subtitles — SKIPPED (no .venv-whisper venv)"
    echo "    To enable: create the venv and install mlx-whisper, then re-run." >&2
    echo "    See INSTRUCTIONS.md → 'Rebuild subtitles'." >&2
  fi
else
  step "3/3  Subtitles — SKIPPED (--no-subtitles)"
fi

step "Done"
echo "  Video:     assets/video/LLNL_Presentation.mp4"
echo "  PDF:       assets/pdf/LLNL_AI_Solutions_Engineer_Presentation.pdf"
[[ "$DO_SUBTITLES" -eq 1 && -x "$WHISPER_PY" ]] && echo "  Subtitles: assets/subtitles/subtitles.vtt"
echo -e "\n\033[1;32m✓ Build complete — video and PDF ready.\033[0m"
