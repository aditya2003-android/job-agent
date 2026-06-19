from playwright.async_api import async_playwright

async def run_job_agent():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )

        page = await browser.new_page()
        await page.goto("https://example.com")

        print("Bot ran successfully")

        await browser.close()
