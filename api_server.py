from fastapi import FastAPI
from bot import run_job_agent

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Job Agent Running"}

@app.get("/run")
async def run():
    await run_job_agent()
    return {"status": "Job agent executed successfully"}
