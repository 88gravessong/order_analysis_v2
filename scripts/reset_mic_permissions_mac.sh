#!/usr/bin/env bash
set -euo pipefail

# Reset macOS Microphone permission for PlayCover (targeted),
# or for all apps with --all.

echo "[reset-mic] Starting..."

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[reset-mic] This script is for macOS only." >&2
  exit 1
fi

if ! command -v tccutil >/dev/null 2>&1; then
  echo "[reset-mic] 'tccutil' not found. This tool exists on macOS 10.14+." >&2
  exit 1
fi

RESET_ALL=false
if [[ ${1-} == "--all" ]]; then
  RESET_ALL=true
fi

if $RESET_ALL; then
  echo "[reset-mic] Resetting Microphone permission for ALL apps..."
  tccutil reset Microphone
  echo "[reset-mic] Done. Relaunch PlayCover and the game, then allow when prompted."
  exit 0
fi

# Try to get PlayCover bundle id via AppleScript first
BUNDLE_ID=""
if command -v osascript >/dev/null 2>&1; then
  BUNDLE_ID=$(osascript -e 'id of app "PlayCover"' 2>/dev/null || true)
fi

# Fallback: mdls on /Applications/PlayCover.app
if [[ -z "$BUNDLE_ID" && -d "/Applications/PlayCover.app" ]]; then
  BUNDLE_ID=$(mdls -name kMDItemCFBundleIdentifier -r "/Applications/PlayCover.app" 2>/dev/null || true)
fi

if [[ -z "$BUNDLE_ID" ]]; then
  echo "[reset-mic] Could not auto-detect PlayCover bundle id."
  echo "[reset-mic] You can run a global reset: 'tccutil reset Microphone'"
  echo "[reset-mic] Or specify bundle id manually: 'tccutil reset Microphone <bundle-id>'"
  exit 2
fi

echo "[reset-mic] Detected PlayCover bundle id: $BUNDLE_ID"
echo "[reset-mic] Resetting Microphone permission for PlayCover only..."
tccutil reset Microphone "$BUNDLE_ID"
echo "[reset-mic] Done. Quit and relaunch PlayCover and the game, then allow when prompted."

