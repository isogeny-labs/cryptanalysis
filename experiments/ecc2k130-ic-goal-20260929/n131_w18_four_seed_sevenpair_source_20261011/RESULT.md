# Exact seven-pair four-seed support on the N131 challenge curve

Seven free W18 pair slots using affine seeds `212,213,214,215`, followed by
one of the frozen 32 signed terminal states, retain an exact
**2,138.64042535 labeled-tuple mean upper ceiling** per uniform public
subgroup point when all four raw preimages are available. This policy removes
one free pair slot and one three-point group link from the existing
eight-free-pair design. The ceiling counts source labels, not observed
ordinary-query decompositions; a smaller and independently checked circuit
is the next gate.

The curve is `y²+xy=x³+1` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, with subgroup order
`680564733841876926932320129493409985129` and curve ID
`EC1N131Ckb1heb5f1998f20b`. The seven free slots use rotations
`0,16,...,96`; the terminal pool is the 32-state pool frozen in the
[all-fiber protocol](../n131_w18_all_fibers_inverse_20261011/protocol.json).
The source census uses the same enumerated W18 rational-mask and folded-column
table as the [four-seed eight-slot census](../n41_n131_affine_four_seed_m16_20261011/support_result.json).

| Exact source measure | Seven free pairs plus terminal |
| --- | ---: |
| Per-seed usable unordered pairs | `33,191; 33,002; 32,776; 32,937` |
| Four-seed edges, each tied to its folded-column pair | **131,906** |
| Nontrivial graph components / maximum component vertices | **28,652 / 30** |
| Small components checked by direct edge-subset enumeration | **28,467** |
| Distinct-column ordered signed tuples over 32 terminal states | **363,870,812,965,469,266,543,693,485,099,729,137,172,480** |
| Four-fiber mean upper ceiling | **2,138.64042535** |

The [exact counter](count.py) models each eligible source pair as an edge
between its two signed-Frobenius folded columns. A set of seven free pairs
has distinct columns exactly when its seven edges form a matching after the
selected terminal state's two columns are removed. It counts matchings of
each graph component through degree seven, then multiplies by `7!` for slot
order and `4^7` for the signed choices. The final mean includes all 32
terminal states, four raw fibers, and division by the subgroup order.
The [Lean proof map](PROOF_MAP.md) records a checked theorem for the
distinct-column/matching equivalence and the remaining obligations for a
fully formalized numerical census.
The [result](result.json) retains all 32 terminal-conditioned counts, the
full matching polynomial through degree eight, source hashes, and the exact
rational ceiling. The counter also reconstructs the earlier fixed-seed
eight-pair graph and reproduces every saved terminal-conditioned matching
count from its independent prior receipt. These checks cover the combinatorial
count; the mean remains an upper ceiling because distinct labels can project
to the same group output.

The present one-seed eight-free-pair all-fiber ceiling is
`4,532.17557765`; the seven-pair four-seed source retains about 47.2% of
that labeled support while eliminating one free pair and one group link.
The planned circuit must bind each pair's affine seed, source rationality,
pair output, and terminal choice exactly, pass a complete constructed
assignment and independent checked-Sage group replay, then solve an unpinned
ordinary public point under a frozen resource cap. Only such a returned and
replayed relation advances the ordinary-yield and rank measurements.
This source-stage proposal has `candidate_id: null`.
