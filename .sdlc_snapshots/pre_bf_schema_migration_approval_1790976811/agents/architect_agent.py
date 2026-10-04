"""
Software Architect & Systems Design Agent.
Defines system architecture, OpenAPI contracts, database schemas, threat models, and ADRs.
"""

from __future__ import annotations
from typing import Dict, Any, List
from .base_agent import BaseSDLCAgent
from orchestrator.models import TaskNode


class ArchitectAgent(BaseSDLCAgent):
    def __init__(self, llm_provider=None):
        super().__init__("Architect", llm_provider)

    def execute(self, task: TaskNode, context: Dict[str, Any]) -> Dict[str, Any]:
        spec = context.get("normalized_specification", {})

        architecture_design = {
            "system_name": "PulseURL Enterprise Shortener",
            "pattern": "Layered Modular Architecture (Router -> Service -> Repository -> Cache)",
            "encoding_strategy": {
                "algorithm": "Base62 (0-9, a-z, A-Z) with SHA-256 seed fallback",
                "length": 6,
                "address_space": 62 ** 6,  # ~56.8 billion unique URLs
                "collision_handling": "Salted SHA-256 linear probe with 3-attempt ceiling"
            },
            "database_schema": {
                "urls_table": {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "short_code": "VARCHAR(32) UNIQUE NOT NULL INDEX",
                    "original_url": "TEXT NOT NULL",
                    "custom_alias": "VARCHAR(64) UNIQUE NULL",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "expires_at": "TIMESTAMP NULL",
                    "is_active": "BOOLEAN DEFAULT TRUE",
                    "click_count": "INTEGER DEFAULT 0"
                },
                "clicks_table": {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "short_code": "VARCHAR(32) NOT NULL INDEX",
                    "timestamp": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "ip_hash": "VARCHAR(64) NOT NULL",
                    "referrer": "VARCHAR(255) NULL",
                    "user_agent": "VARCHAR(255) NULL",
                    "country": "VARCHAR(64) DEFAULT 'Unknown'"
                }
            },
            "api_contracts": [
                {
                    "path": "/api/v1/urls",
                    "method": "POST",
                    "description": "Shorten a long URL with optional alias and TTL expiration in seconds",
                    "request_body": {"url": "str", "custom_alias": "Optional[str]", "ttl_seconds": "Optional[int]"},
                    "response_201": {"short_code": "str", "short_url": "str", "original_url": "str", "expires_at": "str"}
                },
                {
                    "path": "/{short_code}",
                    "method": "GET",
                    "description": "Redirects to destination URL with HTTP 307 Temporary Redirect and click telemetry",
                    "response_307": "Redirect header 'Location'",
                    "response_404": "Link not found or expired"
                },
                {
                    "path": "/api/v1/urls/{short_code}",
                    "method": "GET",
                    "description": "Retrieve link metadata and status",
                    "response_200": {"short_code": "str", "original_url": "str", "created_at": "str", "clicks": "int"}
                },
                {
                    "path": "/api/v1/urls/{short_code}/analytics",
                    "method": "GET",
                    "description": "Aggregated analytics breakdown (referrers, devices, time-series)",
                    "response_200": {"total_clicks": "int", "referrers": "dict", "devices": "dict", "timeline": "list"}
                }
            ],
            "threat_model": {
                "threats_identified": [
                    {"threat": "SSRF via internal loopback target", "mitigation": "Resolve IP and reject private/reserved subnets (127.0.0.1, 10.0.0.0/8, 169.254.0.0/16)"},
                    {"threat": "Open redirect to phishing scheme", "mitigation": "Strict protocol white-listing (http/https only) and known domain safety check"},
                    {"threat": "Denial of Service via link scraping", "mitigation": "Sliding-window token bucket rate limiter (60 requests/minute/IP)"},
                    {"threat": "Database exhaustion via unexpired links", "mitigation": "Enforce optional TTL and async expiration reaper job"}
                ]
            },
            "adr": {
                "id": "ADR-001",
                "title": "Selection of Base62 Shortcode Generation over Random UUIDs",
                "status": "APPROVED",
                "context": "Shortened URLs must be compact for SMS/chat sharing while guaranteeing > 50B collision-resistant codes.",
                "decision": "Use Base62 encoding seeded by SHA-256 digest + auto-incrementing ID offset.",
                "consequences": "URLs are exactly 6 characters, URL-safe without special characters, and deterministic."
            }
        }

        context["api_specification"] = architecture_design["api_contracts"]
        context["architecture_design"] = architecture_design

        return {
            "decision_summary": "Architectural blueprint finalized with Layered Design, Base62 encoding, and Threat Model",
            "rationale": "Base62 offers 56.8 billion distinct compact 6-character tokens with zero URL-escaping overhead. Threat model explicitly addresses SSRF and phishing.",
            "alternatives_rejected": [
                "UUIDv4 (rejected: 36 characters too long for URL shortener)",
                "Sequential Integer ID without encoding (rejected: vulnerable to enumeration/scraping attacks)",
                "NoSQL Key-Value Store (rejected: relational schema required for transactional analytics aggregation)"
            ],
            "architecture": architecture_design
        }
