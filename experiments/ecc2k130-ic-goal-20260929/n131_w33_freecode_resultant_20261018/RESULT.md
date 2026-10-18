# N131 W33 free-code two-pair resultant preflight

An exact target-conditioned two-pair circuit now carries the N41
13-term resultant to the frozen `GF(2^131)` Koblitz instance. It keeps
both 32-bit source codes free, checks their curve-point validity through
inverse witnesses, and tests the resultant with five field multiplications.
The constructed positive's complete assignment satisfies all 46,073 CNF
clauses and 5,643 native XOR rows. The 600-second positive solve and a
300-second solve with the first source code fixed both ended
`BOUNDED_UNKNOWN` at their wall caps. The next solver gate is to recover
that known positive from free source bits within the same worker and memory
envelope, then attempt ordinary point decomposition.

## Frozen instance and method

| Item | Exact setting |
| --- | --- |
| Curve | `EC1N131Ckb1heb5f1998f20b`; `GF(2)[u]/(u^131+u^13+u^2+u+1)`, `y^2+xy=x^3+1` |
| Source | W33, seed mask `898618`, 32 free source bits, product-basis rank 32; distinct source codes |
| Pair rotations | 0 and 18 Frobenius steps |
| Constructed positive | `(5517532314023373700997554907490549211, 1154446546775871399813774752133352167830)`; known source codes 3 and 16722 |
| Frozen ordinary public point | `(877610862732227974378969808549299291499, 2063336771837286479337213121437715536874)` |
| Candidate identity | `candidate_id: null`; actual usable factor-base size and full relation pipeline unresolved |

For each source parameter `a`, the circuit enforces `Tr(a)=0`, an
inverse witness `v=1/(a(a+s))`, `Tr(av)=0`, and `Tr(sv)=0`, where
`s=898618<<1`. These conditions give both pair endpoints on the curve.
The 13-term bivariate resultant has bidegree `(4,4)` in the two still-free
source products. The exporter checks the symbolic remainder in the actual
N131 polynomial ring and checks the known pair products against the
resultant. The native XCNF then enforces it over field-bit arithmetic.

## Measured preflight

| Stage | Constructed positive | Frozen public point |
| --- | ---: | ---: |
| Formula | 15,225 AND; 21,194 variables; 46,073 CNF; 5,643 XOR | same counts |
| Formula size | 2,947,526 bytes | 2,944,913 bytes |
| Circuit build wall | 6.041 s | 4.246 s |
| Complete known-assignment check | 46,073 clauses and 5,643 XOR rows pass | not applicable |
| One-worker CryptoMiniSat 5.14.7 | `BOUNDED_UNKNOWN`, parent wall 600.067 s | gated, not run |
| Sampled peak solver RSS | 67,076,096 bytes | — |

The first-code-pinned positive adds 32 unit clauses, leaving the second
32-bit code and both 131-bit inverse witnesses free. It ended
`BOUNDED_UNKNOWN` at parent wall 300.049 s, sampled peak combined RSS
70,434,816 bytes. Both solver invocations had a 4 GiB RSS cap and one
worker; the solver stdout, stderr, exact commands, formula hashes, and
terminal classifications are in their JSON receipts. These are search
caps on a satisfiable constructed input, so neither run classifies the
ordinary public point.

The exporter took 0.426 s. The run used the checked repository Sage
launcher, with runtime receipts saved for export, build, and pinned solver
setup. Timings here are stage diagnostics on an ordinary host. There is no
IC candidate or single-target online comparison at this gate.

## Proof and replay

The generic quadratic norm and shared-root implication are the checked
Lean declarations `FreeCodeElimination.split_quadratic_norm` and
`FreeCodeElimination.eliminated_zero_iff_shared_root` in the
[N41 proof map](../n41_w11_freecode_resultant_20261018/PROOF_MAP.md).
Their hypotheses include the split first quadratic, Vieta identities,
nonzero leading coefficient, and exact linear remainder. The N131
remainder, source validity, resultant root, and bit-level circuit
assignment are checked computationally by frozen producer and replay;
the curve-level bridge to those generic Lean hypotheses remains open.

Run `python3 verify.py` in this directory to check all pinned source,
formula, protocol, and solver-output hashes and the recorded terminal
statuses. Regeneration uses the repository launcher:

```sh
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w33_freecode_resultant_20261018/export_sage.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w33_freecode_resultant_20261018/build_circuit.py 0
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w33_freecode_resultant_20261018/build_circuit.py 1
```

These producer scripts require absent output files, so regeneration
belongs in a fresh copy of this directory with the frozen protocol
paths updated and rehashed. Existing receipts are immutable evidence.
