# A one-step mixed-degree identity links the rank-raising repaired rows

At D=-7, conductor 14 over F_347, the previously unavailable one-step commutator at anchor 25 gives an exact integer identity between the repaired degree-2 row at source 25, the repaired degree-7 row at source 11, and eight archived rows. With `R_l(s)` denoting the complete multiplicity-aware row of degree `l` at source `s`, the identity is

```text
3 R_2(25) = R_7(11)
             - R_2(1) - R_2(9) - R_2(13) - R_2(17) - R_2(18)
             + 4 R_7(25) - R_2(28) - R_2(29).
```

All row indices in [result.json](result.json) refer to the frozen 32-column matrix; the eight archived row indices are `0, 4, 7, 10, 11, 13, 14, 15`. The scalar 3 is exact. The result explains the prior [boundary experiment](../hecke-commutator-boundary-20261027/RESULT.md): its source-25 search saw one nonzero-coefficient commutator but could not certify the target from archived rows alone because `R_7(11)` was also newly repaired.

| Added rows to the 17-row archive | Rational rank |
| --- | ---: |
| None | 17 |
| `R_2(10)` | 17 |
| `R_2(25)` | 18 |
| `R_7(11)` | 18 |
| `R_2(25)` and `R_7(11)` | 18 |
| All three repaired rows | 18 |

Thus `R_2(25)` and `R_7(11)` represent the same one-dimensional extension of the archived row span. The exact identity supplies an explicit bridge between them; it does not make either row a combination of archived rows alone.

The [protocol](PROTOCOL.md) and [input manifest](inputs.json) freeze the original and corrected matrices, collector, and preceding boundary result. [run.py](run.py) checks complete fibers, modular-polynomial roots, group sums, every commutator coordinate, and all eight subset ranks over the rationals. [verify.py](verify.py) independently recomputes the input hashes, corrected-row multiset, all subset ranks using `Fraction` elimination, the neighbor-multiset expansion, and the 32 integer coordinates. It returned `MIXED_DEGREE_WITNESS_PASS`.

The concrete coordinate identity is stated pointwise as `MixedDegreeWitness.exact_identity` in [formal/MixedDegreeWitness.lean](formal/MixedDegreeWitness.lean). Its proof checks each of the 32 coordinates in Lean with kernel evaluation. The pinned module built successfully, and `#print axioms` listed only standard foundations; see the [proof map](formal/PROOF_MAP.json) and [build check](formal/CHECK.md). The general shifted-operator identity is separately proved in [the preceding formalization](../hecke-d7-local-commutator-20261027/formal/HeckeCommutator.lean). The finite producer and independent replay connect that abstract identity to this particular class and the saved row encodings.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-mixed-degree-witness-20261027/sage-runtime-info.txt
./sage -python experiments/hecke-mixed-degree-witness-20261027/run.py
python3 experiments/hecke-mixed-degree-witness-20261027/verify.py
cd experiments/hecke-mixed-degree-witness-20261027/formal
lake build MixedDegreeWitness
```
