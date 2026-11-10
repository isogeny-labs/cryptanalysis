"""X.509 certificate and public-key parsing on top of the DER decoder.

Produces a :class:`Certificate` with the fields the policy engine needs:
subject, issuer, validity, signature algorithm (+hash), public key algorithm,
key size, named curve, basic constraints, key usage, SANs.  Also parses bare
SubjectPublicKeyInfo and the common private-key encodings so key files on disk
can be inventoried.
"""

from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple

from . import asn1
from .asn1 import DERError, Node
from .oids import CURVE_OIDS, DN_OIDS, EXT_OIDS, HASH_OIDS, PUBLIC_KEY_OIDS, SIGNATURE_OIDS

PEM_RE = re.compile(rb"-----BEGIN ([A-Z0-9 ]+)-----\s*(.*?)\s*-----END \1-----", re.S)


@dataclass
class PublicKeyInfo:
    algorithm: str                      # "rsa", "ec", "dsa", "ed25519", "x25519", "dh", "ml-dsa-65", ...
    key_bits: Optional[int] = None
    curve: Optional[str] = None
    curve_oid: Optional[str] = None
    explicit_curve_params: bool = False
    rsa_exponent: Optional[int] = None
    spki_sha256: Optional[str] = None


@dataclass
class Certificate:
    der: bytes
    version: int
    serial: int
    subject: str
    issuer: str
    not_before: _dt.datetime
    not_after: _dt.datetime
    signature_algorithm: str            # "rsa", "ecdsa", "rsa-pss", ...
    signature_hash: Optional[str]
    signature_oid: str
    public_key: PublicKeyInfo
    is_ca: bool = False
    path_len: Optional[int] = None
    key_usage: List[str] = field(default_factory=list)
    ext_key_usage: List[str] = field(default_factory=list)
    sans: List[str] = field(default_factory=list)
    extensions: Dict[str, bool] = field(default_factory=dict)    # name -> critical
    subject_key_id: Optional[str] = None
    authority_key_id: Optional[str] = None
    parse_warnings: List[str] = field(default_factory=list)

    @property
    def fingerprint_sha256(self) -> str:
        return hashlib.sha256(self.der).hexdigest()

    @property
    def fingerprint_sha1(self) -> str:
        return hashlib.sha1(self.der).hexdigest()

    @property
    def self_signed(self) -> bool:
        if self.subject != self.issuer:
            return False
        if self.subject_key_id and self.authority_key_id:
            return self.subject_key_id == self.authority_key_id
        return True

    @property
    def self_issued(self) -> bool:
        return self.subject == self.issuer

    def validity_days(self) -> int:
        return (self.not_after - self.not_before).days

    def summary(self) -> Dict[str, object]:
        pk = self.public_key
        return {
            "subject": self.subject,
            "issuer": self.issuer,
            "serial": format(self.serial, "x"),
            "not_before": self.not_before.isoformat(),
            "not_after": self.not_after.isoformat(),
            "signature_algorithm": self.signature_algorithm,
            "signature_hash": self.signature_hash,
            "public_key_algorithm": pk.algorithm,
            "key_bits": pk.key_bits,
            "curve": pk.curve,
            "is_ca": self.is_ca,
            "self_signed": self.self_signed,
            "sha256": self.fingerprint_sha256,
            "sans": self.sans[:20],
            "key_usage": self.key_usage,
            "ext_key_usage": self.ext_key_usage,
            "version": self.version,
        }


# ----------------------------------------------------------------------------
# PEM helpers
# ----------------------------------------------------------------------------

def iter_pem(data: bytes) -> Iterator[Tuple[str, bytes]]:
    """Yield (label, der) for every PEM block in data."""
    for m in PEM_RE.finditer(data):
        label = m.group(1).decode()
        body = re.sub(rb"\s+", b"", m.group(2))
        # Skip "Proc-Type:/DEK-Info:" headers of legacy encrypted PEM
        if b":" in body:
            # headers are before a blank line; base64 can't contain ':'
            try:
                body = m.group(2).split(b"\n\n", 1)[1]
                body = re.sub(rb"\s+", b"", body)
            except IndexError:
                continue
        try:
            yield label, base64.b64decode(body, validate=False)
        except Exception:
            continue


