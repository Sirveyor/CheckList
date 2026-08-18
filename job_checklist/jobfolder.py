r"""Job-number parsing and job-folder creation on the network share.

\\192.168.16.90\Job_Folders is mapped to J: on every workstation, so we use
the drive letter rather than the UNC path.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SHARE_ROOT = Path("J:/")
LOG_PATH = SHARE_ROOT / "job_checklist_log.txt"
SUBFOLDERS = ("Fieldwork", "From Client", "Research")

_JOB_NUMBER_RE = re.compile(r"^(\d{2})-(\d+)$")


@dataclass(frozen=True)
class JobNumber:
    raw: str
    year: str
    number: str

    @property
    def parent_folder(self) -> str:
        return self.number[:2] + "0" * (len(self.number) - 2)

    @property
    def job_folder_name(self) -> str:
        return self.number


def parse_job_number(job_number: str) -> JobNumber:
    match = _JOB_NUMBER_RE.match(job_number.strip())
    if not match:
        raise ValueError(f"Job number {job_number!r} is not in the form yy-jobnumber (e.g. 26-25250)")
    year, number = match.groups()
    return JobNumber(raw=job_number.strip(), year=year, number=number)


def job_folder_path(job_number: str, share_root: Path = SHARE_ROOT) -> Path:
    jn = parse_job_number(job_number)
    return share_root / jn.parent_folder / jn.job_folder_name


def ensure_job_folder(job_number: str, share_root: Path = SHARE_ROOT) -> Path:
    """Creates the job folder and its standard subfolders if they don't exist. Returns the job folder path."""
    folder = job_folder_path(job_number, share_root)
    folder.mkdir(parents=True, exist_ok=True)
    for sub in SUBFOLDERS:
        (folder / sub).mkdir(exist_ok=True)
    return folder


def log_job(job_number: str, log_path: Path = LOG_PATH, when: datetime | None = None) -> None:
    when = when or datetime.now()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{when:%Y-%m-%d %H:%M:%S}\t{job_number}\n")
