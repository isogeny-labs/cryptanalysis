# Exact N131 W18 ten-pair circuit and capped SAT gate

The ECC2K-130 W18 source now has an exact ten-pair, nine-link balanced
decomposition circuit with 20 distinct folded factor-base columns. A
deterministic constructed assignment satisfies all 886,526 CNF clauses and
319,282 native XOR rows. Checked Sage independently replays the ten signed
pair sums, all nine group additions, the cofactor-four public point, and its
subgroup membership. [Lean's checked tree theorem](PROOF_MAP.md) proves
that the circuit's group-sum topology equals the serial ten-point sum under
associativity and commutativity.

The exact curve is `y²+xy=x³+1` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, curve ID
`EC1N131Ckb1heb5f1998f20b`, subgroup order
`680564733841876926932320129493409985129`, and cofactor four. The
[frozen protocol](protocol.json) fixes ten W18 pair slots, 33,191 admissible
source codes per slot, the exact distinct-column shield, 524
raw-fiber/Frobenius target choices, a 120-second constructed SAT cap, and a
4-GiB combined RSS cap. The tenth slot repeats rotation zero while the
shield requires its two columns to be distinct from those of every other
slot. This is a constructed-point encoding and solver gate; the candidate
manifest remains unresolved (`candidate_id: null`).

| N131 circuit measure | Prior nine-pair balanced tree | Ten-pair tree |
| --- | ---: | ---: |
| Pair slots | 9 | 10 |
| Required distinct folded columns | 18 | 20 |
| Addition links | 8 | 9 |
| Addition dependency depth | 4 | 4 |
| Variables | 510,634 | 569,369 |
| AND gates | 221,160 | 247,026 |
| CNF clauses | 807,483 | 886,526 |
| Native XOR rows | 286,693 | 319,282 |

The ten-pair formula's uncompressed SHA-256 is
`e415ee585221156c79b0b5f1e63b1df658d6cfed726b3e565d55c6a654a36e45`.
Its deterministic gzip archive and byte replay are bound by
`archive_receipt.json`. The prior nine-pair counts come from its
[result](../n131_w18_ninepair_balanced_20261012/RESULT.md); these are
encoding-size measurements, not a solver-time comparison. The constructed
point and selected source masks are in `fixture.json`; the accepted Sage
runtime was saved in `sage_runtime_info.json` before its replay.

The frozen [solver protocol](solver_protocol.json) ran CryptoMiniSat 5.14.7
with one thread, `--maxtime=110`, and an outer 120-second cap. It parsed the
full native-XOR XCNF, entered search, and recorded 1,211 restart rows. Its
Gaussian setup rejected a 245,675 × 365,925 matrix as too large and disabled
that matrix. At 114.004 seconds exploratory wall time, with 526,172,160
bytes sampled combined peak RSS, it emitted `s INDETERMINATE`; stderr was
empty. The [independent audit](audit_result.json) rebuilt the formula byte
for byte, checked the solver binary and raw logs, and classifies this result
as `CENSORED_TIME`. The frozen runner's raw receipt says `SOLVER_ERROR`
because its terminal parser omitted `s INDETERMINATE`; its `restart_rows`
field also counts 764 diagnostic `c [` lines rather than the `c rst` rows.
That receipt is preserved as written and the audit records both corrections.

The added pair broadens the exact source support from 18 to 20 folded
columns at unchanged tree depth, while this bounded SAT path remains
censored even on its known construction. The next discriminating experiment
is an exact target-conditioned partial-sum filter ahead of the final tree
links: first replay the existing independently verified N41 ten-pair
relation through the filter, then measure N131 surviving candidate count,
index memory, and setup time under a frozen source. Advance to a fresh
ordinary N131 point only if that filter preserves completeness and fits the
resource envelope. A verified single-target online IC time and same-point
rho remain the later pipeline gates.

Reproduce the local checks with:

```sh
python3 experiments/ecc2k130-ic-goal-20260929/n131_w18_tenpair_balanced_20261012/verify_receipts.py
cd experiments/ecc2k130-ic-goal-20260929/n131_w18_tenpair_balanced_20261012 && lean BalancedTen.lean
```

The Sage audit and byte-for-byte formula replay are recorded in the frozen
receipts; their producers use exclusive output creation. Run those producers
in a fresh isolated copy when repeating the experiment.
