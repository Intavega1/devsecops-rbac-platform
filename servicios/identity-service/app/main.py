from fastapi import FastAPI

app = FastAPI(
    title="Identity Service",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "service": "identity-service",
        "status": "healthy",
    }
