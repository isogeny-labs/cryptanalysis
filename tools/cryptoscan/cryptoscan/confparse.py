"""Tolerant, dependency-free parsers for network-device configuration syntaxes.

* `parse_indent_tree`  Cisco/Arista/HP/Huawei style: indentation defines the hierarchy
* `junos_paths`        Junos curly-brace and `set ...` formats -> tuples of tokens
* `brace_paths`        generic brace parser (Junos `;`-terminated, F5/PAN-OS newline-terminated)
* `parse_forti`        FortiOS config/edit/set/next/end trees
* `tokenize`           shlex-like splitting that never raises

None of these validate anything; they extract just enough structure for the
netdev collector to ask "what is configured here".  Secrets are present in the
parsed data (the caller must never copy values out of password fields).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


def tokenize(line: str) -> List[str]:
    """Split on whitespace honouring "double" and 'single' quotes; quotes are removed."""
    out: List[str] = []
    cur: List[str] = []
    quote = ""
    started = False
    i = 0
    while i < len(line):
        c = line[i]
        if quote:
            if c == "\\" and quote == '"' and i + 1 < len(line):
                cur.append(line[i + 1])
                i += 2
                continue
            if c == quote:
                quote = ""
            else:
                cur.append(c)
        elif c in "\"'" and (not cur or c == '"'):
            quote, started = c, True
        elif c.isspace():
            if cur or started:
                out.append("".join(cur))
                cur, started = [], False
        else:
            cur.append(c)
        i += 1
    if cur or started:
        out.append("".join(cur))
    return out


# ---------------------------------------------------------------------------
# indentation trees (Cisco IOS family, Arista EOS, ProCurve, Huawei)
# ---------------------------------------------------------------------------

@dataclass
class INode:
    text: str
    lineno: int
    children: List[INode] = field(default_factory=list)

    def find(self, prefix: str) -> List[INode]:
        return [c for c in self.children if c.text == prefix or c.text.startswith(prefix + " ")]

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


def parse_indent_tree(text: str) -> List[INode]:
    """Parse an indentation-structured CLI configuration into top-level nodes.

    Blank lines, `!` and lone `#` separators are skipped; banner bodies are dropped.
    """
    roots: List[INode] = []
    stack: List[Tuple[int, INode]] = []
    banner_delim: Optional[str] = None
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if banner_delim is not None:
            if banner_delim in line:
                banner_delim = None
            continue
        s = line.strip()
        if not s or s.startswith("!") or s == "#" or s.startswith("#"):
            continue
        m = re.match(r"^banner\s+\S+\s+(\^C|\S)", s)
        if m:
            d = m.group(1)
            if d not in s[m.end():]:
                banner_delim = d
            continue
        indent = len(line) - len(line.lstrip(" \t"))
        node = INode(s, no)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        (stack[-1][1].children if stack else roots).append(node)
        stack.append((indent, node))
    return roots


# ---------------------------------------------------------------------------
# brace formats
# ---------------------------------------------------------------------------

Path = Tuple[str, ...]


def _lex_brace(text: str, newline: bool) -> List[str]:
    """Tokens: words, '{', '}', ';', '[', ']' and (if newline) '\\n'. Comments are dropped."""
    toks: List[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\n":
            if newline:
                toks.append("\n")
            i += 1
        elif c.isspace():
            i += 1
        elif c == "#" and (not toks or toks[-1] in ("{", "}", ";", "\n") or text[i - 1].isspace()):
            while i < n and text[i] != "\n":
                i += 1
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in "{};[]":
            toks.append(c)
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    j += 1
                buf.append(text[j])
                j += 1
            toks.append("".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in "{};[]":
                j += 1
            toks.append(text[i:j])
            i = j
    return toks


def brace_paths(text: str, newline_terminates: bool = False) -> List[Path]:
    """Flatten a brace-structured config into leaf paths.

    `a { b c; d [ x y ]; }` yields ("a","b","c"), ("a","d","x"), ("a","d","y").  Statements ending in
    `{` become path prefixes.  With newline_terminates (F5, PAN-OS) a newline ends a statement.
    `inactive:` blocks/statements (Junos) are dropped.
    """
    toks = _lex_brace(text, newline_terminates)
    out: List[Path] = []
    prefix: List[Tuple[str, ...]] = []
    cur: List[str] = []
    in_list = False
    list_items: List[str] = []

    def emit(path_tokens: List[str]) -> None:
        if not path_tokens:
            return
        flat = [t for p in prefix for t in p] + path_tokens
        if "\x00inactive" in flat:
            return
        out.append(tuple(flat))

    for t in toks:
        if in_list:
            if t == "]":
                in_list = False
                for it in list_items:
                    emit(cur + [it])
                list_items, cur = [], []
            elif t != "\n":
                list_items.append(t)
            continue
        if t == "[":
            in_list = True
            list_items = []
        elif t == "{":
            if cur and cur[0] == "inactive:":
                prefix.append(("\x00inactive",))
            else:
                prefix.append(tuple(x for x in cur if x not in ("protect:", "replace:", "active:")))
            cur = []
        elif t == "}":
            if cur:
                emit(cur)
            cur = []
            if prefix:
                prefix.pop()
        elif t == ";" or (t == "\n" and newline_terminates):
            if cur and cur[0] == "inactive:":
                cur = []
            else:
                emit([x for x in cur if x not in ("protect:", "replace:", "active:")])
                cur = []
        elif t == "\n":
            continue
        else:
            cur.append(t)
    if cur:
        emit(cur)
    return out


def junos_paths(text: str) -> List[Path]:
    """Junos configuration as token tuples; accepts `set ...` lines and curly-brace format."""
    lines = text.splitlines()
    set_format = bool(re.search(r"^\s*set\s+\S", text, re.M)) and not re.search(r"\{\s*$", text, re.M)
    if set_format:
        out: List[Path] = []
        for l in lines:
            s = l.strip()
            if s.startswith("set "):
                out.append(tuple(tokenize(s)[1:]))
            elif s.startswith("delete "):
                gone = tuple(tokenize(s)[1:])
                out = [p for p in out if p[:len(gone)] != gone]
        return [p for p in out if p]
    return brace_paths(text, newline_terminates=False)


def paths_under(paths: List[Path], prefix: Path) -> List[Path]:
    """Paths starting with `prefix`, with the prefix stripped."""
    n = len(prefix)
    return [p[n:] for p in paths if p[:n] == prefix and len(p) > n]


def has_path(paths: List[Path], prefix: Path) -> bool:
    n = len(prefix)
    return any(p[:n] == prefix for p in paths)


# ---------------------------------------------------------------------------
# FortiOS
# ---------------------------------------------------------------------------

@dataclass
class FSection:
    config: str                         # e.g. "vpn ipsec phase1-interface" or "system snmp community>hosts"
    edit: Optional[str]                 # edit id/name, or None for a plain config block
    settings: Dict[str, List[str]] = field(default_factory=dict)

    def get(self, key: str, default: Optional[List[str]] = None) -> Optional[List[str]]:
        return self.settings.get(key, default)

    def first(self, key: str, default: Optional[str] = None) -> Optional[str]:
        v = self.settings.get(key)
        return v[0] if v else default


def parse_forti(text: str) -> List[FSection]:
    """Parse FortiOS `config ... edit ... set ... next ... end` into flat sections."""
    sections: List[FSection] = []
    stack: List[FSection] = []
    cfg_chain: List[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        toks = tokenize(s)
        if not toks:
            continue
        head = toks[0].lower()
        if head == "config" and len(toks) > 1:
            cfg_chain.append(" ".join(toks[1:]))
            sec = FSection(">".join(cfg_chain), None)
            sections.append(sec)
            stack.append(sec)
        elif head == "edit" and len(toks) > 1:
            sec = FSection(">".join(cfg_chain), " ".join(toks[1:]))
            sections.append(sec)
            stack.append(sec)
        elif head == "next":
            if stack and stack[-1].edit is not None:
                stack.pop()
        elif head == "end":
            if stack and stack[-1].edit is not None:
                stack.pop()
            if stack:
                stack.pop()
            if cfg_chain:
                cfg_chain.pop()
        elif head == "set" and len(toks) >= 2 and stack:
            stack[-1].settings[toks[1]] = toks[2:]
        elif head == "append" and len(toks) >= 2 and stack:
            stack[-1].settings.setdefault(toks[1], []).extend(toks[2:])
    return sections
