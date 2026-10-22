"""Encode, decode, and hash text with the standard library."""

from __future__ import annotations

import base64
import binascii
import codecs
import hashlib
import sys
from urllib.parse import quote, unquote

ENCODINGS = ("hex", "base64", "base32", "url", "rot13")
HASHES = ("md5", "sha1", "sha256")


def encode(text: str, fmt: str) -> str:
    data = text.encode("utf-8")
    if fmt == "hex":
        return data.hex()
    if fmt == "base64":
        return base64.b64encode(data).decode("ascii")
    if fmt == "base32":
        return base64.b32encode(data).decode("ascii")
    if fmt == "url":
        return quote(text, safe="")
    if fmt == "rot13":
        return codecs.encode(text, "rot_13")
    raise ValueError(f"unknown encoding: {fmt}")


def decode(text: str, fmt: str) -> str:
    try:
        if fmt == "hex":
            raw = bytes.fromhex("".join(text.split()))
        elif fmt == "base64":
            raw = base64.b64decode("".join(text.split()), validate=True)
        elif fmt == "base32":
            raw = base64.b32decode("".join(text.split()), casefold=True)
        elif fmt == "url":
            return unquote(text.strip())
        elif fmt == "rot13":
            return codecs.decode(text.strip("\n"), "rot_13")
        else:
            raise ValueError(f"unknown encoding: {fmt}")
    except (ValueError, binascii.Error) as exc:
        raise ValueError(f"invalid {fmt}: {exc}") from exc
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("decoded bytes are not valid UTF-8") from exc


def digest(text: str, algo: str) -> str:
    if algo not in HASHES:
        raise ValueError(f"unknown hash: {algo}")
    return hashlib.new(algo, text.encode("utf-8")).hexdigest()


def read_text(text: str | None) -> str:
    if text is not None:
        return text
    if sys.stdin.isatty():
        raise ValueError("pass text or pipe it on stdin")
    return sys.stdin.read()


def run(action: str, kind: str, text: str | None) -> int:
    try:
        payload = read_text(text)
        if action == "encode":
            result = encode(payload, kind)
        elif action == "decode":
            result = decode(payload, kind)
        elif action == "hash":
            result = digest(payload, kind)
        else:
            raise ValueError(f"unknown action: {action}")
    except ValueError as exc:
        print(f"crypt: {exc}", file=sys.stderr)
        return 1
    print(result)
    return 0
