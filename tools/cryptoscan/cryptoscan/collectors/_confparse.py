"""Shared tolerant parsers and path helpers for the config-file collectors.

Nothing here does policy: it only turns text into trees / key-value lists.
"""

from __future__ import annotations

import glob as _glob
import os
import re
from typing import Dict, List, Optional, Tuple, Union

from .. import util

Tree = List[Tuple[str, Union[str, list]]]       # [(key, "value" | nested Tree)]


def strip_quotes(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def join_continuations(text: str) -> List[str]:
    """Split into lines, joining those that end in a backslash."""
    out: List[str] = []
    buf = ""
    for line in text.splitlines():
        if line.rstrip().endswith("\\"):
            buf += line.rstrip()[:-1]
            continue
        out.append(buf + line)
        buf = ""
    if buf:
        out.append(buf)
    return out


def parse_braces(text: str, bracket_sections: bool = False, inline_comments: bool = False,
                 comment_chars: str = "#;", directives: Tuple[str, ...] = ("include", "includedir", "module")
                 ) -> Tuple[Tree, List[Tuple[str, str]]]:
    """Parse `key = value`, `key = {`/`key {` ... `}` blocks and `[section]` headers.

    Returns (tree, includes).  Keys keep their spelling (realm names are case
    sensitive); duplicates are kept in order.  Directive lines such as
    `include FILE` / `includedir DIR` are returned separately, not interpreted.
    """
    root: Tree = []
    stack: List[Tree] = [root]
    base = 1
    includes: List[Tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in comment_chars:
            continue
        if inline_comments:
            line = re.sub(r"\s+#.*$", "", line).strip()
            if not line:
                continue
        if bracket_sections and line.startswith("[") and "]" in line:
            name = line[1:line.index("]")].strip()
            del stack[1:]
            blk: Tree = []
            root.append((name.lower(), blk))
            stack.append(blk)
            base = 2
            continue
        if line.startswith("}"):
            if len(stack) > base:
                stack.pop()
            continue
        if line.endswith("{"):
            key = line[:-1].strip()
            if key.endswith("="):
                key = key[:-1].strip()
            blk = []
            stack[-1].append((strip_quotes(key), blk))
            stack.append(blk)
            continue
        m = re.match(r"([^=\s][^=]*?)\s*=\s*(.*)$", line)
        if m:
            stack[-1].append((m.group(1).strip(), strip_quotes(m.group(2))))
            continue
        parts = line.split(None, 1)
        if parts[0].lower() in directives and len(parts) == 2:
            includes.append((parts[0].lower(), strip_quotes(parts[1])))
    return root, includes


def values(tree: Tree, key: str) -> List[str]:
    k = key.lower()
    return [v for kk, v in tree if isinstance(v, str) and kk.lower() == k]


def first(tree: Tree, key: str, default: Optional[str] = None) -> Optional[str]:
    v = values(tree, key)
    return v[0] if v else default


def blocks(tree: Tree, key: Optional[str] = None) -> List[Tuple[str, Tree]]:
    return [(k, v) for k, v in tree if isinstance(v, list) and (key is None or k.lower() == key.lower())]


def parse_properties(text: str) -> Dict[str, str]:
    """java.security style properties (`key=value`, backslash continuations, # comments)."""
    out: Dict[str, str] = {}
    buf = ""
    for line in text.splitlines():
        s = line.strip()
        if buf:
            s = buf + s
            buf = ""
        elif not s or s[0] in "#!":
            continue
        if s.endswith("\\"):
            buf = s[:-1]
            continue
        m = re.match(r"([^=:\s]+)\s*[=:]\s*(.*)$", s)
        if m:
            out[m.group(1)] = m.group(2).strip()
    if buf:
        m = re.match(r"([^=:\s]+)\s*[=:]\s*(.*)$", buf)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def ctx_glob(ctx, pattern: str) -> List[str]:
    """Glob a host path under the scan root, sorted, files and dirs."""
    try:
        return sorted(_glob.glob(ctx.path(pattern)))
    except OSError:
        return []


def logical(ctx, path: str) -> str:
    """Strip the scan root prefix so locations read like host paths."""
    if ctx.root in ("", "/"):
        return path
    root = ctx.root.rstrip("/")
    if path.startswith(root + "/"):
        return path[len(root):]
    return path


def file_attrs(path: str) -> Dict[str, object]:
    out: Dict[str, object] = {}
    m = util.file_mode(path)
    if m is not None:
        out["mode"] = m
    o = util.file_owner(path)
    if o is not None:
        out["owner"] = o
    return out


def real(path: str) -> str:
    try:
        return os.path.realpath(path)
    except OSError:
        return path


def is_root_host(ctx) -> bool:
    return ctx.root in ("", "/")
