from fastapi import FastAPI
from bot import run_job_agent
import asyncio

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/run-bot")
async def run_bot():
    await run_job_agent()
    return {"status": "Bot executed"}
