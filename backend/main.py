from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()
FRONTEND_INDEX = Path(__file__).resolve().parent.parent / "frontend" / "index.html"


@app.get("/")
async def home():
    return FileResponse(FRONTEND_INDEX)