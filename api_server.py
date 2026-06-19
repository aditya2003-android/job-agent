from fastapi import FastAPI
from playwright.async_api import async_playwright

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Server is running"}

@app.post("/run-agent")
async def run_agent(request: Request):

    body = await request.json()

    platform = body.get("platform", "all")
    limit = body.get("limit", 20)
    dry_run = body.get("dry_run", False)

    jobs = scrape_jobs(
        platform=platform,
        limit=limit
    )

    results = []

    for job in jobs:

        result = apply_to_job(
            job=job,
            dry_run=dry_run
        )

        results.append(result)

    return {
        "status": "success",
        "jobs_processed": len(results),
        "results": results
    }
