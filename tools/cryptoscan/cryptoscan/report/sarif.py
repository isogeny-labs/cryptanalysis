"""SARIF 2.1.0 renderer: ``render(result) -> str`` (JSON) for code-scanning dashboards."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from urllib.parse import quote

from ..model import AssetKind, Finding, ScanResult, Severity
from .summary import host_of, sev_sort_key

LEVEL = {Severity.CRITICAL: "error", Severity.HIGH: "error", Severity.MEDIUM: "warning",
         Severity.LOW: "note", Severity.INFO: "note"}
SECURITY_SEVERITY = {Severity.CRITICAL: "9.5", Severity.HIGH: "8.0", Severity.MEDIUM: "5.0", Severity.LOW: "2.0",
                     Severity.INFO: "0.0"}
_HOSTPORT = re.compile(r"^[A-Za-z0-9._\-\[\]:]+:\d{1,5}$")
_SSH_KINDS = (AssetKind.SSH_SERVER, AssetKind.SSH_CLIENT, AssetKind.SSH_REMOTE)


def location_uri(f: Finding, fallback_host: str) -> str:
    loc = (f.location or "").strip()
    if loc.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", loc):
        return "file://" + quote(loc.replace("\\", "/") if not loc.startswith("/") else loc, safe="/:")
    if loc and _HOSTPORT.match(loc) and "/" not in loc:
        scheme = "ssh" if f.asset_kind in _SSH_KINDS else "tls" if f.asset_kind == AssetKind.TLS_ENDPOINT else "tcp"
        return f"{scheme}://{quote(loc, safe=':[]')}"
    return f"cryptoscan://{quote(fallback_host, safe='')}/{quote(loc or f.asset_name, safe='')}"


def render(result: ScanResult) -> str:
    meta = result.meta
    findings = sorted(result.findings, key=sev_sort_key)
    by_rule: Dict[str, List[Finding]] = {}
    for f in findings:
        by_rule.setdefault(f.rule_id, []).append(f)
    rules: List[Dict[str, Any]] = []
    index: Dict[str, int] = {}
    for rid in sorted(by_rule):
        fs = by_rule[rid]
        top = max(fs, key=lambda f: f.severity)
        tags = sorted({"cryptography", "security"} | {t for f in fs for t in f.tags}
                      | ({"quantum-vulnerable"} if any(f.quantum_vulnerable for f in fs) else set()))
        index[rid] = len(rules)
        refs = sorted({r for f in fs for r in f.references})
        rules.append({
            "id": rid, "name": re.sub(r"[^A-Za-z0-9]+", "", rid.title()) or rid,
            "shortDescription": {"text": top.title},
            "fullDescription": {"text": top.description},
            "help": {"text": top.remediation + (("\nReferences: " + "; ".join(refs)) if refs else ""),
                     "markdown": top.remediation + ("\n\nReferences:\n" + "\n".join(f"- {r}" for r in refs) if refs else "")},
            "defaultConfiguration": {"level": LEVEL[top.severity]},
            "properties": {"tags": tags, "security-severity": SECURITY_SEVERITY[top.severity]},
        })
    results = []
    for f in findings:
        host = host_of(result, f.host)
        results.append({
            "ruleId": f.rule_id, "ruleIndex": index[f.rule_id], "level": LEVEL[f.severity],
            "message": {"text": f"{f.title}: {f.description}"},
            "locations": [{
                "physicalLocation": {"artifactLocation": {"uri": location_uri(f, host)}},
                "logicalLocations": [{"name": f.asset_name, "kind": f.asset_kind.value,
                                      "fullyQualifiedName": f"{host}/{f.asset_name}"}],
            }],
            "partialFingerprints": {"cryptoscan/findingId": f.finding_id},
            "properties": {"severity": f.severity.label, "host": host, "quantum_vulnerable": bool(f.quantum_vulnerable),
                           "deprecation_year": f.deprecation_year, "collector": f.collector,
                           "remediation": f.remediation},
        })
    inv: Dict[str, Any] = {"executionSuccessful": True, "commandLine": " ".join(meta.command_line)}
    if meta.started:
        inv["startTimeUtc"] = meta.started
    if meta.finished:
        inv["endTimeUtc"] = meta.finished
    doc = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "cryptoscan", "version": meta.version or "0", "rules": rules}},
                  "invocations": [inv], "results": results,
                  "properties": {"profile": meta.profile, "hostname": meta.hostname}}],
    }
    return json.dumps(doc, indent=2)
