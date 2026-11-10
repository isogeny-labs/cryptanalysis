"""Report renderers: json (native), md, html, cbom (CycloneDX 1.6), csv, sarif.

``render(result, fmt, **opts)`` dispatches to ``RENDERERS[fmt]``.  Every
renderer is a pure function of the ScanResult (standard library only).

Options per format:
  json   indent=2
  md     max_findings=500
  html   (none)
  cbom   (none)
  csv    which="findings" | "uses", safe=True
  sarif  (none)
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from ..model import ScanResult
from . import cbom, csv_report, html, markdown, sarif, summary
from .summary import summarize

__all__ = ["RENDERERS", "EXTENSIONS", "render", "summarize"]


def _json(result: ScanResult, indent: int = 2, **_: Any) -> str:
    return result.to_json(indent=indent)


RENDERERS: Dict[str, Callable[..., str]] = {
    "json": _json,
    "md": markdown.render,
    "html": html.render,
    "cbom": cbom.render,
    "csv": csv_report.render,
    "sarif": sarif.render,
}
EXTENSIONS = {"json": ".json", "md": ".md", "html": ".html", "cbom": ".cbom.json", "csv": ".csv", "sarif": ".sarif"}


def render(result: ScanResult, fmt: str, **opts: Any) -> str:
    try:
        fn = RENDERERS[fmt]
    except KeyError:
        raise ValueError(f"unknown report format {fmt!r}; choose from {', '.join(sorted(RENDERERS))}") from None
    return fn(result, **opts)
