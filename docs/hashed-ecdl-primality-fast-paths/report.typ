#set page(paper: "a4", margin: 16mm)
#set text(font: "DejaVu Sans", size: 10pt)
#set heading(numbering: none)
= Exact primality setup: bounded tests and checked proofs
2026-10-30 · native development validation · no timing or challenge-solve claim

The ordinary >64-bit primality call previously selected AKS immediately.
The implementation now uses the published thirteen-base deterministic range,
automatically verifies bundled public ECCp-131 proofs, and attempts a bounded
Pocklington proof for other large candidates. Successful proofs are independently
replayed. AKS remains the exact fallback when no proof is produced.

#image("flow.svg", width: 95%)

*Correctness boundary.* The cutoff 3317044064679887385961981 is exclusive.
Passing witnesses above it never certifies primality. Factoring n-1 is bounded;
failure is inconclusive. Cached JSON parsing never bypasses the caller's proof
verification or resource limits. The original ECCp-131 input exercises automatic
verification; full relation search and the contraction crossover are unchanged.

*Sources.* Sorenson/Webster, arXiv:1509.00864, Theorem 1.1;
Handbook of Applied Cryptography, Chapter 4 Fact 4.40 and Chapter 3 Algorithm 3.9.
See README.md for links, commands, source identities, raw development records
and outstanding hard-factorization / admitted-measurement requirements.
