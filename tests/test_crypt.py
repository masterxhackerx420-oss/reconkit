import io
import sys

import pytest

from reconkit.cli import main
from reconkit.crypt import decode, digest, encode


@pytest.mark.parametrize(
    ("fmt", "text", "encoded"),
    [
        ("hex", "hi", "6869"),
        ("base64", "hi", "aGk="),
        ("base32", "hi", "NBUQ===="),
        ("url", "a b/c?", "a%20b%2Fc%3F"),
        ("rot13", "hello", "uryyb"),
    ],
)
def test_encode_decode_roundtrip(fmt, text, encoded):
    assert encode(text, fmt) == encoded
    assert decode(encoded, fmt) == text


def test_decode_ignores_hex_and_base64_whitespace():
    assert decode("68 69\n", "hex") == "hi"
    assert decode("aGk=\n", "base64") == "hi"
    assert decode("nb uq====", "base32") == "hi"


@pytest.mark.parametrize(
    ("algo", "digest_hex"),
    [
        ("md5", "49f68a5c8493ec2c0bf489821c21fc3b"),
        ("sha1", "c22b5f9178342609428d6f51b2c5af4c0bde6a42"),
        ("sha256", "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4"),
    ],
)
def test_hash_digests(algo, digest_hex):
    assert digest("hi", algo) == digest_hex


def test_invalid_decode_is_an_error():
    with pytest.raises(ValueError, match="invalid hex"):
        decode("zz", "hex")
    with pytest.raises(ValueError, match="invalid base64"):
        decode("!!!!", "base64")


def test_cli_base64_roundtrip(capsys):
    assert main(["crypt", "encode", "--base64", "hello"]) == 0
    encoded = capsys.readouterr().out.strip()
    assert encoded == "aGVsbG8="
    assert main(["crypt", "decode", "--base64", encoded]) == 0
    assert capsys.readouterr().out.strip() == "hello"


def test_cli_hash_sha256(capsys):
    assert main(["crypt", "hash", "--sha256", "hi"]) == 0
    assert (
        capsys.readouterr().out.strip()
        == "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4"
    )


def test_cli_encode_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello"))
    assert main(["crypt", "encode", "--base64"]) == 0
    assert capsys.readouterr().out.strip() == "aGVsbG8="


def test_cli_rejects_bad_hex(capsys):
    code = main(["crypt", "decode", "--hex", "zz"])
    captured = capsys.readouterr()
    assert code == 1
    assert "invalid hex" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


def test_cli_requires_an_encoding():
    with pytest.raises(SystemExit) as exc:
        main(["crypt", "encode"])
    assert exc.value.code == 2
