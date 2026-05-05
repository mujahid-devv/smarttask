from fastapi import FastAPI

from app.api import auth, users

app = FastAPI(
    title="SmartTask API",
    version="0.1.0",
)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/")
async def root():
    return {"message": "SmartTask API is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
