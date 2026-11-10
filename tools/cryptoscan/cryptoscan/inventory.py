"""Fleet inventory file: JSON describing what to scan.

Example (``cryptoscan scan --inventory fleet.json``)::

    {
      "profile": "nist",
      "targets": [
        "ssh://bastion.example.net:22",
        "https://www.example.net",
        "smtp://mail.example.net:25",
        "ldap://dc1.example.net:389",
        {"host": "core-sw1.example.net", "port": 22, "service": "ssh", "label": "core switch"},
        {"host": "10.0.0.1", "service": "snmp"}
      ],
      "netdev_configs": ["/srv/rancid/configs/"],
      "extra_paths": ["/opt/app/certs"],
      "options": {"snmp_communities": ["public"], "workers": 32},
      "snmp_probe": false
    }

Targets accept the same ``[label=][service://]host[:port]`` syntax as ``--target``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .collectors.base import ScanContext, Target


def load_inventory(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("inventory must be a JSON object")
    return data


def apply_inventory(ctx: ScanContext, inv: Dict[str, Any]) -> str:
    """Populate ctx from an inventory dict; returns the profile name it requests (or '')."""
    for t in inv.get("targets", []):
        if isinstance(t, str):
            ctx.targets.append(Target.parse(t))
        elif isinstance(t, dict):
            ctx.targets.append(Target(host=t["host"], port=t.get("port"), service=t.get("service", "auto"), label=t.get("label")))
    ctx.netdev_configs.extend(inv.get("netdev_configs", []))
    ctx.extra_paths.extend(inv.get("extra_paths", []))
    ctx.options.update(inv.get("options", {}))
    if "snmp_probe" in inv:
        ctx.snmp_probe = bool(inv["snmp_probe"])
    if "active_probes" in inv:
        ctx.active_probes = bool(inv["active_probes"])
    if "deep_fs_scan" in inv:
        ctx.deep_fs_scan = bool(inv["deep_fs_scan"])
    if "timeout" in inv:
        ctx.timeout = float(inv["timeout"])
    return str(inv.get("profile", ""))


def targets_summary(targets: List[Target]) -> str:
    return ", ".join(f"{t.service}://{t}" if t.service and t.service != "auto" else str(t) for t in targets)
