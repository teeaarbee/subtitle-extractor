## Subtitle Extractor (ffprobe/ffmpeg)

Simple Python GUI to detect and extract SRT subtitle tracks from `.mkv` files using `ffprobe` and `ffmpeg`.

### Requirements
- macOS with Homebrew-installed `ffmpeg`/`ffprobe` (PATH usually `/opt/homebrew/bin` on Apple Silicon, `/usr/local/bin` on Intel)
- Python 3.9+

### Quick start (macOS)
1. Double-click `Run Subtitle Extractor.command` (you may need to right-click → Open the first time).
2. Choose an `.mkv` file. The output folder auto-defaults to the same folder as the MKV (import folder). You can change it if desired. Then select the detected SRT tracks and extract.

If the command file cannot find `ffmpeg`, ensure it is installed and available on PATH.

```bash
brew install ffmpeg
```

### CLI usage (optional)
```bash
python3 -m subtitle_extractor.cli --probe /path/to/video.mkv
# By default extraction outputs to the MKV's folder if --out is omitted
python3 -m subtitle_extractor.cli --extract-all /path/to/video.mkv
```

### Development
- Run tests: `pytest -q`

### Notes
- Only SubRip (`subrip`) subtitle streams are extracted (pure `.srt`).
- Output filenames are derived from the source name and stream language/title.


