import dns.exception
import dns.resolver

from reconkit.cli import main


class _Rdata:
    def __init__(self, text):
        self._text = text

    def to_text(self):
        return self._text


def test_dns_prints_records_and_reverse(monkeypatch, capsys):
    def fake_resolve(qname, rdtype, lifetime=None):
        name = str(qname).rstrip(".").lower()
        assert lifetime == 5.0
        if rdtype == "A" and name == "example.com":
            return [_Rdata("93.184.216.34")]
        if rdtype == "MX" and name == "example.com":
            return [_Rdata("10 mail.example.com.")]
        if rdtype == "PTR":
            return [_Rdata("example.com.")]
        raise dns.resolver.NoAnswer()

    monkeypatch.setattr(dns.resolver, "resolve", fake_resolve)
    assert main(["dns", "example.com"]) == 0
    out = capsys.readouterr().out
    assert "name: example.com" in out
    assert "A: 93.184.216.34" in out
    assert "AAAA: none" in out
    assert "MX: 10 mail.example.com." in out
    assert "NS: none" in out
    assert "TXT: none" in out
    assert "CNAME: none" in out
    assert "reverse: 93.184.216.34 -> example.com." in out
    assert "Traceback" not in out


def test_dns_reverse_lookup_for_an_ip(monkeypatch, capsys):
    def fake_resolve(qname, rdtype, lifetime=None):
        assert rdtype == "PTR"
        assert "8.8.8.8" in str(qname)
        return [_Rdata("dns.google.")]

    monkeypatch.setattr(dns.resolver, "resolve", fake_resolve)
    assert main(["dns", "8.8.8.8"]) == 0
    out = capsys.readouterr().out
    assert out == "ip: 8.8.8.8\nreverse: 8.8.8.8 -> dns.google.\n"


def test_dns_nxdomain_is_a_clear_message(monkeypatch, capsys):
    def fake_resolve(qname, rdtype, lifetime=None):
        raise dns.resolver.NXDOMAIN()

    monkeypatch.setattr(dns.resolver, "resolve", fake_resolve)
    assert main(["dns", "missing.test"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "name: missing.test\nresult: no such domain\n"
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_dns_timeout_does_not_crash(monkeypatch, capsys):
    def fake_resolve(qname, rdtype, lifetime=None):
        raise dns.exception.Timeout()

    monkeypatch.setattr(dns.resolver, "resolve", fake_resolve)
    assert main(["dns", "example.com"]) == 0
    captured = capsys.readouterr()
    assert "A: timed out" in captured.out
    assert "AAAA: timed out" in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_dns_rejects_blank_name(capsys):
    assert main(["dns", "   "]) == 1
    captured = capsys.readouterr()
    assert "missing name" in captured.err
    assert "Traceback" not in captured.err
