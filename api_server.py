from fastapi import FastAPI
from playwright.async_api import async_playwright

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Server is running"}

@app.post("/run-agent")
async def run_agent():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process"
            ]
        )

        page = await browser.new_page()
        await page.goto("https://example.com")

        title = await page.title()

        await browser.close()

    return {"status": "success", "title": title}
