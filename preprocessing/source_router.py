"""
preprocessing/source_router.py

Routes events to the correct source-specific parser based on `source_type`.
"""

from typing import Dict, Any
from parsers.sysmon_parser import SysmonParser
from parsers.auditd_parser import AuditdParser
from parsers.ollama_parser import OllamaParser
from parsers.iam_parser import IamParser
from parsers.vault_parser import VaultParser
from parsers.api_gateway_parser import ApiGatewayParser
from parsers.base_parser import BaseParser

class SourceRouter:
    def __init__(self):
        self.parsers: Dict[str, BaseParser] = {
            "sysmon": SysmonParser(),
            "auditd": AuditdParser(),
            "ollama": OllamaParser(),
            "iam": IamParser(),
            "vault": VaultParser(),
            "api_gateway": ApiGatewayParser(),
        }

    def route_and_parse(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes an envelope dictionary (e.g. from Redis reader), identifies the source type,
        extracts the `raw_payload`, parses it into a structured object using the appropriate parser,
        and returns a new dictionary combining the envelope and the parsed payload.
        """
        source_type = envelope.get("source_type")
        
        if not source_type:
            raise ValueError("Missing 'source_type' in envelope")

        parser = self.parsers.get(source_type)
        if not parser:
            raise ValueError(f"Unknown source_type: {source_type}")

        raw_payload = envelope.get("raw_payload")
        if raw_payload is None:
            raise ValueError("Missing 'raw_payload' in envelope")

        # Parse the string payload into a Python dictionary
        parsed_payload = parser.parse(raw_payload)

        # Return the structured object
        return {
            "envelope": envelope,
            "parsed": parsed_payload,
            "parser_used": type(parser).__name__
        }
