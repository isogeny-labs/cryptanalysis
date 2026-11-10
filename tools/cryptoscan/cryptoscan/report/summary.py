"""Shared aggregation for every report renderer.

``summarize(result)`` turns a :class:`~cryptoscan.model.ScanResult` into one
JSON-friendly dict.  It is a pure function of its input (the reference time for
certificate expiry is ``meta.finished``/``meta.started`` unless ``now`` is
passed), so two calls on the same result are equal and rendering a result that
was round-tripped through JSON gives the same output.

Score formula (``score``): start at 100 and subtract, per severity, ``n * w``
capped at ``cap``::

    critical  25 per finding, capped at 75
    high      10 per finding, capped at 40
    medium     3 per finding, capped at 20
    low        1 per finding, capped at 10
    info       0

The result is floored at 0.  Grade: A >= 90, B >= 80, C >= 70, D >= 60, else F.
The score is a triage aid, not a compliance verdict.
"""

from __future__ import annotations

import datetime as _dt
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from ..model import CryptoUse, Finding, Primitive, ScanResult, Severity
from ..names import security_strength
from ..policy import QUANTUM_SAFE, QUANTUM_VULNERABLE

SEV_ORDER = ["critical", "high", "medium", "low", "info"]
SCORE_WEIGHTS = {"critical": (25, 75), "high": (10, 40), "medium": (3, 20), "low": (1, 10), "info": (0, 0)}
TIMELINE_KEYS = ["2024-and-earlier", "2030", "2033", "2035"]
TIMELINE_LABELS = {
    "2024-and-earlier": "Already disallowed (2024 and earlier)",
    "2030": "Deprecated after 2030",
    "2033": "Deprecated/disallowed 2033",
    "2035": "Disallowed after 2035",
}
CERT_BUCKETS = ["expired", "<30d", "<90d", "<365d", "later"]
PUBKEY_PRIMS = (Primitive.PUBLIC_KEY, Primitive.SIGNATURE, Primitive.KEY_EXCHANGE)
SYM_PRIMS = (Primitive.CIPHER, Primitive.MAC, Primitive.HASH, Primitive.ENCTYPE)
RSA_FAMILY = {"rsa", "rsa-pss", "rsa-kex"}
EC_FAMILY = {"ec", "ecdsa", "ecdh", "ecdhe", "ecdh-static", "ecdsa-sk"}
_DISALLOWED_ALGS = {"dsa", "3des", "des", "des40", "rc4", "ssh1", "ssh1.99", "sslv2", "sslv3", "tls1.0",
                    "tls1.1", "md5", "md2", "md4", "sha1"}


def quantum_status(use: CryptoUse) -> str:
    """'vulnerable', 'safe', 'symmetric/hash' (Grover note applies) or 'n/a'."""
    if use.algorithm in QUANTUM_VULNERABLE:
        return "vulnerable"
    if use.algorithm in QUANTUM_SAFE:
        return "safe"
    if use.primitive in SYM_PRIMS:
        return "symmetric/hash"
    return "n/a"


def parse_time(s: Any) -> Optional[_dt.datetime]:
    if not s:
        return None
    try:
        t = _dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=_dt.timezone.utc)
    return t


def reference_time(result: ScanResult, now: Optional[_dt.datetime] = None) -> _dt.datetime:
    return parse_time(result.meta.finished) or parse_time(result.meta.started) or now or _dt.datetime.now(_dt.timezone.utc)


def grade_for(score: int) -> str:
    for lim, g in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if score >= lim:
            return g
    return "F"


def compute_score(counts: Dict[str, int]) -> int:
    s = 100
    for sev, (w, cap) in SCORE_WEIGHTS.items():
        s -= min(counts.get(sev, 0) * w, cap)
    return max(0, s)


def already_disallowed(f: Finding) -> bool:
    """HIGH+ finding on an algorithm that standards already disallow."""
    if f.severity < Severity.HIGH or f.use is None:
        return False
    u = f.use
    if u.algorithm in RSA_FAMILY and u.key_bits is not None and u.key_bits < 2048:
        return True
    return u.algorithm in _DISALLOWED_ALGS or u.hash_algorithm in ("sha1", "md5")


def sev_sort_key(f: Finding) -> Tuple:
    return (-int(f.severity), f.rule_id, f.asset_name, f.location, f.finding_id)


def host_of(result: ScanResult, host: Optional[str]) -> str:
    return host or result.meta.hostname or "(unknown)"


def asset_worst(result: ScanResult) -> Dict[str, Severity]:
    w: Dict[str, Severity] = {}
    for f in result.findings:
        if f.asset_id not in w or f.severity > w[f.asset_id]:
            w[f.asset_id] = f.severity
    return w


def _num_key(k: str):
    try:
        return (0, int(k), "")
    except ValueError:
        return (1, 0, k)


