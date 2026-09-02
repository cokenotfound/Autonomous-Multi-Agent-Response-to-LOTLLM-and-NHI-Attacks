from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from ingestion.common.redis_stream_writer import publish


app = FastAPI(title="Mock Identity Services")


# ---------------------------------------------------------
# In-memory mock data
# ---------------------------------------------------------

IDENTITIES = {
    "test-service": {
        "token": "token-test-service",
        "role": "service-role",
    },
    "backup-service": {
        "token": "token-backup-service",
        "role": "backup-role",
    },
}

SECRETS = {
    "database/password": "mock-db-password",
    "api/key": "mock-api-key",
}


# ---------------------------------------------------------
# Request models
# ---------------------------------------------------------

class TokenRequest(BaseModel):
    identity: str


class AssumeRoleRequest(BaseModel):
    identity: str
    role: str


# ---------------------------------------------------------
# IAM — Token issuance
# ---------------------------------------------------------

@app.post("/iam/token")
def issue_token(request: TokenRequest):
    success = request.identity in IDENTITIES

    event = {
        "identity": request.identity,
        "event_name": "CreateAccessToken",
        "source_ip": "127.0.0.1",
        "user_agent": "mock-nhi-client",
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    publish("iam", event)

    if not success:
        raise HTTPException(status_code=401, detail="Unknown identity")

    return {
        "access_token": IDENTITIES[request.identity]["token"],
        "identity": request.identity,
    }


# ---------------------------------------------------------
# IAM — Role assumption
# ---------------------------------------------------------

@app.post("/iam/assume-role")
def assume_role(request: AssumeRoleRequest):
    success = request.identity in IDENTITIES

    event = {
        "identity": request.identity,
        "event_name": "AssumeRole",
        "role": request.role,
        "source_ip": "127.0.0.1",
        "user_agent": "mock-nhi-client",
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    publish("iam", event)

    if not success:
        raise HTTPException(status_code=401, detail="Unknown identity")

    return {
        "identity": request.identity,
        "role": request.role,
        "assumed": True,
    }


# ---------------------------------------------------------
# Vault — Secret access
# ---------------------------------------------------------

@app.get("/vault/secret/{path:path}")
def get_secret(
    path: str,
    x_service_identity: Optional[str] = Header(default=None),
):
    if not x_service_identity:
        raise HTTPException(
            status_code=400,
            detail="X-Service-Identity header required",
        )

    success = (
        x_service_identity in IDENTITIES
        and path in SECRETS
    )

    event = {
        "identity": x_service_identity,
        "event_name": "GetSecretValue",
        "secret_path": path,
        "source_ip": "127.0.0.1",
        "user_agent": "mock-nhi-client",
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    publish("vault", event)

    if not success:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized secret access",
        )

    return {
        "secret_path": path,
        "value": SECRETS[path],
    }


# ---------------------------------------------------------
# API Gateway
# ---------------------------------------------------------

@app.post("/gateway/{service}/{action}")
def gateway_call(
    service: str,
    action: str,
    x_service_identity: Optional[str] = Header(default=None),
):
    if not x_service_identity:
        raise HTTPException(
            status_code=400,
            detail="X-Service-Identity header required",
        )

    success = x_service_identity in IDENTITIES

    event = {
        "identity": x_service_identity,
        "event_name": "GatewayCall",
        "service": service,
        "action": action,
        "source_ip": "127.0.0.1",
        "user_agent": "mock-nhi-client",
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    publish("api_gateway", event)

    if not success:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized identity",
        )

    return {
        "service": service,
        "action": action,
        "identity": x_service_identity,
        "success": True,
    }


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------
# Run directly
# ---------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
    )