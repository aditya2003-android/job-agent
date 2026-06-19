import csv
from datetime import datetime, date
from pathlib import Path

FIELDS = [
    "date", "time", "platform", "company",
    "title", "location", "url", "status",
    "cover_letter_preview"
]


class ApplicationTracker:
    def __init__(self, filepath="applications.csv"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _ensure(self):
        if not self.filepath.exists():
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writeheader()

    def log(self, job, platform, status="Applied", cover_letter=""):
        now = datetime.now()

        row = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "platform": platform,
            "company": job.get("company", "").strip(),
            "title": job.get("title", "").strip(),
            "location": job.get("location", "").strip(),
            "url": job.get("url", "").strip(),
            "status": status,
            "cover_letter_preview": cover_letter[:100],
        }

        with open(self.filepath, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow(row)

    def already_applied(self, company, title):
        if not self.filepath.exists():
            return False

        with open(self.filepath, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if (
                    r["company"].strip().lower() == company.strip().lower()
                    and r["title"].strip().lower() == title.strip().lower()
                ):
                    return True
        return False
