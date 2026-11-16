#!/usr/bin/env python3
"""Compile the exact build configuration and its identities, without claiming
that the Lake configuration itself declares any mathematical theorems.
"""
import hashlib
from pathlib import Path
import runpy

path = Path(__file__).with_name("check_native.py")
if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != "0cd21c9fe29b575cd7d0b99f18ed9aca283664b72a5d3786dd6aaed9fc702564":
    raise RuntimeError("native checker pin mismatch")
runpy.run_path(str(path))["main"](config_only=True)
