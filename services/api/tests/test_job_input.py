from pathlib import Path

from app.services.job_input import job_upload_dir, save_job_input


def test_save_job_input_writes_file_with_ext(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "JOB_UPLOAD_DIR", str(tmp_path))
    path = save_job_input(b"point-bytes", ".las")
    p = Path(path)
    assert p.exists()
    assert p.suffix == ".las"
    assert p.read_bytes() == b"point-bytes"
    assert p.parent == tmp_path


def test_job_upload_dir_defaults_to_temp(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "JOB_UPLOAD_DIR", "")
    d = job_upload_dir()
    assert d.name == "carbonscan-jobs"
    assert d.exists()
