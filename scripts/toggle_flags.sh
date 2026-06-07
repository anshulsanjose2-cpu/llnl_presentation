#!/usr/bin/env bash
#
# toggle_flags.sh — flip the boolean flags in src/config.js, then commit & push.
#
# Flips `enabled: true` <-> `enabled: false` for the content lock and/or draft banner,
# then commits the change to main and pushes (the repo is the live GitHub Pages site).
#
#   contentLock.enabled  — hides the deck behind a countdown until showAtUTC
#   draftBanner.enabled  — shows the "WORK IN PROGRESS" badge
#
# Usage:
#   ./scripts/toggle_flags.sh             # flip BOTH flags
#   ./scripts/toggle_flags.sh lock        # flip only contentLock.enabled
#   ./scripts/toggle_flags.sh banner      # flip only draftBanner.enabled
#   ./scripts/toggle_flags.sh all         # flip both (same as no arg)
#
# Options:
#   --dry-run     show the change but don't write, commit, or push
#   --no-push     commit but don't push
#   -h, --help    this help
#
# "Go live" = both flags false (deck visible, no WIP badge).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/src/config.js"

TARGET="all"
DRY_RUN=0
NO_PUSH=0

for arg in "$@"; do
  case "$arg" in
    lock|banner|all) TARGET="$arg" ;;
    --dry-run)       DRY_RUN=1 ;;
    --no-push)       NO_PUSH=1 ;;
    -h|--help)       sed -n '2,33p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

[[ -f "$CONFIG" ]] || { echo "config not found: $CONFIG" >&2; exit 1; }

# Flip the requested flag(s) in-place via python, and report old->new per flag.
SUMMARY="$(TARGET="$TARGET" DRY_RUN="$DRY_RUN" CONFIG="$CONFIG" python3 - <<'PY'
import os, re, sys

path   = os.environ["CONFIG"]
target = os.environ["TARGET"]
dry    = os.environ["DRY_RUN"] == "1"

with open(path) as f:
    src = f.read()

# Map friendly name -> the JS block key whose `enabled:` we flip.
blocks = {"lock": "contentLock", "banner": "draftBanner"}
targets = ["lock", "banner"] if target == "all" else [target]

changes = []
for name in targets:
    key = blocks[name]
    # Find `<key>: {` then the first `enabled: true|false` after it.
    m = re.search(re.escape(key) + r"\s*:\s*\{", src)
    if not m:
        sys.stderr.write(f"could not find block '{key}' in config\n"); sys.exit(1)
    sub = re.compile(r"(enabled\s*:\s*)(true|false)")
    fm = sub.search(src, m.end())
    if not fm:
        sys.stderr.write(f"could not find 'enabled' in block '{key}'\n"); sys.exit(1)
    old = fm.group(2)
    new = "false" if old == "true" else "true"
    src = src[:fm.start()] + fm.group(1) + new + src[fm.end():]
    changes.append(f"{key}.enabled: {old} -> {new}")

if not dry:
    with open(path, "w") as f:
        f.write(src)

print("\n".join(changes))
PY
)"

echo "$SUMMARY" | sed 's/^/  /'

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "(dry run — no changes written)"
  exit 0
fi

cd "$ROOT"
git add "$CONFIG"

# Build a concise commit message from the summary lines.
MSG="Toggle config flags: $(echo "$SUMMARY" | paste -sd '; ' -)"
git commit -q -m "$MSG" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
echo "committed: $MSG"

if [[ "$NO_PUSH" -eq 1 ]]; then
  echo "(--no-push — not pushing)"
  exit 0
fi

git push -q origin main
echo "pushed to origin/main — GitHub Pages will redeploy shortly."
