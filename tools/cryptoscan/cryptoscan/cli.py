"""Command-line interface.

    cryptoscan scan   [--profile nist|cnsa2|bsi|legacy] [--target SPEC ...] [--inventory FILE]
                      [--netdev-config PATH ...] [--path DIR ...] [--root /mnt/image]
                      [--only C,..] [--skip C,..] [--no-network] [--snmp-probe] [--deep]
                      [--out DIR] [--format json,html,md,cbom,csv,sarif] [--fail-on SEVERITY]
    cryptoscan report RESULT.json [--format ...] [--out DIR] [--profile P]   # re-render / re-grade
    cryptoscan merge  a.json b.json ... --out DIR                              # fleet roll-up
    cryptoscan rules  [--profile P]                                            # list rule ids
    cryptoscan collectors                                                      # list collectors
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import os
import sys
from typing import List, Optional

from . import __version__, collectors
from .collectors.base import ScanContext, Target
from .inventory import apply_inventory, load_inventory
from .model import ScanResult, Severity, merge_results
from .policy import PROFILES
from .scanner import regrade, run_scan

FORMATS = ("json", "html", "md", "cbom", "csv", "sarif")


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="cryptoscan", description="Inventory and audit cryptography across an environment (read-only).")
    p.add_argument("--version", action="version", version=f"cryptoscan {__version__}")
    p.add_argument("-v", "--verbose", action="count", default=0)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="collect, grade and report")
    s.add_argument("--profile", choices=sorted(PROFILES), default="nist")
    s.add_argument("--target", "-t", action="append", default=[], metavar="SPEC",
                   help="[label=][service://]host[:port]; service in ssh,https,tls,smtp,imap,pop3,ldap,ftp,postgres,snmp,netdev,auto")
    s.add_argument("--inventory", "-i", metavar="FILE", help="JSON inventory of targets/configs (see cryptoscan.inventory)")
    s.add_argument("--netdev-config", action="append", default=[], metavar="PATH", help="saved network-device config file or directory")
    s.add_argument("--path", action="append", default=[], metavar="DIR", help="extra directory to scan for certificates/keys/configs")
    s.add_argument("--root", default="/", help="filesystem root to inspect (offline image / chroot)")
    s.add_argument("--hostname", help="override the host label for local assets")
    s.add_argument("--only", help="comma-separated collectors to run")
    s.add_argument("--skip", help="comma-separated collectors to skip")
    s.add_argument("--no-network", action="store_true", help="disable all active probes")
    s.add_argument("--snmp-probe", action="store_true", help="allow SNMP v1/v2c community probing of targets (requires authorization)")
    s.add_argument("--snmp-community", action="append", default=[], help="community to try with --snmp-probe (default: public)")
    s.add_argument("--deep", action="store_true", help="walk the whole filesystem for key material (slow)")
    s.add_argument("--timeout", type=float, default=8.0, help="network timeout per connection (s)")
    s.add_argument("--workers", type=int, default=16)
    s.add_argument("--opt", action="append", default=[], metavar="KEY=VALUE", help="collector option")
    _add_output_args(s)
    s.add_argument("--fail-on", choices=[x.label for x in Severity], help="exit 2 if any finding is at or above this severity")
    s.add_argument("--now", help="override the evaluation time (ISO-8601), for reproducible reports")

    r = sub.add_parser("report", help="re-render (and optionally re-grade) a saved JSON result")
    r.add_argument("result")
    r.add_argument("--profile", choices=sorted(PROFILES))
    r.add_argument("--now")
    _add_output_args(r)

    m = sub.add_parser("merge", help="merge several JSON results into one fleet report")
    m.add_argument("results", nargs="+")
    m.add_argument("--profile", choices=sorted(PROFILES), help="re-grade the merged inventory")
    _add_output_args(m)

    ru = sub.add_parser("rules", help="list policy rule ids and profiles")
    ru.add_argument("--profile", choices=sorted(PROFILES), default="nist")
    ru.add_argument("--json", action="store_true")

    sub.add_parser("collectors", help="list collectors")
    return p.parse_args(argv)


def _add_output_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--out", "-o", default="cryptoscan-report", help="output directory (default ./cryptoscan-report)")
    sp.add_argument("--format", "-f", default="json,html,md", help=f"comma list of {','.join(FORMATS)} or 'all'")
    sp.add_argument("--stdout", action="store_true", help="write the first format to stdout instead of files")
    sp.add_argument("--basename", default="cryptoscan", help="file stem inside --out")


def _formats(spec: str) -> List[str]:
    if spec == "all":
        return list(FORMATS)
    out = []
    for f in spec.split(","):
        f = f.strip().lower()
        if f == "markdown":
            f = "md"
        if f not in FORMATS:
            raise SystemExit(f"unknown format {f!r}; choose from {', '.join(FORMATS)}")
        out.append(f)
    return out


def _write_reports(result: ScanResult, args: argparse.Namespace) -> List[str]:
    from . import report
    fmts = _formats(args.format)
    if args.stdout:
        sys.stdout.write(report.render(result, fmts[0]))
        if not sys.stdout.isatty():
            pass
        return []
    os.makedirs(args.out, exist_ok=True)
    written = []
    ext = {"json": "json", "html": "html", "md": "md", "cbom": "cbom.json", "csv": "findings.csv", "sarif": "sarif"}
    for f in fmts:
        path = os.path.join(args.out, f"{args.basename}.{ext[f]}")
        text = report.render(result, f)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        written.append(path)
        if f == "csv":
            path2 = os.path.join(args.out, f"{args.basename}.uses.csv")
            with open(path2, "w", encoding="utf-8") as fh:
                fh.write(report.render(result, "csv", which="uses"))
            written.append(path2)
    return written


def _parse_now(s: Optional[str]) -> Optional[_dt.datetime]:
    if not s:
        return None
    d = _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=_dt.timezone.utc)


def _print_summary(result: ScanResult) -> None:
    c = result.severity_counts()
    print(f"cryptoscan {__version__}: {len(result.assets)} assets, {len(result.findings)} findings "
          f"[critical {c['critical']}, high {c['high']}, medium {c['medium']}, low {c['low']}, info {c['info']}] "
          f"profile={result.meta.profile} collectors={','.join(result.meta.collectors_run)}", file=sys.stderr)
    skipped = {k: v for k, v in result.meta.collectors_skipped.items() if not k.startswith("_")}
    if skipped:
        print("skipped: " + "; ".join(f"{k} ({v})" for k, v in skipped.items()), file=sys.stderr)
    top = {}
    for f in result.findings:
        if f.severity >= Severity.MEDIUM:
            top.setdefault((f.severity, f.rule_id, f.title), 0)
            top[(f.severity, f.rule_id, f.title)] += 1
    for (sev, rid, title), n in sorted(top.items(), key=lambda kv: (-int(kv[0][0]), -kv[1]))[:15]:
        print(f"  {sev.label.upper():8} {rid:28} x{n:<4} {title}", file=sys.stderr)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(level=logging.WARNING - 10 * min(args.verbose, 2), format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr)
    log = logging.getLogger("cryptoscan")

    if args.cmd == "collectors":
        for name, cls in collectors.all_collectors().items():
            print(f"{name:16} {'net ' if cls.needs_network else '    '} {cls.description}")
        return 0

    if args.cmd == "rules":
        from . import rules_doc
        rows = rules_doc.list_rules()
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            print("profiles: " + "; ".join(f"{k}: {v.description}" for k, v in PROFILES.items()))
            for r in rows:
                print(f"{r['rule_id']:28} {r['max_severity']:8} {r['title']}")
        return 0

    if args.cmd == "report":
        with open(args.result, "r", encoding="utf-8") as fh:
            result = ScanResult.from_dict(json.load(fh))
        if args.profile:
            regrade(result, args.profile, now=_parse_now(args.now))
        written = _write_reports(result, args)
        for w in written:
            print(w, file=sys.stderr)
        return 0

    if args.cmd == "merge":
        results = []
        for path in args.results:
            with open(path, "r", encoding="utf-8") as fh:
                results.append(ScanResult.from_dict(json.load(fh)))
        merged = merge_results(results)
        merged.meta.hostname = f"fleet({len(results)} hosts)"
        if args.profile:
            regrade(merged, args.profile)
        written = _write_reports(merged, args)
        _print_summary(merged)
        for w in written:
            print(w, file=sys.stderr)
        return 0

    # ---- scan ------------------------------------------------------------
    ctx = ScanContext(root=args.root, timeout=args.timeout, active_probes=not args.no_network,
                      snmp_probe=args.snmp_probe, deep_fs_scan=args.deep, log=log)
    if args.hostname:
        ctx.hostname = args.hostname
    ctx.options["workers"] = args.workers
    ctx.options["debug"] = args.verbose >= 2
    if args.snmp_community:
        ctx.options["snmp_communities"] = args.snmp_community
    for kv in args.opt:
        k, _, v = kv.partition("=")
        ctx.options[k] = v if v not in ("true", "false") else (v == "true")
    profile = args.profile
    if args.inventory:
        inv_profile = apply_inventory(ctx, load_inventory(args.inventory))
        if inv_profile and args.profile == "nist":
            profile = inv_profile
    for spec in args.target:
        ctx.targets.append(Target.parse(spec))
    ctx.netdev_configs.extend(args.netdev_config)
    ctx.extra_paths.extend(args.path)
    only = [c.strip() for c in args.only.split(",")] if args.only else None
    skip = [c.strip() for c in args.skip.split(",")] if args.skip else None
    result = run_scan(ctx, profile=profile, only=only, skip=skip, now=_parse_now(args.now), command_line=sys.argv)
    written = _write_reports(result, args)
    _print_summary(result)
    for w in written:
        print(w, file=sys.stderr)
    if args.fail_on:
        threshold = Severity[args.fail_on.upper()]
        if any(f.severity >= threshold for f in result.findings):
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
