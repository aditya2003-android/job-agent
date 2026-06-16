"""
linkedin_agent.py
─────────────────
Playwright-based agent for LinkedIn Easy Apply.
Handles login, job search, and multi-step Easy Apply forms.
"""

import random
import time
import logging
from typing import Optional

from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PWTimeout


class LinkedInAgent:
    platform = "LinkedIn"

    def __init__(self, email: str, password: str, headless: bool = False, logger: logging.Logger = None):
        self.email    = email
        self.password = password
        self.headless = headless
        self.log      = logger or logging.getLogger("LinkedInAgent")
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
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
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
        self.log.info("[LinkedIn] Logging in...")

        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        _human_delay(1, 2)

        page.fill("#username", self.email)
        _human_delay(0.3, 0.7)
        page.fill("#password", self.password)
        _human_delay(0.3, 0.7)
        page.click("[data-litms-control-urn='login-submit']")
        page.wait_for_load_state("domcontentloaded")
        _human_delay(2, 4)

        if "checkpoint" in page.url or "challenge" in page.url:
            self.log.warning("[LinkedIn] 2FA / captcha detected — complete it in the browser window, then press Enter here.")
            input("Press Enter once you've passed the verification...")
            page.wait_for_load_state("domcontentloaded")

        self.log.info("[LinkedIn] Login successful")

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
        page  = self._page
        jobs  = []

        # Build experience filter codes  (1=internship, 2=entry)
        exp_map  = {"internship": "1", "entry": "2"}
        exp_code = ",".join(exp_map[e] for e in experience_levels if e in exp_map)

        # Remote filter  (1=on-site, 2=remote, 3=hybrid)
        remote_map  = {"remote_only": "2", "remote_hybrid": "2,3", "all": "1,2,3"}
        remote_code = remote_map.get(remote_pref, "1,2,3")

        url = (
            "https://www.linkedin.com/jobs/search/?"
            f"keywords={query.replace(' ', '%20')}"
            f"&location={location.replace(' ', '%20')}"
            f"&f_AL=true"           # Easy Apply only
            f"&f_E={exp_code}"
            f"&f_WT={remote_code}"
            f"&sortBy=DD"           # Most recent first
        )

        page.goto(url, wait_until="domcontentloaded")
        _human_delay(2, 3)

        job_cards = page.query_selector_all(".job-card-container")[:max_results]

        for card in job_cards:
            try:
                title_el   = card.query_selector(".job-card-list__title")
                company_el = card.query_selector(".job-card-container__primary-description")
                loc_el     = card.query_selector(".job-card-container__metadata-item")
                link_el    = card.query_selector("a.job-card-list__title")

                title   = title_el.inner_text().strip()   if title_el   else ""
                company = company_el.inner_text().strip() if company_el else ""
                loc     = loc_el.inner_text().strip()     if loc_el     else ""
                href    = link_el.get_attribute("href")   if link_el    else ""
                job_id  = href.split("/jobs/view/")[1].split("/")[0] if "/jobs/view/" in (href or "") else ""

                # Blacklist filter
                combined = f"{title} {company}".lower()
                if any(kw.lower() in combined for kw in blacklist_keywords):
                    continue
                if any(co.lower() in company.lower() for co in blacklist_companies):
                    continue

                # Get description (click card)
                card.click()
                _human_delay(1, 2)
                desc_el = page.query_selector(".jobs-description__content")
                description = desc_el.inner_text().strip()[:3000] if desc_el else ""

                jobs.append({
                    "id":          job_id,
                    "title":       title,
                    "company":     company,
                    "location":    loc,
                    "description": description,
                    "url":         f"https://www.linkedin.com/jobs/view/{job_id}/",
                    "platform":    "LinkedIn",
                })

            except Exception as e:
                self.log.debug(f"  Card parse error: {e}")
                continue

        return jobs

    # ── Easy Apply ─────────────────────────────────────────────────────────────

    def apply(self, job: dict, profile: dict, cover_letter: str) -> bool:
        page = self._page
        try:
            page.goto(job["url"], wait_until="domcontentloaded")
            _human_delay(1, 2)

            # Click Easy Apply button
            easy_btn = page.query_selector(".jobs-apply-button--top-card")
            if not easy_btn:
                self.log.debug("  No Easy Apply button found")
                return False
            easy_btn.click()
            _human_delay(1, 2)

            # Walk through the modal steps (up to 8 pages)
            for step in range(8):
                # Fill phone if empty
                phone_input = page.query_selector("input[id*='phoneNumber']")
                if phone_input and not phone_input.input_value():
                    phone_input.fill(profile.get("phone", ""))

                # Fill cover letter / additional text areas
                textareas = page.query_selector_all("textarea")
                for ta in textareas:
                    label = _get_label(page, ta)
                    if any(kw in label.lower() for kw in ["cover", "additional", "message", "motivation"]):
                        if not ta.input_value():
                            ta.fill(cover_letter)
                    elif "linkedin" in label.lower():
                        if not ta.input_value():
                            ta.fill(profile.get("linkedin_url", ""))

                # Fill text inputs by label
                inputs = page.query_selector_all("input[type='text'], input[type='number']")
                for inp in inputs:
                    label = _get_label(page, inp).lower()
                    val   = inp.input_value()
                    if val:
                        continue
                    if "city" in label or "location" in label:
                        inp.fill(profile.get("location", ""))
                    elif "github" in label:
                        inp.fill(profile.get("github_url", ""))
                    elif "portfolio" in label or "website" in label:
                        inp.fill(profile.get("portfolio_url", "") or profile.get("github_url", ""))
                    elif "gpa" in label or "grade" in label:
                        inp.fill(profile.get("gpa", ""))
                    elif "year" in label and "graduation" in label:
                        inp.fill(profile.get("graduation_year", ""))

                # Select yes/no dropdowns (default yes for work authorization etc.)
                selects = page.query_selector_all("select")
                for sel in selects:
                    label = _get_label(page, sel).lower()
                    opts  = sel.query_selector_all("option")
                    opt_vals = [o.get_attribute("value") or "" for o in opts]
                    if any(v.lower() in ("yes", "true") for v in opt_vals):
                        sel.select_option(value=next(
                            v for v in opt_vals if v.lower() in ("yes", "true")
                        ))

                _human_delay(0.5, 1.2)

                # Look for Next / Review / Submit button
                for btn_text in ["Next", "Review", "Submit application"]:
                    btn = page.query_selector(f"button[aria-label='{btn_text}']")
                    if not btn:
                        btn = page.query_selector(f"button:has-text('{btn_text}')")
                    if btn:
                        btn.click()
                        _human_delay(1, 2)
                        break
                else:
                    # No recognised button — modal likely closed or error
                    break

                # Check if modal closed (application submitted)
                if not page.query_selector(".jobs-easy-apply-modal"):
                    self.log.debug("  Modal closed — application submitted")
                    return True

            # Final close of any confirmation modal
            close_btn = page.query_selector("button[aria-label='Dismiss']")
            if close_btn:
                close_btn.click()

            return True

        except PWTimeout:
            self.log.debug("  Timeout during Easy Apply")
            return False
        except Exception as e:
            self.log.debug(f"  Apply error: {e}")
            return False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _human_delay(lo: float = 1, hi: float = 3):
    time.sleep(random.uniform(lo, hi))


def _get_label(page: Page, element) -> str:
    """Try to find the associated label text for a form element."""
    try:
        el_id = element.get_attribute("id")
        if el_id:
            label = page.query_selector(f"label[for='{el_id}']")
            if label:
                return label.inner_text()
        # Fallback: aria-label or placeholder
        return (
            element.get_attribute("aria-label")
            or element.get_attribute("placeholder")
            or ""
        )
    except Exception:
        return ""
