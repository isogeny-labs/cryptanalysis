"""Markdown report renderer: ``render(result, max_findings=500) -> str``."""

from __future__ import annotations

from typing import Any, Iterable, List

from ..model import ScanResult
from ..policy import PROFILES, REF
from .summary import SEV_ORDER, TIMELINE_KEYS, sev_sort_key, summarize


def cell(x: Any, limit: int = 0) -> str:
    """Make a value safe for a Markdown table cell."""
    s = "" if x is None else str(x)
    s = " ".join(s.split())
    if limit and len(s) > limit:
        s = s[: limit - 3] + "..."
    return s.replace("\\", "\\\\").replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")


def _table(headers: List[str], rows: Iterable[Iterable[Any]]) -> List[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(cell(c) if not isinstance(c, _Raw) else str(c) for c in r) + " |")
    return out


class _Raw(str):
    pass


def render(result: ScanResult, max_findings: int = 500) -> str:
    s = summarize(result)
    meta = result.meta
    date = (meta.finished or meta.started or "")[:10] or "undated"
    host = meta.hostname or "unknown host"
    L: List[str] = []
    L.append(f"# Cryptographic Posture Report: {cell(host)} ({cell(meta.profile or 'nist')} profile, {date})")
    L.append("")

    # ---- executive summary ----
    sc = s["severity_counts"]
    pq = s["pqc"]
    if s["total_findings"]:
        tops = ", ".join(f"{r['title']} ({r['count']})" for r in s["top_rules"][:3])
        sev_txt = ", ".join(f"{sc[k]} {k}" for k in SEV_ORDER if sc[k])
        para = (f"cryptoscan inspected {s['total_assets']} cryptographic assets on {host} against the "
                f"`{meta.profile}` profile and raised {s['total_findings']} findings ({sev_txt}). The worst severity is "
                f"**{s['worst'].upper()}**. The most frequent issues are: {tops}. ")
    else:
        para = (f"cryptoscan inspected {s['total_assets']} cryptographic assets on {host} against the "
                f"`{meta.profile}` profile and raised no findings. ")
    if pq["vulnerable_assets"]:
        para += (f"{pq['vulnerable_assets']} of {pq['total_assets']} assets "
                 f"({100.0 * pq['vulnerable_assets'] / max(pq['total_assets'], 1):.1f}%) depend on quantum-vulnerable public-key "
                 f"cryptography; {pq['hybrid_assets']} of them also offer a post-quantum hybrid, leaving "
                 f"{pq['exposure_pct']:.1f}% of all assets exposed to harvest-now-decrypt-later. ")
    else:
        para += "No asset depends on quantum-vulnerable public-key cryptography. "
    para += f"Triage score: **{s['score']}/100 (grade {s['grade']})**."
    L += ["## Executive summary", "", para, ""]

    # ---- scope ----
    L += ["## Scope and coverage", ""]
    L.append(f"- Targets: {cell(', '.join(meta.targets) or 'local host')}")
    L.append(f"- Started: {cell(meta.started or 'n/a')}; finished: {cell(meta.finished or 'n/a')}")
    L.append(f"- Tool: {cell(meta.tool)} {cell(meta.version)}")
    L.append("")
    L += _table(["Collector", "Status", "Reason", "Assets", "Findings"],
                [(c["collector"], c["status"], c["reason"], c["assets"], c["findings"]) for c in s["coverage"]]) \
        if s["coverage"] else ["_No collector information recorded._"]
    L.append("")

    # ---- by severity ----
    L += ["## Findings by severity", ""]
    L += _table(["Severity", "Count"], [(k.upper(), sc[k]) for k in SEV_ORDER])
    L.append("")

    # ---- top issues ----
    L += ["## Top issues", ""]
    if s["top_rules"]:
        L += _table(["Rule", "Title", "Severity", "Count", "Affected assets", "Remediation"],
                    [(r["rule_id"], r["title"], r["severity"].upper(), r["count"], r["assets"], r["remediation"][:200])
                     for r in s["top_rules"][:25]])
        if len(s["top_rules"]) > 25:
            L += ["", f"... {len(s['top_rules']) - 25} more rules (see the findings below)."]
    else:
        L.append("_No findings._")
    L.append("")

    # ---- findings ----
    L += ["## Findings", ""]
    fs = sorted(result.findings, key=sev_sort_key)
    shown = fs[:max_findings] if max_findings is not None and max_findings >= 0 else fs
    cur = None
    for f in shown:
        if f.severity.label != cur:
            cur = f.severity.label
            if L[-1] != "":
                L.append("")
            L += [f"### {cur.upper()}", ""]
            L += ["| Rule | Asset | Host | Location | Detail | Remediation | References |", "|---|---|---|---|---|---|---|"]
        L.append("| " + " | ".join([cell(f.rule_id), cell(f.asset_name, 80), cell(f.host or ""), cell(f.location, 80),
                                    cell(f.description, 300), cell(f.remediation, 300),
                                    cell("; ".join(f.references), 200)]) + " |")
    if len(fs) > len(shown):
        L += ["", f"... {len(fs) - len(shown)} more findings not shown (raise `max_findings` or use the JSON/CSV output)."]
    if not fs:
        L.append("_No findings._")
    L.append("")

    # ---- inventory ----
    L += ["## Cryptographic inventory", ""]
    if s["inventory"]:
        L += _table(["Algorithm", "Primitive", "Strength (bits)", "Quantum status", "#Assets", "#Uses"],
                    [(e["algorithm"], e["primitive"], "" if e["strength"] is None else e["strength"],
                      e["quantum"], e["assets"], e["count"]) for e in s["inventory"]])
        L += ["", "_Symmetric/hash entries lose at most half their strength to Grover's algorithm (AES-128 ~ 64-bit quantum cost); "
                  "public-key entries marked vulnerable are broken outright by Shor's algorithm._"]
    else:
        L.append("_No algorithms recorded._")
    ks = s["key_sizes"]
    if ks["rsa"] or ks["ec"]:
        L += ["", "Key sizes: " + "; ".join(
            f"{fam.upper()}: " + ", ".join(f"{k} x{v}" for k, v in h.items()) for fam, h in ks.items() if h)]
    L.append("")

    # ---- PQC ----
    L += ["## Post-quantum readiness", ""]
    L.append(f"{pq['vulnerable_assets']} of {pq['total_assets']} assets use quantum-vulnerable public-key algorithms "
             f"(RSA, DSA, DH, ECDSA, ECDH, Ed25519 ...); {pq['hybrid_assets']} also offer a post-quantum or hybrid option "
             f"({pq['pq_ready_pct']:.1f}% of the vulnerable assets); {pq['vulnerable_only_assets']} offer no quantum-safe option.")
    L += ["", "**Why it matters (harvest now, decrypt later).** An adversary can record encrypted traffic today and store it "
              "until a cryptographically relevant quantum computer exists; Shor's algorithm would then recover the RSA/ECDH/DH "
              "keys that protected the session and expose the recorded plaintext. Data with a long confidentiality lifetime is "
              "therefore at risk now, which is why key establishment is migrated to ML-KEM hybrids first and signatures after.", ""]
    L += _table(["Timeline bucket", "Findings", "Assets"],
                [(v["label"], v["findings"], v["assets"]) for v in (s["timeline"][k] for k in TIMELINE_KEYS)])
    if pq["asset_names"]:
        names = pq["asset_names"]
        L += ["", "Exposed assets (worst first): " + "; ".join(cell(n, 60) for n in names[:20])
              + (f"; ... {len(names) - 20} more" if len(names) > 20 else "")]
    L.append("")

    # ---- certificates ----
    L += ["## Certificates", ""]
    if s["certificates"]:
        rows = []
        for c in s["certificates"]:
            sans = ", ".join(c["sans"][:5]) + (f" (+{len(c['sans']) - 5})" if len(c["sans"]) > 5 else "")
            rows.append((c["subject"] or c["asset"], c["issuer"], c["key"], c["signature"], c["not_after"], c["days_left"], sans))
        L += _table(["Subject", "Issuer", "Key", "Signature", "notAfter", "Days left", "SANs"], rows)
        ce = s["cert_expiry"]
        L += ["", "Expiry: " + ", ".join(f"{k}: {v}" for k, v in ce.items())]
    else:
        L.append("_No certificates with validity data._")
    L.append("")

    # ---- hosts ----
    L += ["## Hosts", ""]
    L += _table(["Host", "Worst", "Critical", "High", "Medium", "Low", "Info", "Assets"],
                [(h["host"], h["worst"].upper(), *[h["counts"][k] for k in SEV_ORDER], h["assets"]) for h in s["hosts"]]) \
        if s["hosts"] else ["_No hosts._"]
    L.append("")

    # ---- methodology ----
    prof = PROFILES.get(meta.profile)
    L += ["## Methodology", ""]
    L.append(f"Profile `{cell(meta.profile)}`: {cell(prof.description if prof else 'custom profile')}.")
    L += ["", "Severity definitions:", "",
          "- **CRITICAL**: broken or trivially attackable now (sub-80-bit keys, anonymous key exchange, broken ciphers).",
          "- **HIGH**: formally disallowed or practically weak (RSA < 2048, SHA-1 signatures, expired certificates, SSLv3/TLS 1.0).",
          "- **MEDIUM**: below the selected profile or deprecated, fix in the next maintenance window.",
          "- **LOW**: sunset or hygiene items, plan the migration (e.g. quantum-vulnerable algorithms due after 2030).",
          "- **INFO**: informational, inventory or PQC-transition notes.", "",
          "Rule references:", ""]
    refs = set()
    for f in result.findings:
        refs.update(f.references)
    if prof:
        refs.update(prof.references)
    known = set(REF.values())
    for r in sorted(refs):
        L.append(f"- {cell(r)}" + ("" if r in known else ""))
    if not refs:
        L.append("- (none)")
    L += ["", "**Limits.** This is a configuration and inventory review, not a penetration test. Remote probes record what a "
              "server *offers* in a handshake, not what real clients would negotiate with it; local checks read files and "
              "settings and do not prove they are in effect. Findings are graded by a fixed policy and should be validated "
              "before remediation.", ""]
    return "\n".join(L).rstrip() + "\n"
