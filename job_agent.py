import json
import os
import asyncio
from anthropic_helper import generate_cover_letter, score_job_match
from tracker import ApplicationTracker

tracker = ApplicationTracker()


async def run_agent():
    with open("config.json") as f:
        config = json.load(f)

    profile = config["profile"]
    settings = config["agent_settings"]

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    print("Starting job agent...\n")

    # SAMPLE JOB (replace with LinkedIn scraper later)
    jobs = [
        {
            "title": "Data Scientist Intern",
            "company": "Google",
            "location": "Remote",
            "description": "Python, ML, data analysis",
            "url": "https://example.com"
        }
    ]

    applied = 0

    for job in jobs:
        if tracker.already_applied(job["company"], job["title"]):
            continue

        score = score_job_match(api_key, profile, job)

        if score < 50:
            continue

        cover = generate_cover_letter(api_key, profile, job)

        print(f"Applying to {job['company']} - {job['title']}")
        print(cover[:100], "\n")

        tracker.log(job, "demo", "Applied", cover)
        applied += 1

    print(f"\nApplied to {applied} jobs")
