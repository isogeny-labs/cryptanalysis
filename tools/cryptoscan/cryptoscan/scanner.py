"""Scan orchestration: build a ScanContext, run collectors, grade, return a ScanResult."""

from __future__ import annotations

import datetime as _dt
import sys
from typing import Iterable, List, Optional

from . import __version__, collectors
from .collectors.base import ScanContext
from .model import Asset, ScanMeta, ScanResult, utcnow_iso
from .policy import PROFILES, evaluate


def run_scan(ctx: ScanContext, profile: str = "nist", only: Optional[Iterable[str]] = None,
             skip: Optional[Iterable[str]] = None, now: Optional[_dt.datetime] = None,
             command_line: Optional[List[str]] = None) -> ScanResult:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; choose from {', '.join(PROFILES)}")
    only_set = set(only) if only else None
    skip_set = set(skip or ())
    meta = ScanMeta(version=__version__, started=utcnow_iso(), hostname=ctx.hostname, profile=profile,
                    targets=[str(t) for t in ctx.targets], command_line=command_line or sys.argv)
    assets: List[Asset] = []
    registry = collectors.all_collectors()
    for name, cls in registry.items():
        if only_set is not None and name not in only_set:
            meta.collectors_skipped[name] = "not selected"
            continue
        if name in skip_set:
            meta.collectors_skipped[name] = "skipped by request"
            continue
        coll = cls()
        if not coll.default_enabled and (only_set is None or name not in only_set):
            meta.collectors_skipped[name] = "disabled by default (select it with --only)"
            continue
        ok, reason = coll.applicable(ctx)
        if not ok:
            meta.collectors_skipped[name] = reason or "not applicable"
            continue
        ctx.log.info("collector %s: starting", name)
        t0 = _dt.datetime.now()
        found = coll.safe_collect(ctx)
        dt = (_dt.datetime.now() - t0).total_seconds()
        ctx.log.info("collector %s: %d assets in %.1fs", name, len(found), dt)
        assets.extend(found)
        meta.collectors_run.append(name)
    if only_set:
        for name in only_set - set(registry):
            meta.collectors_skipped[name] = "unknown collector"
    findings = evaluate(assets, profile, now=now)
    meta.finished = utcnow_iso()
    result = ScanResult(meta=meta, assets=assets, findings=findings)
    if ctx.warnings:
        result.meta.collectors_skipped.setdefault("_warnings", "; ".join(ctx.warnings[:50]))
    return result


def regrade(result: ScanResult, profile: str, now: Optional[_dt.datetime] = None) -> ScanResult:
    """Re-run the policy on an existing inventory (e.g. compare profiles without rescanning)."""
    result.findings = evaluate(result.assets, profile, now=now)
    result.meta.profile = profile
    return result
