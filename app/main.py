from fastapi import FastAPI

app = FastAPI(
    title="SmartTask API",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "SmartTask API is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
