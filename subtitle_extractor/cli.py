from pathlib import Path
import argparse
from typing import List

from .ffutils import ffprobe_subtitle_streams, extract_subtitles


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect and extract SRT subtitles from MKV")
    parser.add_argument("mkv", nargs="?", help="Path to MKV file")
    parser.add_argument("--probe", action="store_true", help="Only print detected subtitle streams")
    parser.add_argument("--extract-all", action="store_true", help="Extract all SRT subtitle streams")
    parser.add_argument("--out", default=None, help="Output directory (defaults to MKV directory)")
    args = parser.parse_args()

    if not args.mkv:
        parser.error("Please provide path to MKV file")

    mkv_path = Path(args.mkv)
    streams = ffprobe_subtitle_streams(mkv_path)

    if args.probe or not args.extract_all:
        for s in streams:
            print(f"index={s.index}\tcodec={s.codec_name}\tlanguage={s.language}\ttitle={s.title}")
        if args.probe:
            return

    out_dir = Path(args.out) if args.out else mkv_path.parent
    outputs = extract_subtitles(mkv_path, [s for s in streams if s.is_subrip], out_dir)
    for p in outputs:
        print(p)


if __name__ == "__main__":
    main()


