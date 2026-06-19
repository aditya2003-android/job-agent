from fastapi import FastAPI
from bot import run_job_agent
import traceback

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Job Agent Running"}

@app.get("/run")
async def run():
    try:
        await run_job_agent()
        return {"status": "success"}
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }
