"""CSV renderers: ``render(result, which="findings"|"uses", safe=True) -> str``.

``findings``: one row per Finding.  ``uses``: one row per CryptoUse of every
asset.  With ``safe=True`` (default) text cells that start with ``= + - @`` get a
leading apostrophe so spreadsheets never evaluate attacker-controlled strings
(banners, certificate subjects) as formulas.
"""

from __future__ import annotations

import csv
import io
from typing import Any, List

from ..model import ScanResult
from ..names import security_strength
from .summary import asset_worst, host_of, quantum_status, sev_sort_key

FINDING_COLUMNS = ["severity", "rule_id", "title", "host", "asset_kind", "asset_name", "location", "algorithm",
                   "key_bits", "curve", "hash", "raw", "context", "quantum_vulnerable", "deprecation_year",
                   "remediation", "references"]
USE_COLUMNS = ["host", "asset_id", "asset_kind", "asset_name", "location", "collector", "primitive", "algorithm",
               "description", "key_bits", "curve", "hash", "mode", "raw", "context", "negotiated",
               "security_strength", "quantum_status", "worst_finding"]


def _c(x: Any, safe: bool) -> Any:
    if x is None:
        return ""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, str):
        x = " ".join(x.split()) if ("\n" in x or "\r" in x) else x
        if safe and x[:1] in ("=", "+", "-", "@", "\t"):
            return "'" + x
    return x


def render(result: ScanResult, which: str = "findings", safe: bool = True) -> str:
    if which not in ("findings", "uses"):
        raise ValueError(f"which must be 'findings' or 'uses', not {which!r}")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    rows: List[List[Any]] = []
    if which == "findings":
        w.writerow(FINDING_COLUMNS)
        for f in sorted(result.findings, key=sev_sort_key):
            u = f.use
            rows.append([f.severity.label, f.rule_id, f.title, host_of(result, f.host), f.asset_kind.value, f.asset_name,
                         f.location, u.algorithm if u else "", u.key_bits if u else "", u.curve if u else "",
                         u.hash_algorithm if u else "", u.raw if u else "", u.context if u else "",
                         f.quantum_vulnerable, f.deprecation_year, f.remediation, "; ".join(f.references)])
    else:
        w.writerow(USE_COLUMNS)
        worst = asset_worst(result)
        for a in result.assets:
            wf = worst.get(a.asset_id)
            for u in a.uses:
                rows.append([host_of(result, a.host), a.asset_id, a.kind.value, a.name, a.location, a.collector,
                             u.primitive.value, u.algorithm, u.describe(), u.key_bits, u.curve, u.hash_algorithm, u.mode,
                             u.raw, u.context, u.negotiated, security_strength(u), quantum_status(u),
                             wf.label if wf is not None else ""])
    for r in rows:
        w.writerow([_c(x, safe) for x in r])
    return buf.getvalue()
