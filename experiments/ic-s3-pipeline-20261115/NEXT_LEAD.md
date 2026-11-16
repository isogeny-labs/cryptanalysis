# Next candidate: native affine S3 projection

This is a follow-up implementation lead, not a novelty or speed claim. The
existing experiments/pdp-degree-heuristics/htsolver.py implements odd-degree
half-trace projection and meters its Python/native boundary work. Its owning
candidate description is experiments/ic-bench/bench.py lines320–332. Courtois,
[On Splitting a Point with Summation Polynomials](https://eprint.iacr.org/2016/003.pdf),
section2, is the primary prior source for the Artin–Schreier rewriting. The
search excerpt confirms that scope; direct PDF access returned403 here.
No timing or theorem from that paper is transferred to this implementation.

The useful engineering hypothesis is a target-aware native oracle which avoids
building the generic Boolean equations altogether. A further implementation
scope is even extension degree, by using a fixed linear Artin–Schreier section
instead of the odd-degree half trace. Both cases require complete signed-point
lifting, all degeneracies, setup charges and the best current native controls.

Let z be a nonzero target abscissa, s=x+y in V, p=xy in V². The exact S3
identity gives (p/z)²+p/z=s²+b/z². For any fixed trace-one theta and a linear
section G with G(c)²+G(c)=c+Tr(c)theta, impose Tr(s)+Tr(b/z²)=0 and write
p=z(G(s²)+G(b/z²)+epsilon). Project p onto the complement of V² to obtain an
affine system in the basis coefficients of s and one epsilon bit. This is an
algebraic derivation to be checked, not a completed formal proof.

Potential savings to test: cache V² parity checks and G(v_i²) per base, share
one inverse of z per query, solve epsilon jointly instead of twice, enumerate
the residual affine space by Gray updates, and specialize prefix-subspace
membership to a bit mask. Solve X²+sX+p=0, check both roots lie in V and in the
actual signed base, and replay the group sum. Equal abscissae require the
square-root branch; z=0 needs an explicit complete fallback. Never label a
trace obstruction or an unliftable S3 solution a relation.

Native correctness must compare every target on small fields against complete
point-pair enumeration, including even degrees, degenerate bases, x=0, doubling,
and inverse/identity branches. Pipeline performance must use new frozen target
fixtures and immutable candidates, retaining all setup, failed queries and rho.
Counted field/linear operations and measured native time need separate scope;
do not double-charge lifted group additions or use partial XOR counts as the
complete oracle cost.

KB receipt: revision9141e386254340a9bdba3036f2bb706a, SQLite FTS ready. Four
queries covered exact/native half-trace, negative two-summand performance,
relation-collection baseline and general Artin–Schreier sections. The quoted
HalfTraceSolver search restricted to cryptanalysis returned no hits, while
current owning code was present and read; this is not evidence of absence.
Relevant context sources: source:928a7968d9568f3db68f9b272c48add7,
crypto-autoresearcher:ledger/proposals/IDEA-20260926-1db0e8.yaml (explicitly
classifies the Artin–Schreier reduction as classical), and
source:1ee3d510d5914c2f16a6bb31508af54b,
crypto:papers/ecdlp-index-calculus-treatise/sections/falldegree.tex (general
linear-section reformulation). Original current htsolver.py and candidate
wiring were read. Search rankings confer no proof or performance standing.

## Native prototype status,2026-11-15

[pcc:unverified] suite/src/cryptanalysis/s3_affine_projection.rs now implements
the prepared section, product-space parity checks, joint epsilon solve and
Gray enumeration. Producer tests cover: exhaustive nonzero-target checks
for degrees2..8, two basis forms, dimensions up to4 and three constants; and
explicit invalid-input/residual-cap checks including the63-bit boundary.
An additional dense-subspace differential check reaches degrees15/18/31/53/63.
Library clippy passes for the core. The latest native log records the exact
completed check count. Claim PCC-20261116-646058 records this unsigned component
result. No signed-point lifting, target-zero fallback, oracle registration,
IC integration or performance comparison is supplied by this prototype.

## Pipeline evidence guiding the next step

[pcc:unverified] The complete generic/direct panel has48 valid pairs. MITM is
the fastest tested pipeline on these exact bases; the constructor feature has
no algorithmic effect on that control. On N18, reference median table setup is
730056ns versus1172456.5ns median pipeline time. The algebraic methods remain
much slower despite constructor savings. Claims ed23f0 and the replay/bottleneck
claim record the unsigned observations; qualification remains null.

Next implement a complete signed-point adapter for the native core, including
explicit zero-abscissa handling and cap reporting. Measure target-independent
preparation and native query/lifting cost separately. A prefix inverse-square
cache with batch inversion is a candidate setup/query tradeoff: it could remove
the per-candidate inversions without building a quadratic-size pair table.
Compare cache off/on and the best tested MITM on new frozen targets; preserve
setup, all failed queries, relation/rank outcomes and same-target rho. No gain
for the native projection has yet been measured.

A second native specialization to compare after complete lifting works: solve
the projected affine system in column form (images plus coefficient witnesses),
avoiding per-query row transposition. For a polynomial prefix subspace with
2d-2<n, V² is the prefix through degree2d-2, so its quotient projection is a
word shift. Keep a generic parity-check fallback for other bases and verify
both against the current complete finite-field differential reference. This
optimization is planned, not measured or implemented.
