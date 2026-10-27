# A local Hecke commutator certifies twelve recovered D=-7 rows

The same one-step row identity gives exact archived-row certificates
for **all twelve** multiplicity-recovered degree-2 rows in the six
frozen D=-7 class matrices. Nine certificates use six archived rows;
three use eight. Every coefficient is an integer with denominator one.
The fixed selection rule succeeded on the four held-out conductors
42, 70, 150, and 210 after calibration on conductors 60 and 90. It
reduces these twelve certificates to **78 nonzero terms**, compared
with 276 terms for those targets in the Fricke-compressed basis-solve
bundle. The separate degree-7 row at conductor 42 retains its earlier
nine-row exact certificate.

Let `T_l(P)` be the complete Hecke neighbor multiset and
`R_l(P)=T_l(P)-a_l P` its relation row in the free integer module on
the frozen point set. At a source `S`, the tested identity is

```text
sum_{Q in T_l(S)} R_2(Q) - a_l R_2(S)
  = sum_{Q in T_2(S)} R_l(Q) - a_2 R_l(S).
```

Every neighbor is counted with multiplicity. This is the shifted
operator commutator when `T_2` and `T_l` commute. For a candidate
anchor, [run.py](run.py) checks the full integer vector equality,
complete in-class fibers, the classical modular polynomial, group
sums, and the availability of every row other than the selected
degree-2 target in the archived matrix. The nonzero target
coefficient then yields the saved certificate.

| Conductor | Target source → chosen anchor | Partner degree | Archived-row supports |
| ---: | --- | ---: | --- |
| 42 | 67→67, 88→88 | 3 | 6, 6 |
| 60 | 134→134, 145→145 | 3 | 6, 6 |
| 70 | 9→9, 216→216 | 5 | 8, 8 |
| 90 | 157→157, 311→84 | 3 | 6, 8 |
| 150 | 239→239, 524→524 | 3 | 6, 6 |
| 210 | 430→430, 721→721 | 3 | 6, 6 |

The [protocol](PROTOCOL.md) and [input manifest](inputs.json) fixed
all targets, inputs, discovery/holdout split, and the degree/source
search order before running the held-out cases. Each
`result_f*.json` retains the chosen anchor, first-step neighbor
multisets, expanded commutator terms, archived row indices, exact
certificate, and search counts. The [independent integer
validator](validate.py) reconstructs every displayed commutator from
the saved neighbor counts and trace values, checks all expanded terms
against the archived integer rows, and replays the twelve isolated
target identities column by column. It returned
`INDEPENDENT_LOCAL_COMMUTATOR_PASS`.

The [Lean proof map](formal/PROOF_MAP.json) links the abstract
commuting-operator identity to `HeckeCommutator.shifted_commutator`
and the nonzero-coefficient isolation step to
`HeckeCommutator.isolate_one_missing`. The pinned Lean module built,
and `#print axioms` lists only standard foundations; see
[formal/CHECK.md](formal/CHECK.md). The concrete point fibers,
operator commutation on each selected class, and archived-row
availability are checked by the finite receipts. This keeps the
abstract algebraic step and its concrete instance bridge explicit.

From the repository root, reproduce the empirical and proof checks:

```sh
./sage --runtime-info > experiments/hecke-d7-local-commutator-20261027/runtime-info.json
for f in 42 60 70 90 150 210; do
  ./sage -python experiments/hecke-d7-local-commutator-20261027/run.py --conductor "$f"
done
python3 experiments/hecke-d7-local-commutator-20261027/validate.py
cd experiments/hecke-d7-local-commutator-20261027/formal
lake build HeckeCommutator
```

The finite results show why these twelve missing rows are locally
redundant under the recorded complete-fiber conditions. The next
test is a newly selected class and conductor, frozen before row
production, to measure how often this local identity remains
available when repeated degree-2 fibers occur.
