from fastapi import FastAPI

app = FastAPI(
    title="DevSecOps RBAC API Gateway",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "service": "api-gateway",
        "status": "healthy",
    }
