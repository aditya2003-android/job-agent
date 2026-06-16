"""
tracker.py
──────────
Tracks all job applications in a CSV file.
Provides deduplication, daily count, and terminal summary.
"""

import csv
import os
from datetime import datetime, date
from pathlib import Path


FIELDS = [
    "date",
    "time",
    "platform",
    "company",
    "title",
    "location",
    "url",
    "status",
    "cover_letter_preview",
]


class ApplicationTracker:
    def __init__(self, filepath: str = "applications.csv"):
        self.filepath = Path(filepath)
        self._ensure_file()

    def _ensure_file(self):
        if not self.filepath.exists():
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                writer.writeheader()

    def log(
        self,
        job: dict,
        platform: str,
        status: str = "Applied",
        cover_letter: str = "",
    ):
        """Append a new application row."""
        now = datetime.now()
        row = {
            "date":                 now.strftime("%Y-%m-%d"),
            "time":                 now.strftime("%H:%M:%S"),
            "platform":             platform,
            "company":              job.get("company", ""),
            "title":                job.get("title", ""),
            "location":             job.get("location", ""),
            "url":                  job.get("url", ""),
            "status":               status,
            "cover_letter_preview": cover_letter[:120].replace("\n", " "),
        }
        with open(self.filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(row)

    def already_applied(self, company: str, title: str) -> bool:
        """Return True if we've already applied to this exact role at this company."""
        if not self.filepath.exists():
            return False
        with open(self.filepath, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (
                    row.get("company", "").lower() == company.lower()
                    and row.get("title", "").lower() == title.lower()
                    and row.get("status", "") not in ("Failed", "DRY_RUN")
                ):
                    return True
        return False

    def count_today(self) -> int:
        """Count successful applications submitted today."""
        today = date.today().isoformat()
        count = 0
        if not self.filepath.exists():
            return 0
        with open(self.filepath, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("date") == today and row.get("status") == "Applied":
                    count += 1
        return count

    def all_rows(self) -> list:
        if not self.filepath.exists():
            return []
        with open(self.filepath, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def print_summary(self):
        """Print a coloured terminal summary table."""
        rows = self.all_rows()
        if not rows:
            print("\nNo applications tracked yet.\n")
            return

        today      = date.today().isoformat()
        today_rows = [r for r in rows if r.get("date") == today]

        status_counts: dict = {}
        for r in rows:
            s = r.get("status", "Unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        platform_counts: dict = {}
        for r in today_rows:
            p = r.get("platform", "Unknown")
            platform_counts[p] = platform_counts.get(p, 0) + 1

        print("\n" + "═" * 52)
        print("  📊  Application Tracker Summary")
        print("═" * 52)
        print(f"  Total applications (all time) : {len(rows)}")
        print(f"  Applied today                 : {len(today_rows)}")
        print()
        print("  Status breakdown (all time):")
        for status, cnt in sorted(status_counts.items(), key=lambda x: -x[1]):
            bar = "█" * min(cnt, 20)
            print(f"    {status:<12} {cnt:>4}  {bar}")
        print()
        if platform_counts:
            print("  Today by platform:")
            for plat, cnt in platform_counts.items():
                print(f"    {plat:<12} {cnt:>4}")
        print()

        # Last 5 applications
        print("  Recent applications:")
        for r in rows[-5:][::-1]:
            print(f"    {r['date']}  {r['platform']:<10}  {r['company']:<22}  {r['status']}")
        print("═" * 52 + "\n")

    def export_markdown(self, outfile: str = "applications_report.md"):
        """Export full tracker as a Markdown table."""
        rows = self.all_rows()
        if not rows:
            return

        lines = [
            "# Job Application Report",
            f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
            "",
            f"**Total applications:** {len(rows)}",
            "",
            "| Date | Platform | Company | Role | Location | Status |",
            "|------|----------|---------|------|----------|--------|",
        ]
        for r in rows:
            lines.append(
                f"| {r['date']} | {r['platform']} | {r['company']} "
                f"| {r['title']} | {r['location']} | {r['status']} |"
            )

        Path(outfile).write_text("\n".join(lines), encoding="utf-8")
        print(f"Report exported → {outfile}")
