"""CycloneDX 1.6 CBOM renderer: ``render(result) -> str`` (JSON).

Component model
---------------
* one ``cryptographic-asset`` / ``algorithm`` component per distinct
  (primitive, algorithm, key size, curve, hash, mode), de-duplicated across assets;
* one asset-level component per scanned Asset: ``certificate`` for certificates,
  ``protocol`` for SSH/TLS/Kerberos/IPsec/... endpoints and configs, and
  ``related-crypto-material`` for key files, keytabs and the like, plus a
  ``related-crypto-material`` public-key component for every certificate;
* ``dependencies[]`` link each asset-level component to the algorithm components
  it uses; ``evidence.occurrences`` carries the asset location;
* each Finding becomes a ``vulnerabilities[]`` entry affecting its asset component.

Deviations from the brief, all because the CycloneDX 1.6 schema is stricter:
``protocolProperties.type`` has no "kerberos"/"snmp" value, so those are emitted
as "other" with ``cryptoscan:protocol``.  Everything non-standard is kept under
``properties`` with the ``cryptoscan:`` prefix.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from .. import oids
from ..model import Asset, AssetKind, CryptoUse, Primitive, ScanResult
from ..names import security_strength
from ..policy import QUANTUM_SAFE, QUANTUM_VULNERABLE

ALGO_PRIMS = (Primitive.PUBLIC_KEY, Primitive.SIGNATURE, Primitive.KEY_EXCHANGE, Primitive.CIPHER, Primitive.MAC,
              Primitive.HASH, Primitive.KDF, Primitive.ENCTYPE)
CERT_KINDS = (AssetKind.CERTIFICATE, AssetKind.CA_CERTIFICATE)
PROTO_KINDS = (AssetKind.SSH_SERVER, AssetKind.SSH_CLIENT, AssetKind.SSH_REMOTE, AssetKind.TLS_ENDPOINT,
               AssetKind.KERBEROS_CONFIG, AssetKind.IPSEC_CONFIG, AssetKind.VPN_CONFIG, AssetKind.SNMP_AGENT)
MATERIAL_TYPE = {
    AssetKind.PRIVATE_KEY: "private-key", AssetKind.SSH_HOST_KEY: "private-key", AssetKind.SSH_USER_KEY: "private-key",
    AssetKind.SSH_AUTHORIZED_KEY: "public-key", AssetKind.SSH_KNOWN_HOST: "public-key",
    AssetKind.KERBEROS_KEYTAB: "secret-key", AssetKind.KERBEROS_TICKET: "credential", AssetKind.PGP_KEY: "key",
    AssetKind.JAVA_KEYSTORE: "key",
}
KEM_ALGS = {"ml-kem", "ml-kem-512", "ml-kem-768", "ml-kem-1024"}
SIGNATURE_ALGS = {"rsa-pss", "dsa", "ecdsa", "ecdsa-sk", "ed25519", "ed448", "ed25519-sk", "ec", "sm2",
                  "gost-r34.10-2001", "gost-r34.10-2012-256", "gost-r34.10-2012-512"}
KEY_AGREE_ALGS = {"dh", "dhe", "dh-gex", "dh-static", "ecdh", "ecdhe", "ecdh-static", "x25519", "x448", "srp",
                  "ecdh-anon", "dh-anon"}
STREAM_ALGS = {"rc4", "chacha20", "chacha20-poly1305"}
AEAD_MODES = {"gcm", "ccm", "poly1305", "ocb", "siv"}
MODES = {"cbc", "ecb", "ccm", "gcm", "cfb", "ofb", "ctr"}
NIST_PQ_LEVEL = {"ml-kem-512": 1, "ml-kem-768": 3, "ml-kem-1024": 5, "ml-dsa-44": 2, "ml-dsa-65": 3, "ml-dsa-87": 5}
FUNCTIONS = {"signature": ["sign", "verify"], "pke": ["encrypt", "decrypt"], "key-agree": ["keygen", "keyderive"],
             "kem": ["encapsulate", "decapsulate"], "combiner": ["keyderive"], "block-cipher": ["encrypt", "decrypt"],
             "stream-cipher": ["encrypt", "decrypt"], "ae": ["encrypt", "decrypt", "tag"], "mac": ["tag"],
             "hash": ["digest"], "kdf": ["keyderive"], "xof": ["digest"], "drbg": ["generate"]}


def _first_by_dict(table: Dict[str, Any]) -> Dict[Any, str]:
    out: Dict[Any, str] = {}
    for oid, v in table.items():
        out.setdefault(tuple(v) if isinstance(v, (tuple, list)) else v, oid)
    return out


_SIG_OID = _first_by_dict(oids.SIGNATURE_OIDS)
_PK_OID = _first_by_dict(oids.PUBLIC_KEY_OIDS)
_HASH_OID = _first_by_dict(oids.HASH_OIDS)


def slug(s: str, n: int = 40) -> str:
    return (re.sub(r"[^a-z0-9.]+", "-", s.lower()).strip("-") or "x")[:n].strip("-") or "x"


def cdx_primitive(use: CryptoUse) -> str:
    a, p = use.algorithm, use.primitive
    if p == Primitive.SIGNATURE:
        return "signature"
    if p == Primitive.PUBLIC_KEY:
        if a in ("rsa", "rsa-kex"):
            return "pke"
        if a in KEY_AGREE_ALGS:
            return "key-agree"
        if a in KEM_ALGS or a == "hybrid-pq":
            return "kem"
        return "signature" if (a in SIGNATURE_ALGS or a.startswith(("ml-dsa", "slh-dsa"))) else "other"
    if p == Primitive.KEY_EXCHANGE:
        if a == "hybrid-pq":
            return "combiner"
        if a in KEM_ALGS:
            return "kem"
        return "pke" if a == "rsa-kex" else "key-agree"
    if p in (Primitive.CIPHER, Primitive.ENCTYPE):
        if a in STREAM_ALGS and use.mode not in AEAD_MODES:
            return "ae" if "poly1305" in a else "stream-cipher"
        return "ae" if use.mode in AEAD_MODES else "block-cipher"
    return {Primitive.MAC: "mac", Primitive.HASH: "hash", Primitive.KDF: "kdf"}.get(p, "other")


def nist_quantum_level(use: CryptoUse) -> Optional[int]:
    a = use.algorithm
    if a in QUANTUM_VULNERABLE:
        return 0
    if a in NIST_PQ_LEVEL:
        return NIST_PQ_LEVEL[a]
    if a == "hybrid-pq":
        return NIST_PQ_LEVEL.get(str(use.extra.get("kem")), 3)
    if a in QUANTUM_SAFE:
        return None
    if use.primitive in (Primitive.CIPHER, Primitive.MAC, Primitive.HASH, Primitive.ENCTYPE, Primitive.KDF):
        s = security_strength(use)
        if s is None:
            return None
        return 0 if s < 128 else 1 if s < 192 else 3 if s < 256 else 5
    return None


def _oid(use: CryptoUse) -> Optional[str]:
    if use.primitive == Primitive.SIGNATURE:
        return _SIG_OID.get((use.algorithm, use.hash_algorithm))
    if use.primitive == Primitive.PUBLIC_KEY:
        return _PK_OID.get(use.algorithm)
    if use.primitive == Primitive.HASH:
        return _HASH_OID.get(use.algorithm)
    return None


class _Builder:
    def __init__(self) -> None:
        self.used: Set[str] = set()
        self.algs: Dict[Tuple, Dict[str, Any]] = {}
        self.alg_locs: Dict[str, Set[str]] = {}
        self.assets: List[Dict[str, Any]] = []
        self.deps: Dict[str, Set[str]] = {}

    def ref(self, kind: str, name: str, key: str) -> str:
        h = hashlib.sha256(key.encode()).hexdigest()[:12]
        base = f"crypto/{kind}/{slug(name)}"
        r = f"{base}@{h}"
        i = 1
        while r in self.used:
            r = f"{base}@{hashlib.sha256((key + str(i)).encode()).hexdigest()[:12]}"
            i += 1
        self.used.add(r)
        return r

    def algorithm(self, use: CryptoUse, location: str) -> Optional[str]:
        if use.primitive not in ALGO_PRIMS or use.algorithm in ("unknown", "", None):
            return None
        key = (use.primitive.value, use.algorithm, use.key_bits, use.curve, use.hash_algorithm, use.mode)
        comp = self.algs.get(key)
        if comp is None:
            prim = cdx_primitive(use)
            ap: Dict[str, Any] = {"primitive": prim, "executionEnvironment": "software-plain-ram"}
            psi = use.key_bits if use.key_bits else None
            if psi is None and use.primitive == Primitive.HASH:
                m = re.search(r"(\d{3})", use.algorithm)
                psi = int(m.group(1)) if m else None
            if psi:
                ap["parameterSetIdentifier"] = str(psi)
            if use.curve:
                ap["curve"] = use.curve
            if use.mode:
                ap["mode"] = use.mode if use.mode in MODES else "other"
            if use.algorithm == "rsa-kex":
                ap["padding"] = "pkcs1v15"
            ap["cryptoFunctions"] = list(FUNCTIONS.get(prim, ["other"]))
            cl = security_strength(use)
            if cl is not None:
                ap["classicalSecurityLevel"] = cl
            nq = nist_quantum_level(use)
            if nq is not None:
                ap["nistQuantumSecurityLevel"] = nq
            ref = self.ref(prim, use.describe(), "alg|" + "|".join(map(str, key)))
            comp = {"type": "cryptographic-asset", "bom-ref": ref, "name": use.describe(),
                    "cryptoProperties": {"assetType": "algorithm", "algorithmProperties": ap},
                    "properties": [{"name": "cryptoscan:primitive", "value": use.primitive.value},
                                   {"name": "cryptoscan:quantum_vulnerable", "value": str(use.algorithm in QUANTUM_VULNERABLE).lower()}]}
            oid = _oid(use)
            if oid:
                comp["cryptoProperties"]["oid"] = oid
            self.algs[key] = comp
            self.alg_locs[ref] = set()
        ref = comp["bom-ref"]
        if location:
            self.alg_locs[ref].add(location)
        return ref

    def add_asset(self, a: Asset) -> str:
        attrs = a.attributes
        uses = [u for u in a.uses]
        arefs: List[str] = []
        for u in uses:
            r = self.algorithm(u, a.location)
            if r and r not in arefs:
                arefs.append(r)
        props = [{"name": "cryptoscan:asset_kind", "value": a.kind.value},
                 {"name": "cryptoscan:asset_id", "value": a.asset_id},
                 {"name": "cryptoscan:collector", "value": a.collector}]
        if a.host:
            props.append({"name": "cryptoscan:host", "value": a.host})
        has_proto = any(u.primitive == Primitive.PROTOCOL for u in uses)
        deps = set(arefs)
        extra_components: List[Dict[str, Any]] = []

        if a.kind in CERT_KINDS:
            cp: Dict[str, Any] = {"certificateFormat": "X.509", "certificateExtension": "pem"}
            cp["subjectName"] = str(attrs.get("subject") or a.name)
            if attrs.get("issuer"):
                cp["issuerName"] = str(attrs["issuer"])
            if attrs.get("not_before"):
                cp["notValidBefore"] = str(attrs["not_before"])
            if attrs.get("not_after"):
                cp["notValidAfter"] = str(attrs["not_after"])
            sig = next((u for u in uses if u.primitive == Primitive.SIGNATURE), None)
            if sig is not None:
                r = self.algorithm(sig, a.location)
                if r:
                    cp["signatureAlgorithmRef"] = r
            pk = next((u for u in uses if u.primitive == Primitive.PUBLIC_KEY), None)
            ref = self.ref("certificate", cp["subjectName"], "cert|" + a.asset_id)
            if pk is not None:
                kref = self.ref("key", f"public-key-{a.name}", "pubkey|" + a.asset_id)
                aref = self.algorithm(pk, a.location)
                rm: Dict[str, Any] = {"type": "public-key"}
                if aref:
                    rm["algorithmRef"] = aref
                if pk.key_bits:
                    rm["size"] = pk.key_bits
                extra_components.append({"type": "cryptographic-asset", "bom-ref": kref, "name": f"Public key of {a.name}",
                                         "cryptoProperties": {"assetType": "related-crypto-material", "relatedCryptoMaterialProperties": rm},
                                         "evidence": {"occurrences": [{"location": a.location}]}})
                self.deps[kref] = {aref} if aref else set()
                cp["subjectPublicKeyRef"] = kref
                deps.add(kref)
            cprops = {"assetType": "certificate", "certificateProperties": cp}
            for k in ("self_signed", "is_ca", "trust_anchor"):
                if k in attrs:
                    props.append({"name": f"cryptoscan:{k}", "value": str(bool(attrs[k])).lower()})
            comp = {"type": "cryptographic-asset", "bom-ref": ref, "name": cp["subjectName"], "cryptoProperties": cprops}
        elif a.kind in PROTO_KINDS or (a.kind not in MATERIAL_TYPE and has_proto):
            protos = [u.algorithm for u in uses if u.primitive == Primitive.PROTOCOL]
            if a.kind == AssetKind.TLS_ENDPOINT or any(p.startswith(("tls", "ssl")) for p in protos):
                ptype = "tls"
            elif a.kind in (AssetKind.SSH_SERVER, AssetKind.SSH_CLIENT, AssetKind.SSH_REMOTE) or any(p.startswith("ssh") for p in protos):
                ptype = "ssh"
            elif a.kind == AssetKind.IPSEC_CONFIG or any(p.startswith("ipsec") for p in protos):
                ptype = "ipsec"
            elif any(p.startswith("ikev") for p in protos):
                ptype = "ike"
            else:
                ptype = "other"
            pp: Dict[str, Any] = {"type": ptype}
            vers = sorted({re.sub(r"^[a-z]+(?=\d)", "", p) for p in protos if re.search(r"\d", p)},
                          key=lambda v: [int(x) if x.isdigit() else 0 for x in re.split(r"[.\-]", v)])
            if vers:
                pp["version"] = vers[-1]
                if len(vers) > 1:
                    props.append({"name": "cryptoscan:offered_versions", "value": ",".join(vers)})
            elif ptype == "ssh":
                pp["version"] = "2.0"
            if "kerberos" in a.kind.value:
                props.append({"name": "cryptoscan:protocol", "value": "kerberos"})
            elif a.kind == AssetKind.SNMP_AGENT:
                props.append({"name": "cryptoscan:protocol", "value": "snmp"})
            suites: Dict[str, Dict[str, Any]] = {}
            for u in uses:
                if u.context == "tls-cipher-suite" and u.raw:
                    s = suites.setdefault(u.raw, {"name": u.raw, "algorithms": [], "identifiers": []})
                    r = self.algorithm(u, "")
                    if r and r not in s["algorithms"]:
                        s["algorithms"].append(r)
                    iana = u.extra.get("iana")
                    if iana and iana not in s["identifiers"]:
                        s["identifiers"].append(iana)
            if suites:
                pp["cipherSuites"] = [{k: v for k, v in s.items() if v} for _, s in sorted(suites.items())]
            ref = self.ref("protocol", a.name, "proto|" + a.asset_id)
            comp = {"type": "cryptographic-asset", "bom-ref": ref, "name": a.name,
                    "cryptoProperties": {"assetType": "protocol", "protocolProperties": pp}}
        else:
            rm = {"type": MATERIAL_TYPE.get(a.kind, "other")}
            pk = next((u for u in uses if u.primitive == Primitive.PUBLIC_KEY), None)
            if pk is not None:
                r = self.algorithm(pk, a.location)
                if r:
                    rm["algorithmRef"] = r
                if pk.key_bits:
                    rm["size"] = pk.key_bits
            if attrs.get("encrypted") is True:
                rm["securedBy"] = {"mechanism": "Software with passphrase"}
            for k in ("mode", "owner", "encrypted", "fmt"):
                if k in attrs and attrs[k] is not None:
                    props.append({"name": f"cryptoscan:{k}", "value": oct(attrs[k]) if (k == "mode" and isinstance(attrs[k], int)) else str(attrs[k])})
            ref = self.ref("material", a.name, "mat|" + a.asset_id)
            comp = {"type": "cryptographic-asset", "bom-ref": ref, "name": a.name,
                    "cryptoProperties": {"assetType": "related-crypto-material", "relatedCryptoMaterialProperties": rm}}
        comp["properties"] = props
        comp["evidence"] = {"occurrences": [{"location": a.location}]}
        self.deps[comp["bom-ref"]] = deps
        self.assets.append(comp)
        self.assets.extend(extra_components)
        return comp["bom-ref"]


def build(result: ScanResult) -> Dict[str, Any]:
    b = _Builder()
    asset_ref: Dict[str, str] = {}
    for a in result.assets:
        asset_ref[a.asset_id] = b.add_asset(a)

    algs = []
    for comp in b.algs.values():
        locs = sorted(b.alg_locs[comp["bom-ref"]])[:10]
        if locs:
            comp["evidence"] = {"occurrences": [{"location": l} for l in locs]}
        algs.append(comp)
    components = sorted(algs, key=lambda c: c["bom-ref"]) + sorted(b.assets, key=lambda c: c["bom-ref"])
    known = {c["bom-ref"] for c in components}

    dependencies = [{"ref": r, "dependsOn": sorted(d & known)} for r, d in sorted(b.deps.items()) if r in known and d & known]

    vulns = []
    seen: Set[str] = set()
    for f in result.findings:
        vref = f"finding/{f.finding_id}"
        if vref in seen:
            vref = f"{vref}-{len(seen)}"
        seen.add(vref)
        props = [{"name": "cryptoscan:quantum_vulnerable", "value": str(bool(f.quantum_vulnerable)).lower()},
                 {"name": "cryptoscan:deprecation_year", "value": "" if f.deprecation_year is None else str(f.deprecation_year)},
                 {"name": "cryptoscan:finding_id", "value": f.finding_id},
                 {"name": "cryptoscan:location", "value": f.location}]
        if f.host:
            props.append({"name": "cryptoscan:host", "value": f.host})
        props += [{"name": "cryptoscan:reference", "value": r} for r in f.references]
        v: Dict[str, Any] = {"bom-ref": vref, "id": f.rule_id, "source": {"name": "cryptoscan"},
                             "ratings": [{"source": {"name": "cryptoscan"}, "severity": f.severity.label, "method": "other"}],
                             "description": f"{f.title}. {f.description}".strip(),
                             "recommendation": f.remediation, "properties": props}
        if f.asset_id in asset_ref:
            v["affects"] = [{"ref": asset_ref[f.asset_id]}]
        vulns.append(v)

    meta = result.meta
    host = meta.hostname or "unknown"
    digest = hashlib.sha256(json.dumps([components, vulns], sort_keys=True).encode()).hexdigest()
    bom: Dict[str, Any] = {
        "bomFormat": "CycloneDX", "specVersion": "1.6",
        "serialNumber": "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "cryptoscan:" + digest)),
        "version": 1,
        "metadata": {
            "tools": {"components": [{"type": "application", "name": "cryptoscan", "version": meta.version or "0"}]},
            "component": {"type": "device", "bom-ref": f"host/{slug(host)}", "name": host},
            "properties": [{"name": "cryptoscan:profile", "value": meta.profile or ""},
                           {"name": "cryptoscan:targets", "value": ",".join(meta.targets)}],
        },
        "components": components,
        "dependencies": dependencies,
        "vulnerabilities": vulns,
    }
    ts = meta.finished or meta.started
    if ts:
        bom["metadata"]["timestamp"] = ts
    return bom


def render(result: ScanResult) -> str:
    return json.dumps(build(result), indent=2, sort_keys=False)
