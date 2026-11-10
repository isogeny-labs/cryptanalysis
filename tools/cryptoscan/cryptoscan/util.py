"""Small helpers shared by collectors: safe subprocess, safe file reads, walks."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from typing import Iterator, List, Optional, Sequence


@dataclass
class CmdResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int
    error: Optional[str] = None


def which(name: str) -> Optional[str]:
    return shutil.which(name)


def run_cmd(argv: Sequence[str], timeout: float = 20.0, input_text: Optional[str] = None, env: Optional[dict] = None) -> CmdResult:
    """Run a command without a shell; never raises."""
    if not argv or which(argv[0]) is None and not os.path.isabs(argv[0]):
        return CmdResult(False, "", "", -1, f"{argv[0] if argv else '?'}: not found")
    try:
        p = subprocess.run(list(argv), capture_output=True, text=True, timeout=timeout, input=input_text,
                           env=env, errors="replace")
        return CmdResult(p.returncode == 0, p.stdout, p.stderr, p.returncode)
    except subprocess.TimeoutExpired:
        return CmdResult(False, "", "", -1, f"{argv[0]}: timed out after {timeout}s")
    except (OSError, ValueError) as e:
        return CmdResult(False, "", "", -1, f"{argv[0]}: {e}")


def read_bytes(path: str, limit: int = 8 * 1024 * 1024) -> Optional[bytes]:
    """Read a regular file up to `limit` bytes; None if unreadable."""
    try:
        st = os.stat(path)
        if not stat.S_ISREG(st.st_mode) or st.st_size > limit:
            return None
        with open(path, "rb") as fh:
            return fh.read(limit)
    except (OSError, PermissionError):
        return None


def read_text(path: str, limit: int = 8 * 1024 * 1024) -> Optional[str]:
    b = read_bytes(path, limit)
    return None if b is None else b.decode("utf-8", "replace")


def file_mode(path: str) -> Optional[int]:
    try:
        return stat.S_IMODE(os.stat(path).st_mode)
    except OSError:
        return None


def file_owner(path: str) -> Optional[str]:
    try:
        st = os.stat(path)
        try:
            import pwd
            return pwd.getpwuid(st.st_uid).pw_name
        except (ImportError, KeyError):
            return str(st.st_uid)
    except OSError:
        return None


_SKIP_DIRS = {"proc", "sys", "dev", "run", "snap", "node_modules", ".git", "__pycache__", "site-packages", "dist-packages", "lost+found"}


def walk_files(roots: Sequence[str], max_files: int = 200000, max_depth: int = 12,
               skip_dirs: Optional[set] = None, follow_symlinks: bool = False) -> Iterator[str]:
    """Yield regular files under roots, bounded, without crossing into pseudo-filesystems."""
    skip = _SKIP_DIRS | (skip_dirs or set())
    count = 0
    seen_dev_ino = set()
    for root in roots:
        root = os.path.abspath(root)
        if os.path.isfile(root):
            yield root
            continue
        base_depth = root.rstrip("/").count("/")
        for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks, onerror=lambda e: None):
            depth = dirpath.count("/") - base_depth
            if depth >= max_depth:
                dirnames[:] = []
            dirnames[:] = [d for d in dirnames if d not in skip and not (depth == 0 and dirpath == "/" and d in ("proc", "sys", "dev", "run"))]
            try:
                st = os.stat(dirpath)
                key = (st.st_dev, st.st_ino)
                if key in seen_dev_ino:
                    dirnames[:] = []
                    continue
                seen_dev_ino.add(key)
            except OSError:
                continue
            for fn in filenames:
                count += 1
                if count > max_files:
                    return
                yield os.path.join(dirpath, fn)


def home_dirs() -> List[str]:
    """Home directories of local accounts (plus /root), existing only."""
    out = []
    try:
        import pwd
        for pw in pwd.getpwall():
            if pw.pw_dir and os.path.isdir(pw.pw_dir) and pw.pw_dir not in ("/", "/nonexistent", "/bin", "/sbin", "/usr/sbin", "/dev/null"):
                out.append(pw.pw_dir)
    except ImportError:
        pass
    for extra in ("/root", os.path.expanduser("~")):
        if os.path.isdir(extra) and extra not in out:
            out.append(extra)
    return sorted(set(out))
