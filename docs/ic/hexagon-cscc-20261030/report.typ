#set page(paper: "a4", margin: 18mm)
#set text(size: 10pt)
#set heading(numbering: "1.")
#let c = json("catalog.json")
= Hexagon computational-complexity integration
2026-10-30 · isogeny-labs/crypto, with sibling integrations

This report records a source review and native software additions. It reports
no benchmark, new theorem, independently checked source proof, ECDLP result or
scientific state transition. The complete subject snapshot contains 22 works,
including cross-listings and the three current v2 records. All primary PDFs were
retrieved and hashed. Statements and relevant limitations were reviewed;
complete proofs and Lean developments were not independently rechecked.

#image("integration.svg", width: 100%)

== Executable work and scope
The native tensor library now provides exact divisor-prefix counting,
smallest-factor search and complete factorization, plus an exhaustive local-cost
profile reference. The counter is the existing OpenAI-based implementation,
whereas the Hexagon factoring note re-proves an Anthropic engine. This is an
implementation of the reduction, not its source-specific asymptotic proof.

The factor-base factory adds arbitrary bounded-order multiplicative cosets,
norm-one torus traces and Dickson images. Exact supplied-generator checks,
canonical coordinates, deduplication, subgroup filtering and archive replay
remain explicit. These recipes do not by themselves supply a faster PDP solver.

The native catalog checks complete snapshot coverage and retrieves source
claims together with their assumptions and implementation status. Finite
controls reproduce the Boolean three-generator and affine-union constructions;
they do not independently prove universal degree or asymptotic lower bounds.

== Remaining obligations
Independent formal/source audits, the general correctness and cost proof for
contraction, the Anthropic engine port, subexponential weighted contraction and
fast Subset Sum/3SUM implementations remain unperformed. Correctness tests do
not establish runtime improvements. Existing performance/frontier graphs receive
no new data. Full commands, observations and failed attempts are in VALIDATION.md;
the complete discussion is in README.md.

#pagebreak()
== Every source and its integration
#for p in c.papers [
  #block(breakable: false)[
  === #p.title
  #link(p.url)[#p.id] · #p.authors.join(", ")

  #p.learning

  *Scope:* #p.assumptions.join("; ").

  *Integration:* #p.status. #p.integration.join("; ")

  *Evidence:* #p.reported_evidence. Local formal verification: #p.local_formal_verification.

  #text(size: 8pt)[PDF SHA-256: #p.pdf_sha256]
  #v(4pt)
  ]
]
