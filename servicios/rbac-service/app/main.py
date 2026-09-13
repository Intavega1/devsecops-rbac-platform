from fastapi import FastAPI

app = FastAPI(
    title="RBAC Service",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "service": "rbac-service",
        "status": "healthy",
    }
