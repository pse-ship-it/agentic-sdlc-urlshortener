"""
Requirement & Ambiguity Analysis Agent.
Interprets user intent, scores ambiguity, identifies missing specifications, and normalizes into an engineering problem.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List
from .base_agent import BaseSDLCAgent
from orchestrator.models import TaskNode


class RequirementAgent(BaseSDLCAgent):
    def __init__(self, llm_provider=None):
        super().__init__("RequirementAnalyzer", llm_provider)

    def execute(self, task: TaskNode, context: Dict[str, Any]) -> Dict[str, Any]:
        raw_requirement = task.input_payload.get("raw_requirement") or context.get("raw_requirement", "")

        # Analyze ambiguity and intent
        prompt = f"""Analyze this software requirement for a URL Shortener system:
Requirement: "{raw_requirement}"
Assess ambiguity (0.0 to 1.0), extract intent, identify missing specifications, and formulate engineering acceptance criteria."""

        raw_analysis = self.llm.complete(prompt, system_instruction="You are a principal systems analyst.")
        try:
            analysis = json.loads(raw_analysis)
        except Exception:
            # Deterministic heuristic analysis
            ambiguity_score = 0.85 if ("enterprise" in raw_requirement.lower() or "safe" in raw_requirement.lower() and len(raw_requirement.split()) < 10) else 0.10
            is_ambiguous = ambiguity_score > 0.30
            analysis = {
                "is_ambiguous": is_ambiguous,
                "ambiguity_score": ambiguity_score,
                "intent": "Develop or extend URL Shortener service",
                "missing_specifications": [
                    "Rate limit thresholds (requests per minute)",
                    "SSRF loopback protection rules",
                    "Click analytics storage retention"
                ] if is_ambiguous else [],
                "clarification_questions": [
                    "What rate limit (req/min) should be enforced per IP?",
                    "Should private IPv4/IPv6 ranges be blocked to prevent SSRF?",
                    "Is an interactive web dashboard required for observability?"
                ] if is_ambiguous else []
            }

        # Normalize into clear engineering problem
        normalized_spec = {
            "title": "URL Shortener Engineering Specification",
            "functional_requirements": [
                "Generate unique Base62 short codes for valid HTTP/HTTPS URLs",
                "Perform HTTP 307/302 redirects to destination URLs with < 5ms latency",
                "Support custom short aliases with collision detection and graceful fallback",
                "Support optional TTL expiration with automatic link deactivation",
                "Track click events (timestamp, client IP hash, user agent, referrer)"
            ],
            "non_functional_requirements": [
                "Zero-downtime database schema migrations",
                "Sub-10ms redirect response time under cache hits",
                "Sliding-window rate limiting per client IP (default 60 req/min)",
                "Full SSRF protection (prohibit localhost, 127.0.0.1, 10.0.0.0/8, 192.168.0.0/16, etc.)"
            ],
            "acceptance_criteria": [
                "Given a long URL, when shortened, it returns a 6-character short code",
                "Given a valid short code, when queried, it returns a 307 redirect to target",
                "Given an invalid or expired code, it returns HTTP 404 with standard RFC 7807 error payload",
                "Given analytics endpoint query, it aggregates clicks by day, device, and referrer",
                "Given abusive client (> 60 req/min), it returns HTTP 429 Too Many Requests"
            ]
        }

        context["ambiguity_score"] = analysis.get("ambiguity_score", 0.0)
        context["ambiguities"] = analysis.get("missing_specifications", [])
        context["normalized_specification"] = normalized_spec

        return {
            "decision_summary": "Requirement intent normalized into formal SDLC engineering specification",
            "rationale": f"Analyzed requirement with ambiguity score {analysis.get('ambiguity_score', 0.0):.2f}. Formulated 5 functional, 4 non-functional, and 5 acceptance criteria.",
            "alternatives_rejected": [
                "Direct code generation without specification normalization (rejected: high risk of scope creep)",
                "Assuming default unverified rate limits without formal criteria (rejected: enterprise governance violation)"
            ],
            "analysis": analysis,
            "normalized_specification": normalized_spec
        }
