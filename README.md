![reconkit banner](docs/reconkit-banner.jpg)

# reconkit

A single Python CLI for DNS lookups, Google dork queries, everyday encoding, proxy checks, and IP/CIDR summaries.

**Authorized use only.** Point reconkit at domains, proxies, and addresses you own or are allowed to investigate. It is a local helper for your own targets, not a scanner for networks you do not have permission to check.

## Install

Python 3.9 or newer. From a clone of this repo:

```bash
python -m pip install .
reconkit --help
```

Virtualenv setup for Linux, macOS, and Windows, plus timeout and dependency troubleshooting, is in [INSTALL.md](INSTALL.md).

To run the tests:

```bash
python -m pip install -e ".[dev]"
pytest
```

## Commands

### dns

Resolve A, AAAA, MX, NS, TXT, and CNAME records. When an address comes back, reconkit also asks for its PTR. Pass an IP to do only the reverse lookup. A missing name, a timeout, or an empty record set prints a message and does not dump a traceback.

```bash
reconkit dns example.com
reconkit dns 8.8.8.8
```

### dork

Build a Google dork from the flags you pass and print the query plus a `google.com/search` URL. This command only builds a string. It does not contact Google.

```bash
reconkit dork --site example.com --filetype pdf
```

```text
site:example.com filetype:pdf
https://www.google.com/search?q=site%3Aexample.com+filetype%3Apdf
```

Phrases with spaces are quoted (`intitle:"index of"`).

### crypt

Encode or decode text as hex, base64, base32, URL encoding, or rot13, or print an md5, sha1, or sha256 digest. The standard library does the work. Omit the text argument to read stdin exactly (a trailing newline changes the digest).

```bash
reconkit crypt encode --base64 hello
reconkit crypt decode --hex 6869
reconkit crypt hash --sha256 hi
printf 'hello' | reconkit crypt encode --base64
```

`hello` encodes to `aGVsbG8=`. `hi` hashed with sha256 is `8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4`.

### proxy

Read `host:port` lines from a file or stdin (`#` comments and blank lines are skipped). reconkit requests a URL through each proxy at the same time and prints a table of the ones that respond, with status and latency.

```bash
printf '%s\n' '1.2.3.4:8080' '10.0.0.1:3128' | reconkit proxy
reconkit proxy proxies.txt --timeout 3 --url http://example.com
```

Lines without a scheme are tried as `http://`. A connection error or timeout leaves that proxy out of the table.

### ip

Show what the standard library knows about an address or CIDR: version, privacy, netmask, broadcast, size, and the address list when the network has 256 addresses or fewer. A single global IP also gets a geo and whois-style lookup (country, city, org, ASN) from [ipapi.co](https://ipapi.co/). Private networks, other non-routable addresses, and CIDR blocks skip that call. If the lookup fails, the local summary is still printed.

```bash
reconkit ip 192.168.0.0/30
reconkit ip 8.8.8.8
```

```text
input: 192.168.0.0/30
network: 192.168.0.0/30
version: IPv4
private: yes
broadcast: 192.168.0.3
netmask: 255.255.255.252
prefix: 30
address count: 4
usable count: 2
address list:
  192.168.0.0
  192.168.0.1
  192.168.0.2
  192.168.0.3
usable hosts:
  192.168.0.1
  192.168.0.2
lookup: skipped (private network)
```
