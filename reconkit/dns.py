"""Resolve DNS records, or reverse-lookup an IP."""

from __future__ import annotations

import ipaddress
import sys

import dns.exception
import dns.resolver
import dns.reversename

RECORD_TYPES = ("A", "AAAA", "MX", "NS", "TXT", "CNAME")


def _is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def _query(qname, rdtype: str, timeout: float):
    try:
        answer = dns.resolver.resolve(qname, rdtype, lifetime=timeout)
    except dns.resolver.NXDOMAIN:
        return "nxdomain", []
    except dns.resolver.NoAnswer:
        return "none", []
    except dns.resolver.NoNameservers:
        return "no-nameservers", []
    except dns.exception.Timeout:
        return "timeout", []
    except dns.exception.DNSException as exc:
        return "error", [f"{exc.__class__.__name__}: {exc}"]
    texts = [rdata.to_text() for rdata in answer]
    if not texts:
        return "none", []
    return "ok", texts


def _status_line(rdtype: str, status: str, values: list[str]) -> list[str]:
    if status == "ok":
        return [f"{rdtype}: {value}" for value in values]
    if status == "none":
        return [f"{rdtype}: none"]
    if status == "timeout":
        return [f"{rdtype}: timed out"]
    if status == "no-nameservers":
        return [f"{rdtype}: no nameservers"]
    if status == "nxdomain":
        return [f"{rdtype}: no such domain"]
    detail = values[0] if values else status
    return [f"{rdtype}: {detail}"]


def _reverse_lines(ip: str, timeout: float) -> list[str]:
    try:
        rev = dns.reversename.from_address(ip)
    except dns.exception.DNSException as exc:
        return [f"reverse: {exc.__class__.__name__}: {exc}"]
    status, values = _query(rev, "PTR", timeout)
    if status == "ok":
        return [f"reverse: {ip} -> {value}" for value in values]
    label = {
        "none": "none",
        "nxdomain": "no such domain",
        "timeout": "timed out",
        "no-nameservers": "no nameservers",
    }.get(status, values[0] if values else status)
    return [f"reverse: {ip} -> {label}"]


def render(name: str, timeout: float = 5.0) -> str:
    name = name.strip()
    if not name:
        raise ValueError("missing name")
    if any(ch.isspace() for ch in name):
        raise ValueError(f"invalid name: {name}")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if _is_ip(name):
        return "\n".join([f"ip: {name}", *_reverse_lines(name, timeout)])

    lines = [f"name: {name}"]
    ips: list[str] = []
    for rdtype in RECORD_TYPES:
        status, values = _query(name, rdtype, timeout)
        if status == "nxdomain":
            lines.append("result: no such domain")
            return "\n".join(lines)
        lines.extend(_status_line(rdtype, status, values))
        if status == "ok" and rdtype in ("A", "AAAA"):
            ips.extend(values)
    for ip in ips:
        lines.extend(_reverse_lines(ip, timeout))
    return "\n".join(lines)


def run(name: str, timeout: float = 5.0) -> int:
    try:
        print(render(name, timeout=timeout))
    except ValueError as exc:
        print(f"dns: {exc}", file=sys.stderr)
        return 1
    return 0
