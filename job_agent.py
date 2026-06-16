"""
AI Job Application Agent
========================
Automates job applications on LinkedIn (Easy Apply) and Indeed (Quick Apply)
with AI-powered cover letter generation via the Anthropic API.

Usage:
    python job_agent.py                          # Run with config.json defaults
    python job_agent.py --limit 10               # Cap at 10 applications
    python job_agent.py --platform linkedin      # LinkedIn only
    python job_agent.py --platform indeed        # Indeed only
    python job_agent.py --dry-run                # Preview without submitting
"""

import argparse
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path

from anthropic_helper import generate_cover_letter
from linkedin_agent import LinkedInAgent
from indeed_agent import IndeedAgent
from tracker import ApplicationTracker

# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging(log_file: str) -> logging.Logger:
    logger = logging.getLogger("JobAgent")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", "%H:%M:%S")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = logging.FileHandler(log_file)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# ── Config loader ──────────────────────────────────────────────────────────────

def load_config(path: str = "config.json") -> dict:
    with open(path, "r") as f:
        cfg = json.load(f)
    key = cfg["agent_settings"].get("anthropic_api_key", "")
    if not key or key == "YOUR_ANTHROPIC_API_KEY_HERE":
        raise ValueError(
            "Set your Anthropic API key in config.json → agent_settings.anthropic_api_key\n"
            "Get one at: https://console.anthropic.com"
        )
    return cfg


# ── Human-like delay ───────────────────────────────────────────────────────────

def human_delay(lo: float = 2, hi: float = 5):
    time.sleep(random.uniform(lo, hi))


# ── Main orchestrator ──────────────────────────────────────────────────────────

def run_agent(
    config: dict,
    platform: str = "all",
    limit: int = None,
    dry_run: bool = False,
    logger: logging.Logger = None,
):
    profile   = config["profile"]
    search    = config["job_search"]
    settings  = config["agent_settings"]
    creds     = config["credentials"]

    cap = limit or settings["max_applications_per_day"]
    tracker = ApplicationTracker(settings["tracker_file"])
    applied_today = tracker.count_today()

    logger.info(f"=== Job Agent Started — cap: {cap}/day, platform: {platform}, dry-run: {dry_run} ===")
    logger.info(f"Applications already submitted today: {applied_today}")

    remaining = cap - applied_today
    if remaining <= 0:
        logger.info("Daily limit reached. Come back tomorrow!")
        return

    total_applied = 0
    agents = []

    if platform in ("all", "linkedin"):
        agents.append(
            LinkedInAgent(
                email=creds["linkedin"]["email"],
                password=creds["linkedin"]["password"],
                headless=settings["headless"],
                logger=logger,
            )
        )

    if platform in ("all", "indeed"):
        agents.append(
            IndeedAgent(
                email=creds["indeed"]["email"],
                password=creds["indeed"]["password"],
                headless=settings["headless"],
                logger=logger,
            )
        )

    for agent in agents:
        if total_applied >= remaining:
            break

        try:
            agent.login()
            human_delay(2, 4)

            for role in search["roles"]:
                if total_applied >= remaining:
                    break

                for location in search["locations"]:
                    if total_applied >= remaining:
                        break

                    logger.info(f"[{agent.platform}] Searching: '{role}' in '{location}'")

                    jobs = agent.search_jobs(
                        query=role,
                        location=location,
                        experience_levels=search["experience_levels"],
                        remote_pref=search["remote_preference"],
                        blacklist_keywords=search["blacklisted_keywords"],
                        blacklist_companies=search["blacklisted_companies"],
                    )

                    logger.info(f"  Found {len(jobs)} eligible jobs")

                    for job in jobs:
                        if total_applied >= remaining:
                            break

                        # Skip already-applied jobs
                        if tracker.already_applied(job["company"], job["title"]):
                            logger.info(f"  Skip (already applied): {job['title']} @ {job['company']}")
                            continue

                        # AI cover letter
                        logger.info(f"  Generating cover letter for: {job['title']} @ {job['company']}")
                        cover_letter = generate_cover_letter(
                            api_key=settings["anthropic_api_key"],
                            profile=profile,
                            job=job,
                        )

                        if dry_run:
                            logger.info(f"  [DRY RUN] Would apply: {job['title']} @ {job['company']}")
                            logger.info(f"  Cover letter preview: {cover_letter[:120]}...")
                            tracker.log(job, agent.platform, status="DRY_RUN")
                            total_applied += 1
                            continue

                        # Submit
                        success = agent.apply(
                            job=job,
                            profile=profile,
                            cover_letter=cover_letter,
                        )

                        status = "Applied" if success else "Failed"
                        tracker.log(job, agent.platform, status=status, cover_letter=cover_letter)

                        if success:
                            total_applied += 1
                            logger.info(f"  ✓ Applied ({total_applied}/{remaining}): {job['title']} @ {job['company']}")
                        else:
                            logger.warning(f"  ✗ Failed: {job['title']} @ {job['company']}")

                        lo, hi = settings["delay_between_applications_seconds"]
                        human_delay(lo, hi)

                    human_delay(*settings["delay_between_searches_seconds"])

        except Exception as e:
            logger.error(f"[{agent.platform}] Error: {e}", exc_info=True)
        finally:
            agent.close()

    logger.info(f"=== Session complete. Applied to {total_applied} jobs. ===")
    tracker.print_summary()


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Job Application Agent")
    parser.add_argument("--config",   default="config.json",   help="Path to config file")
    parser.add_argument("--platform", default="all",            choices=["all", "linkedin", "indeed"])
    parser.add_argument("--limit",    type=int,  default=None,  help="Max applications this session")
    parser.add_argument("--dry-run",  action="store_true",      help="Preview without submitting")
    args = parser.parse_args()

    config = load_config(args.config)
    logger = setup_logging(config["agent_settings"]["log_file"])

    run_agent(
        config=config,
        platform=args.platform,
        limit=args.limit,
        dry_run=args.dry_run,
        logger=logger,
    )


if __name__ == "__main__":
    main()
