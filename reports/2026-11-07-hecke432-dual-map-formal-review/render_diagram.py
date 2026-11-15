"""Render the review's proof-boundary diagram from fixed labeled facts."""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).with_name("proof-boundary.svg")


def box(x, y, w, h, title, lines, fill="#eef4ff"):
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="#354967" stroke-width="2"/>',
             f'<text x="{x+18}" y="{y+30}" class="title">{escape(title)}</text>']
    for n, line in enumerate(lines):
        parts.append(f'<text x="{x+18}" y="{y+58+n*23}" class="body">{escape(line)}</text>')
    return "\n".join(parts)


svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="620" viewBox="0 0 1120 620" role="img" aria-label="Hecke 432 dual coordinate proof boundary">
<style>
  .heading { font: 700 27px sans-serif; fill: #152c45; }
  .title { font: 700 17px sans-serif; fill: #152c45; }
  .body { font: 15px sans-serif; fill: #243b54; }
  .label { font: 14px sans-serif; fill: #354967; }
  .small { font: 13px sans-serif; fill: #354967; }
</style>
<rect width="1120" height="620" fill="white"/>
<text x="42" y="48" class="heading">Level-432 dual coordinate proof boundary</text>
<text x="42" y="77" class="small">Producer 06335430 · review plan 45f21e2 · exact Lean build and fidelity verdict pending</text>
'''
svg += box(42, 112, 450, 130, "Source affine equation", ["B: Y² = X³ − 16", "Domain: field elements with X ≠ 0"])
svg += box(627, 112, 450, 130, "Target affine equation", ["E: V² = U³ + 432", "U = (X³ − 64)/X²", "V = Y(X³ + 128)/X³"], "#edfaee")
svg += '''<path d="M492 176 L627 176" stroke="#20734a" stroke-width="3" marker-end="url(#arrow)"/>
<text x="502" y="157" class="label">Lean algebraic implication</text>
'''
svg += box(42, 337, 450, 125, "Archived modular map to B", ["X₀(432) → B", "Normalized map and cusp behavior", "Separate geometric input"], "#fff4e7")
svg += box(627, 337, 450, 125, "Quarter-shift map to E", ["X₀(432) → E", "Comparison through q-series and Sturm", "Full Lean bridge remains open"], "#fff4e7")
svg += '''<path d="M267 337 L267 242" stroke="#b56924" stroke-width="3" stroke-dasharray="9 7" marker-end="url(#arrowOrange)"/>
<path d="M852 242 L852 337" stroke="#b56924" stroke-width="3" stroke-dasharray="9 7" marker-end="url(#arrowOrange)"/>
<path d="M492 400 L627 400" stroke="#b56924" stroke-width="3" stroke-dasharray="9 7" marker-end="url(#arrowOrange)"/>
<text x="506" y="380" class="label">identity requires bridge</text>
<text x="42" y="516" class="body">Solid green: affine curve-equation obligation under review. Dashed orange: not supplied by this theorem.</text>
<text x="42" y="545" class="small">Exceptional points X = 0 and infinity, global morphism, group law, and degree-three status need separate proof.</text>
<defs>
<marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#20734a"/></marker>
<marker id="arrowOrange" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#b56924"/></marker>
</defs>
</svg>
'''
OUT.write_text(svg)
print(OUT)
