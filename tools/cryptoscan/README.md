# cryptoscan — environment-wide audit of outdated cryptography

`cryptoscan` inventories the cryptography an environment actually relies on
(SSH, TLS, X.509 and CA trust stores, Kerberos, network devices, web and mail
servers, IPsec/VPN, local key material, system crypto policies), grades every
algorithm choice against a selectable policy profile, and renders one
consolidated report: JSON, HTML, Markdown, CycloneDX 1.6 CBOM, CSV and SARIF.

It is **standard-library Python 3.9+** with no third-party dependencies, so the
same file tree runs unmodified on the bastion, the KDC, the mail relay or an
offline image mount. `openssl`, `ssh-keyscan`, `klist`, `gpg`, `certutil` and
`nginx -v` are used when present to enrich results and never required.

It is **read-only**. It never modifies the host, never authenticates, never
sends credentials. Active probes are handshake-only (an SSH `KEXINIT`
exchange, a TLS `ClientHello`, and, only when explicitly enabled, one SNMP
`GET sysDescr` per community). Password hashes, SNMP community strings, key
bytes and Kerberos key material are never written to any report.

## Quick start

```sh
cd tools/cryptoscan

# This host, local collectors only, every report format into ./cryptoscan-report/
python3 -m cryptoscan scan --no-network --format all

# This host plus remote endpoints
python3 -m cryptoscan scan \
    --target ssh://bastion.example.net \
    --target https://www.example.net \
    --target smtp://mail.example.net:25 \
    --target ldap://dc1.example.net:389 \
    --netdev-config /srv/rancid/configs/ \
    --profile nist --format json,html,md,cbom

# A fleet, from an inventory file (see examples/fleet.json)
python3 -m cryptoscan scan --inventory examples/fleet.json --out reports/fleet

# Re-grade a saved inventory under a stricter profile without rescanning
python3 -m cryptoscan report reports/fleet/cryptoscan.json --profile cnsa2 --format md

# Merge per-host JSON results collected elsewhere into one report
python3 -m cryptoscan merge host-a.json host-b.json host-c.json --out reports/all

# What can be found, and by which collector
python3 -m cryptoscan rules
python3 -m cryptoscan collectors
```

Exit code 2 with `--fail-on high` (or any severity) makes it usable as a CI or
compliance gate. `--root /mnt/image` audits an offline root filesystem.
`--hostname` labels local assets for fleet merges.

## What is audited

