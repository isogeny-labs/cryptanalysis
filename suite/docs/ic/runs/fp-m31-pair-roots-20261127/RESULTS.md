# M31 reusable pair-root index: local producer result

The frozen local panel completed 64 measured processes (32 matched
baseline/candidate and 32 candidate A/A), plus two warm-ups, with zero process
failures or timeouts. Every matched arm returned the same relation count and
canonical signed-term digest. These are producer-local observations, not an
independently admitted speedup or a new PCC claim. [pcc:unverified]

| Target | Arity | Baseline median cold | Candidate median cold | Ratio | Relation/digest parity |
|:--|--:|--:|--:|--:|:--|
| Q0 | 3 | 0.698518365 s | 0.0360002435 s | 19.4032x | 0 / 0, exact |
| Q0 | 4 | 33.916857560 s | 1.7775180505 s | 19.0810x | 27 / 2866247195168869544, exact |
| Q1 | 3 | 0.7246190185 s | 0.0402512755 s | 18.0024x | 0 / 0, exact |
| Q1 | 4 | 34.0867282395 s | 1.8075276210 s | 18.8582x | 26 / 8555810665033450451, exact |

The candidate A/A median ratios were 1.0761, 1.0317, 1.0100 and 1.0258 for
Q0/m3, Q0/m4, Q1/m3 and Q1/m4 respectively. The smallest matched effect
(18.0024x) is therefore much larger than the largest observed A/A order
effect (1.0761x). No uncertainty interval, independent execution proof or
isolation tier is assigned. [pcc:unverified]

The mechanism moves the target-independent signed two-point root set into a
lazy per-workspace hash index. m=3 and m=4 reuse it across all queries; m=2
does not build it. The index preserves the old canonical scan order and every
returned row is replayed in the target group. Existing exhaustive p=127,
p=8191 and full certificate tests pass on Rust 1.78 and stable in hosted CI.
[pcc:unverified]

Scope limits: the m=3 cells produced zero relations on these fixed prefixes,
so they measure failed root queries rather than useful relation throughput.
The m=4 cells produced 27 and 26 identical relations, but this panel stops at
decomposition and replay; it does not include full relation collection,
linear algebra, recovered public logarithm, matched rho, or signed independent
verification. The result is a measured stage acceleration, not yet a qualified
end-to-end IC improvement. [pcc:unverified]

Raw evidence is committed at `raw/panel.json` (SHA-256
`1844af5f9a6451ba06a6075d8d1be9a4b3cd5b8cc5cb543ec434fe81687dd8d8`)
and `raw/aa.json` (SHA-256
`2e26a7a5f093fcd0c2a7eb63a9dad483f4938e8dff3507002341e1f94412ed91`).
The exact release binary hashes, commands, per-process wall/cold/setup/online
times, stdout, stderr, relation counts and digests are inside those files.
[pcc:unverified]
