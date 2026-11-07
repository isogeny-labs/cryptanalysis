#set page(paper: "a4", margin: 10mm)
#set text(font: "Libertinus Serif", size: 9pt, lang: "en")
#set par(leading: 0.42em, justify: true)
#set heading(numbering: none)

#align(center)[
  #text(size: 19pt, weight: "bold")[Dₖ = −39 Hecke rank audit]
  #linebreak()
  #text(size: 10pt, fill: rgb("425b72"))[Evidence-linked visual record • exploratory finite case • 2026-10-28]
]

#v(4pt)
#block(fill: rgb("fff3df"), stroke: (paint: rgb("e6bd73"), thickness: 0.8pt), inset: 8pt, radius: 4pt)[
  #text(weight: "bold")[Provenance.] This report summarizes already-published run and audit artifacts; it does not repeat the experiment. `PROTOCOL.md` and the result first appear together in the PR, so this is an exploratory comparison, not an independently verifiable holdout. The figure is an audit-flow schematic, not a literal graph of points or isogenies.
]

#v(7pt)
#image("d39-evidence-map.svg", width: 96%)

#v(2pt)
= Recorded observations
The exploratory class walk on #emph[X₀(11)/F₃₆₇], with #emph[Dₖ = −39], conductor #emph[f = 6], and Hecke degrees 2 and 3, records 64 distinct rational points. The matrix audit verifies 32 degree-2 and 16 degree-3 rows. Its sparse rank checks report Hecke rank 40, rising to 52 after 64 Atkin–Lehner rows, consistently over F₁₁, F₁₀₀₉, and F₁₀₀₀₀₀₀₀₀₇.

The independent conductor audit assigns the 64 points across conductors 1, 2, 3, and 6 as 8, 8, 24, and 24 points. The graph audit starts from 32 degree-2 rows and records four incidence components. Two satisfy the signed-cancellation certificate, each with 12 rows; together they cover all 24 conductor-6 floor columns with coefficients +1 or −1. Two components were rejected because row and lower-column counts differ. This certificate does not identify the components with ideal-class orbits; the reported class-action explanation remains conjectural.

= Graph-update disposition
We checked the study directory and `docs/ecdlp-surfaces/` visual sources. This case adds a finite signed-incidence audit but does not certify new point-level graph edges or change the established transfer diagram. No canonical graph source or rendered figure is updated. The SVG below is a local evidence-flow schematic only; exact point edges are intentionally omitted.

= Evidence links
- #link("https://github.com/isogeny-labs/cryptanalysis/blob/95465ba76f5fe0d3e6ecf672c1e974c654e1ed0f/experiments/ecdlp-hecke-d39-holdout-20261026/RESULT.md")[RESULT.md] — scope, exploratory provenance, recorded results, and limitations.
- #link("https://github.com/isogeny-labs/cryptanalysis/blob/95465ba76f5fe0d3e6ecf672c1e974c654e1ed0f/experiments/ecdlp-hecke-d39-holdout-20261026/PROTOCOL.md")[PROTOCOL.md] — frozen parameters and prediction, published jointly with the result.
- #link("https://github.com/isogeny-labs/cryptanalysis/blob/95465ba76f5fe0d3e6ecf672c1e974c654e1ed0f/experiments/ecdlp-hecke-d39-holdout-20261026/matrix_audit.json")[matrix_audit.json] — row counts and rank checks; binds raw input SHA-256 `4bcc8eb1905a9ed79a47cc31820e722dc7a6ff87f18bb37aeebafa35e6cc6df9`.
- #link("https://github.com/isogeny-labs/cryptanalysis/blob/95465ba76f5fe0d3e6ecf672c1e974c654e1ed0f/experiments/ecdlp-hecke-d39-holdout-20261026/conductor_audit.json")[conductor_audit.json] — verified conductor census; binds the same raw input hash.
- #link("https://github.com/isogeny-labs/cryptanalysis/blob/95465ba76f5fe0d3e6ecf672c1e974c654e1ed0f/experiments/ecdlp-hecke-d39-holdout-20261026/graph_audit.json")[graph_audit.json] — signed incidence certificate; binds raw input and conductor audit hashes.
- #link("https://github.com/isogeny-labs/cryptanalysis/blob/95465ba76f5fe0d3e6ecf672c1e974c654e1ed0f/experiments/ecdlp-hecke-d39-holdout-20261026/class_order_audit.json")[class_order_audit.json] — checked order 12 for form (2, 1, 44) in discriminant −351; its connection to rational-lift components is still conjectural.
- #link("https://github.com/isogeny-labs/cryptanalysis/blob/95465ba76f5fe0d3e6ecf672c1e974c654e1ed0f/experiments/ecdlp-hecke-d39-holdout-20261026/launch.json")[launch.json] and #link("https://github.com/isogeny-labs/cryptanalysis/blob/95465ba76f5fe0d3e6ecf672c1e974c654e1ed0f/experiments/ecdlp-hecke-d39-holdout-20261026/runtime-info.json")[runtime-info.json] — original launch receipt and runtime facts.

#v(4pt)
#text(size: 8pt, fill: rgb("425b72"))[All numerical values above are transcribed from the linked JSON records; no values were newly measured or recomputed for this report. The source data and prior result records remain unchanged.]
