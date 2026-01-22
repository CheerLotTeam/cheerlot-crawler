from fastapi import FastAPI

from app.routers import crawl

app = FastAPI(title="Cheerlot Crawler API")

app.include_router(crawl.router)


@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
