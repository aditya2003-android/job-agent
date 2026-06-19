import asyncio
from playwright.async_api import async_playwright

LINKEDIN_EMAIL = "your_email"
LINKEDIN_PASSWORD = "your_password"

JOB_URL = "https://www.linkedin.com/jobs/search/?keywords=python"

async def run_bot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        context = await browser.new_context()
        page = await context.new_page()

        # LOGIN
        await page.goto("https://www.linkedin.com/login")

        await page.fill("#username", LINKEDIN_EMAIL)
        await page.fill("#password", LINKEDIN_PASSWORD)

        await page.click("button[type='submit']")
        await page.wait_for_timeout(5000)

        # GO TO JOBS
        await page.goto(JOB_URL)
        await page.wait_for_timeout(5000)

        jobs = page.locator(".jobs-search-results__list-item")

        count = await jobs.count()

        applied = 0

        for i in range(count):
            job = jobs.nth(i)

            try:
                await job.scroll_into_view_if_needed()
                await job.click()
                await page.wait_for_timeout(3000)

                # EASY APPLY BUTTON
                apply_btn = page.locator("button:has-text('Easy Apply')")

                if await apply_btn.count() == 0:
                    continue

                await apply_btn.scroll_into_view_if_needed()
                await apply_btn.click()
                await page.wait_for_timeout(2000)

                # SUBMIT BUTTON
                submit_btn = page.locator("button:has-text('Submit application')")

                if await submit_btn.count() > 0:
                    await submit_btn.scroll_into_view_if_needed()
                    await submit_btn.click()
                    applied += 1
                    await page.wait_for_timeout(2000)

                # CLOSE MODAL
                close_btn = page.locator("button[aria-label='Dismiss']")
                if await close_btn.count() > 0:
                    await close_btn.click()

            except Exception as e:
                print("Error applying:", e)
                continue

        await browser.close()
        return f"Applied to {applied} jobs"
