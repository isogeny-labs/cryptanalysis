"""Collector interface.

A collector inspects one kind of source (local SSH configuration, a remote TLS
endpoint, a Kerberos keytab, ...) and returns Assets with CryptoUses.  It must
never grade: the policy engine does that.  It must never raise for an
environmental problem (missing file, no permission, closed port): record the
problem in `Asset.errors` or `ScanContext.warn()` and carry on.
"""

from __future__ import annotations

import logging
import socket
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..model import Asset


@dataclass
class Target:
    """A network target: host[:port] with an optional service hint."""

    host: str
    port: Optional[int] = None
    service: Optional[str] = None     # "ssh", "tls", "https", "smtp", "ldap", "snmp", "kerberos", "auto"
    label: Optional[str] = None

    @classmethod
    def parse(cls, spec: str, default_service: str = "auto") -> Target:
        service = default_service
        label = None
        if "=" in spec and not spec.startswith("["):
            label, spec = spec.split("=", 1)
        if "://" in spec:
            service, spec = spec.split("://", 1)
            spec = spec.rstrip("/")
        host, port = spec, None
        if spec.startswith("["):                      # [v6]:port
            h, _, rest = spec[1:].partition("]")
            host = h
            if rest.startswith(":"):
                port = int(rest[1:])
        elif spec.count(":") == 1:
            host, p = spec.split(":")
            port = int(p) if p else None
        return cls(host=host, port=port, service=service, label=label)

    def __str__(self) -> str:
        return f"{self.host}:{self.port}" if self.port else self.host


@dataclass
class ScanContext:
    """Everything a collector may need; constructed once per run by the CLI."""

    hostname: str = field(default_factory=socket.gethostname)
    root: str = "/"                                     # filesystem root to inspect (for offline images)
    targets: List[Target] = field(default_factory=list)
    netdev_configs: List[str] = field(default_factory=list)   # offline device config files
    extra_paths: List[str] = field(default_factory=list)       # extra dirs to scan for certs/keys
    options: Dict[str, object] = field(default_factory=dict)   # free-form per-collector options
    timeout: float = 8.0                                # network timeout per connection
    cmd_timeout: float = 20.0
    active_probes: bool = True                          # allow network connections
    snmp_probe: bool = False                            # allow SNMP community probing (needs consent)
    deep_fs_scan: bool = False                          # walk the whole filesystem for key material
    max_files: int = 200000
    log: logging.Logger = field(default_factory=lambda: logging.getLogger("cryptoscan"))
    warnings: List[str] = field(default_factory=list)

    def path(self, *parts: str) -> str:
        """Join a path under the inspected root (so offline images work)."""
        import os
        p = os.path.join(*parts)
        if self.root in ("", "/"):
            return p
        return os.path.join(self.root, p.lstrip("/"))

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        self.log.warning(msg)

    def opt(self, key: str, default=None):
        return self.options.get(key, default)


class Collector:
    """Base class.  Subclasses set `name`, `description`, and implement collect()."""

    name: str = "base"
    description: str = ""
    needs_network: bool = False
    default_enabled: bool = True

    def applicable(self, ctx: ScanContext) -> Tuple[bool, str]:
        """Return (True, "") to run, or (False, reason) to skip."""
        if self.needs_network and not ctx.active_probes:
            return False, "active probes disabled"
        return True, ""

    def collect(self, ctx: ScanContext) -> List[Asset]:
        raise NotImplementedError

    def safe_collect(self, ctx: ScanContext) -> List[Asset]:
        try:
            return self.collect(ctx)
        except Exception as e:                     # a collector bug must not kill the scan
            ctx.warn(f"collector {self.name} failed: {type(e).__name__}: {e}")
            if ctx.opt("debug"):
                import traceback
                traceback.print_exc(file=sys.stderr)
            return []