def pem_has_encryption_headers(data: bytes) -> bool:
    return b"Proc-Type: 4,ENCRYPTED" in data or b"DEK-Info:" in data


def load_certificates(data: bytes) -> List[Certificate]:
    """Parse all certificates from PEM or DER input (also PKCS#7 bundles)."""
    certs: List[Certificate] = []
    if b"-----BEGIN" in data:
        for label, der in iter_pem(data):
            if label in ("CERTIFICATE", "X509 CERTIFICATE", "TRUSTED CERTIFICATE"):
                try:
                    certs.append(parse_certificate(der))
                except DERError:
                    continue
            elif label in ("PKCS7", "CMS"):
                certs.extend(_certs_from_pkcs7(der))
        return certs
    # Binary: try one certificate, then PKCS#7, then concatenated DER
    try:
        return [parse_certificate(data)]
    except DERError:
        pass
    pk7 = _certs_from_pkcs7(data)
    if pk7:
        return pk7
    rest = data
    while rest:
        try:
            node, rest = asn1.decode_prefix(rest)
            certs.append(parse_certificate(node.raw))
        except DERError:
            break
    return certs


def _certs_from_pkcs7(der: bytes) -> List[Certificate]:
    try:
        root = asn1.decode(der)
        if not root.is_sequence or len(root.children) < 2:
            return []
        if root.children[0].as_oid() != "1.2.840.113549.1.7.2":
            return []
        signed = root.children[1].children[0]         # [0] EXPLICIT SignedData
        certs_node = signed.context(0)
        if certs_node is None:
            return []
        return [parse_certificate(c.raw) for c in certs_node.children if c.is_sequence]
    except (DERError, IndexError):
        return []


# ----------------------------------------------------------------------------
# Certificate parsing
# ----------------------------------------------------------------------------

def _dn_to_string(node: Node) -> str:
    parts = []
    for rdn in node.children:              # SET OF AttributeTypeAndValue
        for atv in rdn.children:
            if len(atv.children) < 2:
                continue
            oid = atv.children[0].as_oid()
            name = DN_OIDS.get(oid, oid)
            parts.append(f"{name}={atv.children[1].as_str()}")
    return ",".join(parts)


def _algorithm_identifier(node: Node) -> Tuple[str, Optional[Node]]:
    oid = node.children[0].as_oid()
    params = node.children[1] if len(node.children) > 1 else None
    return oid, params


def _pss_hash(params: Optional[Node]) -> Optional[str]:
    # RSASSA-PSS-params ::= SEQUENCE { hashAlgorithm [0] ... } ; default SHA-1
    if params is None or not params.children:
        return "sha1"
    h = params.context(0)
    if h is None:
        return "sha1"
    try:
        return HASH_OIDS.get(h.children[0].children[0].as_oid(), "unknown")
    except (DERError, IndexError):
        return "unknown"


