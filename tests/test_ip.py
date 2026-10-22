import ipaddress

import requests

from reconkit.cli import main
from reconkit.ip import render


def test_cidr_30_expansion(capsys):
    code = main(["ip", "192.168.0.0/30"])
    out = capsys.readouterr().out
    assert code == 0
    assert "input: 192.168.0.0/30" in out
    assert "network: 192.168.0.0/30" in out
    assert "version: IPv4" in out
    assert "private: yes" in out
    assert "broadcast: 192.168.0.3" in out
    assert "netmask: 255.255.255.252" in out
    assert "prefix: 30" in out
    assert "address count: 4" in out
    assert "usable count: 2" in out
    address_list = out.split("address list:", 1)[1].split("usable hosts:", 1)[0]
    usable = out.split("usable hosts:", 1)[1]
    for addr in ("192.168.0.0", "192.168.0.1", "192.168.0.2", "192.168.0.3"):
        assert addr in address_list
    assert "192.168.0.1" in usable
    assert "192.168.0.2" in usable
    assert "192.168.0.0" not in usable
    assert "192.168.0.3" not in usable
    assert "lookup: skipped (private network)" in out


def test_cidr_matches_ipaddress_hosts():
    text = render("192.168.0.0/30")
    network = ipaddress.ip_network("192.168.0.0/30")
    usable = text.split("usable hosts:", 1)[1]
    for host in network.hosts():
        assert str(host) in usable.split("lookup:", 1)[0]


def test_host_bits_are_masked_to_the_network(capsys):
    assert main(["ip", "192.168.0.1/30"]) == 0
    out = capsys.readouterr().out
    assert "input: 192.168.0.1/30" in out
    assert "network: 192.168.0.0/30" in out


def test_slash_31_and_32_follow_ipaddress(capsys):
    assert main(["ip", "192.168.0.0/31"]) == 0
    out = capsys.readouterr().out
    network = ipaddress.ip_network("192.168.0.0/31")
    assert "address count: 2" in out
    assert f"usable count: {len(list(network.hosts()))}" in out

    assert main(["ip", "192.168.0.5/32"]) == 0
    out = capsys.readouterr().out
    single = ipaddress.ip_network("192.168.0.5/32")
    assert "address count: 1" in out
    assert f"usable count: {len(list(single.hosts()))}" in out
    assert "192.168.0.5" in out


def test_ipv6_prefix_lists_stdlib_addresses(capsys):
    assert main(["ip", "2001:db8::/126"]) == 0
    out = capsys.readouterr().out
    network = ipaddress.ip_network("2001:db8::/126")
    assert f"address count: {network.num_addresses}" in out
    assert f"netmask: {network.netmask}" in out
    assert f"usable count: {len(list(network.hosts()))}" in out
    for addr in network:
        assert str(addr) in out


def test_large_cidr_summarizes_without_listing_every_host(capsys):
    assert main(["ip", "10.0.0.0/16"]) == 0
    out = capsys.readouterr().out
    assert "address count: 65536" in out
    assert "usable count: 65534" in out
    assert "address list: omitted (65536 addresses; showing first and last only)" in out
    assert "first: 10.0.0.0" in out
    assert "last: 10.0.255.255" in out
    assert "10.0.0.1" not in out


def test_private_ip_skips_public_lookup(monkeypatch, capsys):
    def boom(*args, **kwargs):
        raise AssertionError("private address should not be looked up")

    monkeypatch.setattr("reconkit.ip.fetch_lookup", boom)
    assert main(["ip", "10.1.2.3"]) == 0
    out = capsys.readouterr().out
    assert "target: 10.1.2.3" in out
    assert "private: yes" in out
    assert "global: no" in out
    assert "reverse name: 3.2.1.10.in-addr.arpa" in out
    assert "lookup: skipped (private address)" in out


def test_public_lookup_prints_geo_and_whois_fields(monkeypatch, capsys):
    def fake_get(url, timeout, headers=None):
        assert url == "https://ipapi.co/8.8.8.8/json/"
        assert timeout == 8.0

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "country_name": "United States",
                    "region": "California",
                    "city": "Mountain View",
                    "org": "GOOGLE",
                    "asn": "AS15169",
                    "latitude": 37.386,
                    "longitude": -122.0838,
                    "timezone": "America/Los_Angeles",
                }

        return Response()

    monkeypatch.setattr("reconkit.ip.requests.get", fake_get)
    assert main(["ip", "8.8.8.8"]) == 0
    out = capsys.readouterr().out
    assert "private: no" in out
    assert "global: yes" in out
    assert "country: United States" in out
    assert "city: Mountain View" in out
    assert "org: GOOGLE" in out
    assert "asn: AS15169" in out
    assert "lat: 37.386" in out


def test_lookup_failure_keeps_local_facts(monkeypatch, capsys):
    def boom(ip, timeout):
        raise requests.Timeout("timed out")

    monkeypatch.setattr("reconkit.ip.fetch_lookup", boom)
    assert main(["ip", "1.1.1.1"]) == 0
    captured = capsys.readouterr()
    assert "target: 1.1.1.1" in captured.out
    assert "reverse name: 1.1.1.1.in-addr.arpa" in captured.out
    assert "lookup: failed" in captured.out
    assert "timed out" in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_bad_target_is_a_message(capsys):
    assert main(["ip", "not-an-ip"]) == 1
    captured = capsys.readouterr()
    assert "not an IP address or CIDR: not-an-ip" in captured.err
    assert "Traceback" not in captured.err
    assert main(["ip", "192.168.0.0/99"]) == 1
    assert "not an IP address or CIDR" in capsys.readouterr().err
