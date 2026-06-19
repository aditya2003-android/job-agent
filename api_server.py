from fastapi import FastAPI
import subprocess

app = FastAPI()


@app.get("/")
def home():
    return {"status": "running"}


@app.get("/run")
def run_agent():
    subprocess.Popen(["python3", "job_agent.py"])
    return {"status": "started"}
