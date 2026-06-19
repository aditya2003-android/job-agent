from fastapi import FastAPI
from bot import run_job_agent

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Server is running"}

@app.post("/run-agent")   # ✅ FIXED (match Railway request)
async def run_agent():
    try:
        await run_job_agent()
        return {"status": "Bot ran successfully"}
    except Exception as e:
        return {"error": str(e)}
