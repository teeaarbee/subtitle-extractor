## Subtitle Extractor (ffprobe/ffmpeg)

Simple Python GUI to detect and extract SRT subtitle tracks from common video files (e.g., `.mkv`, `.mp4`, `.mov`, `.m4v`, `.webm`, `.avi`) using `ffprobe` and `ffmpeg`.

### Requirements
- macOS with Homebrew-installed `ffmpeg`/`ffprobe` (PATH usually `/opt/homebrew/bin` on Apple Silicon, `/usr/local/bin` on Intel)
- Python 3.9+

### Quick start (macOS)
1. Double-click `Run Subtitle Extractor.command` (you may need to right-click → Open the first time).
2. Choose a video file (e.g., `.mkv`, `.mp4`, `.mov`). The output folder auto-defaults to the same folder as the source. You can change it if desired. Then select the detected SRT tracks and extract.

If the command file cannot find `ffmpeg`, ensure it is installed and available on PATH.

```bash
brew install ffmpeg
```

### CLI usage (optional)
```bash
python3 -m subtitle_extractor.cli --probe /path/to/video.mkv
# Works with other formats too
python3 -m subtitle_extractor.cli --probe /path/to/video.mp4

# By default extraction outputs to the source folder if --out is omitted
python3 -m subtitle_extractor.cli --extract-all /path/to/video.mkv
```

### Development
- Run tests: `pytest -q`

### Notes
- Only SubRip (`subrip`) subtitle streams are extracted (pure `.srt`). Other subtitle codecs are ignored.
- Output filenames are derived from the source name and stream language/title.

### Remote/Network Files (NAS, etc.)
- **Important**: Extracting subtitles from remote files (over network/internet) requires reading through the entire video file since subtitles are interleaved with video data.
- **For MKV files**: The tool automatically attempts to use `mkvextract` (if available) which is more efficient for remote extraction.
  - Install mkvtoolnix: `brew install mkvtoolnix` (optional but recommended for faster network extraction)
- **Best practice**: For very slow connections, copy the video file locally first, then extract subtitles.
- **Timeouts**: Remote extraction has a 10-minute timeout (vs 2 minutes for local files).


