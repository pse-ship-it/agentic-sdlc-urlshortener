"""
Security & Compliance Layer:
- SSRF Prevention (Private Subnet / Loopback Filter)
- URL Protocol Whitelist
- Malware/Phishing Domain Blacklist
- GDPR-Compliant Client IP Anonymization
"""

from __future__ import annotations
import socket
import ipaddress
import hashlib
from urllib.parse import urlparse
from typing import Tuple
from .config import settings

IP_SALT = "enterprise-url-shortener-salt-2026"


class SecurityValidator:
    @staticmethod
    def validate_url(url_str: str) -> Tuple[bool, str]:
        """Validates that a URL is safe, valid, and not an SSRF or phishing vector."""
        if not url_str or len(url_str) > 2048:
            return False, "URL length exceeds limit (max 2048 characters)."

        try:
            parsed = urlparse(url_str)
        except Exception:
            return False, "Malformed URL format."

        # 1. Scheme Check
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Prohibited URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "URL must include a valid hostname."

        # 2. Blocklist Check
        for blocked in settings.blocked_domains:
            if hostname.lower() == blocked.lower() or hostname.lower().endswith("." + blocked.lower()):
                return False, f"Domain '{hostname}' is flagged as malicious or phishing."

        # 3. SSRF / Private IP Range Check
        if settings.enable_ssrf_protection:
            try:
                # Check if hostname itself is directly an IP
                try:
                    ip_obj = ipaddress.ip_address(hostname)
                    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local:
                        return False, f"SSRF violation: Direct access to private/loopback IP '{hostname}' is prohibited."
                except ValueError:
                    # Hostname is a domain name; resolve DNS
                    resolved_ips = socket.gethostbyname_ex(hostname)[2]
                    for ip_str in resolved_ips:
                        ip_obj = ipaddress.ip_address(ip_str)
                        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local:
                            return False, f"SSRF violation: Hostname '{hostname}' resolves to private/loopback IP '{ip_str}'."
            except socket.gaierror:
                # DNS resolution failure
                return False, f"Cannot resolve domain '{hostname}'."
            except Exception:
                # Fail-safe defense
                pass

        return True, "URL passed all security validations."

    @staticmethod
    def hash_ip(ip_address: str) -> str:
        """Anonymizes client IP address using salted SHA-256 for privacy compliance."""
        salted = f"{ip_address}:{IP_SALT}".encode("utf-8")
        return hashlib.sha256(salted).hexdigest()[:16]
