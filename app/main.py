from fastapi import FastAPI
from app.routers import scraper
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(title="Web Scraper API", version="1.0.0")

app.include_router(scraper.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

