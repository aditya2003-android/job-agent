from playwright.async_api import async_playwright

async def run_job_agent():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )

            context = await browser.new_context()
            page = await context.new_page()

            await page.goto("https://example.com", timeout=60000)

            print("✅ Bot ran successfully")

            await browser.close()

    except Exception as e:
        print("❌ BOT ERROR:", str(e))
        raise e