def parse_spki(node: Node) -> PublicKeyInfo:
    """Parse a SubjectPublicKeyInfo node."""
    alg_oid, params = _algorithm_identifier(node.children[0])
    alg = PUBLIC_KEY_OIDS.get(alg_oid, alg_oid)
    _, keybytes = node.children[1].as_bitstring()
    info = PublicKeyInfo(algorithm=alg, spki_sha256=hashlib.sha256(node.raw).hexdigest())
    if alg in ("rsa", "rsa-pss"):
        try:
            seq = asn1.decode(keybytes)
            n = seq.children[0].as_int()
            info.key_bits = n.bit_length()
            info.rsa_exponent = seq.children[1].as_int()
        except (DERError, IndexError):
            pass
    elif alg == "ec":
        if params is not None and params.tag == asn1.OID:
            oid = params.as_oid()
            info.curve_oid = oid
            name, bits = CURVE_OIDS.get(oid, (oid, None))
            info.curve, info.key_bits = name, bits
        elif params is not None and params.is_sequence:
            info.explicit_curve_params = True
            info.curve = "explicit"
            try:   # ECParameters: version, fieldID{SEQ{oid, p}}, ...
                p = params.children[1].children[1]
                if p.tag == asn1.INTEGER:
                    info.key_bits = p.as_int().bit_length()
            except (DERError, IndexError):
                pass
        else:
            # Uncompressed point length gives the field size
            if keybytes and keybytes[0] == 4:
                info.key_bits = ((len(keybytes) - 1) // 2) * 8
    elif alg == "dsa":
        try:
            if params is not None and params.is_sequence:
                info.key_bits = params.children[0].as_int().bit_length()
            else:
                info.key_bits = asn1.decode(keybytes).as_int().bit_length()
        except (DERError, IndexError):
            pass
    elif alg == "dh":
        try:
            if params is not None and params.is_sequence:
                info.key_bits = params.children[0].as_int().bit_length()
        except (DERError, IndexError):
            pass
    elif alg in ("ed25519", "x25519"):
        info.key_bits, info.curve = 256, "curve25519"
    elif alg in ("ed448", "x448"):
        info.key_bits, info.curve = 448, "curve448"
    elif alg.startswith("ml-kem-"):
        info.key_bits = {"512": 512, "768": 768, "1024": 1024}[alg.split("-")[-1]]
    elif alg.startswith("ml-dsa-"):
        info.key_bits = {"44": 128, "65": 192, "87": 256}[alg.split("-")[-1]]
    return info


_KU_BITS = ["digitalSignature", "nonRepudiation", "keyEncipherment", "dataEncipherment",
            "keyAgreement", "keyCertSign", "cRLSign", "encipherOnly", "decipherOnly"]
_EKU = {
    "1.3.6.1.5.5.7.3.1": "serverAuth", "1.3.6.1.5.5.7.3.2": "clientAuth",
    "1.3.6.1.5.5.7.3.3": "codeSigning", "1.3.6.1.5.5.7.3.4": "emailProtection",
    "1.3.6.1.5.5.7.3.8": "timeStamping", "1.3.6.1.5.5.7.3.9": "OCSPSigning",
    "2.5.29.37.0": "anyExtendedKeyUsage", "1.3.6.1.4.1.311.10.3.4": "efs",
    "1.3.6.1.5.5.7.3.5": "ipsecEndSystem", "1.3.6.1.5.5.7.3.6": "ipsecTunnel",
    "1.3.6.1.5.5.7.3.7": "ipsecUser", "1.3.6.1.5.5.8.2.2": "ikeIntermediate",
    "1.3.6.1.5.2.3.5": "kdc", "1.3.6.1.4.1.311.20.2.2": "smartCardLogon",
}


def parse_certificate(der: bytes) -> Certificate:
    try:
        root = asn1.decode(der)
    except DERError:
        # Tolerate trailing garbage after the certificate
        root, _ = asn1.decode_prefix(der)
        der = root.raw
    if not root.is_sequence or len(root.children) != 3:
        raise DERError("not a Certificate SEQUENCE")
    tbs, sigalg, _sig = root.children
    idx = 0
    version = 1
    if tbs.children and tbs.children[0].tag_class == 2 and tbs.children[0].tag == 0:
        version = tbs.children[0].children[0].as_int() + 1
        idx = 1
    serial = tbs.children[idx].as_int()
    # tbs.children[idx+1] = signature AlgorithmIdentifier (inner)
    issuer = _dn_to_string(tbs.children[idx + 2])
    validity = tbs.children[idx + 3]
    not_before = validity.children[0].as_time()
    not_after = validity.children[1].as_time()
    subject = _dn_to_string(tbs.children[idx + 4])
    spki = parse_spki(tbs.children[idx + 5])

    sig_oid, sig_params = _algorithm_identifier(sigalg)
    sig_alg, sig_hash = SIGNATURE_OIDS.get(sig_oid, (sig_oid, None))
    if sig_alg == "rsa-pss":
        sig_hash = _pss_hash(sig_params)

    cert = Certificate(der=der, version=version, serial=serial, subject=subject, issuer=issuer,
                       not_before=not_before, not_after=not_after, signature_algorithm=sig_alg,
                       signature_hash=sig_hash, signature_oid=sig_oid, public_key=spki)

    exts = tbs.context(3) if version == 3 else None
    if exts is not None and exts.children:
        for ext in exts.children[0].children:
            try:
                _parse_extension(cert, ext)
            except (DERError, IndexError, ValueError) as e:
                cert.parse_warnings.append(f"extension parse error: {e}")
    return cert


def _parse_extension(cert: Certificate, ext: Node) -> None:
    oid = ext.children[0].as_oid()
    critical = False
    val_idx = 1
    if len(ext.children) == 3:
        critical = ext.children[1].value == b"\xff"
        val_idx = 2
    value = ext.children[val_idx].value
    name = EXT_OIDS.get(oid, oid)
    cert.extensions[name] = critical
    if name == "basicConstraints":
        node = asn1.decode(value)
        for c in node.children:
            if c.tag == asn1.BOOLEAN:
                cert.is_ca = c.value == b"\xff"
            elif c.tag == asn1.INTEGER:
                cert.path_len = c.as_int()
    elif name == "keyUsage":
        unused, bits = asn1.decode(value).as_bitstring()
        if bits:
            flags = int.from_bytes(bits, "big")
            nbits = len(bits) * 8 - unused
            for i, label in enumerate(_KU_BITS):
                if i < nbits and flags >> (len(bits) * 8 - 1 - i) & 1:
                    cert.key_usage.append(label)
    elif name == "extKeyUsage":
        for c in asn1.decode(value).children:
            o = c.as_oid()
            cert.ext_key_usage.append(_EKU.get(o, o))
    elif name == "subjectAltName":
        for gn in asn1.decode(value).children:
            if gn.tag_class != 2:
                continue
            if gn.tag == 2:
                cert.sans.append("DNS:" + gn.value.decode("ascii", "replace"))
            elif gn.tag == 1:
                cert.sans.append("email:" + gn.value.decode("ascii", "replace"))
            elif gn.tag == 7:
                if len(gn.value) == 4:
                    cert.sans.append("IP:" + ".".join(str(b) for b in gn.value))
                elif len(gn.value) == 16:
                    import ipaddress
                    cert.sans.append("IP:" + str(ipaddress.IPv6Address(gn.value)))
            elif gn.tag == 6:
                cert.sans.append("URI:" + gn.value.decode("ascii", "replace"))
    elif name == "subjectKeyIdentifier":
        cert.subject_key_id = asn1.decode(value).value.hex()
    elif name == "authorityKeyIdentifier":
        kid = asn1.decode(value).context(0)
        if kid is not None:
            cert.authority_key_id = kid.value.hex()


# ----------------------------------------------------------------------------
# Private / public key files
# ----------------------------------------------------------------------------

@dataclass
class KeyFileInfo:
    kind: str                       # "private" | "public" | "encrypted-private" | "unknown"
    fmt: str                        # "pkcs8", "pkcs1", "sec1", "openssh", "dsa", "spki", "pkcs8-encrypted", "pkcs12"
    public_key: Optional[PublicKeyInfo] = None
    encrypted: bool = False
    note: Optional[str] = None


def parse_key_data(data: bytes) -> List[KeyFileInfo]:
    """Identify key material in a file (PEM or DER). Never raises."""
    out: List[KeyFileInfo] = []
    if b"-----BEGIN" in data:
        legacy_enc = pem_has_encryption_headers(data)
        for label, der in iter_pem(data):
            try:
                if label == "RSA PRIVATE KEY":
                    info = _pkcs1_private(der) if not legacy_enc else None
                    out.append(KeyFileInfo("encrypted-private" if legacy_enc else "private", "pkcs1", info, legacy_enc))
                elif label == "EC PRIVATE KEY":
                    info = _sec1_private(der) if not legacy_enc else None
                    out.append(KeyFileInfo("encrypted-private" if legacy_enc else "private", "sec1", info, legacy_enc))
                elif label == "DSA PRIVATE KEY":
                    info = _dsa_private(der) if not legacy_enc else None
                    out.append(KeyFileInfo("encrypted-private" if legacy_enc else "private", "dsa", info, legacy_enc))
                elif label == "PRIVATE KEY":
                    out.append(KeyFileInfo("private", "pkcs8", _pkcs8_private(der)))
                elif label == "ENCRYPTED PRIVATE KEY":
                    out.append(KeyFileInfo("encrypted-private", "pkcs8-encrypted", None, True, _pkcs8_enc_note(der)))
                elif label == "OPENSSH PRIVATE KEY":
                    out.append(_openssh_private(der))
                elif label == "PUBLIC KEY":
                    out.append(KeyFileInfo("public", "spki", parse_spki(asn1.decode(der))))
                elif label == "RSA PUBLIC KEY":
                    seq = asn1.decode(der)
                    out.append(KeyFileInfo("public", "pkcs1", PublicKeyInfo("rsa", seq.children[0].as_int().bit_length())))
                elif label == "DH PARAMETERS":
                    seq = asn1.decode(der)
                    out.append(KeyFileInfo("parameters", "dhparam", PublicKeyInfo("dh", seq.children[0].as_int().bit_length())))
                elif label == "EC PARAMETERS":
                    node = asn1.decode(der)
                    name, bits = CURVE_OIDS.get(node.as_oid(), (node.as_oid(), None)) if node.tag == asn1.OID else ("explicit", None)
                    out.append(KeyFileInfo("parameters", "ecparam", PublicKeyInfo("ec", bits, name)))
            except (DERError, IndexError, ValueError, KeyError) as e:
                out.append(KeyFileInfo("unknown", label.lower(), None, False, f"parse error: {e}"))
        return out
    # DER
    for parser, fmt in ((_pkcs8_private, "pkcs8"), (_pkcs1_private, "pkcs1"), (_sec1_private, "sec1")):
        try:
            info = parser(data)
            if info:
                out.append(KeyFileInfo("private", fmt, info))
                return out
        except (DERError, IndexError, ValueError, KeyError):
            continue
    try:
        out.append(KeyFileInfo("public", "spki", parse_spki(asn1.decode(data))))
    except (DERError, IndexError, ValueError):
        pass
    if data[:4] == b"\x30\x82" or data[:2] == b"\x30\x80":
        try:
            if _looks_like_pkcs12(data):
                out.append(KeyFileInfo("encrypted-private", "pkcs12", None, True, "PKCS#12 container (password protected)"))
        except DERError:
            pass
    return out


def _pkcs1_private(der: bytes) -> PublicKeyInfo:
    seq = asn1.decode(der)
    if len(seq.children) < 9 or seq.children[0].as_int() != 0:
        raise DERError("not PKCS#1 RSAPrivateKey")
    n = seq.children[1].as_int()
    return PublicKeyInfo("rsa", n.bit_length(), rsa_exponent=seq.children[2].as_int())


def _sec1_private(der: bytes) -> PublicKeyInfo:
    seq = asn1.decode(der)
    if seq.children[0].as_int() != 1:
        raise DERError("not SEC1 ECPrivateKey")
    info = PublicKeyInfo("ec")
    params = seq.context(0)
    if params is not None and params.children and params.children[0].tag == asn1.OID:
        oid = params.children[0].as_oid()
        info.curve_oid = oid
        info.curve, info.key_bits = CURVE_OIDS.get(oid, (oid, None))
    else:
        info.key_bits = len(seq.children[1].value) * 8
        if params is not None:
            info.explicit_curve_params = True
            info.curve = "explicit"
    return info


def _dsa_private(der: bytes) -> PublicKeyInfo:
    seq = asn1.decode(der)
    if len(seq.children) != 6:
        raise DERError("not DSAPrivateKey")
    return PublicKeyInfo("dsa", seq.children[1].as_int().bit_length())


def _pkcs8_private(der: bytes) -> PublicKeyInfo:
    seq = asn1.decode(der)
    if seq.children[0].as_int() not in (0, 1):
        raise DERError("not PKCS#8")
    alg_oid, params = _algorithm_identifier(seq.children[1])
    alg = PUBLIC_KEY_OIDS.get(alg_oid, alg_oid)
    inner = seq.children[2].value
    if alg == "rsa":
        return _pkcs1_private(inner)
    if alg == "ec":
        info = PublicKeyInfo("ec")
        if params is not None and params.tag == asn1.OID:
            oid = params.as_oid()
            info.curve_oid = oid
            info.curve, info.key_bits = CURVE_OIDS.get(oid, (oid, None))
        else:
            info.explicit_curve_params = params is not None
            info.curve = "explicit" if params is not None else None
            try:
                info.key_bits = len(asn1.decode(inner).children[1].value) * 8
            except (DERError, IndexError):
                pass
        return info
    if alg == "dsa":
        bits = params.children[0].as_int().bit_length() if params is not None and params.is_sequence else None
        return PublicKeyInfo("dsa", bits)
    if alg in ("ed25519", "x25519"):
        return PublicKeyInfo(alg, 256, "curve25519")
    if alg in ("ed448", "x448"):
        return PublicKeyInfo(alg, 448, "curve448")
    return PublicKeyInfo(alg)


def _pkcs8_enc_note(der: bytes) -> str:
    try:
        seq = asn1.decode(der)
        oid, params = _algorithm_identifier(seq.children[0])
        if oid == "1.2.840.113549.1.5.13":            # PBES2
            kdf = params.children[0]
            enc = params.children[1]
            enc_oid = enc.children[0].as_oid()
            kdf_oid = kdf.children[0].as_oid()
            prf = "hmac-sha1"
            if kdf_oid == "1.2.840.113549.1.5.12":     # PBKDF2
                p = kdf.children[1]
                iters = p.children[1].as_int()
                for c in p.children[2:]:
                    if c.is_sequence:
                        prf = {"1.2.840.113549.2.7": "hmac-sha1", "1.2.840.113549.2.9": "hmac-sha256",
                               "1.2.840.113549.2.11": "hmac-sha512"}.get(c.children[0].as_oid(), c.children[0].as_oid())
                enc_name = {"2.16.840.1.101.3.4.1.2": "aes-128-cbc", "2.16.840.1.101.3.4.1.42": "aes-256-cbc",
                            "1.2.840.113549.3.7": "des-ede3-cbc", "1.3.14.3.2.7": "des-cbc"}.get(enc_oid, enc_oid)
                return f"PBES2 pbkdf2 iterations={iters} prf={prf} cipher={enc_name}"
            return f"PBES2 kdf={kdf_oid}"
        legacy = {"1.2.840.113549.1.5.3": "pbeWithMD5AndDES-CBC", "1.2.840.113549.1.5.10": "pbeWithSHA1AndDES-CBC",
                  "1.2.840.113549.1.12.1.3": "pbeWithSHAAnd3-KeyTripleDES-CBC", "1.2.840.113549.1.12.1.6": "pbeWithSHAAnd40BitRC2-CBC",
                  "1.2.840.113549.1.12.1.1": "pbeWithSHAAnd128BitRC4"}
        return f"PBES1 {legacy.get(oid, oid)}"
    except (DERError, IndexError):
        return "unknown encryption scheme"


def _looks_like_pkcs12(der: bytes) -> bool:
    root, _ = asn1.decode_prefix(der)
    return (root.is_sequence and root.children and root.children[0].tag == asn1.INTEGER
            and root.children[0].as_int() == 3 and len(root.children) >= 2
            and root.children[1].is_sequence and root.children[1].children
            and root.children[1].children[0].tag == asn1.OID
            and root.children[1].children[0].as_oid() == "1.2.840.113549.1.7.1")


def _openssh_private(blob: bytes) -> KeyFileInfo:
    from .sshkeys import parse_openssh_private_blob
    return parse_openssh_private_blob(blob)
