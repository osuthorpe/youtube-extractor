import json
from transcript_manager import TranscriptManager


def _video_info(title="Example Video"):
    return {
        "title": title,
        "duration": 120,
        "uploader": "Test Channel",
    }


def _transcript(include_segments=True):
    segments = ["[00:00 - 00:05] Hello world"] if include_segments else []
    return {
        "full_text": "Hello world",
        "segments": segments,
        "language": "en",
    }


def test_save_transcript_generates_unique_metadata(tmp_path):
    manager = TranscriptManager(output_dir=tmp_path)

    manager.save_transcript(
        _video_info("First"), _transcript(), "https://youtu.be/first"
    )
    manager.save_transcript(
        _video_info("Second"), _transcript(), "https://youtu.be/second"
    )

    with open(manager.metadata_file, "r", encoding="utf-8") as handle:
        stored_metadata = json.load(handle)

    assert len(stored_metadata) == 2

    folders = {entry["folder"] for entry in stored_metadata.values()}
    assert len(folders) == 2


def test_load_metadata_recovers_from_corrupted_file(tmp_path):
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text("not-json", encoding="utf-8")

    manager = TranscriptManager(output_dir=tmp_path)

    assert manager.metadata == {}
    assert not metadata_file.exists()

    backup_file = tmp_path / "metadata.json.bak"
    assert backup_file.exists()

    manager.save_transcript(_video_info(), _transcript(), "https://youtu.be/example")
    assert manager.metadata_file.exists()

    with open(manager.metadata_file, "r", encoding="utf-8") as handle:
        stored_metadata = json.load(handle)

    assert len(stored_metadata) == 1
