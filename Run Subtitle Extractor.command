#!/bin/zsh

# Make Homebrew ffmpeg visible
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer venv in repo if exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Launch GUI
python3 -m subtitle_extractor.gui

exit 0


