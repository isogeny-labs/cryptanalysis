"""Data model shared by every collector, the policy engine and the reports.

An *Asset* is a thing that carries cryptography (a host key, a certificate, a
daemon configuration, a keytab entry).  A *CryptoUse* is one concrete algorithm
choice found on that asset (an RSA-1024 public key, a `diffie-hellman-group1-sha1`
key exchange, an `rc4-hmac` enctype).  The policy engine turns each CryptoUse
into zero or more *Findings*.  Collectors only produce assets and uses; they
never grade.  That keeps the grading rules in one place and testable.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import enum
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


class Severity(enum.IntEnum):
    """Ordered so that max() picks the worst."""

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def label(self) -> str:
        return self.name.lower()


class Primitive(str, enum.Enum):
    """What role the algorithm plays.  Used to pick the right rule family."""

    PUBLIC_KEY = "public_key"          # RSA / EC / DSA / EdDSA / DH key material
    SIGNATURE = "signature"            # signature algorithm (incl. its hash)
    KEY_EXCHANGE = "key_exchange"      # DH groups, ECDH curves, KEMs, SSH kex names
    CIPHER = "cipher"                  # symmetric cipher (+ mode)
    MAC = "mac"
    HASH = "hash"
    PROTOCOL = "protocol"              # SSLv3, TLS1.0, SSHv1, SNMPv1, NTLM ...
    KDF = "kdf"
    ENCTYPE = "enctype"                # Kerberos encryption type
    CERTIFICATE = "certificate"        # certificate-level properties (validity, ...)
    CONFIG = "config"                  # a configuration knob (FIPS mode, policy)


class AssetKind(str, enum.Enum):
    SSH_SERVER = "ssh_server"
    SSH_CLIENT = "ssh_client"
    SSH_HOST_KEY = "ssh_host_key"
    SSH_USER_KEY = "ssh_user_key"
    SSH_AUTHORIZED_KEY = "ssh_authorized_key"
    SSH_KNOWN_HOST = "ssh_known_host"
    SSH_REMOTE = "ssh_remote"
    TLS_ENDPOINT = "tls_endpoint"
    CERTIFICATE = "certificate"
    CA_CERTIFICATE = "ca_certificate"
    PRIVATE_KEY = "private_key"
    TRUST_STORE = "trust_store"
    KERBEROS_CONFIG = "kerberos_config"
    KERBEROS_KEYTAB = "kerberos_keytab"
    KERBEROS_TICKET = "kerberos_ticket"
    NETWORK_DEVICE = "network_device"
    IPSEC_CONFIG = "ipsec_config"
    VPN_CONFIG = "vpn_config"
    SYSTEM_POLICY = "system_policy"
    PGP_KEY = "pgp_key"
    SNMP_AGENT = "snmp_agent"
    JAVA_KEYSTORE = "java_keystore"
    OTHER = "other"


@dataclass
class CryptoUse:
    """One concrete algorithm occurrence on an asset."""

    primitive: Primitive
    algorithm: str                      # canonical lower-case name, e.g. "rsa", "ecdsa", "aes-128-cbc"
    key_bits: Optional[int] = None      # modulus / group size in bits
    curve: Optional[str] = None         # named curve, canonical ("p-256", "secp256k1", "curve25519")
    hash_algorithm: Optional[str] = None   # for signatures / MACs / PRFs
    mode: Optional[str] = None          # cipher mode ("cbc", "gcm", ...)
    raw: Optional[str] = None           # the name exactly as the source spelled it
    context: Optional[str] = None       # "kex", "hostkey", "cipher", "mac", "tgt-session-key" ...
    negotiated: Optional[bool] = None   # True = observed in use, False = merely offered/configured
    extra: Dict[str, Any] = field(default_factory=dict)

    def describe(self) -> str:
        parts = [self.algorithm]
        if self.key_bits:
            parts.append(f"{self.key_bits}-bit")
        if self.curve:
            parts.append(self.curve)
        if self.hash_algorithm:
            parts.append(f"with {self.hash_algorithm}")
        if self.mode:
            parts.append(f"({self.mode})")
        return " ".join(parts)


@dataclass
class Asset:
    kind: AssetKind
    name: str                               # human label ("sshd on host-a", "/etc/ssl/certs/x.pem")
    location: str                           # file path, host:port, device name
    collector: str                          # which collector produced it
    host: Optional[str] = None              # the host the asset belongs to (for fleet scans)
    uses: List[CryptoUse] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)   # cert subject, expiry, owner, perms, ...
    errors: List[str] = field(default_factory=list)            # non-fatal problems while collecting
    asset_id: str = ""

    def __post_init__(self) -> None:
        if not self.asset_id:
            h = hashlib.sha256(f"{self.kind.value}|{self.host or ''}|{self.location}|{self.name}".encode()).hexdigest()
            self.asset_id = h[:16]

    def add(self, use: CryptoUse) -> CryptoUse:
        self.uses.append(use)
        return use


@dataclass
class Finding:
    """A graded problem.  One asset + one use (or asset-level) -> one finding."""

    rule_id: str                      # stable id, e.g. "PK-RSA-LT-2048"
    title: str
    severity: Severity
    asset_id: str
    asset_kind: AssetKind
    asset_name: str
    location: str
    collector: str
    description: str
    remediation: str
    host: Optional[str] = None
    use: Optional[CryptoUse] = None
    references: List[str] = field(default_factory=list)
    quantum_vulnerable: bool = False       # Shor-breakable public-key material
    deprecation_year: Optional[int] = None  # policy-driven "disallowed after" year
    tags: List[str] = field(default_factory=list)
    finding_id: str = ""

    def __post_init__(self) -> None:
        if not self.finding_id:
            key = f"{self.rule_id}|{self.asset_id}|{self.use.raw if self.use else ''}|{self.use.context if self.use else ''}"
            self.finding_id = hashlib.sha256(key.encode()).hexdigest()[:16]


@dataclass
class ScanMeta:
    tool: str = "cryptoscan"
    version: str = ""
    started: str = ""
    finished: str = ""
    hostname: str = ""
    profile: str = ""
    targets: List[str] = field(default_factory=list)
    collectors_run: List[str] = field(default_factory=list)
    collectors_skipped: Dict[str, str] = field(default_factory=dict)
    command_line: List[str] = field(default_factory=list)


@dataclass
class ScanResult:
    meta: ScanMeta
    assets: List[Asset] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)

    # ---- helpers used by the reports ------------------------------------
    def severity_counts(self) -> Dict[str, int]:
        counts = {s.label: 0 for s in Severity}
        for f in self.findings:
            counts[f.severity.label] += 1
        return counts

    def worst(self) -> Severity:
        return max((f.severity for f in self.findings), default=Severity.INFO)

    def findings_for(self, asset_id: str) -> List[Finding]:
        return [f for f in self.findings if f.asset_id == asset_id]

    def to_dict(self) -> Dict[str, Any]:
        return _to_jsonable(dataclasses.asdict(self))

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ScanResult:
        meta = ScanMeta(**d.get("meta", {}))
        assets = []
        for a in d.get("assets", []):
            a = dict(a)
            a["kind"] = AssetKind(a["kind"])
            a["uses"] = [_use_from_dict(u) for u in a.get("uses", [])]
            assets.append(Asset(**a))
        findings = []
        for f in d.get("findings", []):
            f = dict(f)
            f["severity"] = Severity(f["severity"]) if isinstance(f["severity"], int) else Severity[f["severity"].upper()]
            f["asset_kind"] = AssetKind(f["asset_kind"])
            if f.get("use"):
                f["use"] = _use_from_dict(f["use"])
            findings.append(Finding(**f))
        return cls(meta=meta, assets=assets, findings=findings)


def _use_from_dict(u: Dict[str, Any]) -> CryptoUse:
    u = dict(u)
    u["primitive"] = Primitive(u["primitive"])
    return CryptoUse(**u)


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, Severity):
        return obj.label
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.hex()
    return obj


def utcnow_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def merge_results(results: Iterable[ScanResult]) -> ScanResult:
    """Merge per-host results into one fleet report (deduplicating by id)."""
    results = list(results)
    if not results:
        return ScanResult(meta=ScanMeta())
    base = results[0]
    seen_assets = {a.asset_id for a in base.assets}
    seen_findings = {f.finding_id for f in base.findings}
    for r in results[1:]:
        for a in r.assets:
            if a.asset_id not in seen_assets:
                base.assets.append(a)
                seen_assets.add(a.asset_id)
        for f in r.findings:
            if f.finding_id not in seen_findings:
                base.findings.append(f)
                seen_findings.add(f.finding_id)
        base.meta.targets.extend(t for t in r.meta.targets if t not in base.meta.targets)
        base.meta.collectors_run.extend(c for c in r.meta.collectors_run if c not in base.meta.collectors_run)
    return base
