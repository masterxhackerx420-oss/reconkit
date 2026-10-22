import requests

from reconkit.cli import main
from reconkit.proxy import parse_proxies


def test_parse_proxies_keeps_valid_lines_and_reports_junk():
    text = """
    # comment
    1.2.3.4:8080

    http://10.0.0.1:3128
    https://[2001:db8::1]:443
    not a proxy
    1.2.3.4:99999
    socks5://10.0.0.2:1080
    """
    good, bad = parse_proxies(text)
    assert good == [
        "http://1.2.3.4:8080",
        "http://10.0.0.1:3128",
        "https://[2001:db8::1]:443",
    ]
    assert bad == [
        "not a proxy",
        "1.2.3.4:99999",
        "socks5://10.0.0.2:1080",
    ]


def test_proxy_table_lists_only_responding_proxies(monkeypatch, capsys, tmp_path):
    path = tmp_path / "proxies.txt"
    path.write_text(
        "\n".join(
            [
                "# pool",
                "1.2.3.4:8080",
                "bad-entry",
                "10.0.0.9:1",
                "",
            ]
        ),
        encoding="utf-8",
    )
    seen = []

    def fake_get(url, **kwargs):
        proxy = kwargs["proxies"]["http"]
        seen.append(proxy)
        assert url == "http://example.com"
        assert kwargs["timeout"] == 5.0
        if proxy.endswith(":1"):
            raise requests.Timeout("timed out")

        class Response:
            status_code = 204

            def close(self):
                return None

        return Response()

    monkeypatch.setattr("reconkit.proxy.requests.get", fake_get)
    code = main(["proxy", str(path), "--workers", "4"])
    captured = capsys.readouterr()
    assert code == 0
    assert set(seen) == {"http://1.2.3.4:8080", "http://10.0.0.9:1"}
    assert "http://1.2.3.4:8080" in captured.out
    assert "204" in captured.out
    assert "10.0.0.9" not in captured.out
    assert "1 of 2 proxies responded" in captured.out
    assert "proxy: skipped invalid entry: bad-entry" in captured.err
    assert "Traceback" not in captured.err


def test_proxy_preserves_input_order(monkeypatch, capsys, tmp_path):
    path = tmp_path / "proxies.txt"
    path.write_text("2.2.2.2:2\n1.1.1.1:1\n", encoding="utf-8")

    def fake_get(url, **kwargs):
        class Response:
            status_code = 200

            def close(self):
                return None

        return Response()

    monkeypatch.setattr("reconkit.proxy.requests.get", fake_get)
    assert main(["proxy", str(path)]) == 0
    out = capsys.readouterr().out
    assert out.find("2.2.2.2") < out.find("1.1.1.1")
    assert "2 of 2 proxies responded" in out


def test_proxy_missing_file_and_empty_list(capsys, tmp_path):
    assert main(["proxy", str(tmp_path / "missing.txt")]) == 1
    captured = capsys.readouterr()
    assert "cannot read" in captured.err
    assert "Traceback" not in captured.err

    empty = tmp_path / "empty.txt"
    empty.write_text("# nothing\n\n", encoding="utf-8")
    assert main(["proxy", str(empty)]) == 1
    assert "no proxies to check" in capsys.readouterr().err
