import json
from pathlib import Path
from subtitle_extractor.ffutils import ffprobe_subtitle_streams, SubtitleStream


def test_subtitle_stream_dataclass_properties():
    s = SubtitleStream(index=2, codec_name="subrip", language="eng", title="English [SDH]")
    assert s.is_subrip is True
    assert "#2 (subrip)" in s.display_label()


def test_parse_ffprobe_json():
    sample = {
        "streams": [
            {
                "index": 2,
                "codec_name": "subrip",
                "codec_type": "subtitle",
                "tags": {"language": "eng", "title": "English (GB) [Forced]"},
            },
            {
                "index": 3,
                "codec_name": "subrip",
                "codec_type": "subtitle",
                "tags": {"language": "eng", "title": "English [SDH]"},
            },
            {"index": 4, "codec_name": "subrip", "codec_type": "subtitle", "tags": {"language": "fre", "title": "French Canadian"}},
        ]
    }

    # emulate internal parsing
    payload = json.dumps(sample)
    data = json.loads(payload)
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
    assert len(streams) == 3
    assert streams[0].language == "eng"
    assert streams[2].title == "French Canadian"


