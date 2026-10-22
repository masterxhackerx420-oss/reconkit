import pytest

from reconkit.cli import main
from reconkit.dork import build_query, search_url


def test_build_query_site_and_filetype():
    query = build_query(site="example.com", filetype="pdf")
    assert query == "site:example.com filetype:pdf"
    assert search_url(query) == (
        "https://www.google.com/search?q=site%3Aexample.com+filetype%3Apdf"
    )


def test_build_query_quotes_phrases_and_keeps_operator_order():
    query = build_query(
        intext="password reset",
        site="example.com",
        intitle='index of "backup"',
        inurl="/admin",
        filetype="xls",
    )
    assert query == (
        'site:example.com filetype:xls intitle:"index of backup" '
        'inurl:/admin intext:"password reset"'
    )
    url = search_url(query)
    assert url.startswith("https://www.google.com/search?q=")
    assert "site%3Aexample.com" in url
    assert "+" in url


def test_build_query_ignores_blank_flags():
    assert build_query(site="  example.com  ", filetype="  ") == "site:example.com"


def test_build_query_requires_a_flag():
    with pytest.raises(ValueError):
        build_query()


def test_cli_prints_query_and_url(capsys):
    code = main(["dork", "--site", "example.com", "--filetype", "pdf"])
    out = capsys.readouterr().out
    assert code == 0
    assert out == (
        "site:example.com filetype:pdf\n"
        "https://www.google.com/search?q=site%3Aexample.com+filetype%3Apdf\n"
    )


def test_cli_rejects_empty_dork(capsys):
    code = main(["dork", "--site", "   "])
    captured = capsys.readouterr()
    assert code == 1
    assert "provide at least one" in captured.err
    assert captured.out == ""
