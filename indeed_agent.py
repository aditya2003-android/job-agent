"""
indeed_agent.py
───────────────
Playwright-based agent for Indeed Quick Apply.
Handles login, job search with filters, and Quick Apply form submission.
"""

import random
import time
import logging
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PWTimeout


class IndeedAgent:
    platform = "Indeed"

    def __init__(self, email: str, password: str, headless: bool = False, logger: logging.Logger = None):
        self.email    = email
        self.password = password
        self.headless = headless
        self.log      = logger or logging.getLogger("IndeedAgent")
        self._pw      = None
        self._browser: Optional[Browser] = None
        self._page:    Optional[Page]    = None

    # ── Browser lifecycle ──────────────────────────────────────────────────────

    def _start(self):
        self._pw      = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        self._page = ctx.new_page()

    def close(self):
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass

    # ── Login ──────────────────────────────────────────────────────────────────

    def login(self):
        self._start()
        page = self._page
        self.log.info("[Indeed] Logging in...")

        page.goto("https://secure.indeed.com/account/login", wait_until="domcontentloaded")
        _human_delay(1, 2)

        # Enter email
        try:
            page.fill("#ifl-InputFormField-3", self.email)
        except Exception:
            page.fill("input[type='email']", self.email)
        _human_delay(0.5, 1)

        page.click("[data-tn-element='auth-page-email-submit-button']")
        _human_delay(1, 2)

        # Enter password
        try:
            page.fill("#ifl-InputFormField-7", self.password)
        except Exception:
            page.fill("input[type='password']", self.password)
        _human_delay(0.3, 0.7)

        page.click("[data-tn-element='auth-page-sign-in-password-form-submit-button']")
        page.wait_for_load_state("domcontentloaded")
        _human_delay(2, 3)

        if "challenge" in page.url or "captcha" in page.url.lower():
            self.log.warning("[Indeed] CAPTCHA / verification detected — complete it manually, then press Enter.")
            input("Press Enter once you've passed the verification...")
            page.wait_for_load_state("domcontentloaded")

        self.log.info("[Indeed] Login successful")

    # ── Search ─────────────────────────────────────────────────────────────────

    def search_jobs(
        self,
        query: str,
        location: str,
        experience_levels: list,
        remote_pref: str,
        blacklist_keywords: list,
        blacklist_companies: list,
        max_results: int = 10,
    ) -> list:
        page = self._page
        jobs = []

        # Remote filter
        remote_params = {
            "remote_only":   "&sc=0kf%3Aattr(DSQF7)%3B",
            "remote_hybrid": "&sc=0kf%3Aattr(DSQF7)explvl(ENTRY_LEVEL)%3B",
            "all":           "",
        }
        remote_param = remote_params.get(remote_pref, "")

        # Entry-level filter
        exp_param = "&sc=0kf%3Aexplvl(ENTRY_LEVEL)%3B" if "entry" in experience_levels else ""

        url = (
            "https://www.indeed.com/jobs?"
            f"q={query.replace(' ', '+')}"
            f"&l={location.replace(' ', '+')}"
            f"&fromage=7"    # posted in last 7 days
            f"&sort=date"
            + remote_param
            + exp_param
        )

        page.goto(url, wait_until="domcontentloaded")
        _human_delay(2, 3)

        job_cards = page.query_selector_all(".job_seen_beacon, .tapItem")[:max_results]

        for card in job_cards:
            try:
                title_el   = card.query_selector(".jobTitle span, [data-testid='jobTitle']")
                company_el = card.query_selector("[data-testid='company-name'], .companyName")
                loc_el     = card.query_selector("[data-testid='text-location'], .companyLocation")
                link_el    = card.query_selector("a[id^='job_'], a.jcs-JobTitle")

                title   = title_el.inner_text().strip()   if title_el   else ""
                company = company_el.inner_text().strip() if company_el else ""
                loc     = loc_el.inner_text().strip()     if loc_el     else ""
                href    = link_el.get_attribute("href")   if link_el    else ""

                if not title or not company:
                    continue

                combined = f"{title} {company}".lower()
                if any(kw.lower() in combined for kw in blacklist_keywords):
                    continue
                if any(co.lower() in company.lower() for co in blacklist_companies):
                    continue

                # Click to get full description & check for Easy Apply
                card.click()
                _human_delay(1, 2)

                # Check for Indeed Easy Apply button
                apply_btn = page.query_selector(
                    "button[id='indeedApplyButton'], "
                    "button[data-testid='IndeedApplyButton'], "
                    ".indeedApplyButton"
                )
                if not apply_btn:
                    continue  # Skip jobs without Easy Apply

                desc_el     = page.query_selector("#jobDescriptionText")
                description = desc_el.inner_text()[:3000] if desc_el else ""

                job_id = ""
                if "jk=" in (href or ""):
                    job_id = href.split("jk=")[1].split("&")[0]

                jobs.append({
                    "id":          job_id,
                    "title":       title,
                    "company":     company,
                    "location":    loc,
                    "description": description,
                    "url":         f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else href,
                    "platform":    "Indeed",
                })

            except Exception as e:
                self.log.debug(f"  Card parse error: {e}")
                continue

        return jobs

    # ── Quick Apply ────────────────────────────────────────────────────────────

    def apply(self, job: dict, profile: dict, cover_letter: str) -> bool:
        page = self._page
        try:
            # Navigate to job and click Easy Apply
            page.goto(job["url"], wait_until="domcontentloaded")
            _human_delay(1, 2)

            apply_btn = page.query_selector(
                "button[id='indeedApplyButton'], "
                "button[data-testid='IndeedApplyButton'], "
                ".indeedApplyButton"
            )
            if not apply_btn:
                return False

            apply_btn.click()
            _human_delay(2, 3)

            # Indeed opens in an iframe — switch into it
            frame = None
            for f in page.frames:
                if "indeedapply" in f.url or "apply.indeed" in f.url:
                    frame = f
                    break

            if not frame:
                # Fallback: use main page
                frame = page

            # Walk steps (up to 10 pages)
            for step in range(10):
                _human_delay(1, 2)

                # Resume upload (if prompted and resume exists)
                file_input = frame.query_selector("input[type='file']")
                if file_input:
                    resume = profile.get("resume_path", "")
                    if resume and __import__("pathlib").Path(resume).exists():
                        file_input.set_input_files(resume)
                        _human_delay(1, 2)

                # Fill text inputs
                for inp in frame.query_selector_all("input[type='text'], input[type='tel'], input[type='email']"):
                    label  = _get_label_frame(frame, inp).lower()
                    val    = inp.input_value()
                    if val:
                        continue
                    if "name" in label and "first" in label:
                        inp.fill(profile.get("full_name", "").split()[0])
                    elif "name" in label and "last" in label:
                        parts = profile.get("full_name", "").split()
                        inp.fill(parts[-1] if len(parts) > 1 else "")
                    elif "email" in label:
                        inp.fill(profile.get("email", ""))
                    elif "phone" in label:
                        inp.fill(profile.get("phone", ""))
                    elif "city" in label or "location" in label:
                        inp.fill(profile.get("location", ""))

                # Fill textareas (cover letter / additional info)
                for ta in frame.query_selector_all("textarea"):
                    label = _get_label_frame(frame, ta).lower()
                    if not ta.input_value():
                        if any(kw in label for kw in ["cover", "additional", "message", "tell us"]):
                            ta.fill(cover_letter)
                        elif "experience" in label or "background" in label:
                            ta.fill(profile.get("summary", ""))

                # Handle yes/no radio / select for work authorization
                for sel in frame.query_selector_all("select"):
                    opts = [o.get_attribute("value") or "" for o in sel.query_selector_all("option")]
                    yes_val = next((v for v in opts if v.lower() in ("yes", "true", "1")), None)
                    if yes_val:
                        sel.select_option(value=yes_val)

                # Radios: prefer Yes
                for radio in frame.query_selector_all("input[type='radio']"):
                    val = (radio.get_attribute("value") or "").lower()
                    if val in ("yes", "true"):
                        radio.check()

                _human_delay(0.5, 1)

                # Find and click next/submit button
                clicked = False
                for btn_text in ["Continue", "Next", "Review your application", "Submit your application", "Apply now"]:
                    btn = frame.query_selector(f"button:has-text('{btn_text}')")
                    if btn and btn.is_enabled():
                        btn.click()
                        _human_delay(1.5, 2.5)
                        clicked = True
                        break

                if not clicked:
                    break

                # Check for confirmation
                body_text = frame.inner_text("body").lower() if frame.query_selector("body") else ""
                if any(kw in body_text for kw in ["application submitted", "application sent", "you applied", "successfully applied"]):
                    return True

            return True

        except PWTimeout:
            self.log.debug("  Timeout during Indeed Apply")
            return False
        except Exception as e:
            self.log.debug(f"  Apply error: {e}")
            return False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _human_delay(lo: float = 1, hi: float = 3):
    time.sleep(random.uniform(lo, hi))


def _get_label_frame(frame, element) -> str:
    """Try to find associated label text for a form element within a frame."""
    try:
        el_id = element.get_attribute("id")
        if el_id:
            label = frame.query_selector(f"label[for='{el_id}']")
            if label:
                return label.inner_text()
        return (
            element.get_attribute("aria-label")
            or element.get_attribute("placeholder")
            or ""
        )
    except Exception:
        return ""
