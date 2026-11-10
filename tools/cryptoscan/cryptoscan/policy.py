"""Policy engine: turns CryptoUse occurrences into graded Findings.

Profiles
--------
nist    NIST SP 800-131A Rev.2 (transitions), SP 800-57 Pt.1 Rev.5 (strengths),
        SP 800-52 Rev.2 (TLS), FIPS 186-5 (DSA withdrawn, binary curves
        deprecated), NIST IR 8547 (PQC transition: 112-bit quantum-vulnerable
        algorithms deprecated after 2030, all quantum-vulnerable public-key
        algorithms disallowed after 2035).  Default.
cnsa2   NSA CNSA 2.0: RSA >= 3072, ECDH/ECDSA P-384 only, SHA-384, AES-256,
        ML-KEM-1024 / ML-DSA-87 / LMS / XMSS; quantum-vulnerable algorithms
        flagged for transition.
bsi     BSI TR-02102-1 (2024): RSA/DH >= 3000 bits, EC >= 250 bits, SHA-2/3 only,
        AES; prefers Brainpool/NIST prime curves; 3DES not permitted.
legacy  Brownfield triage: only broken or formally disallowed algorithms are
        raised above INFO (RSA < 2048, DSA, SHA-1/MD5 signatures, RC4/DES/3DES,
        SSLv3/TLS1.0/1.1, SSHv1, DES/RC4 Kerberos, SNMPv1/v2c).

Every rule is a pure function of (asset, use, profile, now); nothing here does
I/O.  Rule ids are stable so that reports can be diffed between runs.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from .model import Asset, AssetKind, CryptoUse, Finding, Primitive, Severity

REF = {
    "131A": "NIST SP 800-131A Rev.2",
    "57": "NIST SP 800-57 Part 1 Rev.5",
    "52": "NIST SP 800-52 Rev.2",
    "8547": "NIST IR 8547 (Transition to Post-Quantum Cryptography Standards)",
    "186-5": "FIPS 186-5",
    "CNSA2": "NSA CNSA 2.0 (Sep 2022, updated 2024)",
    "BSI": "BSI TR-02102-1 (2024-01)",
    "RFC8996": "RFC 8996 (Deprecating TLS 1.0 and TLS 1.1)",
    "RFC7568": "RFC 7568 (Deprecating SSLv3)",
    "RFC6176": "RFC 6176 (Prohibiting SSLv2)",
    "RFC7465": "RFC 7465 (Prohibiting RC4)",
    "RFC8429": "RFC 8429 (Deprecate 3DES and RC4 in Kerberos)",
    "RFC6649": "RFC 6649 (Deprecate DES in Kerberos)",
    "RFC8270": "RFC 8270 (Increase SSH minimum DH modulus to 2048)",
    "RFC9142": "RFC 9142 (SSH key exchange recommendations)",
    "RFC8332": "RFC 8332 (rsa-sha2-256/512 for SSH)",
    "RFC9155": "RFC 9155 (Deprecating MD5 and SHA-1 signature hashes in TLS 1.2)",
    "RFC9325": "RFC 9325 (BCP 195: TLS/DTLS recommendations)",
    "RFC9395": "RFC 9395 (Deprecation of IKEv1)",
    "RFC3447": "RFC 3447 / PKCS#1",
    "SWEET32": "Sweet32 (CVE-2016-2183): 64-bit block ciphers",
    "LOGJAM": "Logjam (CVE-2015-4000): 1024-bit DH",
    "TERRAPIN": "Terrapin (CVE-2023-48795)",
    "CAB": "CA/Browser Forum Baseline Requirements",
    "RFC8709": "RFC 8709 (Ed25519/Ed448 in SSH)",
    "OPENSSH88": "OpenSSH 8.8 release notes (ssh-rsa SHA-1 signatures disabled)",
    "OPENSSH70": "OpenSSH 7.0 release notes (ssh-dss disabled)",
    "FIPS203": "FIPS 203 (ML-KEM)", "FIPS204": "FIPS 204 (ML-DSA)", "FIPS205": "FIPS 205 (SLH-DSA)",
    "SNMP": "RFC 3414 (SNMPv3 USM); SNMPv1/v2c send community strings in clear",
    "KRBWEAK": "MIT krb5 allow_weak_crypto documentation",
}

QUANTUM_VULNERABLE = {"rsa", "rsa-pss", "rsa-kex", "dsa", "dh", "dhe", "dh-gex", "dh-static", "ec", "ecdsa",
                      "ecdh", "ecdhe", "ecdh-static", "ed25519", "ed448", "x25519", "x448", "ecdsa-sk",
                      "ed25519-sk", "gost-r34.10-2001", "gost-r34.10-2012-256", "gost-r34.10-2012-512", "sm2",
                      "srp", "ecdh-anon", "dh-anon"}
QUANTUM_SAFE = {"hybrid-pq", "ml-kem", "ml-kem-512", "ml-kem-768", "ml-kem-1024", "ml-dsa-44", "ml-dsa-65",
                "ml-dsa-87", "lms", "xmss", "hss"}
BINARY_CURVES = ("sect", "k-", "b-")
NIST_PRIME = {"p-224", "p-256", "p-384", "p-521"}
SIXTY_FOUR_BIT_BLOCK = {"3des", "blowfish", "idea", "cast5", "seed", "rc2", "des", "des40", "kasumi", "magma"}
BROKEN_CIPHERS = {"rc4", "rc2", "des", "des40", "null"}
BROKEN_HASHES = {"md2", "md4", "md5", "crc32", "crc", "none"}


@dataclass
class Profile:
    name: str
    description: str
    rsa_min_bits: int               # below this -> finding at rsa_min_severity
    rsa_min_severity: Severity
    ec_min_bits: int
    ec_min_severity: Severity
    dh_min_bits: int
    dh_min_severity: Severity
    hash_min: str                   # weakest acceptable hash for signatures/MACs
    sym_min_bits: int
    allowed_curves: Optional[set]   # None = any safe curve
    sha1_signature_severity: Severity
    tls12_severity: Severity
    cbc_severity: Severity          # TLS/SSH CBC modes
    quantum_report: bool            # emit PQC transition findings
    pq_deprecation_year: Optional[int]
    pq_disallow_year: Optional[int]
    strict_pq: bool = False         # cnsa2: non-PQ is itself a finding
    references: List[str] = field(default_factory=list)


PROFILES: Dict[str, Profile] = {
    "nist": Profile(
        name="nist", description="NIST SP 800-131A r2 / SP 800-57 / FIPS 186-5 / IR 8547 transition timeline",
        rsa_min_bits=2048, rsa_min_severity=Severity.HIGH, ec_min_bits=224, ec_min_severity=Severity.HIGH,
        dh_min_bits=2048, dh_min_severity=Severity.HIGH, hash_min="sha224", sym_min_bits=112,
        allowed_curves=None, sha1_signature_severity=Severity.HIGH, tls12_severity=Severity.INFO,
        cbc_severity=Severity.LOW, quantum_report=True, pq_deprecation_year=2030, pq_disallow_year=2035,
        references=[REF["131A"], REF["57"], REF["186-5"], REF["8547"]]),
    "cnsa2": Profile(
        name="cnsa2", description="NSA CNSA 2.0 (RSA>=3072, P-384, SHA-384, AES-256, ML-KEM-1024/ML-DSA-87)",
        rsa_min_bits=3072, rsa_min_severity=Severity.MEDIUM, ec_min_bits=384, ec_min_severity=Severity.MEDIUM,
        dh_min_bits=3072, dh_min_severity=Severity.MEDIUM, hash_min="sha384", sym_min_bits=256,
        allowed_curves={"p-384"}, sha1_signature_severity=Severity.HIGH, tls12_severity=Severity.LOW,
        cbc_severity=Severity.MEDIUM, quantum_report=True, pq_deprecation_year=2027, pq_disallow_year=2033,
        strict_pq=True, references=[REF["CNSA2"]]),
    "bsi": Profile(
        name="bsi", description="BSI TR-02102-1 (RSA/DH>=3000, EC>=250, SHA-2/3, AES)",
        rsa_min_bits=3000, rsa_min_severity=Severity.MEDIUM, ec_min_bits=250, ec_min_severity=Severity.MEDIUM,
        dh_min_bits=3000, dh_min_severity=Severity.MEDIUM, hash_min="sha256", sym_min_bits=128,
        allowed_curves=None, sha1_signature_severity=Severity.HIGH, tls12_severity=Severity.LOW,
        cbc_severity=Severity.MEDIUM, quantum_report=True, pq_deprecation_year=2030, pq_disallow_year=None,
        references=[REF["BSI"]]),
    "legacy": Profile(
        name="legacy", description="Brownfield triage: only broken or formally disallowed algorithms are raised",
        rsa_min_bits=2048, rsa_min_severity=Severity.HIGH, ec_min_bits=224, ec_min_severity=Severity.HIGH,
        dh_min_bits=2048, dh_min_severity=Severity.HIGH, hash_min="sha1", sym_min_bits=112,
        allowed_curves=None, sha1_signature_severity=Severity.MEDIUM, tls12_severity=Severity.INFO,
        cbc_severity=Severity.INFO, quantum_report=False, pq_deprecation_year=None, pq_disallow_year=None,
        references=[REF["131A"]]),
}

_HASH_ORDER = {"md2": 0, "md4": 0, "md5": 0, "crc32": 0, "sha1": 1, "ripemd160": 1, "sha224": 2, "sha256": 3,
               "sha512-224": 2, "sha512-256": 3, "sha3-224": 2, "sha3-256": 3, "sha384": 4, "sha3-384": 4,
               "sha512": 5, "sha3-512": 5, "streebog-256": 3, "streebog-512": 5, "sm3": 3, "cmac": 3}


def _hash_rank(h: Optional[str]) -> Optional[int]:
    return _HASH_ORDER.get(h) if h else None


RuleFn = Callable[["Context"], List[Finding]]


@dataclass
class Context:
    asset: Asset
    use: Optional[CryptoUse]
    profile: Profile
    now: _dt.datetime
    strict_legacy: bool = False

    def finding(self, rule_id: str, title: str, severity: Severity, description: str, remediation: str,
                references: Tuple[str, ...] = (), quantum: bool = False, year: Optional[int] = None,
                tags: Tuple[str, ...] = ()) -> Finding:
        if self.profile.name == "legacy" and severity < Severity.MEDIUM and not self.strict_legacy:
            severity = Severity.INFO
        return Finding(rule_id=rule_id, title=title, severity=severity, asset_id=self.asset.asset_id,
                       asset_kind=self.asset.kind, asset_name=self.asset.name, location=self.asset.location,
                       collector=self.asset.collector, description=description, remediation=remediation,
                       host=self.asset.host, use=self.use, references=list(references), quantum_vulnerable=quantum,
                       deprecation_year=year, tags=list(tags))


# ---------------------------------------------------------------------------
# Rules per primitive
# ---------------------------------------------------------------------------

def _is_trust_anchor(asset: Asset) -> bool:
    """Trust-store entries, and any self-signed CA certificate: its self-signature is never verified."""
    a = asset.attributes
    return (asset.kind in (AssetKind.CA_CERTIFICATE, AssetKind.TRUST_STORE) or bool(a.get("trust_anchor"))
            or bool(a.get("is_ca") and a.get("self_signed")))


TEST_PATH_RE = re.compile(r"/(tests?|test_data|testdata|test-data|fixtures?|examples?|samples?|dummyserver|testing|mock(s|data)?|spec)(/|$)", re.I)


def is_test_material(location: str) -> bool:
    """Heuristic: key/cert material that ships inside a test or example tree of some package."""
    return bool(location and TEST_PATH_RE.search(location))


def rule_public_key(ctx: Context) -> List[Finding]:
    u, p = ctx.use, ctx.profile
    out: List[Finding] = []
    alg, bits = u.algorithm, u.key_bits
    where = f"{u.context or 'key'} on {ctx.asset.name}"
    if alg in ("rsa", "rsa-pss", "rsa-kex"):
        if bits is not None:
            if bits < 1024:
                out.append(ctx.finding("PK-RSA-BROKEN", f"RSA key of {bits} bits is factorable", Severity.CRITICAL,
                                       f"RSA-{bits} ({where}) offers under 80 bits of security and has been publicly factored at this size.",
                                       "Replace with RSA-3072 or better, or ECDSA P-256/Ed25519; plan the move to ML-DSA/ML-KEM.",
                                       (REF["131A"], REF["57"]), quantum=True))
            elif bits < 2048:
                out.append(ctx.finding("PK-RSA-LT-2048", f"RSA key of {bits} bits (disallowed since 2014)", Severity.HIGH,
                                       f"RSA-{bits} ({where}) gives about 80 bits of security; NIST disallowed it for all uses after 2013.",
                                       "Re-key at 3072 bits or move to an elliptic-curve or post-quantum algorithm.",
                                       (REF["131A"],), quantum=True))
            elif bits < p.rsa_min_bits:
                out.append(ctx.finding("PK-RSA-BELOW-PROFILE", f"RSA key of {bits} bits is below the {p.name} minimum of {p.rsa_min_bits}",
                                       p.rsa_min_severity, f"RSA-{bits} ({where}) is about 112 bits of security; the {p.name} profile requires {p.rsa_min_bits}-bit moduli.",
                                       f"Re-key at >= {p.rsa_min_bits} bits.", tuple(p.references), quantum=True, year=p.pq_deprecation_year))
            elif bits < 3072 and p.pq_deprecation_year and p.name == "nist":
                out.append(ctx.finding("PK-RSA-2048-SUNSET", "RSA-2048 is deprecated after 2030 (112-bit security)", Severity.LOW,
                                       f"RSA-{bits} ({where}) provides 112 bits of security; NIST IR 8547 deprecates 112-bit quantum-vulnerable algorithms after 2030 and disallows them after 2035.",
                                       "Plan migration to ML-DSA (signatures) / ML-KEM (key establishment); use RSA-3072+ in the interim.",
                                       (REF["8547"],), quantum=True, year=2030))
        if u.extra.get("rsa_exponent") == 3 or ctx.asset.attributes.get("rsa_exponent") == 3:
            out.append(ctx.finding("PK-RSA-E3", "RSA public exponent 3", Severity.LOW,
                                   "Exponent e=3 is safe only with correct padding; it has a history of implementation flaws (Bleichenbacher '06 signature forgery).",
                                   "Prefer e=65537.", (REF["RFC3447"],)))
    elif alg == "dsa":
        sev = Severity.CRITICAL if (bits or 1024) < 2048 else Severity.HIGH
        out.append(ctx.finding("PK-DSA", f"DSA key ({bits or 'unknown'} bits): algorithm withdrawn", sev,
                               f"DSA ({where}) was withdrawn for signature generation by FIPS 186-5 and is disabled in OpenSSH since 7.0; 1024-bit DSA offers only 80 bits.",
                               "Replace with ECDSA P-256/P-384, Ed25519, or ML-DSA.", (REF["186-5"], REF["OPENSSH70"]), quantum=True))
    elif alg in ("ec", "ecdsa", "ecdh", "ecdhe", "ecdh-static", "ecdsa-sk"):
        curve = (u.curve or "").lower()
        if curve == "explicit":
            out.append(ctx.finding("PK-EC-EXPLICIT", "Elliptic-curve key with explicit (non-named) parameters", Severity.MEDIUM,
                                   f"Explicit curve parameters ({where}) cannot be validated against a standard and are rejected by modern validators (RFC 5480, CAB BR).",
                                   "Re-issue with a named curve.", (REF["CAB"],), quantum=True))
        elif bits is not None and bits < 224:
            out.append(ctx.finding("PK-EC-LT-224", f"Elliptic curve {curve or ''} of {bits} bits (< 112-bit security)", Severity.HIGH,
                                   f"Curves under 224 bits ({where}) give under 112 bits of security and are disallowed by NIST since 2014.",
                                   "Use P-256/P-384 or Curve25519/448; plan the move to ML-DSA/ML-KEM.", (REF["131A"],), quantum=True))
        elif curve.startswith(BINARY_CURVES):
            out.append(ctx.finding("PK-EC-BINARY", f"Binary-field curve {curve} (deprecated)", Severity.MEDIUM,
                                   f"NIST deprecated the binary curves (B-/K- families) in FIPS 186-5 / SP 800-186; {where}.",
                                   "Move to a prime-field curve (P-256/P-384) or Curve25519.", (REF["186-5"],), quantum=True))
        elif p.allowed_curves is not None and curve not in p.allowed_curves:
            out.append(ctx.finding("PK-EC-NOT-IN-PROFILE", f"Curve {curve} is not permitted by the {p.name} profile", p.ec_min_severity,
                                   f"The {p.name} profile allows only {', '.join(sorted(p.allowed_curves))}; found {curve} ({where}).",
                                   f"Use {', '.join(sorted(p.allowed_curves))} or a CNSA 2.0 post-quantum algorithm.", tuple(p.references), quantum=True, year=p.pq_disallow_year))
        elif bits is not None and bits < p.ec_min_bits:
            out.append(ctx.finding("PK-EC-BELOW-PROFILE", f"Curve {curve} ({bits} bits) is below the {p.name} minimum of {p.ec_min_bits}", p.ec_min_severity,
                                   f"{where}", f"Use a curve of >= {p.ec_min_bits} bits.", tuple(p.references), quantum=True))
        elif bits is not None and bits < 256 and p.name == "nist":
            out.append(ctx.finding("PK-EC-224-SUNSET", f"Curve {curve} (112-bit security) deprecated after 2030", Severity.LOW,
                                   f"{where}: NIST IR 8547 deprecates 112-bit quantum-vulnerable algorithms after 2030.",
                                   "Move to P-256 or better now, and to ML-DSA/ML-KEM by 2030.", (REF["8547"],), quantum=True, year=2030))
        elif curve == "secp256k1" and p.name != "legacy":
            out.append(ctx.finding("PK-EC-SECP256K1", "secp256k1 is not a NIST/BSI-approved curve", Severity.LOW,
                                   f"{where}: secp256k1 is sound but outside FIPS 186-5 / SP 800-186 and TR-02102.", "Use P-256 where compliance matters.", (REF["186-5"],), quantum=True))
        elif curve.startswith("brainpool") and p.name in ("nist", "cnsa2"):
            out.append(ctx.finding("PK-EC-BRAINPOOL", f"Brainpool curve {curve} is not NIST-approved", Severity.LOW,
                                   f"{where}", "Acceptable under BSI; use P-256/P-384 for NIST/CNSA compliance.", (REF["186-5"],), quantum=True))
    elif alg in ("dh", "dhe", "dh-gex", "dh-static", "dh-anon"):
        if alg == "dh-gex" and bits is None:
            if u.hash_algorithm == "sha1":
                pass   # handled by signature/hash rule for kex
        elif bits is not None:
            if bits < 1024:
                out.append(ctx.finding("PK-DH-BROKEN", f"Diffie-Hellman group of {bits} bits", Severity.CRITICAL,
                                       f"{where}: DH groups under 1024 bits are breakable with academic resources (export-grade, Logjam).",
                                       "Use >= 2048-bit groups (ffdhe2048+), ECDH, or an ML-KEM hybrid.", (REF["LOGJAM"],), quantum=True))
            elif bits < 2048:
                out.append(ctx.finding("PK-DH-LT-2048", f"Diffie-Hellman group of {bits} bits (Logjam class)", Severity.HIGH,
                                       f"{where}: 1024-bit DH is within reach of nation-state precomputation (Logjam) and disallowed by NIST since 2014; RFC 8270 raised the SSH minimum to 2048.",
                                       "Use >= 2048-bit groups, ECDH (curve25519), or ML-KEM hybrids.", (REF["LOGJAM"], REF["RFC8270"], REF["131A"]), quantum=True))
            elif bits < p.dh_min_bits:
                out.append(ctx.finding("PK-DH-BELOW-PROFILE", f"DH group of {bits} bits is below the {p.name} minimum of {p.dh_min_bits}", p.dh_min_severity,
                                       f"{where}", f"Use >= {p.dh_min_bits}-bit groups or ECDH/ML-KEM.", tuple(p.references), quantum=True, year=p.pq_deprecation_year))
            elif bits < 3072 and p.name == "nist":
                out.append(ctx.finding("PK-DH-2048-SUNSET", "2048-bit DH deprecated after 2030 (112-bit security)", Severity.LOW,
                                       f"{where}", "Prefer ECDH/curve25519 now and ML-KEM hybrids as they become available.", (REF["8547"],), quantum=True, year=2030))
        if alg == "dh-anon":
            out.append(ctx.finding("KX-ANON", "Anonymous (unauthenticated) key exchange", Severity.CRITICAL,
                                   f"{where}: anonymous DH/ECDH provides no server authentication and is trivially man-in-the-middled.",
                                   "Disable aNULL / ADH / AECDH suites.", (REF["RFC9325"],)))
    elif alg in ("ed25519", "ed448", "x25519", "x448", "ed25519-sk"):
        if p.strict_pq:
            out.append(ctx.finding("PK-NOT-CNSA", f"{alg} is not a CNSA 2.0 algorithm", Severity.MEDIUM,
                                   f"{where}: CNSA 2.0 permits only P-384, RSA-3072+ and the post-quantum set.", "Use P-384 or ML-DSA/ML-KEM.", (REF["CNSA2"],), quantum=True, year=p.pq_disallow_year))
    elif alg in ("gost-r34.10-2001",):
        out.append(ctx.finding("PK-GOST-2001", "GOST R 34.10-2001 (withdrawn 2019)", Severity.HIGH, f"{where}", "Use GOST R 34.10-2012 or an international algorithm.", (), quantum=True))
    return out


def rule_signature(ctx: Context) -> List[Finding]:
    u, p = ctx.use, ctx.profile
    out: List[Finding] = []
    h = u.hash_algorithm
    alg = u.algorithm
    where = f"{u.context or 'signature'} on {ctx.asset.name}"
    anchor = _is_trust_anchor(ctx.asset) and ctx.asset.attributes.get("self_signed", False)
    if h in BROKEN_HASHES:
        if anchor and u.context == "certificate-signature":
            out.append(ctx.finding("SIG-ANCHOR-WEAK-HASH", f"Trust anchor self-signed with {h} (informational)", Severity.INFO,
                                   f"The self-signature of a root certificate is not verified by relying parties; {h} here is cosmetic. Key size still matters.",
                                   "No action required for the signature itself.", (REF["CAB"],)))
        else:
            out.append(ctx.finding("SIG-HASH-BROKEN", f"{alg} signature with {h} (collision-broken)", Severity.CRITICAL,
                                   f"{where}: {h} collisions are practical; chosen-prefix collisions allow certificate/signature forgery.",
                                   "Re-sign with SHA-256 or stronger.", (REF["131A"], REF["RFC9155"])))
    elif h == "sha1" and alg == "dsa" and u.context in ("hostkey", "pubkey-auth", "ca-signature", "hostbased-auth"):
        pass   # SIG-DSA below covers ssh-dss entirely
    elif h == "sha1":
        if anchor and u.context == "certificate-signature":
            out.append(ctx.finding("SIG-ANCHOR-WEAK-HASH", "Trust anchor self-signed with SHA-1 (informational)", Severity.INFO,
                                   "The self-signature of a root certificate is not verified by relying parties.", "No action required for the signature itself.", (REF["CAB"],)))
        elif u.context == "hostkey" and u.raw in ("ssh-rsa", "x509v3-ssh-rsa"):
            out.append(ctx.finding("SSH-RSA-SHA1", "ssh-rsa host-key/signature algorithm uses SHA-1", Severity.HIGH if p.name != "legacy" else Severity.MEDIUM,
                                   f"{where}: the 'ssh-rsa' signature algorithm hashes with SHA-1 (RFC 4253). OpenSSH 8.8 disabled it by default; RFC 8332 replaces it with rsa-sha2-256/512. (The RSA key itself can stay.)",
                                   "Remove ssh-rsa from HostKeyAlgorithms / PubkeyAcceptedAlgorithms; keep rsa-sha2-256, rsa-sha2-512, ssh-ed25519.",
                                   (REF["RFC8332"], REF["OPENSSH88"])))
        else:
            out.append(ctx.finding("SIG-HASH-SHA1", f"{alg} signature with SHA-1", p.sha1_signature_severity,
                                   f"{where}: SHA-1 is collision-broken (SHAttered 2017, chosen-prefix 2020) and disallowed for signature generation since 2013; NIST retires SHA-1 entirely by 2030.",
                                   "Re-sign with SHA-256 or stronger.", (REF["131A"], REF["RFC9155"])))
    elif h is not None and _hash_rank(h) is not None and _hash_rank(h) < _hash_rank(p.hash_min):
        out.append(ctx.finding("SIG-HASH-BELOW-PROFILE", f"{alg} signature with {h} is below the {p.name} minimum ({p.hash_min})", Severity.MEDIUM if p.name == "cnsa2" else Severity.LOW,
                               f"{where}", f"Use {p.hash_min} or stronger.", tuple(p.references)))
    if alg == "dsa" or (alg == "unknown" and (u.raw or "").startswith("ssh-dss")):
        out.append(ctx.finding("SIG-DSA", "DSA signature algorithm (withdrawn)", Severity.HIGH,
                               f"{where}: DSA is withdrawn by FIPS 186-5; ssh-dss is 1024-bit and disabled in OpenSSH since 7.0.",
                               "Remove ssh-dss / DSA; use Ed25519, ECDSA, or rsa-sha2-*.", (REF["186-5"], REF["OPENSSH70"]), quantum=True))
    if u.context in ("hostkey", "pubkey-auth", "ca-signature", "hostbased-auth") and u.key_bits and alg in ("rsa", "ecdsa"):
        out.extend(rule_public_key(ctx))
    if alg in ("ecdsa", "ed25519", "ed448") and u.context in ("hostkey", "pubkey-auth", "ca-signature", "hostbased-auth") and not u.key_bits:
        pass
    if alg in ("ed25519", "ed448") and p.strict_pq:
        out.extend(rule_public_key(ctx))
    if u.extra.get("protocol") == "1":
        out.append(ctx.finding("SSH-PROTOCOL-1", "SSH protocol version 1 key", Severity.CRITICAL, f"{where}", "Remove SSHv1 keys and configuration.", ()))
    return out


def rule_key_exchange(ctx: Context) -> List[Finding]:
    u, p = ctx.use, ctx.profile
    out: List[Finding] = []
    alg = u.algorithm
    if u.extra.get("marker"):
        return out
    where = f"{u.context or 'kex'} '{u.raw}' on {ctx.asset.name}"
    if alg in ("dh", "dh-gex", "ecdh", "dhe", "ecdhe", "dh-anon", "ecdh-anon", "dh-static", "ecdh-static"):
        out.extend(rule_public_key(ctx))
        if alg in ("dh-static", "ecdh-static"):
            out.append(ctx.finding("KX-NO-PFS", "Static (non-ephemeral) key exchange: no forward secrecy", Severity.MEDIUM,
                                   f"{where}: static DH/ECDH keys mean a later key compromise decrypts recorded sessions.",
                                   "Use ECDHE/DHE (or TLS 1.3).", (REF["52"], REF["RFC9325"])))
    if alg == "rsa-kex":
        sev = Severity.CRITICAL if (u.key_bits or 2048) < 2048 else Severity.MEDIUM
        out.append(ctx.finding("KX-RSA", "RSA key transport: no forward secrecy, Bleichenbacher/ROBOT surface", sev,
                               f"{where}: static RSA key exchange leaks every past session if the key is later compromised and is the target of padding-oracle attacks (ROBOT, Marvin).",
                               "Use ECDHE suites / TLS 1.3; disable kRSA.", (REF["52"], REF["RFC9325"])))
    if u.hash_algorithm == "sha1" and alg != "rsa-kex":
        out.append(ctx.finding("KX-SHA1", f"Key exchange {u.raw} hashes with SHA-1", Severity.HIGH if alg in ("dh", "dh-gex") else Severity.MEDIUM,
                               f"{where}: RFC 9142 moves SHA-1 key exchanges to SHOULD NOT / MUST NOT.",
                               "Prefer curve25519-sha256, diffie-hellman-group16-sha512, or the PQ hybrids (sntrup761x25519-sha512, mlkem768x25519-sha256).", (REF["RFC9142"],)))
    if alg == "unknown" and u.raw and u.raw.startswith("gss-"):
        return out
    if p.strict_pq and alg in QUANTUM_VULNERABLE and alg not in ("dh-anon", "ecdh-anon"):
        out.append(ctx.finding("KX-NOT-PQ", f"Key exchange {u.raw} is not quantum-resistant", Severity.MEDIUM,
                               f"{where}: CNSA 2.0 requires ML-KEM-1024 (or a hybrid) for key establishment on the transition timeline.",
                               "Enable ML-KEM hybrids (X25519MLKEM768 for TLS, mlkem768x25519-sha256 / sntrup761x25519-sha512 for SSH).", (REF["CNSA2"], REF["FIPS203"]), quantum=True, year=p.pq_disallow_year))
    if alg == "hybrid-pq" and u.extra.get("kem") == "kyber768-draft":
        out.append(ctx.finding("KX-PQ-DRAFT", "Pre-standard Kyber draft hybrid", Severity.LOW, f"{where}", "Move to X25519MLKEM768 (FIPS 203 ML-KEM).", (REF["FIPS203"],)))
    return out


def rule_cipher(ctx: Context) -> List[Finding]:
    u, p = ctx.use, ctx.profile
    out: List[Finding] = []
    alg, bits, mode = u.algorithm, u.key_bits, u.mode
    where = f"{u.context or 'cipher'} '{u.raw}' on {ctx.asset.name}"
    ex = u.extra
    if ex.get("export"):
        out.append(ctx.finding("CIPHER-EXPORT", "Export-grade cipher suite", Severity.CRITICAL, f"{where}: 40/56-bit export suites are breakable in minutes (FREAK, Logjam).", "Disable all EXPORT suites.", (REF["LOGJAM"],)))
    if alg == "null" or bits == 0:
        out.append(ctx.finding("CIPHER-NULL", "NULL cipher (no confidentiality)", Severity.CRITICAL, f"{where}", "Disable eNULL / 'none' ciphers.", (REF["RFC9325"],)))
    elif alg == "rc4":
        out.append(ctx.finding("CIPHER-RC4", "RC4 stream cipher (prohibited)", Severity.CRITICAL, f"{where}: RC4 keystream biases allow plaintext recovery (RFC 7465 prohibits it in TLS; OpenSSH removed arcfour in 7.6).", "Replace with AES-GCM or ChaCha20-Poly1305.", (REF["RFC7465"],)))
    elif alg in ("des", "des40"):
        out.append(ctx.finding("CIPHER-DES", "Single DES (56-bit, brute-forceable)", Severity.CRITICAL, f"{where}", "Replace with AES.", (REF["131A"],)))
    elif alg == "rc2":
        out.append(ctx.finding("CIPHER-RC2", "RC2 cipher", Severity.CRITICAL, f"{where}", "Replace with AES.", (REF["131A"],)))
    elif alg == "3des":
        sev = Severity.HIGH
        out.append(ctx.finding("CIPHER-3DES", "Triple-DES (disallowed after 2023; Sweet32)", sev,
                               f"{where}: 64-bit blocks allow birthday attacks on long sessions (Sweet32); NIST disallowed 3DES for encryption after 2023.",
                               "Replace with AES-128/256-GCM.", (REF["SWEET32"], REF["131A"])))
    elif alg in SIXTY_FOUR_BIT_BLOCK:
        out.append(ctx.finding("CIPHER-64BIT-BLOCK", f"{alg} has a 64-bit block (Sweet32 class)", Severity.HIGH, f"{where}", "Replace with AES or ChaCha20-Poly1305.", (REF["SWEET32"],)))
    elif alg in ("aes", "camellia", "aria", "serpent", "twofish", "sm4", "chacha20-poly1305", "kuznyechik"):
        if bits is not None and bits < p.sym_min_bits:
            out.append(ctx.finding("CIPHER-BELOW-PROFILE", f"{alg}-{bits} is below the {p.name} minimum of {p.sym_min_bits} bits", Severity.MEDIUM if p.name == "cnsa2" else Severity.LOW,
                                   f"{where}", f"Use {alg.upper()}-{p.sym_min_bits}.", tuple(p.references)))
        if mode == "cbc":
            if u.context == "cipher" and ctx.asset.kind in (AssetKind.SSH_SERVER, AssetKind.SSH_CLIENT, AssetKind.SSH_REMOTE):
                out.append(ctx.finding("SSH-CBC", f"SSH CBC-mode cipher {u.raw}", Severity.MEDIUM,
                                       f"{where}: CBC in SSH is vulnerable to plaintext recovery (CVE-2008-5161) and is disabled by default in OpenSSH.",
                                       "Use aes*-gcm@openssh.com, chacha20-poly1305@openssh.com or aes*-ctr.", (REF["TERRAPIN"],)))
            else:
                out.append(ctx.finding("TLS-CBC", f"CBC-mode cipher suite {u.raw}", p.cbc_severity,
                                       f"{where}: MAC-then-encrypt CBC suites have a history of padding-oracle attacks (BEAST, Lucky13, POODLE-TLS); SP 800-52r2 and BCP 195 prefer AEAD.",
                                       "Prefer AES-GCM / ChaCha20-Poly1305 and TLS 1.3.", (REF["52"], REF["RFC9325"])))
        if mode == "ccm-8":
            out.append(ctx.finding("TLS-CCM8", "AES-CCM with 64-bit tag", Severity.LOW, f"{where}: 8-byte authentication tags are weak for general use.", "Prefer GCM or CCM with 128-bit tags.", (REF["RFC9325"],)))
        if alg == "chacha20-poly1305" and ctx.asset.kind in (AssetKind.SSH_SERVER, AssetKind.SSH_CLIENT, AssetKind.SSH_REMOTE) and not ctx.asset.attributes.get("kex_strict"):
            out.append(ctx.finding("SSH-TERRAPIN", "chacha20-poly1305@openssh.com without strict key exchange (Terrapin)", Severity.MEDIUM,
                                   f"{where}: CVE-2023-48795 allows prefix truncation unless both sides support kex-strict (OpenSSH >= 9.6).",
                                   "Upgrade OpenSSH to 9.6+ (strict kex) or disable chacha20-poly1305 and *-etm CBC ciphers.", (REF["TERRAPIN"],)))
    # TLS suite-level properties
    if u.context == "tls-cipher-suite":
        kx = ex.get("kx")
        if ex.get("auth") == "none" or kx in ("dh-anon", "ecdh-anon"):
            out.append(ctx.finding("KX-ANON", "Anonymous (unauthenticated) cipher suite", Severity.CRITICAL, f"{where}", "Disable aNULL suites.", (REF["RFC9325"],)))
        elif kx == "rsa-kex":
            out.append(ctx.finding("KX-RSA", "RSA key transport suite: no forward secrecy", Severity.MEDIUM,
                                   f"{where}: static-RSA suites expose recorded traffic to later key compromise and to padding oracles (ROBOT).", "Prefer ECDHE suites or TLS 1.3.", (REF["52"], REF["RFC9325"])))
        elif kx in ("dh-static", "ecdh-static"):
            out.append(ctx.finding("KX-NO-PFS", "Static (EC)DH suite: no forward secrecy", Severity.MEDIUM, f"{where}", "Use ECDHE suites.", (REF["52"],)))
        if ex.get("auth") == "dsa":
            out.append(ctx.finding("SIG-DSA", "DSS-authenticated cipher suite", Severity.HIGH, f"{where}", "Remove DHE-DSS suites.", (REF["186-5"],), quantum=True))
        if u.hash_algorithm == "md5":
            out.append(ctx.finding("MAC-MD5", "HMAC-MD5 cipher suite", Severity.HIGH, f"{where}", "Disable MD5 suites.", (REF["RFC9155"],)))
        elif u.hash_algorithm == "sha1" and not ex.get("aead") and p.name == "cnsa2":
            out.append(ctx.finding("MAC-SHA1-PROFILE", "HMAC-SHA1 suite not permitted by CNSA 2.0", Severity.MEDIUM, f"{where}", "Use AES-256-GCM-SHA384.", (REF["CNSA2"],)))
        if p.strict_pq and bits == 128 and alg == "aes":
            pass   # already CIPHER-BELOW-PROFILE
        if ex.get("protocol") in ("tls1.3",) and alg == "aes" and bits == 128 and p.name == "cnsa2":
            pass
    return out


def rule_mac(ctx: Context) -> List[Finding]:
    u, p = ctx.use, ctx.profile
    out: List[Finding] = []
    where = f"{u.context or 'mac'} '{u.raw}' on {ctx.asset.name}"
    h = u.hash_algorithm
    if u.algorithm == "null":
        out.append(ctx.finding("MAC-NULL", "No integrity protection", Severity.CRITICAL, where, "Enable a MAC.", ()))
    elif h in ("md5", "md4", "md2"):
        out.append(ctx.finding("MAC-MD5", f"HMAC-{h.upper()} ({u.raw})", Severity.HIGH, f"{where}: MD5-based MACs are disallowed; OpenSSH removed hmac-md5 from defaults years ago.", "Use hmac-sha2-256-etm@openssh.com / hmac-sha2-512-etm@openssh.com.", (REF["131A"],)))
    elif u.extra.get("truncated") or (u.key_bits is not None and u.key_bits < 96):
        out.append(ctx.finding("MAC-TRUNCATED", f"Truncated MAC tag ({u.key_bits} bits): {u.raw}", Severity.HIGH if (u.key_bits or 96) < 96 else Severity.MEDIUM,
                               f"{where}: 64/96-bit tags fall short of the 128-bit target.", "Use hmac-sha2-256/512 or umac-128.", (REF["131A"],)))
    elif h == "sha1":
        out.append(ctx.finding("MAC-SHA1", f"HMAC-SHA1 ({u.raw})", Severity.LOW if p.name in ("nist", "legacy") else Severity.MEDIUM,
                               f"{where}: HMAC-SHA1 is not collision-sensitive and remains approved by NIST, but it is deprecated by most hardening guides and not allowed by {p.name if p.name != 'nist' else 'CNSA/BSI'}.",
                               "Prefer hmac-sha2-256-etm@openssh.com / hmac-sha2-512-etm@openssh.com.", (REF["RFC9142"],)))
    elif h == "ripemd160":
        out.append(ctx.finding("MAC-RIPEMD", "HMAC-RIPEMD160", Severity.LOW, where, "Prefer hmac-sha2-*.", ()))
    if u.mode != "etm" and ctx.asset.kind in (AssetKind.SSH_SERVER, AssetKind.SSH_CLIENT, AssetKind.SSH_REMOTE) and u.algorithm in ("hmac", "umac") and p.name != "legacy":
        out.append(ctx.finding("SSH-MAC-EAM", f"Encrypt-and-MAC construction ({u.raw})", Severity.INFO, f"{where}: non-ETM MACs leak plaintext length information with CBC ciphers.", "Prefer the *-etm@openssh.com variants.", ()))
    return out


def rule_hash(ctx: Context) -> List[Finding]:
    u, p = ctx.use, ctx.profile
    out: List[Finding] = []
    where = f"{u.context or 'hash'} on {ctx.asset.name}"
    if u.algorithm in BROKEN_HASHES:
        out.append(ctx.finding("HASH-BROKEN", f"{u.algorithm} in use", Severity.HIGH, f"{where}", "Use SHA-256 or better.", (REF["131A"],)))
    elif u.algorithm == "sha1":
        out.append(ctx.finding("HASH-SHA1", "SHA-1 in use", Severity.MEDIUM if u.context in ("signature", "fingerprint", "pbkdf") else Severity.LOW, f"{where}", "Use SHA-256 or better.", (REF["131A"],)))
    elif _hash_rank(u.algorithm) is not None and _hash_rank(u.algorithm) < _hash_rank(p.hash_min):
        out.append(ctx.finding("HASH-BELOW-PROFILE", f"{u.algorithm} is below the {p.name} minimum ({p.hash_min})", Severity.LOW, where, f"Use {p.hash_min}+.", tuple(p.references)))
    return out


def rule_protocol(ctx: Context) -> List[Finding]:
    u, p = ctx.use, ctx.profile
    out: List[Finding] = []
    a = u.algorithm
    where = f"{ctx.asset.name}"
    table = {
        "sslv2": ("PROTO-SSLV2", "SSLv2 enabled", Severity.CRITICAL, "SSLv2 is prohibited (RFC 6176) and enables DROWN cross-protocol attacks.", (REF["RFC6176"],)),
        "sslv3": ("PROTO-SSLV3", "SSLv3 enabled", Severity.CRITICAL, "SSLv3 is broken (POODLE) and deprecated by RFC 7568.", (REF["RFC7568"],)),
        "tls1.0": ("PROTO-TLS10", "TLS 1.0 enabled", Severity.HIGH, "TLS 1.0 is deprecated by RFC 8996 and disallowed by NIST SP 800-52r2 and PCI DSS.", (REF["RFC8996"], REF["52"])),
        "tls1.1": ("PROTO-TLS11", "TLS 1.1 enabled", Severity.HIGH, "TLS 1.1 is deprecated by RFC 8996.", (REF["RFC8996"], REF["52"])),
        "dtls1.0": ("PROTO-DTLS10", "DTLS 1.0 enabled", Severity.HIGH, "DTLS 1.0 is deprecated by RFC 8996.", (REF["RFC8996"],)),
        "ssh1": ("SSH-PROTOCOL-1", "SSH protocol 1 enabled", Severity.CRITICAL, "SSHv1 has unfixable integrity flaws (CRC32 insertion attack).", ()),
        "ssh1.99": ("SSH-PROTOCOL-1", "SSH server advertises protocol 1.99 (SSHv1 compatible)", Severity.CRITICAL, "The server accepts SSHv1 sessions.", ()),
        "snmpv1": ("PROTO-SNMPV1", "SNMPv1 enabled", Severity.HIGH, "SNMPv1 has no cryptographic protection; community strings travel in clear text.", (REF["SNMP"],)),
        "snmpv2c": ("PROTO-SNMPV2C", "SNMPv2c enabled", Severity.HIGH, "SNMPv2c has no cryptographic protection; community strings travel in clear text.", (REF["SNMP"],)),
        "snmpv3-noauth": ("PROTO-SNMPV3-NOAUTH", "SNMPv3 user without authentication", Severity.HIGH, "noAuthNoPriv gives no integrity or confidentiality.", (REF["SNMP"],)),
        "snmpv3-noprivacy": ("PROTO-SNMPV3-NOPRIV", "SNMPv3 user without privacy", Severity.MEDIUM, "authNoPriv sends management data in clear.", (REF["SNMP"],)),
        "telnet": ("PROTO-TELNET", "Telnet management enabled", Severity.CRITICAL, "Credentials and sessions are sent in clear text.", ()),
        "http-mgmt": ("PROTO-HTTP-MGMT", "Unencrypted HTTP management interface", Severity.HIGH, "Credentials and configuration travel in clear text.", ()),
        "ftp": ("PROTO-FTP", "FTP (clear text) enabled", Severity.HIGH, "Credentials travel in clear text.", ()),
        "tftp": ("PROTO-TFTP", "TFTP enabled", Severity.MEDIUM, "No authentication or encryption.", ()),
        "ikev1": ("PROTO-IKEV1", "IKEv1 in use", Severity.HIGH, "IKEv1 is deprecated by RFC 9395; aggressive mode with PSK leaks a crackable hash.", (REF["RFC9395"],)),
        "ikev1-aggressive": ("PROTO-IKEV1-AGGR", "IKEv1 aggressive mode", Severity.CRITICAL, "Aggressive mode exposes the PSK hash to offline cracking.", (REF["RFC9395"],)),
        "pptp": ("PROTO-PPTP", "PPTP VPN", Severity.CRITICAL, "MS-CHAPv2/MPPE are broken (DES-based, crackable in under a day).", ()),
        "l2tp-ipsec-psk": ("PROTO-L2TP-PSK", "L2TP/IPsec with shared PSK", Severity.MEDIUM, "Group PSKs are weak authentication.", ()),
        "ntlmv1": ("PROTO-NTLMV1", "NTLMv1 / LM authentication", Severity.CRITICAL, "LM/NTLMv1 hashes are DES-based and crackable instantly (rainbow tables).", ()),
        "ntlmv2": ("PROTO-NTLMV2", "NTLMv2 authentication permitted", Severity.LOW, "NTLM relays and offline cracking remain possible; Kerberos is preferred.", ()),
        "wep": ("PROTO-WEP", "WEP wireless encryption", Severity.CRITICAL, "WEP is recoverable in minutes.", ()),
        "wpa-tkip": ("PROTO-WPA-TKIP", "WPA/TKIP wireless encryption", Severity.HIGH, "TKIP is RC4-based and deprecated.", ()),
        "smbv1": ("PROTO-SMBV1", "SMBv1 enabled", Severity.CRITICAL, "SMBv1 has no signing/encryption protection comparable to SMB3 and is the EternalBlue vector.", ()),
        "ldap-cleartext": ("PROTO-LDAP-CLEAR", "LDAP simple bind without TLS", Severity.HIGH, "Passwords cross the network in clear.", ()),
        "rdp-no-nla": ("PROTO-RDP-NONLA", "RDP without Network Level Authentication", Severity.MEDIUM, "Pre-auth exposure of the RDP stack.", ()),
        "tls1.2": ("PROTO-TLS12", "TLS 1.2 (no TLS 1.3)", p.tls12_severity, "TLS 1.2 remains approved; SP 800-52r2 requires TLS 1.3 support by 2024 and CNSA 2.0 expects TLS 1.3 for PQ hybrids.", (REF["52"],)),
    }
    if a in table:
        rid, title, sev, desc, refs = table[a]
        if a == "tls1.2" and ctx.asset.attributes.get("tls1.3"):
            return out
        fix = {"tls1.0": "Set the minimum protocol to TLS 1.2 (MinProtocol / ssl_protocols / ssl-min-version).",
               "tls1.1": "Set the minimum protocol to TLS 1.2.",
               "sslv3": "Disable SSLv3.", "sslv2": "Disable SSLv2.",
               "snmpv1": "Move to SNMPv3 authPriv (SHA-256 / AES-128+) and remove community strings.",
               "snmpv2c": "Move to SNMPv3 authPriv (SHA-256 / AES-128+) and remove community strings.",
               "ikev1": "Migrate tunnels to IKEv2 with AES-GCM, SHA-2 and DH group 14+/19+/31.",
               "ssh1": "Remove 'Protocol 1' and SSHv1 host keys.",
               "ssh1.99": "Disable SSHv1 ('ip ssh version 2' on Cisco; remove 'Protocol 1').",
               "tls1.2": "Enable TLS 1.3 alongside TLS 1.2."}.get(a, "Disable the protocol and move to its modern replacement.")
        out.append(ctx.finding(rid, title, sev, f"{where}: {desc}", fix, refs))
    return out


def rule_enctype(ctx: Context) -> List[Finding]:
    u, p = ctx.use, ctx.profile
    out: List[Finding] = []
    et = u.extra.get("enctype", u.raw)
    if u.extra.get("negated"):
        return out
    where = f"{u.context or 'enctype'} '{u.raw}' on {ctx.asset.name}"
    if u.algorithm == "des":
        out.append(ctx.finding("KRB-DES", f"Kerberos single-DES enctype {et}", Severity.CRITICAL,
                               f"{where}: DES enctypes are deprecated by RFC 6649 (56-bit, brute-forceable); MIT krb5 refuses them unless allow_weak_crypto is set.",
                               "Remove des-* from all enctype lists; re-key principals with aes256-cts-hmac-sha384-192 / aes256-cts-hmac-sha1-96.", (REF["RFC6649"],)))
    elif u.algorithm == "rc4":
        sev = Severity.CRITICAL if (u.key_bits or 128) < 128 else Severity.HIGH
        out.append(ctx.finding("KRB-RC4", f"Kerberos RC4-HMAC enctype {et}", sev,
                               f"{where}: rc4-hmac keys are the unsalted NT (MD4) password hash, so ticket encryption is only as strong as the password (Kerberoasting, pass-the-hash); RFC 8429 deprecates it.",
                               "Remove rc4-hmac (arcfour-hmac) from default_tgs_enctypes / default_tkt_enctypes / permitted_enctypes and from msDS-SupportedEncryptionTypes; use AES.", (REF["RFC8429"],)))
    elif u.algorithm == "3des":
        out.append(ctx.finding("KRB-3DES", f"Kerberos triple-DES enctype {et}", Severity.HIGH,
                               f"{where}: des3-cbc-sha1 is deprecated by RFC 8429 and removed from MIT krb5 1.21 defaults.", "Replace with AES enctypes.", (REF["RFC8429"],)))
    elif u.algorithm == "aes" and u.hash_algorithm == "sha1" and p.name in ("cnsa2", "bsi"):
        out.append(ctx.finding("KRB-AES-SHA1-PROFILE", f"Kerberos {et} uses HMAC-SHA1 (profile {p.name})", Severity.LOW,
                               f"{where}: RFC 8009 defines SHA-2 variants.", "Prefer aes256-cts-hmac-sha384-192 (RFC 8009) where all KDCs/clients support it.", (REF["BSI"],)))
    elif u.algorithm == "aes" and u.key_bits == 128 and p.strict_pq:
        out.append(ctx.finding("CIPHER-BELOW-PROFILE", f"Kerberos {et} is AES-128 (CNSA 2.0 requires AES-256)", Severity.MEDIUM, where, "Prefer aes256-* enctypes.", (REF["CNSA2"],)))
    elif u.algorithm == "unknown" and u.extra.get("etype_id") is not None:
        out.append(ctx.finding("KRB-UNKNOWN-ENCTYPE", f"Unknown Kerberos enctype {u.raw}", Severity.LOW, where, "Verify the enctype against RFC 3961 registry.", ()))
    return out


def rule_certificate(ctx: Context) -> List[Finding]:
    """Asset-level certificate checks (validity window, constraints)."""
    a, p, now = ctx.asset, ctx.profile, ctx.now
    out: List[Finding] = []
    attrs = a.attributes
    nb, na = attrs.get("not_before"), attrs.get("not_after")
    anchor = _is_trust_anchor(a)

    def _parse(t):
        if not t:
            return None
        try:
            return _dt.datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        except ValueError:
            return None

    nbd, nad = _parse(nb), _parse(na)
    if nad is not None:
        if nad < now:
            days = (now - nad).days
            out.append(ctx.finding("CERT-EXPIRED", f"Certificate expired {days} days ago", Severity.MEDIUM if anchor else Severity.HIGH,
                                   f"{a.name}: notAfter {na}.", "Renew or remove the certificate." if not anchor else "Remove the expired root from the trust store.", (REF["CAB"],)))
        elif (nad - now).days <= 30:
            out.append(ctx.finding("CERT-EXPIRING", f"Certificate expires in {(nad - now).days} days", Severity.MEDIUM, f"{a.name}: notAfter {na}.", "Renew the certificate.", ()))
    if nbd is not None and nbd > now:
        out.append(ctx.finding("CERT-NOT-YET-VALID", "Certificate not yet valid", Severity.MEDIUM, f"{a.name}: notBefore {nb}.", "Check clock skew or re-issue.", ()))
    if nbd and nad and not anchor and not attrs.get("is_ca"):
        days = (nad - nbd).days
        if days > 398 and "serverAuth" in (attrs.get("ext_key_usage") or []) and not attrs.get("self_signed"):
            out.append(ctx.finding("CERT-LONG-VALIDITY", f"Leaf certificate validity of {days} days exceeds 398", Severity.LOW,
                                   f"{a.name}", "Issue leaf certificates for <= 398 days (CA/B BR; 47 days from 2029).", (REF["CAB"],)))
    if attrs.get("version") and int(attrs["version"]) < 3 and not anchor:
        out.append(ctx.finding("CERT-V1", "X.509 version 1 certificate (no extensions)", Severity.LOW, f"{a.name}", "Re-issue as v3 with SAN, keyUsage and basicConstraints.", (REF["CAB"],)))
    if a.kind == AssetKind.CERTIFICATE and attrs.get("ext_key_usage") and "serverAuth" in attrs["ext_key_usage"] and not attrs.get("sans") and not attrs.get("self_signed"):
        out.append(ctx.finding("CERT-NO-SAN", "Server certificate without subjectAltName", Severity.LOW, f"{a.name}: modern clients ignore the CN.", "Re-issue with SAN entries.", (REF["CAB"],)))
    if attrs.get("self_signed") and not attrs.get("is_ca") and a.kind == AssetKind.CERTIFICATE and not attrs.get("is_default_snakeoil"):
        out.append(ctx.finding("CERT-SELF-SIGNED", "Self-signed end-entity certificate", Severity.INFO, f"{a.name}", "Issue from an internal CA so clients can validate it.", ()))
    if attrs.get("serial_bits") is not None and int(attrs["serial_bits"]) < 64 and not anchor and p.name != "legacy":
        out.append(ctx.finding("CERT-SHORT-SERIAL", f"Serial number has only {attrs['serial_bits']} bits", Severity.INFO, f"{a.name}: CA/B BR requires >= 64 bits of CSPRNG output to resist chosen-prefix collisions.", "Use a conformant CA.", (REF["CAB"],)))
    if attrs.get("explicit_curve_params"):
        pass  # covered by PK-EC-EXPLICIT
    return out


def rule_private_key(ctx: Context) -> List[Finding]:
    a = ctx.asset
    out: List[Finding] = []
    attrs = a.attributes
    if a.kind not in (AssetKind.PRIVATE_KEY, AssetKind.SSH_HOST_KEY, AssetKind.SSH_USER_KEY):
        return out
    mode = attrs.get("mode")
    if mode is not None and (int(mode) & 0o077):
        sev = Severity.HIGH if int(mode) & 0o004 else Severity.MEDIUM
        out.append(ctx.finding("KEY-PERMS", f"Private key readable by {'others' if int(mode) & 0o004 else 'group'} (mode {int(mode):04o})", sev,
                               f"{a.location}", "chmod 600 the key file; check ownership.", ()))
    if attrs.get("encrypted") is False and a.kind == AssetKind.SSH_USER_KEY:
        out.append(ctx.finding("KEY-UNENCRYPTED", "Unencrypted user private key on disk", Severity.LOW, f"{a.location}", "Protect the key with a passphrase (ssh-keygen -p -a 64) or move it to a hardware token / agent.", ()))
    if attrs.get("encrypted") is False and a.kind == AssetKind.PRIVATE_KEY and attrs.get("fmt") not in ("openssh",) and not attrs.get("service_key"):
        out.append(ctx.finding("KEY-UNENCRYPTED", "Unencrypted private key on disk", Severity.INFO, f"{a.location}", "Confirm the key belongs to a service that needs it unattended; otherwise encrypt it.", ()))
    note = attrs.get("encryption_note") or ""
    if "des-cbc" in note or "PBES1" in note or "RC2" in note or "RC4" in note or "md5" in note.lower() and "pbe" in note.lower():
        out.append(ctx.finding("KEY-WEAK-PBE", f"Private key encrypted with a legacy PBE scheme ({note})", Severity.MEDIUM, f"{a.location}", "Re-encrypt with PBES2 / AES-256 / PBKDF2-HMAC-SHA256 (openssl pkcs8 -topk8 -v2 aes-256-cbc -v2prf hmacWithSHA256).", ()))
    elif "prf=hmac-sha1" in note:
        out.append(ctx.finding("KEY-PBKDF2-SHA1", "Private key PBKDF2 uses HMAC-SHA1 PRF", Severity.INFO, f"{a.location}", "Re-encrypt with -v2prf hmacWithSHA256.", ()))
    if attrs.get("fmt") == "openssh" and attrs.get("encrypted") and "kdf=none" in note:
        pass
    if attrs.get("fmt") == "pkcs1" and attrs.get("encrypted"):
        out.append(ctx.finding("KEY-LEGACY-PEM-ENC", "Legacy PEM encryption (MD5-derived key, no iteration)", Severity.MEDIUM, f"{a.location}", "Convert to PKCS#8 PBES2 (openssl pkcs8 -topk8 -v2 aes-256-cbc).", ()))
    return out


def rule_config(ctx: Context) -> List[Finding]:
    """CONFIG primitive: generic knobs recorded by collectors as algorithm=<knob>."""
    u, p = ctx.use, ctx.profile
    out: List[Finding] = []
    k, v = u.algorithm, (u.raw or "")
    where = f"{ctx.asset.name}"
    if k == "crypto-policy":
        pol = v.upper()
        if pol.startswith("LEGACY"):
            out.append(ctx.finding("CFG-CRYPTO-POLICY-LEGACY", f"System crypto policy is {v}", Severity.HIGH, f"{where}: LEGACY re-enables TLS 1.0/1.1, DH-1024, SHA-1 signatures and 3DES system-wide.", "update-crypto-policies --set DEFAULT (or FUTURE / FIPS).", ()))
        elif pol.startswith("DEFAULT:SHA1") or ":SHA1" in pol:
            out.append(ctx.finding("CFG-CRYPTO-POLICY-SHA1", f"System crypto policy {v} re-enables SHA-1 signatures", Severity.MEDIUM, where, "Drop the SHA1 subpolicy once dependent systems are fixed.", ()))
        elif pol in ("DEFAULT",) and p.name in ("cnsa2", "bsi"):
            out.append(ctx.finding("CFG-CRYPTO-POLICY-DEFAULT", "System crypto policy DEFAULT (profile expects FUTURE/FIPS)", Severity.LOW, where, "update-crypto-policies --set FUTURE.", ()))
    elif k == "fips-mode":
        if v in ("0", "off", "disabled") and p.name in ("cnsa2",):
            out.append(ctx.finding("CFG-FIPS-OFF", "FIPS mode disabled", Severity.LOW, where, "Enable FIPS mode if required by policy.", ()))
    elif k == "openssl-seclevel":
        try:
            lvl = int(v)
        except ValueError:
            lvl = 1
        if lvl < 2:
            out.append(ctx.finding("CFG-OPENSSL-SECLEVEL", f"OpenSSL security level {lvl} (< 2) allows 80-bit/SHA-1/1024-bit material", Severity.MEDIUM, where, "Set CipherString = DEFAULT@SECLEVEL=2 in openssl.cnf.", ()))
    elif k == "openssl-min-protocol":
        pass  # emitted as PROTOCOL use too
    elif k == "ssh-fingerprint-hash" and v.lower() == "md5":
        out.append(ctx.finding("CFG-SSH-FPR-MD5", "FingerprintHash md5", Severity.LOW, where, "Use the default sha256.", ()))
    elif k == "ssh-protocol" and "1" in v.split(","):
        out.append(ctx.finding("SSH-PROTOCOL-1", "SSH 'Protocol 1' configured", Severity.CRITICAL, where, "Remove the Protocol directive.", ()))
    elif k == "krb-allow-weak-crypto" and v.lower() in ("true", "yes", "1"):
        out.append(ctx.finding("KRB-ALLOW-WEAK", "allow_weak_crypto = true", Severity.HIGH, f"{where}: re-enables DES, RC4-export and other weak enctypes library-wide.", "Set allow_weak_crypto = false (default).", (REF["KRBWEAK"],)))
    elif k == "krb-permitted-contains-weak":
        pass
    elif k == "java-disabled-algorithms-missing":
        out.append(ctx.finding("CFG-JAVA-DISABLED-ALGS", f"java.security weakens jdk.tls.disabledAlgorithms ({v})", Severity.MEDIUM, where, "Restore the JDK default disabled-algorithm list.", ()))
    elif k == "ssh-kex-strict" and v == "false":
        pass
    elif k == "ssh-version":
        out.extend(_ssh_version_findings(ctx, v))
    elif k == "openssl-version":
        out.extend(_openssl_version_findings(ctx, v))
    elif k == "dh-param-missing":
        out.append(ctx.finding("CFG-DHPARAM-DEFAULT", f"{v}", Severity.LOW, where, "Set ssl_dhparam / SSLOpenSSLConfCmd DHParameters to a >= 2048-bit group (ffdhe2048+).", (REF["LOGJAM"],)))
    elif k == "weak-moduli":
        out.append(ctx.finding("SSH-WEAK-MODULI", f"/etc/ssh/moduli contains {v} groups under 2048 bits", Severity.MEDIUM, where, "awk '$5 >= 3071' /etc/ssh/moduli > moduli.safe && mv moduli.safe /etc/ssh/moduli", (REF["RFC8270"],)))
    elif k == "snmp-auth-proto":
        if v.lower() in ("md5",):
            out.append(ctx.finding("SNMP-AUTH-MD5", "SNMPv3 authentication with MD5", Severity.MEDIUM, where, "Use SHA-256 (usmHMAC192SHA256AuthProtocol) or at least SHA-1.", (REF["SNMP"],)))
    elif k == "snmp-priv-proto":
        if v.lower() in ("des", "des56"):
            out.append(ctx.finding("SNMP-PRIV-DES", "SNMPv3 privacy with DES", Severity.HIGH, where, "Use AES-128 or AES-256.", (REF["SNMP"],)))
        elif v.lower() in ("3des",):
            out.append(ctx.finding("SNMP-PRIV-3DES", "SNMPv3 privacy with 3DES", Severity.MEDIUM, where, "Use AES-128 or AES-256.", (REF["SNMP"],)))
    elif k == "password-hash":
        weak = {"type7": ("Cisco type 7 (reversible Vigenère)", Severity.CRITICAL), "type5": ("Cisco type 5 (MD5 crypt)", Severity.MEDIUM),
                "type4": ("Cisco type 4 (unsalted SHA-256, weaker than type 5)", Severity.HIGH), "type0": ("clear-text password", Severity.CRITICAL),
                "md5crypt": ("MD5-crypt ($1$)", Severity.MEDIUM), "descrypt": ("DES-crypt", Severity.HIGH), "junos-9": ("Junos $9$ (reversible)", Severity.CRITICAL),
                "junos-1": ("Junos $1$ MD5", Severity.MEDIUM), "ntlm": ("NT hash (unsalted MD4)", Severity.HIGH), "sha1crypt": ("SHA-1 based hash", Severity.LOW)}
        if v in weak:
            label, sev = weak[v]
            out.append(ctx.finding("CFG-PASSWORD-HASH", f"Stored secret uses {label}", sev, f"{where} ({u.context})", "Use type 8/9 (PBKDF2-SHA256 / scrypt) on Cisco, $6$ SHA-512-crypt or better elsewhere; never type 7.", ()))
    elif k == "wireguard":
        pass
    return out


def _ssh_version_findings(ctx: Context, banner: str) -> List[Finding]:
    import re
    out: List[Finding] = []
    m = re.search(r"OpenSSH[_-](\d+)\.(\d+)", banner)
    if m:
        major, minor = int(m.group(1)), int(m.group(2))
        ver = major + minor / 100
        if ver < 7.4:
            out.append(ctx.finding("SSH-OLD-OPENSSH", f"OpenSSH {major}.{minor} is end-of-life with known CVEs", Severity.HIGH, f"{ctx.asset.name}: banner {banner}", "Upgrade OpenSSH.", ()))
        elif ver < 9.6:
            out.append(ctx.finding("SSH-TERRAPIN-VERSION", f"OpenSSH {major}.{minor} predates strict key exchange (Terrapin)", Severity.LOW, f"{ctx.asset.name}: banner {banner}", "Upgrade to OpenSSH 9.6+ or disable chacha20-poly1305 and *-etm CBC.", (REF["TERRAPIN"],)))
    elif re.search(r"SSH-1\.(5|99)", banner):
        out.append(ctx.finding("SSH-PROTOCOL-1", "SSH-1.x banner", Severity.CRITICAL, f"{ctx.asset.name}: {banner}", "Disable SSHv1.", ()))
    return out


def _openssl_version_findings(ctx: Context, ver: str) -> List[Finding]:
    import re
    out: List[Finding] = []
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", ver)
    if m:
        maj, mi = int(m.group(1)), int(m.group(2))
        if maj < 1 or (maj == 1 and mi < 1):
            out.append(ctx.finding("CFG-OPENSSL-EOL", f"OpenSSL {ver} is end-of-life", Severity.HIGH, ctx.asset.name, "Upgrade to OpenSSL 3.x.", ()))
        elif maj == 1:
            out.append(ctx.finding("CFG-OPENSSL-EOL", f"OpenSSL {ver} (1.x) is end-of-life since Sep 2023", Severity.MEDIUM, ctx.asset.name, "Upgrade to OpenSSL 3.x LTS.", ()))
    return out


RULES: Dict[Primitive, RuleFn] = {
    Primitive.PUBLIC_KEY: rule_public_key,
    Primitive.SIGNATURE: rule_signature,
    Primitive.KEY_EXCHANGE: rule_key_exchange,
    Primitive.CIPHER: rule_cipher,
    Primitive.MAC: rule_mac,
    Primitive.HASH: rule_hash,
    Primitive.PROTOCOL: rule_protocol,
    Primitive.ENCTYPE: rule_enctype,
    Primitive.CONFIG: rule_config,
}


def _pqc_summary(asset: Asset, profile: Profile, now: _dt.datetime) -> List[Finding]:
    """One INFO/LOW finding per asset that depends on quantum-vulnerable public-key crypto."""
    if not profile.quantum_report:
        return []
    qv = [u for u in asset.uses if u.algorithm in QUANTUM_VULNERABLE and u.primitive in (Primitive.PUBLIC_KEY, Primitive.SIGNATURE, Primitive.KEY_EXCHANGE)
          and not u.extra.get("negated")]
    if not qv:
        return []
    qs = [u for u in asset.uses if u.algorithm in QUANTUM_SAFE]
    algs = sorted({u.describe() for u in qv})
    has_hybrid = bool(qs)
    ctx = Context(asset, None, profile, now)
    sev = Severity.INFO if has_hybrid else (Severity.LOW if profile.pq_disallow_year else Severity.INFO)
    note = " Quantum-safe alternatives are also offered." if has_hybrid else ""
    return [ctx.finding("PQC-TRANSITION", "Depends on quantum-vulnerable public-key cryptography" + (" (hybrid PQ also available)" if has_hybrid else ""), sev,
                        f"{asset.name} uses {', '.join(algs[:8])}{' ...' if len(algs) > 8 else ''}; all of these fall to Shor's algorithm on a cryptographically relevant quantum computer. Data encrypted today is exposed to harvest-now-decrypt-later.{note}",
                        f"Inventory this asset for the PQC migration plan; target ML-KEM (FIPS 203) hybrids for key establishment and ML-DSA (FIPS 204) / SLH-DSA (FIPS 205) for signatures before {profile.pq_disallow_year or 2035}.",
                        (REF["8547"], REF["FIPS203"], REF["FIPS204"]), quantum=True, year=profile.pq_deprecation_year, tags=("pqc",))]


def evaluate(assets: List[Asset], profile_name: str = "nist", now: Optional[_dt.datetime] = None) -> List[Finding]:
    """Grade every asset against a profile.  Deterministic; duplicate findings collapse."""
    profile = PROFILES[profile_name]
    now = now or _dt.datetime.now(_dt.timezone.utc)
    findings: Dict[str, Finding] = {}
    for asset in assets:
        for use in asset.uses:
            rule = RULES.get(use.primitive)
            if rule is None:
                continue
            for f in rule(Context(asset, use, profile, now)):
                findings.setdefault(f.finding_id, f)
        ctx = Context(asset, None, profile, now)
        for f in rule_certificate(ctx) + rule_private_key(ctx) + _pqc_summary(asset, profile, now):
            findings.setdefault(f.finding_id, f)
        for err in asset.errors:
            f = ctx.finding("COLLECT-ERROR", "Collector could not fully inspect this asset", Severity.INFO, err, "Re-run with sufficient privileges or inspect manually.", ())
            findings.setdefault(f.finding_id, f)
    out = list(findings.values())
    for f in out:
        if f.rule_id not in ("PQC-TRANSITION", "COLLECT-ERROR") and f.asset_kind in (
                AssetKind.CERTIFICATE, AssetKind.CA_CERTIFICATE, AssetKind.PRIVATE_KEY, AssetKind.JAVA_KEYSTORE,
                AssetKind.SSH_USER_KEY, AssetKind.PGP_KEY) and is_test_material(f.location):
            # Test fixtures shipped inside packages are inventory, not exposure: keep them visible but quiet.
            f.tags.append("test-data")
            if f.severity > Severity.LOW:
                f.description += " [Capped at LOW: the file lives in a test/example tree.]"
                f.severity = Severity.LOW
    out.sort(key=lambda f: (-int(f.severity), f.rule_id, f.asset_name, f.location))
    return out
