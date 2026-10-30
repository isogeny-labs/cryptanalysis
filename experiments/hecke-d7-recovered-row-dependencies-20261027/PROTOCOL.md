# Frozen exact-dependency test for recovered D=-7 Hecke rows

`inputs.json` fixes the six archived D=-7 class matrices and both
collector replay receipts by SHA-256. The target set consists of all
thirteen rows admitted by the multiplicity-aware collector at
conductors 42, 60, 70, 90, 150, and 210. Each target row is compared
with its own archived integer relation matrix. The question is whether
its unchanged exact rational rank has a direct row-span certificate.

For each conductor, select a deterministic independent archived-row
basis from column pivots of the matrix transpose modulo 1,000,000,007.
Check that this basis size equals the archived rational rank. Solve
the target row against that basis over `QQ`; store its nonzero rational
coefficients as integer numerators over one positive denominator.
Verify the full integer vector identity, including every zero column,
in a separate pure-Python script. Record coefficient support and size,
and preserve any unsolved target with explicit status. The certificates
explain the measured rank stability for the exact saved matrices;
the protocol does not infer a uniform class-action theorem.
