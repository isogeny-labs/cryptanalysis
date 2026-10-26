# Exact conjugacy of the two degree-144 quartic presentations

The two relative quartics over the degree-36 field `L=K(s)`, `s²=2`, are exchanged by the exact automorphism `σ(s)=-s`, `σ|K=id`. The same coefficientwise identity holds for all three recorded Kummer radicands. Thus the two quartics represent conjugate presentations over `L`; their local splitting data pair under the corresponding permutation of primes of `L`.

The exact rational-vector audit checked all five quartic coefficients and all three radicands. A checked-Sage replay formed `σ(P)` from each prime ideal's generators and matched it to a unique prime over the same rational `p`. It verified `σ²(P)=P` and matched the left quartic's squarefree residue-factor degrees at `P` to the right quartic's degrees at `σ(P)` for all **26** base places at `p=13,17,19,29,37`. Four base places are fixed by `σ`; the other 22 participate in 11 pairs.

| Rational prime | Base places paired | Places fixed by `σ` | Relative pattern |
| ---: | ---: | ---: | --- |
| 13 | 2 | 2 | `[2,2]` |
| 17 | 2 | 0 | `[2,2]` |
| 19 | 18 | 0 | `[1,1,1,1]` |
| 29 | 2 | 0 | `[2,2]` |
| 37 | 2 | 2 | `[2,2]` |

`protocol.json` freezes the exact source hashes, primes, automorphism, and 300-second cap. `conjugacy_result.json` records the rational coefficient identities. `pairing_attempt.json` records a 12.094-second checked-Sage run; `prime_pairing_result.json` lists every prime permutation and matched pattern. `audit_result.json` checks source hashes, the prime involution, and the prior frozen observations. The Sage build is in `sage-runtime-info.txt`.

## Proof and formalization map

Write the ordered monic quartics as `g_L,g_R ∈ L[z]`. The serialized coefficients give `g_R=σ(g_L)` exactly, where `σ` acts coefficientwise. For each recorded radicand `Δ_i`, the coefficients likewise give `Δ_i^R=σ(Δ_i^L)`. Transporting the quotient presentation along `σ` maps the left roots to the right roots; transporting a prime `P` of `L` to `σ(P)` preserves residue polynomial factor degrees. Squarefree reduction at the selected places makes these degrees the local relative residue degrees. This pairs the sides at conjugate places; it does not assert equality at the same place when `σ(P)≠P`.

`ConjugateFactors.lean` checks two generic implications: `conjugate_factor_identity` transports a polynomial factor identity by a ring automorphism; `conjugate_ideal_membership` transports ideal membership. `lean-output.txt` contains successful compilation and `#print axioms`; only standard Lean foundations `propext`, `Classical.choice`, and `Quot.sound` appear. Toolchain `leanprover/lean4:v4.35.0-rc4`, mathlib4 revision `021c46bdd042f67b538b9f9871d556a93713a9a9`. The formalization is **partial**: the exact 36-dimensional field representation, large coefficient certificates, quotient-field isomorphism, and prime-residue factor-degree transport are not yet encoded as Lean declarations. The next formal step is the quotient-field/prime transport theorem, followed by importing the exact coefficients.

## Replay

From the repository root:

```sh
python3 experiments/hecke-432-j1728-quartic-conjugacy-20261026/conjugacy_audit.py
python3 experiments/hecke-432-j1728-quartic-conjugacy-20261026/pair_bounded.py
python3 experiments/hecke-432-j1728-quartic-conjugacy-20261026/audit.py
```

The bounded runner invokes `/Volumes/SSD990/cryptanalysis/sage -python`. The results are structural and exact; the recorded time is a local stage wall time.
