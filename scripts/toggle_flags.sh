#!/usr/bin/env bash
#
# toggle_flags.sh — flip the content-lock flag in src/config.js, then commit & push.
#
# Flips `enabled: true` <-> `enabled: false` for the content lock,
# then commits the change to main and pushes (the repo is the live GitHub Pages site).
#
#   contentLock.enabled  — hides the deck behind a countdown until showAtUTC
#
# Usage:
#   ./scripts/toggle_flags.sh             # flip contentLock.enabled
#
# Options:
#   --dry-run     show the change but don't write, commit, or push
#   --no-push     commit but don't push
#   -h, --help    this help
#
# "Go live" = flag false (deck visible).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/src/config.js"

TARGET="lock"
DRY_RUN=0
NO_PUSH=0

for arg in "$@"; do
  case "$arg" in
    --dry-run)       DRY_RUN=1 ;;
    --no-push)       NO_PUSH=1 ;;
    -h|--help)       sed -n '2,29p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

[[ -f "$CONFIG" ]] || { echo "config not found: $CONFIG" >&2; exit 1; }

# Flip the requested flag(s) in-place via python, and report old->new per flag.
SUMMARY="$(TARGET="$TARGET" DRY_RUN="$DRY_RUN" CONFIG="$CONFIG" python3 - <<'PY'
import os, re, sys, json

path   = os.environ["CONFIG"]
target = os.environ["TARGET"]
dry    = os.environ["DRY_RUN"] == "1"
flag_json = os.path.join(os.path.dirname(os.path.dirname(path)), "flag.json")

with open(path) as f:
    src = f.read()

changes = []   # plain-English lines shown on screen
commit = []    # technical lines used for the commit message

key = "contentLock"
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
commit.append(f"{key}.enabled: {old} -> {new}")

state = "ON  — deck is hidden behind the countdown" if new == "true" \
        else "OFF — deck is visible to everyone"
changes.append(f"Content lock is now {state}")

if not dry:
    with open(path, "w") as f:
        f.write(src)
    # Keep flag.json (the static read-only API endpoint) in sync with config.js.
    sm = re.search(r"showAtUTC\s*:\s*[\"']([^\"']*)[\"']", src)
    flag = {"contentLock": {"enabled": new == "true",
                            "showAtUTC": sm.group(1) if sm else None}}
    with open(flag_json, "w") as f:
        json.dump(flag, f, indent=2)
        f.write("\n")

# Two blocks separated by a blank line: display lines, then commit lines.
print("\n".join(changes))
print()
print("\n".join(commit))
PY
)"

DISPLAY="$(printf '%s' "$SUMMARY" | sed '/^$/q' | sed '/^$/d')"
COMMIT_LINES="$(printf '%s' "$SUMMARY" | sed '1,/^$/d')"

echo "$DISPLAY" | sed 's/^/  /'

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "(dry run — no changes written)"
  exit 0
fi

cd "$ROOT"
git add "$CONFIG" "$ROOT/flag.json"

# Build a concise commit message from the technical summary lines (unchanged format).
MSG="Toggle config flags: $(echo "$COMMIT_LINES" | paste -sd '; ' -)"
git commit -q -m "$MSG" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
echo "committed: $MSG"

if [[ "$NO_PUSH" -eq 1 ]]; then
  echo "(--no-push — not pushing)"
  exit 0
fi

git push -q origin main
echo "pushed to origin/main — GitHub Pages will redeploy shortly."
