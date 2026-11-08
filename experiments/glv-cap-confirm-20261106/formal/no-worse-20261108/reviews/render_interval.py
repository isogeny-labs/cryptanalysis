"""Render the frozen published intervals used by the no-worse logic review."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = Decimal("10000000000000000")
ROWS = [
    ("pooled 40", 9633305383496846, 10206439763276927, "98.75%"),
    ("pooled 41", 9607939208626060, 10185748136395380, "98.75%"),
    ("pooled 42", 9539100281038944, 10106357048268606, "98.75%"),
    ("pooled 43", 9495902517552110, 10071181450938511, "98.75%"),
    ("j = 0", 9860137324692078, 10186699532206690, "95%"),
]


def x(value: int | Decimal) -> float:
    return 150 + float((Decimal(value) / S - Decimal("0.94")) / Decimal("0.09")) * 630


def main() -> None:
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="390" viewBox="0 0 900 390">',
        '<rect width="900" height="390" fill="white"/>',
        '<style>text{font-family:DejaVu Sans,Arial,sans-serif;fill:#172333} .label{font-size:15px} .small{font-size:12px;fill:#526477}</style>',
        '<text x="150" y="28" font-size="19" font-weight="bold">Published ratio intervals and registered threshold</text>',
        '<text x="150" y="47" class="small">Source: glv-cap-confirm-20261106/results.json; intervals are printed aggregates, not a raw-row replay</text>',
        f'<line x1="{x(S):.1f}" y1="67" x2="{x(S):.1f}" y2="312" stroke="#be3144" stroke-width="2" stroke-dasharray="6 4"/>',
        f'<text x="{x(S)+7:.1f}" y="75" class="small">1.0 threshold</text>',
    ]
    for i, (label, lo, hi, coverage) in enumerate(ROWS):
        y = 101 + i * 48
        color = "#176b9a" if i < 4 else "#98522d"
        parts.extend([
            f'<text x="20" y="{y+5}" class="label">{label}</text>',
            f'<line x1="{x(lo):.1f}" y1="{y}" x2="{x(hi):.1f}" y2="{y}" stroke="{color}" stroke-width="5"/>',
            f'<circle cx="{x(lo):.1f}" cy="{y}" r="5" fill="{color}"/>',
            f'<circle cx="{x(hi):.1f}" cy="{y}" r="5" fill="{color}"/>',
            f'<text x="790" y="{y+5}" class="small">{coverage}</text>',
        ])
    for value in (Decimal("0.94"), Decimal("0.96"), Decimal("0.98"), Decimal("1.00"), Decimal("1.02")):
        px = x(value * S)
        parts.extend([
            f'<line x1="{px:.1f}" y1="329" x2="{px:.1f}" y2="335" stroke="#526477"/>',
            f'<text x="{px-17:.1f}" y="352" class="small">{value:.2f}</text>',
        ])
    parts.extend([
        '<line x1="150" y1="329" x2="780" y2="329" stroke="#526477"/>',
        '<text x="360" y="379" class="small">ratio (printed endpoint divided by 10^16)</text>',
        '</svg>',
    ])
    (HERE / "intervals.svg").write_text("\n".join(parts) + "\n")


if __name__ == "__main__":
    main()
