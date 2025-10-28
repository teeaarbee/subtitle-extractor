import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse


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


def _is_remote_file(file_path: Path) -> bool:
    """Check if the file path is a remote/network location."""
    path_str = str(file_path)
    # Check for URL schemes
    parsed = urlparse(path_str)
    if parsed.scheme in {'http', 'https', 'ftp', 'smb', 'nfs', 'afp'}:
        return True
    # Check for network paths (macOS/UNIX)
    if path_str.startswith('/Volumes/') or path_str.startswith('//'):
        return True
    # Check for SMB/CIFS paths
    if path_str.startswith('smb://') or path_str.startswith('\\\\'):
        return True
    return False


def _run_command(command: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # Make Homebrew installs discoverable
    extra_path = "/opt/homebrew/bin:/usr/local/bin"
    env["PATH"] = f"{extra_path}:{env.get('PATH','')}"
    try:
        return subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"Command timed out after {timeout} seconds.\n\n"
            f"When extracting subtitles from remote files (NAS/network), ffmpeg must read "
            f"through the entire video file since subtitles are interleaved with video data.\n\n"
            f"Solutions:\n"
            f"1. Copy the video file locally first, then extract subtitles\n"
            f"2. Use a faster network connection\n"
            f"3. Use tools like mkvextract (for MKV files) which may be more efficient"
        ) from e


def ffprobe_subtitle_streams(mkv_path: Path) -> List[SubtitleStream]:
    command = [
        "ffprobe",
        "-v",
        "error",
        # Optimize for network/remote files
        "-probesize", "50M",  # Limit initial probing data
        "-analyzeduration", "50M",  # Limit analysis duration
        "-select_streams",
        "s",
        "-show_entries",
        "stream=index,codec_name,codec_type:stream_tags=language,title",
        "-of",
        "json",
        str(mkv_path),
    ]
    # 60 second overall timeout for the entire probe operation
    result = _run_command(command, timeout=60)
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


def _try_mkvextract(
    mkv_path: Path,
    stream: SubtitleStream,
    out_path: Path,
    timeout: int = 120,
) -> bool:
    """
    Try to use mkvextract for MKV files - it's much faster for remote files.
    Returns True if successful, False if mkvextract not available or failed.
    """
    try:
        # Check if mkvextract is available
        check_cmd = ["mkvextract", "--version"]
        check_result = _run_command(check_cmd, timeout=5)
        if check_result.returncode != 0:
            return False
        
        # Use mkvextract to extract subtitle track
        command = [
            "mkvextract",
            str(mkv_path),
            "tracks",
            f"{stream.index}:{out_path}",
        ]
        result = _run_command(command, timeout=timeout)
        return result.returncode == 0
    except (RuntimeError, FileNotFoundError, subprocess.SubprocessError):
        # mkvextract not available or failed
        return False


def extract_subtitles(
    mkv_path: Path,
    streams: Iterable[SubtitleStream],
    out_dir: Path,
) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if file is remote and warn user
    is_remote = _is_remote_file(mkv_path)
    is_mkv = mkv_path.suffix.lower() in {'.mkv', '.webm'}
    
    if is_remote:
        print(f"\n⚠️  WARNING: Extracting from remote/network file: {mkv_path}")
        if is_mkv:
            print("   Attempting to use mkvextract (faster for MKV files over network)...")
        else:
            print("   This requires reading through the entire video file and may take a long time.")
            print("   For faster extraction, consider copying the file locally first.")
        print()
    
    outputs: List[Path] = []
    for stream in streams:
        if not stream.is_subrip:
            continue
        out_path = build_output_filename(mkv_path, stream, out_dir)
        
        # Use longer timeout for remote files (10 minutes), shorter for local (2 minutes)
        timeout = 600 if is_remote else 120
        
        # Try mkvextract first for MKV files (especially remote ones)
        if is_mkv and _try_mkvextract(mkv_path, stream, out_path, timeout):
            outputs.append(out_path)
            continue
        
        # Fall back to ffmpeg
        if is_mkv and is_remote:
            print(f"   mkvextract not available or failed, using ffmpeg (this will be slower)...")
        
        command = [
            "ffmpeg",
            "-y",
            # Optimize for network/remote files
            "-probesize", "50M",  # Limit initial probing data
            "-analyzeduration", "50M",  # Limit analysis duration
            "-fflags", "+fastseek",  # Enable fast seeking
            "-i",
            str(mkv_path),
            "-map",
            f"0:{stream.index}",
            "-c", "copy",  # Copy codec without re-encoding
            str(out_path),
        ]
        result = _run_command(command, timeout=timeout)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed for stream {stream.index}: {result.stderr.splitlines()[-1] if result.stderr else ''}"
            )
        outputs.append(out_path)
    return outputs


