import tempfile
from pathlib import Path
from app.youtube.transcript import TranscriptManager


def test_transcript_cache():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        mgr = TranscriptManager(cache_dir=tmp_path)

        vid = "test_vid_123"
        sample_text = "This is a cached transcript content for testing."

        assert mgr.is_cached(vid) is False
        mgr.save_cache(vid, sample_text)

        assert mgr.is_cached(vid) is True
        loaded = mgr.read_cached(vid)
        assert loaded == sample_text
