"""Shared helpers for the collector tests."""

import os
import shutil
import tempfile

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
CERTS = os.path.join(FIX, "certs")
KEYS = os.path.join(FIX, "keys")


def cert_path(name: str) -> str:
    return os.path.join(CERTS, name)


def key_path(name: str) -> str:
    return os.path.join(KEYS, name)


def read(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def pem_to_der(pem: bytes) -> bytes:
    from cryptoscan import x509
    return x509.load_certificates(pem)[0].der


def make_root() -> str:
    """A fresh temporary directory to use as ScanContext.root."""
    return tempfile.mkdtemp(prefix="cryptoscan-test-")


def put(root: str, rel: str, data: bytes, mode: int = 0o644) -> str:
    path = os.path.join(root, rel.lstrip("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)
    os.chmod(path, mode)
    return path


def rmtree(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)
