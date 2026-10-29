#set page(paper: "a4", margin: 18mm)
#set text(size: 9.5pt)
#set par(justify: true)
= Native hashed ECDL: sampling and recursive audit
2026-10-29 · Development correctness; no performance or security claim

The six supplied approaches already have a native Rust implementation in
`crates/hashed-ecdl-tensor`: the relation reduction, exact Boolean counter and
deterministic witness finder, Fourier multiplier, exceptional point addition,
affine-hashed bases and source parameter guards. Its byte-identical mirror is
in cryptanalysis. This change adds the previously absent random sampling path
of Bochum Lemma 1 and strengthens forced recursive controls.

== Exact prefix sampling
For current count C and zero-prefix count C0, choose zero with probability
C0/C and one with probability (C-C0)/C. Forced branches use no entropy. Pins
condition the distribution. Empty languages return `None`; work and entropy
errors propagate. One initial contraction plus at most one per unpinned
interface bit suffices. Sampling is uniform over language words only for a
parsimonious encoding; otherwise auxiliary multiplicities determine weights.

#image("sampling.svg", width: 100%)

Two focused tests check every draw in a six-element equiprobable fixture,
the 1:2 projection weights, pinned and empty interfaces, empty languages,
entropy failure and zero work budget. These are exact distribution checks,
without statistical tolerances. Existing deterministic relation finding is
unchanged.

== Both taper levels
Existing forced controls used u=1 and odd Hermite nodes. The new control uses
u=2, a=2, L=4 and radix 2, two parallel edges and a degree-4 extension ring at
precision 3. Three label layouts and three predicate pairs give nine exact
comparisons with direct contraction. Valuations zero and one exercise different
coordinates, multiplicities and child precisions. Forced tests bypass source
admission: they do not verify admitted general recursion or its asymptotic cost.

== Cost interpretation
For the illustrative exponent E=b/m+mb/sqrt(log2(b)), minimizing in continuous
m gives m=(log2(b))^(1/4) and E=2b/(log2(b))^(1/4). Its exponent equals rho's
b/2 at log2(b)=256, or b=2^256 bits. At b=256, integer m=2 gives about 309.02
against rho's 128. These are illustrative derived exponents, not operation
measurements. Setting the constant to one after collapsing the expression
instead gives equality at log2(b)=16. Neither convention supplies an actual
cryptanalytic crossover.

== Evidence and limits
The starting native panel passed 27 tests. New focused controls pass; final
commands, outcomes and failures are in `validation.txt`. The full component
map, pinned primary-source links and remaining obligations are in `README.md`.
Primary review covered Bochum v0.2 §§2–3 and the October 25 OpenAI manuscript,
Appendix D.4.1–D.4.6, including immutable creation precision and tapered recovery.

Literal admission guards select finite-size fallback on practical networks.
General correctness, complexity and space accounting remain independently
unaudited. No benchmark, cloud experiment, deployed-curve run, new theorem or
Lean proof is claimed. No canonical IC/rho graph changes because no admitted
measurement changes. The canonical problem remains
`problems/hashed-ecdl-tensor-backend.md`.
