#!/usr/bin/env bash
# One-time setup on macOS. Run from the repo folder:  bash scripts/setup_mac.sh
set -e
cd "$(dirname "$0")/.."
REPO="$(pwd)"

if ! command -v brew >/dev/null; then
  echo "Homebrew is needed: https://brew.sh  (install it, then run this again)"; exit 1
fi
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
command -v uv >/dev/null || brew install uv
command -v python3.12 >/dev/null || brew install python@3.12

python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

PROFILE="$HOME/.zshrc"
if ! grep -q "ELEVENLABS_MCP_BASE_PATH" "$PROFILE" 2>/dev/null; then
  read -r -p "ElevenLabs API key (Enter to skip): " KEY
  {
    echo ""
    echo "# clip-factory"
    [ -n "$KEY" ] && echo "export ELEVENLABS_API_KEY=\"$KEY\""
    echo "export ELEVENLABS_MCP_BASE_PATH=\"$REPO\""
  } >> "$PROFILE"
  echo "Saved to $PROFILE. Open a new terminal so it takes effect."
fi

.venv/bin/python -m clipfactory check || true
echo ""
echo "Done. Next: add music to assets/music/<mood>/ and sound effects to assets/sfx/, then run 'claude' in this folder."
