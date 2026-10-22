"""Build a Google dork query string. Does not contact Google."""

from __future__ import annotations

import sys
from urllib.parse import quote_plus

_OPERATORS = ("site", "filetype", "intitle", "inurl", "intext")


def build_query(
    site: str | None = None,
    filetype: str | None = None,
    intitle: str | None = None,
    inurl: str | None = None,
    intext: str | None = None,
) -> str:
    """Return a ready-to-paste dork such as ``site:example.com filetype:pdf``."""
    values = {
        "site": site,
        "filetype": filetype,
        "intitle": intitle,
        "inurl": inurl,
        "intext": intext,
    }
    parts: list[str] = []
    for op in _OPERATORS:
        raw = values[op]
        if raw is None:
            continue
        text = str(raw).strip()
        if not text:
            continue
        if any(ch.isspace() for ch in text):
            text = text.replace('"', "")
            parts.append(f'{op}:"{text}"')
        else:
            parts.append(f"{op}:{text}")
    if not parts:
        raise ValueError(
            "provide at least one of --site, --filetype, --intitle, --inurl, --intext"
        )
    return " ".join(parts)


def search_url(query: str) -> str:
    """Return a google.com/search URL for a finished query string."""
    return "https://www.google.com/search?q=" + quote_plus(query)


def render(
    site: str | None = None,
    filetype: str | None = None,
    intitle: str | None = None,
    inurl: str | None = None,
    intext: str | None = None,
) -> str:
    query = build_query(
        site=site,
        filetype=filetype,
        intitle=intitle,
        inurl=inurl,
        intext=intext,
    )
    return query + "\n" + search_url(query)


def run(
    site: str | None = None,
    filetype: str | None = None,
    intitle: str | None = None,
    inurl: str | None = None,
    intext: str | None = None,
) -> int:
    try:
        print(
            render(
                site=site,
                filetype=filetype,
                intitle=intitle,
                inurl=inurl,
                intext=intext,
            )
        )
    except ValueError as exc:
        print(f"dork: {exc}", file=sys.stderr)
        return 1
    return 0
