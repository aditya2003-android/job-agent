from fastapi import FastAPI
from bot import run_job_agent

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Running"}

@app.get("/run")
async def run():
    await run_job_agent()   # ✅ MUST have await
    return {"status": "done"}
