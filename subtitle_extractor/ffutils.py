import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class SubtitleStream:
    index: int
    codec_name: str
    language: Optional[str]
    title: Optional[str]

    @property
    def is_subrip(self) -> bool:
        return self.codec_name.lower() in {"subrip", "srt"}

    def display_label(self) -> str:
        parts: List[str] = []
        if self.language:
            parts.append(self.language)
        if self.title:
            parts.append(self.title)
        label = " - ".join(parts) if parts else f"stream {self.index}"
        return f"#{self.index} ({self.codec_name}) - {label}"


def _run_command(command: List[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # Make Homebrew installs discoverable
    extra_path = "/opt/homebrew/bin:/usr/local/bin"
    env["PATH"] = f"{extra_path}:{env.get('PATH','')}"
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
        text=True,
    )


def ffprobe_subtitle_streams(mkv_path: Path) -> List[SubtitleStream]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index,codec_name,codec_type:stream_tags=language,title",
        "-of",
        "json",
        str(mkv_path),
    ]
    result = _run_command(command)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")
    data = json.loads(result.stdout or "{}")
    streams = []
    for s in data.get("streams", []):
        tags = s.get("tags", {}) or {}
        streams.append(
            SubtitleStream(
                index=int(s["index"]),
                codec_name=str(s.get("codec_name", "")),
                language=tags.get("language"),
                title=tags.get("title"),
            )
        )
    return streams


def build_output_filename(source: Path, stream: SubtitleStream, out_dir: Path) -> Path:
    base = source.stem
    lang = (stream.language or "und").replace(" ", "_")
    title = (stream.title or "").strip().replace(" ", "_")
    parts = [base, lang]
    if title:
        parts.append(title)
    parts.append(f"s{stream.index}")
    filename = ".".join([p for p in parts if p]) + ".srt"
    return out_dir / filename


def extract_subtitles(
    mkv_path: Path,
    streams: Iterable[SubtitleStream],
    out_dir: Path,
) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    for stream in streams:
        if not stream.is_subrip:
            continue
        out_path = build_output_filename(mkv_path, stream, out_dir)
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(mkv_path),
            "-map",
            f"0:{stream.index}",
            str(out_path),
        ]
        result = _run_command(command)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed for stream {stream.index}: {result.stderr.splitlines()[-1] if result.stderr else ''}"
            )
        outputs.append(out_path)
    return outputs


