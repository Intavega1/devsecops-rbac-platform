from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="Audit Service",
    version="0.1.0",
)


class AuditEvent(BaseModel):
    user_id: str
    action: str
    service: str
    status: str
    details: str | None = None


@app.get("/health")
def health():
    return {
        "service": "audit-service",
        "status": "healthy",
    }


@app.post("/audit/events")
def create_audit_event(event: AuditEvent):
    return {
        "message": "Audit event received",
        "event": event.model_dump(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
