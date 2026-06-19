import asyncio
from playwright.async_api import async_playwright

INDEED_EMAIL = "your_email"
INDEED_PASSWORD = "your_password"

JOB_URL = "https://www.indeed.com/jobs?q=python+developer"

async def safe_click(locator):
    try:
        await locator.scroll_into_view_if_needed()
        await locator.wait_for(state="visible", timeout=5000)
        await locator.click()
        return True
    except:
        return False


async def run_bot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        context = await browser.new_context()
        page = await context.new_page()

        # OPEN INDEED
        await page.goto(JOB_URL)
        await page.wait_for_timeout(5000)

        jobs = page.locator(".job_seen_beacon")

        count = await jobs.count()
        applied = 0

        for i in range(count):
            job = jobs.nth(i)

            try:
                await job.scroll_into_view_if_needed()
                await job.click()
                await page.wait_for_timeout(3000)

                # APPLY BUTTON
                apply_btn = page.locator("text=Apply Now")

                if await apply_btn.count() == 0:
                    continue

                clicked = await safe_click(apply_btn)
                if not clicked:
                    continue

                await page.wait_for_timeout(3000)

                # HANDLE NEW TAB (Indeed opens apply page sometimes)
                pages = context.pages
                if len(pages) > 1:
                    apply_page = pages[-1]
                else:
                    apply_page = page

                await apply_page.wait_for_timeout(2000)

                # TRY SUBMIT
                submit_btn = apply_page.locator("button:has-text('Submit')")

                if await submit_btn.count() > 0:
                    await safe_click(submit_btn)
                    applied += 1
                    await apply_page.wait_for_timeout(2000)

                # CLOSE TAB IF NEW
                if apply_page != page:
                    await apply_page.close()

            except Exception as e:
                print("Error:", e)
                continue

        await browser.close()
        return f"Applied to {applied} jobs"