| Collector | Sources | Examples of what it detects |
|---|---|---|
| `ssh_local` | `sshd -T` or `sshd_config` (+`Include`, `Match`, `+`/`-`/`^` lists), `ssh_config`, host keys, `/etc/ssh/moduli`, user keys, `authorized_keys`, `known_hosts`, Dropbear | `diffie-hellman-group1-sha1`, `ssh-rsa` (SHA-1 signatures), `ssh-dss`, CBC ciphers, `hmac-md5`, `umac-64`, RSA-1024 keys, weak DH moduli, world-readable or unencrypted keys, `Protocol 1`, pre-Terrapin OpenSSH |
| `ssh_remote` | SSH servers reached over the network | Everything the server *offers* in its `KEXINIT` (kex, host-key, cipher, MAC lists), protocol 1.99, host-key sizes via `ssh-keyscan` |
| `tls_remote` | TLS and STARTTLS endpoints (HTTPS, SMTP, IMAP, POP3, FTP, LDAP, PostgreSQL, XMPP, RDP) | SSLv3/TLS 1.0/1.1, RC4, 3DES, export and NULL suites, RSA key transport, anonymous DH, 1024-bit DHE, missing TLS 1.3, SHA-1 or RSA-1024 certificates, expired chains, hostname mismatch, PQ hybrid support |
| `certs_local` | System trust stores (Debian, RHEL, Alpine, SUSE), locally added anchors, service certificates, Java keystores (JKS, JCEKS, PKCS#12), NSS databases | RSA-1024 or SHA-1 roots, expired anchors, enterprise CAs added locally, weak PKCS#12 PBE (RC2-40, 3DES), v1 certificates, long-lived leaves |
| `keys_local` | Private keys, DH/EC parameter files under service and home directories (whole filesystem with `--deep`) | Key sizes, legacy PEM encryption, PBES1, PBKDF2-SHA1, mode 0644, unencrypted keys, 1024-bit `dhparam`, key/certificate pairing by SPKI hash |
| `kerberos` | `krb5.conf` (+`includedir`), `kdc.conf`, keytabs, credential caches, `smb.conf`, offline `msDS-SupportedEncryptionTypes` export | `des-cbc-crc`, `rc4-hmac`, `des3-cbc-sha1`, `allow_weak_crypto`, NTLMv1, SMBv1, accounts still advertising RC4 |
| `netdev` | Saved running-configs: Cisco IOS/IOS-XE/NX-OS/IOS-XR/ASA, Junos, Arista EOS, FortiOS, PAN-OS, MikroTik, Huawei VRP, HP/Aruba, F5; optional telnet/HTTP/SNMP probes | SSHv1, weak SSH algorithms, SNMPv1/v2c, SNMPv3 MD5/DES, type-7 and MD5 passwords, telnet and HTTP management, IKEv1 (aggressive), DES/3DES/MD5 transforms, DH group 1/2, TLS 1.0 management planes, RSA-1024 device keys |
| `web_servers` | nginx, Apache httpd, HAProxy, Postfix, Dovecot, Exim, lighttpd, Tomcat, Spring, Traefik, Envoy, kube-apiserver/kubelet/etcd flags | Protocol and cipher directives (expanded through `openssl ciphers`), missing `dhparam`, 1024-bit DH, legacy defaults of old releases, referenced certificates and keys |
| `ipsec` | strongSwan, libreswan, racoon, OpenVPN, WireGuard, PPTP, L2TP | IKEv1 and aggressive mode, `3des-md5-modp1024`, BF-CBC, SHA-1 auth, PPTP |
| `pgp` | APT and RPM signing keyrings, GnuPG homes (built-in RFC 4880/9580 parser; `gpg` only on a private copy of public keyrings) | RSA-1024 and DSA-1024 signing keys, SHA-1 self-signatures, expired or revoked keys |
| `system_policy` | RHEL crypto-policies, FIPS mode, OpenSSL version and `openssl.cnf` (`SECLEVEL`, `MinProtocol`, legacy provider), GnuTLS priorities, Java `java.security`, `login.defs`/PAM/shadow hash types, optional LUKS | `LEGACY` policy, SECLEVEL 1, TLS 1.0 minimum, weakened `jdk.tls.disabledAlgorithms`, MD5-crypt or DES-crypt password hashes, EOL OpenSSL |

Every finding carries a stable rule id (`python3 -m cryptoscan rules` lists the
109 ids the engine can emit), the asset, the exact raw name as the source spelled
it, a remediation and the standards it rests on.

## Policy profiles

| Profile | Basis | Notable thresholds |
|---|---|---|
| `nist` (default) | NIST SP 800-131A Rev.2, SP 800-57 Pt.1 Rev.5, SP 800-52 Rev.2, FIPS 186-5, NIST IR 8547 | RSA/DH < 2048 and EC < 224 are HIGH (disallowed since 2014); DSA withdrawn; SHA-1 signatures HIGH; 3DES HIGH (disallowed after 2023); RSA-2048 / P-224 / DH-2048 flagged LOW as "deprecated after 2030, disallowed after 2035"; TLS 1.2-only is INFO |
| `cnsa2` | NSA CNSA 2.0 | RSA ≥ 3072, ECDH/ECDSA P-384 only, SHA-384, AES-256; any non-post-quantum key exchange is MEDIUM; Ed25519/X25519 not permitted |
| `bsi` | BSI TR-02102-1 (2024) | RSA/DH ≥ 3000, EC ≥ 250, SHA-2/3 only, CBC in TLS MEDIUM |
| `legacy` | Brownfield triage | Only broken or formally disallowed material is raised above INFO (RSA < 2048, DSA, SHA-1/MD5 signatures, RC4/DES/3DES, SSLv3/TLS 1.0/1.1, SSHv1, DES/RC4 Kerberos, SNMPv1/v2c) |

Profiles are a re-grade of the saved JSON inventory, not a rescan.

### Post-quantum exposure

Every asset that depends on RSA, DSA, finite-field or elliptic-curve
Diffie-Hellman, ECDSA or EdDSA receives one `PQC-TRANSITION` finding naming the
algorithms, whether a quantum-safe hybrid (`X25519MLKEM768`,
`mlkem768x25519-sha256`, `sntrup761x25519-sha512`) is also offered, and the
NIST IR 8547 dates (deprecated after 2030 for 112-bit security, disallowed
after 2035). The HTML and Markdown reports roll this up into a readiness
section and a deprecation timeline, which is the input a harvest-now-
decrypt-later risk review needs.

### Severity conventions

| Severity | Meaning |
|---|---|
| CRITICAL | Practically broken today: RC4, DES, export suites, MD5 signatures, SSLv2/v3, SSHv1, DH < 1024, anonymous key exchange, Telnet management, type-7 passwords, Kerberos DES |
| HIGH | Formally disallowed or attack-demonstrated: RSA/DH 1024, DSA, SHA-1 signatures, 3DES, TLS 1.0/1.1, SNMPv1/v2c, Kerberos RC4/3DES, IKEv1, world-readable keys, expired certificates |
| MEDIUM | Weakens the protocol or the profile forbids it: no forward secrecy, CBC in SSH, truncated MACs, SNMPv3 MD5, below-profile key sizes, legacy PEM encryption |
| LOW | Sunset material and hygiene: RSA-2048 / P-224 after 2030, HMAC-SHA1, missing `dhparam`, long-lived or SAN-less certificates |
| INFO | Inventory facts: PQC exposure, root self-signatures, TLS 1.2 presence under `nist` |

Two deliberate quiet zones: a self-signed CA's own signature hash is
informational (relying parties never verify it; its key size is still graded),
and key or certificate material found under `tests/`, `fixtures/`, `examples/`
or similar trees is tagged `test-data` and capped at LOW.

## Reports

| Format | File | Use |
|---|---|---|
| `json` | `cryptoscan.json` | Complete inventory and findings; input to `report`, `merge`, diffs between runs (ids are stable) |
| `html` | `cryptoscan.html` | Single self-contained page: score, severity tiles, top rules, PQC donut, expiry timeline, filterable and sortable findings, asset and algorithm inventories, coverage, methodology. No external resources |
| `md` | `cryptoscan.md` | Same content for wikis, tickets and PRs |
| `cbom` | `cryptoscan.cbom.json` | CycloneDX 1.6 cryptographic bill of materials: algorithm, certificate, protocol and key-material components with classical and NIST quantum security levels, dependencies, and findings as vulnerabilities |
| `csv` | `cryptoscan.findings.csv`, `cryptoscan.uses.csv` | Spreadsheets; formula-injection safe |
| `sarif` | `cryptoscan.sarif` | Upload to code-scanning / security dashboards |

## Targets and inventories

Targets are `[label=][service://]host[:port]`. Services: `ssh`, `https`/`tls`,
`smtp`, `smtps`, `imap`, `imaps`, `pop3`, `pop3s`, `ldap`, `ldaps`, `ftp`,
`ftps`, `postgres`, `xmpp`, `rdp`, `snmp`, `netdev`, `auto`. With `auto`,
the port decides (22 → SSH, 443/8443/465/993/... → TLS, 25/587/143/110/21/389/
5432 → STARTTLS, 23/80/161 → device management probes).

An inventory (`--inventory fleet.json`, see `examples/fleet.json`) lists
targets, directories of saved device configurations, extra paths to scan,
collector options and the probe switches. Options that collectors read:

| Option | Collector | Meaning |
|---|---|---|
| `workers` | remote collectors | thread pool size (16) |
| `tls_max_handshakes`, `tls_target_deadline` | `tls_remote` | caps per endpoint (120 handshakes, 90 s) |
| `keyscan` | `ssh_remote` | use `ssh-keyscan` for host-key sizes (true) |
| `snmp_communities` | `netdev` | communities tried with `--snmp-probe` (`public`) |
| `home_dirs`, `home_scan_depth` | `ssh_local`, `keys_local` | override home discovery; home walk depth (2, or 6 with `--deep`) |
| `ad_enctype_export` | `kerberos` | CSV/JSON export of `msDS-SupportedEncryptionTypes` (PowerShell command in the module docstring) |
| `krb5_version`, `openvpn_version` | `kerberos`, `ipsec` | library versions for default-list inference on offline roots |
| `luks` | `system_policy` | opt-in `cryptsetup luksDump` inventory (needs root) |

Pass any option with `--opt key=value`.

## Authorisation and safety

Remote probing is a network action. Run it only against systems you are
authorised to assess; `--no-network` restricts the run to local sources and
offline configuration files. SNMP community probing is off unless
`--snmp-probe` is given, because it sends a community string on the wire.

## Design

```
collectors/*   discover assets and record CryptoUse occurrences (never grade)
names.py       normalise OpenSSH, IANA/OpenSSL TLS, Kerberos and device spellings
policy.py      profiles + rules: (asset, use, profile, now) -> findings, pure functions
report/*       summary, markdown, html, cbom, csv, sarif
asn1.py x509.py sshkeys.py jks.py keytab.py snmp.py sshwire.py   dependency-free parsers
```

Collectors never grade and the policy never does I/O, so a new rule is one
function and a new source is one collector. `python3 -m cryptoscan rules`
derives the rule catalogue from the engine itself, which keeps the
documentation honest.

## Tests

```sh
cd tools/cryptoscan
python3 -m unittest discover -s tests -v
ruff check .
```

The suite is offline: committed fixtures (certificates and keys generated with
`openssl` at fixture time, hand-built keytabs, OpenPGP packets, device
configurations) and in-process fake SSH, TLS, SMTP, PostgreSQL and SNMP
services on loopback. CI (`.github/workflows/cryptoscan.yml`) runs it on
Python 3.9 and 3.13 and self-scans the runner.

## Limitations

- Windows hosts are not inspected directly (Schannel, AD policy, DPAPI); the
  Kerberos collector accepts an offline Active Directory export instead.
- Remote probes report what a server *offers*; what real clients negotiate
  depends on the client. Use the configuration collectors for the server side.
- SSLv2/SSLv3 cannot be probed by Python's `ssl` module; `openssl s_client` is
  used when available, otherwise the report says the probe was unsupported.
- No source-code scanning for application-embedded cryptography, no HSM/KMS
  inventories, no DTLS probing, and SNMPv3 users are not enumerated.
- JCEKS secret-key entries and MySQL STARTTLS are not decoded.
