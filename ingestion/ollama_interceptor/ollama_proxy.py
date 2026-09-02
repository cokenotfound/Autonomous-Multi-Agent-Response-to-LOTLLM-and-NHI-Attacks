import json
import time

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

from ingestion.common.redis_stream_writer import publish


app = FastAPI()

OLLAMA_URL = "http://127.0.0.1:11434"


@app.post("/api/generate")
async def generate(
    request: Request,
    x_service_identity: str = Header(default=None),
):
    if not x_service_identity:
        raise HTTPException(
            status_code=400,
            detail="X-Service-Identity header is required",
        )

    body = await request.json()

    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json=body,
        )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    try:
        response_data = response.json()
    except Exception:
        response_data = response.text

    telemetry = {
        "identity": x_service_identity,
        "model": body.get("model"),
        "prompt": body.get("prompt"),
        "response": response_data.get("response")
        if isinstance(response_data, dict)
        else response_data,
        "latency_ms": latency_ms,
        "source_ip": request.client.host if request.client else None,
    }

    publish(
        "ollama",
        telemetry,
        host="localhost",
    )

    return JSONResponse(
        status_code=response.status_code,
        content=response_data,
    )


@app.post("/api/chat")
async def chat(
    request: Request,
    x_service_identity: str = Header(default=None),
):
    if not x_service_identity:
        raise HTTPException(
            status_code=400,
            detail="X-Service-Identity header is required",
        )

    body = await request.json()

    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json=body,
        )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    try:
        response_data = response.json()
    except Exception:
        response_data = response.text

    telemetry = {
        "identity": x_service_identity,
        "model": body.get("model"),
        "prompt": body.get("messages"),
        "response": response_data,
        "latency_ms": latency_ms,
        "source_ip": request.client.host if request.client else None,
    }

    publish(
        "ollama",
        telemetry,
        host="localhost",
    )

    return JSONResponse(
        status_code=response.status_code,
        content=response_data,
    )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )