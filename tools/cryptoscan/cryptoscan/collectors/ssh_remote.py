"""Remote SSH collector: handshake-only KEXINIT probe of ssh targets.

Records every algorithm the server advertises (negotiated=False), the banner,
and, when `ssh-keyscan` is installed, the public host keys with their sizes.
No authentication is attempted.  Options: `workers` (default 16), `keyscan`
(default True).
"""

from __future__ import annotations

import concurrent.futures
from typing import List, Optional, Tuple

from .. import names, sshwire
from ..model import Asset, AssetKind, CryptoUse, Primitive
from . import register
from .base import Collector, ScanContext, Target

_MARKERS = {"ext-info-s", "ext-info-c", "kex-strict-s-v00@openssh.com", "kex-strict-c-v00@openssh.com"}


def _ssh_port(t: Target) -> Optional[int]:
    """Port to probe, or None when the target is not an SSH target."""
    svc = (t.service or "auto").lower()
    if svc == "ssh":
        return t.port or 22
    if svc == "auto" and (t.port is None or t.port == 22):
        return 22
    return None


def _directional(asset: Asset, c2s: List[str], s2c: List[str], make) -> None:
    for name in c2s + [n for n in s2c if n not in c2s]:
        a, b = name in c2s, name in s2c
        direction = "both" if a and b else ("c2s" if a else "s2c")
        asset.add(make(name, negotiated=False, extra={"direction": direction}))


@register
class SSHRemoteCollector(Collector):
    name = "ssh_remote"
    description = "Remote SSH servers: advertised kex/host-key/cipher/MAC lists via a handshake-only KEXINIT probe"
    needs_network = True

    def applicable(self, ctx: ScanContext) -> Tuple[bool, str]:
        ok, why = super().applicable(ctx)
        if not ok:
            return ok, why
        if not any(_ssh_port(t) is not None for t in ctx.targets):
            return False, "no ssh targets"
        return True, ""

    def collect(self, ctx: ScanContext) -> List[Asset]:
        targets = [(t, p) for t in ctx.targets for p in [_ssh_port(t)] if p is not None]
        if not targets:
            return []
        workers = max(1, int(ctx.opt("workers", 16)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, len(targets))) as ex:
            futs = [ex.submit(self._one, ctx, t, p) for t, p in targets]
            return [f.result() for f in futs]

    def _one(self, ctx: ScanContext, t: Target, port: int) -> Asset:
        loc = f"[{t.host}]:{port}" if ":" in t.host else f"{t.host}:{port}"
        asset = Asset(AssetKind.SSH_REMOTE, f"ssh {t.label or loc}", loc, self.name, host=t.host)
        try:
            pr = sshwire.probe(t.host, port, ctx.timeout)
        except Exception as e:  # defensive: probe() should not raise
            asset.errors.append(f"probe failed: {type(e).__name__}: {e}")
            return asset
        asset.attributes["reachable"] = bool(pr.banner)
        if pr.banner:
            asset.attributes.update(banner=pr.banner, software=pr.software, protocol_version=pr.protocol_version)
            asset.add(CryptoUse(Primitive.CONFIG, "ssh-version", raw=pr.banner, context="ssh-version", negotiated=True))
            if pr.protocol_version == "1.99":
                asset.add(CryptoUse(Primitive.PROTOCOL, "ssh1.99", raw=pr.banner, context="ssh-protocol", negotiated=True))
            elif pr.protocol_version.startswith("1."):
                asset.add(CryptoUse(Primitive.PROTOCOL, "ssh1", raw=pr.banner, context="ssh-protocol", negotiated=True))
        if not pr.ok:
            asset.errors.append(f"ssh probe: {pr.error}")
            return asset
        asset.attributes.update(kex_strict=pr.kex_strict, ext_info=pr.ext_info,
                                compression=pr.compression, first_kex_follows=pr.first_kex_follows)
        for n in pr.kex:
            if n not in _MARKERS:
                asset.add(names.ssh_kex(n, negotiated=False))
        for n in pr.hostkey:
            asset.add(names.ssh_hostkey(n, negotiated=False))
        _directional(asset, pr.ciphers_c2s, pr.ciphers_s2c, names.ssh_cipher)
        _directional(asset, pr.macs_c2s, pr.macs_s2c, names.ssh_mac)
        if ctx.opt("keyscan", True):
            try:
                for k in sshwire.fetch_host_keys(t.host, port, ctx):
                    asset.add(CryptoUse(Primitive.PUBLIC_KEY, k.info.algorithm, key_bits=k.info.key_bits,
                                        curve=k.info.curve, raw=k.key_type, context="hostkey-material",
                                        extra={"source": "ssh-keyscan",
                                               **({"rsa_exponent": k.info.rsa_exponent} if k.info.rsa_exponent else {})}))
            except Exception as e:
                asset.errors.append(f"ssh-keyscan failed: {type(e).__name__}: {e}")
        return asset
