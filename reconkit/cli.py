"""Argument dispatch for the reconkit console script."""

from __future__ import annotations

import argparse
import sys

from reconkit import __version__, crypt, dns, dork, ip, proxy


def _add_codec_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--hex", action="store_const", const="hex", dest="fmt")
    group.add_argument("--base64", action="store_const", const="base64", dest="fmt")
    group.add_argument("--base32", action="store_const", const="base32", dest="fmt")
    group.add_argument("--url", action="store_const", const="url", dest="fmt")
    group.add_argument("--rot13", action="store_const", const="rot13", dest="fmt")
    parser.add_argument(
        "text",
        nargs="?",
        help="text to process; reads stdin when omitted",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reconkit",
        description=(
            "DNS, dork, encoding, proxy, and IP helpers for authorized use "
            "on your own targets."
        ),
        epilog=(
            "Authorized use only: investigate targets you own or have "
            "permission to check."
        ),
    )
    parser.add_argument("--version", action="version", version=f"reconkit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    p_dns = sub.add_parser("dns", help="resolve records or reverse-lookup an IP")
    p_dns.add_argument("name", help="domain name or IP address")
    p_dns.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="seconds to wait for an answer (default: 5)",
    )
    p_dns.set_defaults(func=_cmd_dns)

    p_dork = sub.add_parser("dork", help="build a Google dork query and search URL")
    p_dork.add_argument("--site", help="site: operator")
    p_dork.add_argument("--filetype", help="filetype: operator")
    p_dork.add_argument("--intitle", help="intitle: operator")
    p_dork.add_argument("--inurl", help="inurl: operator")
    p_dork.add_argument("--intext", help="intext: operator")
    p_dork.set_defaults(func=_cmd_dork)

    p_crypt = sub.add_parser("crypt", help="encode, decode, or hash text")
    crypt_sub = p_crypt.add_subparsers(dest="action", required=True, metavar="action")
    for action, help_text in (("encode", "encode text"), ("decode", "decode text")):
        cmd = crypt_sub.add_parser(action, help=help_text)
        _add_codec_flags(cmd)
        cmd.set_defaults(func=_cmd_crypt)
    p_hash = crypt_sub.add_parser("hash", help="print md5, sha1, or sha256")
    hash_group = p_hash.add_mutually_exclusive_group(required=True)
    hash_group.add_argument("--md5", action="store_const", const="md5", dest="fmt")
    hash_group.add_argument("--sha1", action="store_const", const="sha1", dest="fmt")
    hash_group.add_argument("--sha256", action="store_const", const="sha256", dest="fmt")
    p_hash.add_argument(
        "text",
        nargs="?",
        help="text to hash; reads stdin when omitted",
    )
    p_hash.set_defaults(func=_cmd_crypt)

    p_proxy = sub.add_parser("proxy", help="check which proxies answer a test request")
    p_proxy.add_argument(
        "source",
        nargs="?",
        default="-",
        help="file of host:port lines, or - for stdin (default: -)",
    )
    p_proxy.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="per-proxy timeout in seconds (default: 5)",
    )
    p_proxy.add_argument(
        "--workers",
        type=int,
        default=20,
        help="concurrent checks (default: 20, max: 200)",
    )
    p_proxy.add_argument(
        "--url",
        default="http://example.com",
        help="URL requested through each proxy (default: http://example.com)",
    )
    p_proxy.set_defaults(func=_cmd_proxy)

    p_ip = sub.add_parser("ip", help="show IP/CIDR details and a public lookup")
    p_ip.add_argument("target", help="IP address or CIDR")
    p_ip.add_argument(
        "--timeout",
        type=float,
        default=8.0,
        help="public lookup timeout in seconds (default: 8)",
    )
    p_ip.add_argument(
        "--no-lookup",
        action="store_true",
        help="skip the public geo and whois-style lookup",
    )
    p_ip.set_defaults(func=_cmd_ip)
    return parser


def _cmd_dns(args: argparse.Namespace) -> int:
    return dns.run(args.name, timeout=args.timeout)


def _cmd_dork(args: argparse.Namespace) -> int:
    return dork.run(
        site=args.site,
        filetype=args.filetype,
        intitle=args.intitle,
        inurl=args.inurl,
        intext=args.intext,
    )


def _cmd_crypt(args: argparse.Namespace) -> int:
    return crypt.run(args.action, args.fmt, args.text)


def _cmd_proxy(args: argparse.Namespace) -> int:
    return proxy.run(
        args.source,
        timeout=args.timeout,
        workers=args.workers,
        url=args.url,
    )


def _cmd_ip(args: argparse.Namespace) -> int:
    return ip.run(args.target, timeout=args.timeout, lookup=not args.no_lookup)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("reconkit: interrupted", file=sys.stderr)
        return 130
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
