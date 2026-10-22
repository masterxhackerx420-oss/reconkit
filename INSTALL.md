# Installing reconkit

reconkit is a command-line tool. Installing it puts a `reconkit` script on your `PATH` and installs three Python packages with it: [dnspython](https://pypi.org/project/dnspython/) (imported as `dns`), [requests](https://pypi.org/project/requests/), and [rich](https://pypi.org/project/rich/). Encoding (`crypt`) and dork query building use only the Python standard library. Tests are optional and need pytest.

## Requirements

- Python 3.9 or newer (`python3 --version` or `py -3 --version`)
- `pip` for that same interpreter (`python -m pip --version`)
- Network access to PyPI while installing (`pypi.org` and `files.pythonhosted.org`)

No C compiler is required for a normal install. dnspython, requests, and rich publish wheels, and pip downloads setuptools (the build backend declared in `pyproject.toml`) on its own.

You do not need a GitHub account. You do need `git` if you clone the repository.

## Install from source

```bash
git clone https://github.com/masterxhackerx420-oss/reconkit.git
cd reconkit
python -m pip install .
```

On Windows, if `python` is not on `PATH`, use `py -3 -m pip install .` instead.

`pip install .` builds the package from the current directory and installs the `reconkit` console script (`reconkit.cli:main`). It also installs `dnspython>=2.4`, `requests>=2.31`, and `rich>=13.0`.

Upgrade pip first if it is older than the one shipped with Python 3.9:

```bash
python -m pip install --upgrade pip
python -m pip install .
```

To install the test extra as well:

```bash
python -m pip install -e ".[dev]"
pytest
```

That extra is pytest only. `-e` installs an editable checkout, so edits under `reconkit/` are picked up without reinstalling.

## Virtual environments

Install into a virtual environment so reconkit does not mix with other projects. Create the environment with the same Python you will use to run the tool.

### Linux and macOS

```bash
git clone https://github.com/masterxhackerx420-oss/reconkit.git
cd reconkit
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

Leave the environment later with `deactivate`.

### Windows

From `cmd.exe`:

```bat
git clone https://github.com/masterxhackerx420-oss/reconkit.git
cd reconkit
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install .
```

From PowerShell, activation is `.venv\Scripts\Activate.ps1`. If execution policy blocks that script, use `cmd.exe` for the activate step, or run `.venv\Scripts\python -m pip install .` without activating and call `.venv\Scripts\reconkit` directly.

## Verify

Activate the environment you installed into, then run:

```bash
reconkit --help
reconkit dork --site example.com --filetype pdf
```

`--help` lists `dns`, `dork`, `crypt`, `proxy`, and `ip`. The dork command only builds a string. It does not use the network. Expected output:

```text
site:example.com filetype:pdf
https://www.google.com/search?q=site%3Aexample.com+filetype%3Apdf
```

These are offline too, if you want a second check:

```bash
reconkit crypt encode --base64 hello
reconkit ip 192.168.0.0/30
```

`crypt encode --base64 hello` prints `aGVsbG8=`. The `/30` command prints the netmask `255.255.255.252`, four addresses, and two usable hosts, and it skips the public lookup because the network is private.

If `reconkit` is not found but the install succeeded, the environment is not active or its scripts directory is not on `PATH`. From the repo you can run `python -m reconkit --help` with the interpreter that performed the install.

## Troubleshooting

### Network and timeout errors

`dork` and `crypt` never open a connection. `dns`, `proxy`, and a public `ip` lookup do.

**DNS.** `reconkit dns` asks your system resolver through dnspython. The default wait is 5 seconds per query (`--timeout`). A slow or blocked resolver does not raise a traceback. Each record type gets a line such as `A: timed out`, `AAAA: none`, or `MX: no nameservers`. An unknown name prints `result: no such domain`. The process still exits 0 after printing that report. Raise the wait with `reconkit dns example.com --timeout 15` if the resolver is just slow. A timeout here is local DNS, not PyPI and not ipapi.co.

**Proxy.** `reconkit proxy` requests `http://example.com` through each `host:port` line (override with `--url`). The default per-proxy timeout is 5 seconds (`--timeout`). A connection error or timeout drops that proxy from the table. If nothing answers, the command prints `proxy: no working proxies` on stderr and exits 1. Invalid lines print `proxy: skipped invalid entry: ...` and are not checked. This command needs working proxy addresses; it is not an offline check.

**IP lookup.** `reconkit ip 8.8.8.8` prints local facts from the standard library, then requests `https://ipapi.co/<ip>/json/` with a default timeout of 8 seconds (`--timeout`). On a network or HTTP failure the local block is still printed and the last line looks like `lookup: failed (Timeout: ...)` or `lookup: failed (HTTPError: ...)`. The exit code stays 0. Private, loopback, reserved, and other non-global addresses skip the call (`lookup: skipped (private address)` and similar). A CIDR skips it as well. `reconkit ip 8.8.8.8 --no-lookup` prints only the local facts.

### Missing system packages

`python3 -m venv .venv` on Debian or Ubuntu fails with `ensurepip is not available` when the venv package is not installed. Install it, delete the half-created `.venv`, and create it again:

```bash
sudo apt install python3-venv
rm -rf .venv
python3 -m venv .venv
```

If that Python is specifically 3.12, the package name may be `python3.12-venv`. `pip` itself comes from the `python3-pip` package when you are not using a venv.

On macOS, install Python 3.9+ from [python.org](https://www.python.org/downloads/) or Homebrew (`brew install python`). The Homebrew binary is often `python3`. Use that same name for `python3 -m venv` and `python3 -m pip`.

On Windows, install Python from [python.org](https://www.python.org/downloads/) and enable "Add python.exe to PATH", or rely on the `py` launcher (`py -3`). If activation is blocked in PowerShell, use `cmd.exe` or call `.venv\Scripts\python.exe` and `.venv\Scripts\reconkit.exe` by path.

`ModuleNotFoundError: No module named 'venv'` means that install of Python was built without venv. Use another Python 3.9+ install, or install the distro package above.

### dnspython, requests, and rich

The console script imports every subcommand, so `reconkit --help` needs all three packages. A failed or partial install shows up immediately:

- `ModuleNotFoundError: No module named 'dns'` or `'dns.resolver'` — dnspython is missing. The PyPI project to install is **`dnspython`**, not a project named `dns`. A leftover `dns` distribution can shadow dnspython. Remove both, then reinstall this project:

  ```bash
  python -m pip uninstall -y dns dnspython
  python -m pip install .
  ```

- `ModuleNotFoundError: No module named 'requests'` or `No module named 'rich'` — that dependency was not installed into this interpreter. Check `python -m pip show requests rich dnspython` using the same `python` that launched reconkit. `which reconkit` (or `where reconkit` on Windows) should point into that environment.

- `error: externally-managed-environment` — the system Python refuses pip installs. Create a venv with the steps above and install there. Do not use `--break-system-packages` unless you intend to change the system interpreter.

- `Could not find a version that satisfies the requirement dnspython` (or requests) — pip cannot see a release that supports this Python, or it cannot reach PyPI. Confirm `python --version` is 3.9 or newer and that `python -m pip install --upgrade pip` can reach the network. Corporate TLS interception sometimes breaks pip until you point it at your CA bundle (`pip config set global.cert /path/to/ca.pem`) or use a machine that can reach `pypi.org`.

- Build fails while isolating `setuptools>=68` — pip is too old to fetch the build backend, or PyPI is blocked. Upgrade pip, then run `python -m pip install .` again from the repository root (the directory that contains `pyproject.toml`).

After fixing the environment, `python -c "import dns.resolver, requests, rich"` should print nothing, and `reconkit --help` should list the five commands.
