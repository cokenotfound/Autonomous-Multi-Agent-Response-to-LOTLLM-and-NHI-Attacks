"""
preprocessing/normalization/field_normalizer.py

Normalizes source-specific fields into a common event representation schema.
Preserves the raw payload.
"""
from typing import Dict, Any

class FieldNormalizer:
    def normalize(self, event_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps fields to a common schema.
        Returns the modified event_obj containing a 'common_event' dictionary.
        """
        if not event_obj.get("is_valid", False):
            return event_obj

        envelope = event_obj["envelope"]
        parsed = event_obj["parsed"]
        source_type = envelope["source_type"]
        
        # Base common fields
        common = {
            "event_id": envelope["envelope_id"],
            "timestamp": event_obj.get("normalized_timestamp", envelope["ingested_at"]),
            "source_type": source_type,
            "host": envelope["host"],
            
            # Initialize optional fields as None
            "identity": None,
            "event_type": None,
            "action": None,
            "process_name": None,
            "process_path": None,
            "parent_process": None,
            "parent_pid": None,
            "command_line": None,
            "resource": None,
            "source_ip": None,
            "user_agent": None,
            "model": None,
            "prompt": None,
            "response": None,
            "success": None,
            "latency_ms": None,
            
            # VERY IMPORTANT: Preserve raw payload
            "raw_payload": envelope["raw_payload"]
        }

        # Source-specific mappings
        if source_type == "sysmon":
            common["event_type"] = parsed.get("EventType")
            common["identity"] = parsed.get("User")
            if common["identity"] and "\\" in common["identity"]:
                # strip domain prefix for easier correlation (e.g. DESKTOP\alice -> alice)
                common["identity"] = common["identity"].split("\\")[-1]
                
            common["process_path"] = parsed.get("Image")
            if common["process_path"]:
                common["process_name"] = common["process_path"].split("\\")[-1]
            
            common["parent_process"] = parsed.get("ParentImage")
            common["parent_pid"] = parsed.get("ParentProcessId")
            common["command_line"] = parsed.get("CommandLine")
            common["source_ip"] = parsed.get("SourceIp")
            common["resource"] = parsed.get("DestinationIp") or parsed.get("QueryName")

        elif source_type == "auditd":
            common["event_type"] = parsed.get("syscall") or "audit_event"
            common["identity"] = parsed.get("uid_name")
            common["process_path"] = parsed.get("exe")
            if common["process_path"]:
                common["process_name"] = common["process_path"].split("/")[-1]
            
            if "EXECVE" in parsed:
                args = parsed["EXECVE"].get("args", [])
                common["command_line"] = " ".join(args) if args else None
                
            common["success"] = (parsed.get("success") == "yes")

        elif source_type == "iam":
            common["event_type"] = parsed.get("event_type")
            common["identity"] = parsed.get("username")
            common["source_ip"] = parsed.get("client_ip")
            common["success"] = parsed.get("success")
            common["user_agent"] = parsed.get("user_agent")
            
        elif source_type == "vault":
            common["event_type"] = parsed.get("event_type")
            common["identity"] = parsed.get("username")
            common["resource"] = parsed.get("path")
            common["success"] = parsed.get("success")

        elif source_type == "api_gateway":
            common["event_type"] = "api_request"
            common["identity"] = parsed.get("username")
            common["action"] = parsed.get("method")
            common["resource"] = parsed.get("path")
            common["source_ip"] = parsed.get("client_ip")
            status = parsed.get("response_status")
            common["success"] = (status is not None and 200 <= status < 400)

        elif source_type == "ollama":
            common["event_type"] = parsed.get("event_type")
            common["identity"] = parsed.get("identity")
            common["source_ip"] = parsed.get("source_ip")
            common["latency_ms"] = parsed.get("latency_ms")
            
            # Extract request/response details safely
            req = parsed.get("request", {})
            resp = parsed.get("response", {})
            
            if isinstance(req, dict):
                import json
                try:
                    body = json.loads(req.get("body", "{}"))
                    common["model"] = body.get("model")
                    common["prompt"] = body.get("prompt")
                except Exception:
                    pass
                    
            if isinstance(resp, dict):
                import json
                try:
                    body = json.loads(resp.get("body", "{}"))
                    common["response"] = body.get("response")
                    common["success"] = (resp.get("status_code", 500) == 200)
                except Exception:
                    pass

        event_obj["common_event"] = common
        return event_obj