def cert_rows(result: ScanResult, now: Optional[_dt.datetime] = None) -> List[Dict[str, Any]]:
    """Certificate-bearing assets (attributes.not_after) sorted by expiry."""
    ref = reference_time(result, now)
    rows = []
    for a in result.assets:
        at = a.attributes
        na = parse_time(at.get("not_after"))
        if na is None:
            continue
        days = int((na - ref).total_seconds() // 86400)
        if na < ref:
            bucket = "expired"
        elif days < 30:
            bucket = "<30d"
        elif days < 90:
            bucket = "<90d"
        elif days < 365:
            bucket = "<365d"
        else:
            bucket = "later"
        key = at.get("public_key_algorithm") or ""
        if at.get("key_bits"):
            key += f" {at['key_bits']}"
        if at.get("curve"):
            key += f" {at['curve']}"
        sig = at.get("signature_algorithm") or ""
        if at.get("signature_hash"):
            sig += f" with {at['signature_hash']}"
        rows.append({"asset_id": a.asset_id, "asset": a.name, "host": a.host or "", "subject": str(at.get("subject") or ""),
                     "issuer": str(at.get("issuer") or ""), "key": key.strip(), "signature": sig.strip(),
                     "not_after": str(at.get("not_after")), "days_left": days, "bucket": bucket,
                     "sans": [str(s) for s in (at.get("sans") or [])]})
    rows.sort(key=lambda r: (parse_time(r["not_after"]), r["asset"], r["asset_id"]))
    return rows


def summarize(result: ScanResult, now: Optional[_dt.datetime] = None) -> Dict[str, Any]:
    meta = result.meta
    findings = result.findings
    counts = result.severity_counts()
    worst = result.worst().label if findings else "none"
    score = compute_score(counts)
    asset_by_id = {a.asset_id: a for a in result.assets}

    # ---- simple counters ------------------------------------------------
    by_collector = Counter(f.collector for f in findings)
    assets_by_collector = Counter(a.collector for a in result.assets)
    by_kind = Counter(a.kind.value for a in result.assets)
    findings_by_kind = Counter(f.asset_kind.value for f in findings)

    # ---- rules ------------------------------------------------------------
    per_rule: Dict[str, List[Finding]] = defaultdict(list)
    for f in findings:
        per_rule[f.rule_id].append(f)
    top_rules = []
    for rid, fs in per_rule.items():
        titles = Counter(f.title for f in fs)
        rems = Counter(f.remediation for f in fs)
        top_rules.append({
            "rule_id": rid,
            "title": sorted(titles.items(), key=lambda kv: (-kv[1], kv[0]))[0][0],
            "count": len(fs),
            "severity": max(f.severity for f in fs).label,
            "assets": len({f.asset_id for f in fs}),
            "remediation": sorted(rems.items(), key=lambda kv: (-kv[1], kv[0]))[0][0],
        })
    top_rules.sort(key=lambda r: (-SEV_ORDER[::-1].index(r["severity"]), -r["count"], r["rule_id"]))

    # ---- hosts ------------------------------------------------------------
    hosts: Dict[str, Dict[str, Any]] = {}

    def _h(name: str) -> Dict[str, Any]:
        return hosts.setdefault(name, {"host": name, "worst": "none", "counts": {s: 0 for s in SEV_ORDER},
                                       "assets": 0, "findings": 0})
    for a in result.assets:
        _h(host_of(result, a.host))["assets"] += 1
    for f in findings:
        h = _h(host_of(result, f.host))
        h["counts"][f.severity.label] += 1
        h["findings"] += 1
    for h in hosts.values():
        for s in SEV_ORDER:
            if h["counts"][s]:
                h["worst"] = s
                break
    host_list = sorted(hosts.values(), key=lambda h: (SEV_ORDER.index(h["worst"]) if h["worst"] in SEV_ORDER else 9, h["host"]))
    by_host = {h["host"]: h["findings"] for h in host_list}

    # ---- algorithm inventory ----------------------------------------------
    inv: Dict[Tuple[str, str], Dict[str, Any]] = {}
    inv_assets: Dict[Tuple[str, str], set] = defaultdict(set)
    for a in result.assets:
        for u in a.uses:
            k = (u.primitive.value, u.describe())
            e = inv.get(k)
            if e is None:
                q = quantum_status(u)
                e = inv[k] = {"primitive": k[0], "algorithm": k[1], "count": 0, "assets": 0,
                              "strength": security_strength(u), "quantum": q,
                              "quantum_note": ("Grover's algorithm halves effective symmetric/hash strength; "
                                               "AES-256 / SHA-384+ keep a comfortable margin.") if q == "symmetric/hash" else ""}
            e["count"] += 1
            inv_assets[k].add(a.asset_id)
    for k, e in inv.items():
        e["assets"] = len(inv_assets[k])
    inventory = sorted(inv.values(), key=lambda e: (-e["count"], e["primitive"], e["algorithm"]))

    # ---- PQC readiness ------------------------------------------------------
    worst_by_asset = asset_worst(result)
    vuln_ids, hybrid_ids = [], []
    for a in result.assets:
        qv = [u for u in a.uses if u.primitive in PUBKEY_PRIMS and u.algorithm in QUANTUM_VULNERABLE and not u.extra.get("negated")]
        if not qv:
            continue
        vuln_ids.append(a.asset_id)
        if any(u.algorithm in QUANTUM_SAFE for u in a.uses):
            hybrid_ids.append(a.asset_id)
    vuln_ids_sorted = sorted(vuln_ids, key=lambda i: (-int(worst_by_asset.get(i, Severity.INFO)), asset_by_id[i].name, i))
    n_assets = len(result.assets)
    pqc = {
        "total_assets": n_assets,
        "vulnerable_assets": len(vuln_ids),
        "hybrid_assets": len(hybrid_ids),
        "vulnerable_only_assets": len(vuln_ids) - len(hybrid_ids),
        "no_public_key_assets": n_assets - len(vuln_ids),
        "pq_ready_pct": round(100.0 * len(hybrid_ids) / len(vuln_ids), 1) if vuln_ids else 0.0,
        "exposure_pct": round(100.0 * (len(vuln_ids) - len(hybrid_ids)) / n_assets, 1) if n_assets else 0.0,
        "asset_names": [asset_by_id[i].name for i in vuln_ids_sorted],
    }

    # ---- deprecation timeline -------------------------------------------------
    tl_f = {k: 0 for k in TIMELINE_KEYS}
    tl_a: Dict[str, set] = {k: set() for k in TIMELINE_KEYS}
    for f in findings:
        if already_disallowed(f) or (f.deprecation_year is not None and f.deprecation_year <= 2024):
            k = "2024-and-earlier"
        elif f.deprecation_year is not None and str(f.deprecation_year) in tl_f:
            k = str(f.deprecation_year)
        else:
            continue
        tl_f[k] += 1
        tl_a[k].add(f.asset_id)
    timeline = {k: {"label": TIMELINE_LABELS[k], "findings": tl_f[k], "assets": len(tl_a[k])} for k in TIMELINE_KEYS}

    # ---- certificates -------------------------------------------------------------
    certs = cert_rows(result, now)
    cert_counts = {b: 0 for b in CERT_BUCKETS}
    for c in certs:
        cert_counts[c["bucket"]] += 1

    # ---- key sizes ----------------------------------------------------------------
    rsa_h: Counter = Counter()
    ec_h: Counter = Counter()
    for a in result.assets:
        for u in a.uses:
            if u.primitive not in PUBKEY_PRIMS:
                continue
            if u.algorithm in RSA_FAMILY and u.key_bits:
                rsa_h[str(u.key_bits)] += 1
            elif u.algorithm in EC_FAMILY or (u.curve and u.algorithm in ("ec", "ecdsa")):
                ec_h[str(u.curve or u.key_bits or "unknown")] += 1
    key_sizes = {"rsa": {k: rsa_h[k] for k in sorted(rsa_h, key=_num_key)},
                 "ec": {k: ec_h[k] for k in sorted(ec_h, key=_num_key)}}

    # ---- collector coverage ---------------------------------------------------------
    coverage = []
    for c in meta.collectors_run:
        coverage.append({"collector": c, "status": "run", "reason": "", "assets": assets_by_collector.get(c, 0),
                         "findings": by_collector.get(c, 0)})
    for c in sorted(meta.collectors_skipped):
        coverage.append({"collector": c, "status": "skipped", "reason": str(meta.collectors_skipped[c]),
                         "assets": assets_by_collector.get(c, 0), "findings": by_collector.get(c, 0)})

    return {
        "tool": meta.tool, "version": meta.version, "profile": meta.profile, "hostname": meta.hostname,
        "started": meta.started, "finished": meta.finished, "targets": list(meta.targets),
        "command_line": list(meta.command_line),
        "total_findings": len(findings), "total_assets": n_assets,
        "severity_counts": counts, "worst": worst,
        "by_collector": dict(sorted(by_collector.items())),
        "assets_by_collector": dict(sorted(assets_by_collector.items())),
        "by_asset_kind": dict(sorted(by_kind.items())),
        "findings_by_asset_kind": dict(sorted(findings_by_kind.items())),
        "by_host": by_host, "hosts": host_list,
        "top_rules": top_rules, "inventory": inventory, "pqc": pqc, "timeline": timeline,
        "cert_expiry": cert_counts, "certificates": certs, "key_sizes": key_sizes,
        "coverage": coverage, "score": score, "grade": grade_for(score),
    }
