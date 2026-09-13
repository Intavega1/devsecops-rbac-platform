from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI(
    title="DevSecOps RBAC API Gateway",
    version="0.2.0",
)

SERVICES = {
    "identity": "http://identity-service:8000",
    "rbac": "http://rbac-service:8000",
    "sync": "http://sync-service:8000",
    "audit": "http://audit-service:8000",
}


@app.get("/health")
def health():
    return {
        "service": "api-gateway",
        "status": "healthy",
    }


@app.get("/api/{service}/health")
async def service_health(service: str):
    if service not in SERVICES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service: {service}",
        )

    url = f"{SERVICES[service]}/health"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)

        return {
            "gateway": "healthy",
            "service": service,
            "service_status": response.json(),
        }

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Service unavailable: {service}",
        ) from exc
