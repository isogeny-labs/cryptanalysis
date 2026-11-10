"""Collector registry.  Import order defines report order."""

from __future__ import annotations

from typing import Dict, Type

from .base import Collector, ScanContext, Target  # noqa: F401

_REGISTRY: Dict[str, Type[Collector]] = {}
LOAD_ERRORS: Dict[str, str] = {}


def register(cls: Type[Collector]) -> Type[Collector]:
    _REGISTRY[cls.name] = cls
    return cls


def all_collectors() -> Dict[str, Type[Collector]]:
    _load()
    return dict(_REGISTRY)


def get(name: str) -> Type[Collector]:
    _load()
    return _REGISTRY[name]


_loaded = False


def _load() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    import importlib
    for mod in ("system_policy", "ssh_local", "ssh_remote", "tls_remote", "certs_local", "keys_local",
                "kerberos", "netdev", "ipsec", "web_servers", "pgp"):
        try:
            importlib.import_module(f"{__name__}.{mod}")
        except ImportError as e:   # a missing optional collector must not break the package
            import logging
            logging.getLogger("cryptoscan").debug("collector %s unavailable: %s", mod, e)
        except Exception as e:     # a broken collector must not take the scanner down
            import logging
            logging.getLogger("cryptoscan").warning("collector %s failed to load: %s: %s", mod, type(e).__name__, e)
            LOAD_ERRORS[mod] = f"{type(e).__name__}: {e}"
