"""IP and CIDR summary, plus a public geo / whois-style lookup for one global IP."""

from __future__ import annotations

import ipaddress
import sys

import requests

_LIST_LIMIT = 256
_LOOKUP_FIELDS = (
    ("country", "country_name"),
    ("region", "region"),
    ("city", "city"),
    ("postal", "postal"),
    ("lat", "latitude"),
    ("lon", "longitude"),
    ("timezone", "timezone"),
    ("org", "org"),
    ("asn", "asn"),
    ("network", "network"),
)


def parse_target(text: str):
    value = text.strip()
    if not value:
        raise ValueError("missing address")
    try:
        if "/" in value:
            return ipaddress.ip_network(value, strict=False)
        return ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValueError(f"not an IP address or CIDR: {value}") from exc


def _yn(flag: bool) -> str:
    return "yes" if flag else "no"


def _skip_reason(ip) -> str | None:
    if ip.is_unspecified:
        return "unspecified address"
    if ip.is_loopback:
        return "loopback address"
    if ip.is_link_local:
        return "link-local address"
    if ip.is_multicast:
        return "multicast address"
    if ip.is_reserved:
        return "reserved address"
    if ip.is_private:
        return "private address"
    if not ip.is_global:
        return "non-global address"
    return None


def _usable_count(network) -> int:
    # /31, /32, /127, and /128 are special in ipaddress and tiny, so count
    # those with hosts(). Wider IPv4 nets drop network and broadcast.
    # Wider IPv6 nets drop only the subnet-router anycast address.
    total = network.num_addresses
    if total <= 2:
        return len(list(network.hosts()))
    if network.version == 6:
        return total - 1
    return total - 2


def fetch_lookup(ip: str, timeout: float) -> dict:
    """Ask ipapi.co for geo and whois-style fields. Raises on failure."""
    response = requests.get(
        f"https://ipapi.co/{ip}/json/",
        headers={"User-Agent": "reconkit/0.1", "Accept": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError("lookup returned non-JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("lookup returned an unexpected payload")
    if data.get("error"):
        reason = data.get("reason") or "lookup failed"
        raise ValueError(str(reason))
    return data


def _lookup_lines(ip, timeout: float, lookup: bool) -> list[str]:
    if not lookup:
        return ["lookup: skipped"]
    reason = _skip_reason(ip)
    if reason:
        return [f"lookup: skipped ({reason})"]
    try:
        data = fetch_lookup(str(ip), timeout)
    except requests.RequestException as exc:
        return [f"lookup: failed ({exc.__class__.__name__}: {exc})"]
    except ValueError as exc:
        return [f"lookup: failed ({exc})"]
    lines = ["lookup:"]
    for label, key in _LOOKUP_FIELDS:
        value = data.get(key)
        if value is None or value == "":
            continue
        lines.append(f"  {label}: {value}")
    if len(lines) == 1:
        lines.append("  (no fields returned)")
    return lines


def render_address(raw: str, ip, timeout: float, lookup: bool) -> str:
    lines = [
        f"input: {raw.strip()}",
        f"target: {ip}",
        f"version: IPv{ip.version}",
        f"private: {_yn(ip.is_private)}",
        f"global: {_yn(ip.is_global)}",
        f"loopback: {_yn(ip.is_loopback)}",
        f"reverse name: {ip.reverse_pointer}",
    ]
    lines.extend(_lookup_lines(ip, timeout, lookup))
    return "\n".join(lines)


def render_network(raw: str, network) -> str:
    total = network.num_addresses
    lines = [
        f"input: {raw.strip()}",
        f"network: {network}",
        f"version: IPv{network.version}",
        f"private: {_yn(bool(network.is_private))}",
        f"broadcast: {network.broadcast_address}",
        f"netmask: {network.netmask}",
        f"prefix: {network.prefixlen}",
        f"address count: {total}",
    ]
    if total <= _LIST_LIMIT:
        hosts = list(network.hosts())
        lines.append(f"usable count: {len(hosts)}")
        lines.append("address list:")
        lines.extend(f"  {addr}" for addr in network)
        lines.append("usable hosts:")
        if hosts:
            lines.extend(f"  {host}" for host in hosts)
        else:
            lines.append("  (none)")
    else:
        lines.append(f"usable count: {_usable_count(network)}")
        lines.append(
            f"address list: omitted ({total} addresses; showing first and last only)"
        )
        lines.append(f"first: {network.network_address}")
        lines.append(f"last: {network.broadcast_address}")
    if network.is_private:
        lines.append("lookup: skipped (private network)")
    else:
        lines.append(
            "lookup: skipped (pass a single IP for geo and whois-style fields)"
        )
    return "\n".join(lines)


def render(target: str, timeout: float = 8.0, lookup: bool = True) -> str:
    parsed = parse_target(target)
    if isinstance(parsed, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
        return render_network(target, parsed)
    return render_address(target, parsed, timeout=timeout, lookup=lookup)


def run(target: str, timeout: float = 8.0, lookup: bool = True) -> int:
    if timeout <= 0:
        print("ip: timeout must be positive", file=sys.stderr)
        return 1
    try:
        print(render(target, timeout=timeout, lookup=lookup))
    except ValueError as exc:
        print(f"ip: {exc}", file=sys.stderr)
        return 1
    return 0
