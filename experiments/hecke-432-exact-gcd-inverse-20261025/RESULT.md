# Exact polynomial gcd recovers rational B candidates at three complete primes

For a rational pair \((C,E)\), let \(P_B(C,T)\) be the exact degree-12
B-coordinate polynomial and let
\(F_E(T)=T^3-x_E T^2-64\) be the numerator of the degree-three
isogeny relation. The [gcd evaluator](gcd_inverse_sage.py) computes
\(g(T)=\gcd(P_B(C,T),F_E(T))\), lifts every rational root to
\(B:y^2=x^3-16\), and retains **all** B points mapping exactly to E.
It does not need the rational \(N/D\) branch to choose a root, so it
gives a defined candidate-set calculation at the branch's exceptional
inputs.

The complete rational \((C,E)\) screens at p=883, 887, and 997
contain **3,536 pairs**. The gcd algorithm returns exactly one
rational B point for each of the **3,528 verified source pairs** and
an empty candidate set for the eight extra p887 resolvent pairs.
Every returned B point equals the independently audited rational
branch output. At p887, eight of those valid pairs each represent two
level-432 kernel chains; both chains map to the same B candidate.

| Prime | Rational pairs | Linear gcd with one B candidate | Linear gcd with no B candidate | Quadratic gcd with no B candidate |
| ---: | ---: | ---: | ---: | ---: |
| 883 | 864 | 864 | 0 | 0 |
| 887 | 872 | 864 | 4 | 4 |
| 997 | 1800 | 1800 | 0 | 0 |

The four p887 pairs with \(E=(322,0)\) have
\(g(T)=T+81\), selecting \(x_B=806\), which does not lift to a
rational point of B. The four pairs where the prior rational branch
had numerator and denominator both zero have
\(g(T)=T^2+713T+567\). This quadratic has no root in
\(\mathbf F_{887}\). Thus the exact gcd calculation explains the
eight exceptional branch statuses by rational B-lift failure, without
discarding a source pair.

The [frozen protocol](protocol.json) hashes the exact P_B equation,
isogeny and branch formulas, and every pair shard from the preceding
source-free cross-prime screen. The checked-Sage producer records the
specialized P_B degree, monic gcd coefficients, rational gcd roots,
and full B candidate set in [result shards](result.json). Its
[runtime receipt](sage-runtime-info.txt) identifies the accepted
local build.

The separate [integer-polynomial audit](audit.py) reconstructs P_B
from its 89 integer terms, implements Euclidean and extended Euclidean
algorithms modulo each prime, and verifies **3,536 explicit Bézout
identities and both divisibility checks**. It independently scans
each gcd polynomial's rational roots, enumerates B y-coordinates,
checks the B equation and exact B-to-E map, and compares every
candidate set to the Sage producer and earlier source-free branch
receipt. The [audit receipt](audit.json) preserves all eight p887
exceptional pairs and zero mismatches.

A separate [double-fiber replay](double_b_audit.py), with its own
[frozen inputs](double_b_protocol.json), rebuilds the corrected p887
source-to-C/E join. Its [receipt](double_b_audit.json) lists all eight
double pairs, both source-chain keys for each, and the common B point.
Every one of the 872 corrected chains matches its pair's gcd candidate.

## Proof map

| Result | Proof or replay |
| --- | --- |
| Common roots of P_B and F_E equal roots of their gcd | Pinned Lean theorem `ExactGCDInverse.common_root_iff_gcd_root` proves the evaluation-level implication from explicit divisibility and Bézout identities and zero laws. It preserves all evaluation points and both directions. |
| Concrete gcd and Bézout identities at 3,536 pairs | Sage polynomial gcds and independent modular-integer extended Euclidean replay, including coefficient equality and divisibility, with hash-bound inputs. |
| Rational B candidates and agreement with source images | Exhaustive rational gcd-root and B-point lifting, exact isogeny checks, and comparison to the independently audited cross-prime source-pair sets. |

The [Lean build](formal/build-output.txt) passes; `#print axioms`
reports **no axioms** for the abstract root-equivalence theorem. The
[dependency record](formal/DEPENDENCIES.json) pins Lean/Std and states
the proof boundary. The concrete finite-field coefficients, Euclidean
traces, and modular source identifications are executable arithmetic
certificates here, not encoded as Lean polynomials. The generic
characteristic-zero modular statement relies on the previously
proved P_B identity; this experiment establishes the exact rational
candidate sets at its three declared primes.

Replay from the repository root:

~~~sh
./sage --runtime-info
./sage -python experiments/hecke-432-exact-gcd-inverse-20261025/gcd_inverse_sage.py
python3 experiments/hecke-432-exact-gcd-inverse-20261025/audit.py
python3 experiments/hecke-432-exact-gcd-inverse-20261025/double_b_audit.py
cd experiments/hecke-432-exact-gcd-inverse-20261025/formal && lean GCDRoot.lean
cd .. && shasum -a 256 -c SEAL.sha256
~~~

The next inverse step is to enumerate level-432 kernel-chain
preimages of each valid \((C,E,B)\) triple directly, preserving the
eight observed double source fibers. The gcd calculation supplies
the complete rational B candidate set for that step at the three
measured primes.
