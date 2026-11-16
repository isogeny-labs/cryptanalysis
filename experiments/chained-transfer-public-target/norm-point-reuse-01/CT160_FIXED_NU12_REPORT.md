# CT160 — exact independent census of the **actual** fixed nu12 q223 source and target

2026-11-16 — [pcc:unverified]. Preregistered [protocol](CT160_FIXED_NU12_CENSUS_PROTOCOL.md) published as commit 82da74f before running the full native-independent C++ experiment. This report is about source-specific finite-field point counts and an obstruction, **not** a complete ECDLP speedup.

## Important difference from CT158

CT158's explicit quadratic twist of the original E0 short model is NOT literally the fixed nu12 source. The actual fixed source is TwistedPair::construct's twist of ThirdHop::construct(c). This experiment uses *actual published coefficients and generators* from `experiments/chained-transfer-public-target/reports/twisted-pair-result-01/render-data.json`; the prior producer's report is only an **input** to check. The real native record source had SHA256 4ddfcba9151ee522988611a370161122d30109f77c26f39c34a58cfa386f0060; this run did not recapture that 20 MB native file.

Over K = F223[z]/(z^3-3), the actual fixed models are:
- source y^2=x^3+(167,76,41)x+(27,91,187);
- target y^2=x^3+(207,175,148)x+(175,89,34).
The public source/target generators are respectively ((55,126,141),(110,98,213)) and ((65,114,83),(100,34,29)).

## Reproduced exact field counts

A standalone C++17 implementation builds the full square-value roster for every one of 223^3=11,089,567 field values. It then classifies **every RHS** for both actual fixed models and the separately counted CT158 original short twist as a cross-control, without calling the Rust elliptic arithmetic.

| Independent curve | RHS zero | Nonzero square RHS | Nonsquare RHS | Full group order |
| --- | ---: | ---: | ---: | ---: |
| Actual fixed nu12 source | 3 | 5,543,420 | 5,546,144 | **11,086,844** |
| Actual fixed nu12 target | 3 | 5,543,420 | 5,546,144 | **11,086,844** |
| Explicit original E0 twist control (CT158 model) | 3 | 5,543,420 | 5,546,144 | **11,086,844** |
| Actual source with B[0] changed 27->28 | 1 | 5,544,780 | 5,544,786 | **11,089,562** |

The nominal count and mutated count completed locally in ~2.5 seconds each with ~12.4 MB maximum RSS for the process. This is an arithmetic census timing only, not cryptanalytic performance.

Separately written Python group arithmetic verified that z^3-3 is irreducible over F223, both actual curves are nonsingular, q=2,771,711 is prime by trial division, each published nonzero on-curve generator satisfies [q]G=O, and the only possible multiple of q in the Hasse interval [11,082,908,11,096,228] is 4q=11,086,844. Three changed-model/point controls rejected. Normal and -O Python produced byte-identical outputs. Thus the census and group-order certificates are separate implementations.

## New mathematical scope conclusion

For **the actual fixed source and target**, independently counted Frobenius trace over K is T = 223^3+1-11,086,844 = **+2724**, not just a conditional inference from CT158's separately twisted original.

The 59 Hasse-admissible integer prime-field traces t satisfy |t|<=floor(2 sqrt 223)=29. For each, the cubic-base-change trace is t^3-3*223*t. None equals +2724; the minimum absolute gap is **112**.

An F223-defined nonzero homomorphism from any elliptic A/F223 to the Weil restriction Res_{K/F223}(E_fixed) would induce a shared Frobenius factor: a root of x^2-tx+223 must also satisfy x^6-2724*x^3+223^3=0. Reduction modulo the quadratic polynomial forces t^3-669t=2724, contrary to the exhaustive 59-trace check. Hence this specific F223 elliptic-to-fixed-Weil-restriction Hom group is zero, using the standard Frobenius/Hom torsion-free argument. This **does not** rule out different finite fields, other target Jacobians, nonhomomorphic algorithms, or unknown alternative transfers.

Since the actual fixed source, actual fixed target and CT158 explicit original twist all have exactly the same order over K, the finite-field elliptic-curve isogeny theorem implies the **existence** of K-isogenies among them. It does NOT construct the isogeny needed by a DLP transfer, certify a degree-13 or degree-169 chain, or establish that the proposed degree-eight Jacobian quotient is F223-defined. This closes CT158's numerical source-order binding gap, not the explicit map or complete solver gate.

## Reproduction and raw evidence

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
c++ -std=c++17 -O3 -Wall -Wextra -Werror "$D/ct160_fixed_nu12_census.cpp" -o /tmp/ct160-census
/tmp/ct160-census > /tmp/ct160-whole.json
/tmp/ct160-census --mutate-source-B0 > /tmp/ct160-mutant.json
cmp /tmp/ct160-whole.json "$D/CT160_FULL_CENSUS.json"
cmp /tmp/ct160-mutant.json "$D/CT160_MUTANT_CENSUS.json"
python3 -B "$D/ct160_fixed_nu12_generator_audit.py" > /tmp/ct160-group.json
python3 -O -B "$D/ct160_fixed_nu12_generator_audit.py" > /tmp/ct160-group-opt.json
cmp /tmp/ct160-group.json /tmp/ct160-group-opt.json
cmp /tmp/ct160-group.json "$D/CT160_GENERATOR_AUDIT.json"
```

Local source SHA256 C++ 9005e1f77f7b3af785f8d1829d3d0cbd0a7451a2883b9a80c9f78f24e431de59; Python f9b8e6ea570190593ff1de8d30b05c91d02ca45c7f0cdd54a32625faad3b8551. Raw nominal 58af5c02d3a5afc722e1662e2fb5ade0534e65f824a29c97abc51dab827d08c8; mutant f9a892e908b0c8e4c11200f707ea23f9aa6ab00adf2d4500535a2fb9ccc3e9b1; Python certificate 42f0d3826ff899ed08867c70c77f540e980c8519e9b387c93a410d26d1e1aa2a. Local results are not signed PCC and hosted CI is separately checked; do not infer hosted pass from source publication.

## Program priority remains actual complete ECDLP

No entire original/reuse 695/701 Jacobian native records were independently replayed; same-host C169/C13_first/C13_second/D native pricing is still owner budget/admission-gated. Complete public prime-field ECDLP transferred solve against optimized rho/BSGS/IC including setup, correction, transport, linear algebra, verification, memory and paired uncertainty is still required. This negative result prunes only a specific same-characteristic F223 source bridge, and supplies no global cross-characteristic impossibility. No paid compute or protected merge launched.

References: CT151 Frobenius Hom certificate; CT152 original source census; CT158 explicit original twist census; primary actual twisted-pair Rust and fixed native render-data.json; classical Tate isogeny characterization. Research-KB not loaded here; checked these concrete primary sources and reports, no novelty claim.
