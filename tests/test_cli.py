import pytest

from reconkit.cli import main


def test_help_lists_every_command(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for name in ("dns", "dork", "crypt", "proxy", "ip"):
        assert name in out
    assert "Authorized use only" in out
