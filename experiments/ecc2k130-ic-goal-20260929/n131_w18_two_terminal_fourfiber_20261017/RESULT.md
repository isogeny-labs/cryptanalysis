# Four raw fibers in the N131 two-terminal residual selector

The four-fiber selector expands the frozen W18 two-terminal source from one to four raw preimages of the same public subgroup point while keeping seven pair states free. It computes the exact residual `T_k - (P_i + P_j)` for each admissible terminal choice `(i,j)` and raw fiber `k`, then links a one-hot triple selector to the seven-pair source circuit. The resulting 8,320 residual rows and their source bindings were independently checked on the N131 curve. An unpinned N41 ordinary relation supplies a separate four-fiber group-law control. The frozen N131 public-point search reached its 600-second cap with status `BOUNDED_UNKNOWN`.

## Method and source bound

The field is `GF(2)[t]/(t^131+t^13+t^2+t+1)` and the curve is `y^2+xy=x^3+1`, `EC1N131Ckb1heb5f1998f20b`, with subgroup order `680564733841876926932320129493409985129` and cofactor four. The public workload is `cc09e7eb202a`. Four raw preimages differ by the four torsion offsets and project to its one public subgroup point. The W18 seed-212 pool has seven free pair rotations and two terminal rotations, 48 signed states in each terminal slot, 2,080 admissible distinct terminal sums, and 33,191 source codes per free pair. The source census gives a one-raw labeled-tuple mean ceiling of `0.554579433463`; summing the four individual ceilings gives `2.218317733852`. This is a ceiling on a source mean, not a success probability or an independence assertion.

The [protocol](protocol.json) froze the target, raw-fiber indices, source hashes, selector law, one worker, 590-second solver limit, 600-second target-dependent wall cap, and 4-GiB sampled combined-RSS cap before the public query. The circuit adds four raw selector bits and 8,320 active terminal/fiber conjunctions. It forbids 224 incompatible terminal pairs; the exact residual table has zero exceptional raw choices. `candidate_id` remains `null` because the complete IC pipeline is not specified.

## Controls and public query

| Check or measure | Recorded result |
| --- | ---: |
| N41 unpinned ordinary seven-pair relation split into five free and two terminal pairs | `PASS_UNPINNED_N41_FOURFIBER_SELECTOR_CONTROL` |
| N131 constructed assignment | 543,701 clauses and 220,947 native XOR rows all satisfied |
| Independently replayed constructed/public N131 residuals | 8,320 / 8,320 |
| Variables / AND gates / clauses / native XOR rows | 402,572 / 179,828 / 543,701 / 220,947 |
| Public ordinary XCNF SHA-256 | `dacb1f21dcc4fb4a1be6d43ef8661233e7830fd6b7c2734021fc57504982c7d6` |
| Public query solver terminal status | `BOUNDED_UNKNOWN`, `TARGET_DEPENDENT_TIMEOUT` |
| Target-dependent attempt / sampled peak combined RSS | 598.064997167 s / 704,937,984 B |
| Solver restart rows / terminal SAT or UNSAT status lines | 1,775 / 0 |

The exclusive target-dependent phases were residual generation **2.685211 s**, formula construction **3.483729 s**, serialization **0.036900 s**, solver launch/search/stop **591.858249 s**, and terminal parse **0.000908 s**. Their sum is **598.064997 s**. The solver's process exited `-9` after the parent-enforced timeout; the raw [stdout](solver.stdout.txt) and [stderr](solver.stderr.txt) are retained. The public XCNF is 20,488,321 bytes. The exact [public XCNF](ordinary.xcnf.gz) and [constructed XCNF](control.xcnf.gz) are saved as deterministic gzip archives; the terminal audit checks each decompressed length and SHA-256. The default CryptoMiniSat run selected zero Gaussian matrices from its large XOR components; 14 candidate components exceeded its matrix limits. This observation motivates a bounded matrix-setting or smaller-component experiment but does not rank the two without a paired replay.

The [N41 control receipt](n41_control_result.json) checks four raw points against the same subgroup point and identifies the raw fiber that leaves the archived five-free-pair sum. Checked Sage independently recomputed all [constructed residuals](control_sage_audit_result.json) and [public residuals](public_sage_audit_result.json), including reciprocal coordinates. The [terminal audit](audit_result.json) checks frozen source and result hashes, the formula hash, all phase costs, the cap, solver transcript, and status. Run the local checks with the repository launcher:

```sh
./sage --runtime-info
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w18_two_terminal_fourfiber_20261017/n41_control.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w18_two_terminal_fourfiber_20261017/audit_control_sage.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w18_two_terminal_fourfiber_20261017/audit_public_sage.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w18_two_terminal_fourfiber_20261017/audit.py
```

The selector's structural implication and coefficient identity are proved in [FourFiberSelector.lean](FourFiberSelector.lean), pinned to Lean 4.34.1. `lean FourFiberSelector.lean` passes and both `#print axioms` reports contain only `propext`; see [proof map](PROOF_MAP.md) and [build output](lean_check.log). The concrete emitted-CNF/curve bridge remains a computationally checked obligation.

The next experiment should use the saved public formula and a *frozen*, one-worker solver-configuration sweep that isolates Gaussian component activation and charges each full attempt. A prior seven-pair formula activated large matrices under raised limits and still returned `BOUNDED_UNKNOWN` at its cap, so the more valuable algorithmic follow-up is a target-derived partial-sum rejection rule that removes whole incompatible seven-pair families before search. Preserve the unpinned N41 gate, replay any N131 row independently, and keep censored runs as recorded.
