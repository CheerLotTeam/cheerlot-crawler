from fastapi import FastAPI

app = FastAPI(title="Cheerlot Crawler API")


@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
