from fastapi import FastAPI

app = FastAPI(
    title="Excel Sync Service",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "service": "sync-service",
        "status": "healthy",
    }
