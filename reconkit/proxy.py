"""Check which host:port proxies answer a test request."""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from rich.console import Console
from rich.table import Table

_MAX_WORKERS = 200


def normalize_proxy(line: str) -> str | None:
    """Return ``scheme://host:port`` or None when the line is not a proxy."""
    value = line.strip()
    scheme = "http"
    rest = value
    if "://" in value:
        scheme, rest = value.split("://", 1)
        if scheme not in ("http", "https"):
            return None
    if rest.startswith("["):
        end = rest.find("]")
        if end < 0 or len(rest) <= end + 2 or rest[end + 1] != ":":
            return None
        host = rest[: end + 1]
        port_text = rest[end + 2 :]
        if not host[1:-1]:
            return None
    else:
        if rest.count(":") != 1:
            return None
        host, port_text = rest.split(":", 1)
        if not host:
            return None
    if not port_text.isdigit():
        return None
    port = int(port_text)
    if port < 1 or port > 65535:
        return None
    return f"{scheme}://{host}:{port}"


def parse_proxies(text: str) -> tuple[list[str], list[str]]:
    """Split proxy text into normalized proxies and invalid lines.

    Blank lines and ``#`` comments are ignored.
    """
    good: list[str] = []
    bad: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        normalized = normalize_proxy(line)
        if normalized is None:
            bad.append(line)
        else:
            good.append(normalized)
    return good, bad


def check_one(proxy: str, url: str, timeout: float):
    """Return ``(proxy, status_code, latency_ms)`` when a response arrives."""
    started = time.perf_counter()
    try:
        response = requests.get(
            url,
            proxies={"http": proxy, "https": proxy},
            headers={"User-Agent": "reconkit/0.1"},
            timeout=timeout,
        )
        status = response.status_code
        response.close()
    except requests.RequestException:
        return None
    latency_ms = (time.perf_counter() - started) * 1000.0
    return proxy, status, latency_ms


def check_all(proxies: list[str], url: str, timeout: float, workers: int):
    """Check proxies concurrently and keep the input order."""
    if not proxies:
        return []
    worker_count = max(1, min(workers, len(proxies)))
    results = [None] * len(proxies)
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(check_one, proxy, url, timeout): index
            for index, proxy in enumerate(proxies)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception:
                results[index] = None
    return [item for item in results if item is not None]


def render_table(rows) -> None:
    table = Table(title="Working proxies")
    table.add_column("Proxy")
    table.add_column("Status", justify="right")
    table.add_column("Latency", justify="right")
    for proxy, status, latency_ms in rows:
        table.add_row(proxy, str(status), f"{latency_ms:.0f} ms")
    console = Console(
        file=sys.stdout,
        highlight=False,
        soft_wrap=True,
        width=120,
        force_terminal=False,
    )
    console.print(table)


def run(source: str, timeout: float = 5.0, workers: int = 20, url: str = "http://example.com") -> int:
    if timeout <= 0:
        print("proxy: timeout must be positive", file=sys.stderr)
        return 1
    if workers < 1 or workers > _MAX_WORKERS:
        print(f"proxy: workers must be from 1 to {_MAX_WORKERS}", file=sys.stderr)
        return 1
    try:
        if source == "-":
            text = sys.stdin.read()
        else:
            with open(source, encoding="utf-8") as handle:
                text = handle.read()
    except (OSError, UnicodeError) as exc:
        print(f"proxy: cannot read {source}: {exc}", file=sys.stderr)
        return 1

    good, bad = parse_proxies(text)
    for line in bad:
        print(f"proxy: skipped invalid entry: {line}", file=sys.stderr)
    if not good:
        print("proxy: no proxies to check", file=sys.stderr)
        return 1

    rows = check_all(good, url, timeout, workers)
    if not rows:
        print("proxy: no working proxies", file=sys.stderr)
        return 1
    render_table(rows)
    print(f"{len(rows)} of {len(good)} proxies responded")
    return 0
