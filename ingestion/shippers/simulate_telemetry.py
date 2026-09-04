import random
import time
from datetime import datetime, timezone

from ingestion.common.redis_stream_writer import publish


IDENTITIES = [
    "test-service",
    "research-agent",
    "ci-runner",
    "etl-service",
]

HOSTS = [
    "simulated-linux-host",
    "simulated-windows-host",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def publish_event(source, payload, host="simulated-host"):
    event_id = publish(source, payload, host=host)
    print(f"[{source}] {event_id}")


# ---------------------------------------------------------
# SYSMON
# ---------------------------------------------------------

def generate_sysmon_events():
    events = [
        {
            "EventID": 1,
            "event_type": "Process Create",
            "image": "C:\\Windows\\System32\\cmd.exe",
            "command_line": "cmd.exe /c whoami",
            "parent_image": "C:\\Windows\\explorer.exe",
            "user": "test-service",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "EventID": 1,
            "event_type": "Process Create",
            "image": "C:\\Windows\\System32\\powershell.exe",
            "command_line": "powershell.exe -Command Get-Process",
            "parent_image": "C:\\Windows\\explorer.exe",
            "user": "test-service",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "EventID": 1,
            "event_type": "Process Create",
            "image": "C:\\Windows\\System32\\cmd.exe",
            "command_line": "cmd.exe /c ipconfig",
            "parent_image": "C:\\Windows\\System32\\services.exe",
            "user": "ci-runner",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "EventID": 3,
            "event_type": "Network Connection",
            "source_ip": "10.0.0.25",
            "destination_ip": "10.0.0.10",
            "destination_port": 443,
            "image": "C:\\Program Files\\Agent\\agent.exe",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "EventID": 11,
            "event_type": "File Create",
            "file_path": "C:\\Temp\\agent_output.txt",
            "image": "C:\\Program Files\\Agent\\agent.exe",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "EventID": 22,
            "event_type": "DNS Query",
            "query_name": "api.internal.local",
            "image": "C:\\Program Files\\Agent\\agent.exe",
            "timestamp": now(),
            "simulated": True,
        },
    ]

    for event in events:
        publish_event(
            "sysmon",
            event,
            host="simulated-windows-host",
        )


# ---------------------------------------------------------
# AUDITD
# ---------------------------------------------------------

def generate_auditd_events():
    events = [
        {
            "record_type": "EXECVE",
            "command": "/usr/bin/whoami",
            "arguments": ["whoami"],
            "uid": 1001,
            "identity": "test-service",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "record_type": "EXECVE",
            "command": "/usr/bin/ls",
            "arguments": ["ls", "-la"],
            "uid": 1001,
            "identity": "test-service",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "record_type": "SYSCALL",
            "syscall": "execve",
            "command": "/usr/bin/python3",
            "uid": 1002,
            "identity": "etl-service",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "record_type": "PATH",
            "path": "/tmp/etl_output.json",
            "operation": "CREATE",
            "uid": 1002,
            "identity": "etl-service",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "record_type": "EXECVE",
            "command": "/bin/bash",
            "arguments": ["bash", "-c", "curl http://internal-api"],
            "uid": 1003,
            "identity": "ci-runner",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "record_type": "SYSCALL",
            "syscall": "connect",
            "destination": "10.0.0.20:443",
            "uid": 1003,
            "identity": "ci-runner",
            "timestamp": now(),
            "simulated": True,
        },
    ]

    for event in events:
        publish_event(
            "auditd",
            event,
            host="simulated-linux-host",
        )


# ---------------------------------------------------------
# OLLAMA
# ---------------------------------------------------------

def generate_ollama_events():
    events = [
        {
            "identity": "research-agent",
            "model": "mistral:v0.3",
            "prompt": "Explain the difference between TCP and UDP.",
            "response": "TCP is connection-oriented while UDP is connectionless.",
            "latency_ms": 820,
            "source_ip": "127.0.0.1",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "test-service",
            "model": "mistral:v0.3",
            "prompt": "What is authentication?",
            "response": "Authentication verifies the identity of a user or service.",
            "latency_ms": 730,
            "source_ip": "127.0.0.1",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "research-agent",
            "model": "mistral:v0.3",
            "prompt": "Generate a Python script that lists running processes.",
            "response": "Simulated generated response.",
            "latency_ms": 1100,
            "source_ip": "127.0.0.1",
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "ci-runner",
            "model": "mistral:v0.3",
            "prompt": "Explain how to inspect network connections on Linux.",
            "response": "Use standard system networking tools.",
            "latency_ms": 900,
            "source_ip": "127.0.0.1",
            "timestamp": now(),
            "simulated": True,
        },
    ]

    for event in events:
        publish_event(
            "ollama",
            event,
            host="simulated-llm-host",
        )


# ---------------------------------------------------------
# IAM
# ---------------------------------------------------------

def generate_iam_events():
    events = [
        {
            "identity": "test-service",
            "event_name": "CreateAccessToken",
            "source_ip": "10.0.0.15",
            "user_agent": "mock-nhi-client",
            "success": True,
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "research-agent",
            "event_name": "AssumeRole",
            "role": "research-role",
            "source_ip": "10.0.0.16",
            "user_agent": "mock-nhi-client",
            "success": True,
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "ci-runner",
            "event_name": "CreateAccessToken",
            "source_ip": "10.0.0.17",
            "user_agent": "mock-ci-client",
            "success": True,
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "unknown-service",
            "event_name": "CreateAccessToken",
            "source_ip": "10.0.0.99",
            "user_agent": "unknown-client",
            "success": False,
            "timestamp": now(),
            "simulated": True,
        },
    ]

    for event in events:
        publish_event(
            "iam",
            event,
            host="simulated-identity-host",
        )


# ---------------------------------------------------------
# VAULT
# ---------------------------------------------------------

def generate_vault_events():
    events = [
        {
            "identity": "test-service",
            "event_name": "GetSecretValue",
            "secret_path": "database/password",
            "source_ip": "10.0.0.15",
            "success": True,
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "research-agent",
            "event_name": "GetSecretValue",
            "secret_path": "research/api-key",
            "source_ip": "10.0.0.16",
            "success": True,
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "ci-runner",
            "event_name": "GetSecretValue",
            "secret_path": "ci/deployment-token",
            "source_ip": "10.0.0.17",
            "success": True,
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "unknown-service",
            "event_name": "GetSecretValue",
            "secret_path": "database/password",
            "source_ip": "10.0.0.99",
            "success": False,
            "timestamp": now(),
            "simulated": True,
        },
    ]

    for event in events:
        publish_event(
            "vault",
            event,
            host="simulated-vault-host",
        )


# ---------------------------------------------------------
# API GATEWAY
# ---------------------------------------------------------

def generate_api_gateway_events():
    events = [
        {
            "identity": "test-service",
            "service": "users",
            "action": "GET /users",
            "source_ip": "10.0.0.15",
            "success": True,
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "research-agent",
            "service": "research",
            "action": "GET /reports",
            "source_ip": "10.0.0.16",
            "success": True,
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "ci-runner",
            "service": "deployment",
            "action": "POST /deploy",
            "source_ip": "10.0.0.17",
            "success": True,
            "timestamp": now(),
            "simulated": True,
        },
        {
            "identity": "unknown-service",
            "service": "admin",
            "action": "POST /admin/delete",
            "source_ip": "10.0.0.99",
            "success": False,
            "timestamp": now(),
            "simulated": True,
        },
    ]

    for event in events:
        publish_event(
            "api_gateway",
            event,
            host="simulated-api-host",
        )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":
    print("\nStarting simulated telemetry generation...\n")

    generate_sysmon_events()
    generate_auditd_events()
    generate_ollama_events()
    generate_iam_events()
    generate_vault_events()
    generate_api_gateway_events()

    print("\nSimulation complete.")
    print("All six Redis Streams should now contain simulated telemetry.")