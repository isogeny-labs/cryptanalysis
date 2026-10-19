# N131 W33 sign-norm transfer and direct-enumeration comparison

The N41 sign-norm certificate transfers to the exact N131 Koblitz curve and W33 five-pair source construction. Eight frozen boxes on one public target each contain 32 root choices and 32 sign choices. Each box has one common binary mask taking value one on all 32 sign products; together they certify 8,192 finite assignments. The constructed control retains its archived relation at root/sign `[0,27]` and has a zero sign product.

The field is `GF(2)[u]/(u^131+u^13+u^2+u+1)`, the curve is `y²+xy=x³+1`, and the exact curve ID is `EC1N131Ckb1heb5f1998f20b`. Each five-slot box uses two W33 codes per slot, 20 distinct folded source columns, and ten distinct output x coordinates separate from the target x. The public point and source-selection seed are fixed in `panel_protocol.json`; the complete panel is `panel.json`. The 64-code source pool was built under the 180 s/4 GiB one-worker cap. The positive and public runs were separately frozen, with the positive gate preceding the public run.

| Run | Status | Monitored parent wall | Sampled combined peak RSS | Relevant output |
| --- | --- | ---: | ---: | --- |
| Panel construction | COMPLETE | 14.058 s | 286,916,608 B | 9 exact boxes |
| Constructed control | COMPLETE | 9.791 s | 286,375,936 B | One relation at `[0,27]` |
| Public sign norm | COMPLETE | 27.115 s | 287,457,280 B | 8 certified boxes; 8,192 assignments |
| Independent Sage replay | COMPLETE | 13.059 s | 287,604,736 B | 55 source codes, 9,216 assignments, 288 products, 256 mask values |
| Direct public enumeration | COMPLETE | 5.632 s | 283,328,512 B | The same 8,192 assignments |

The direct-enumeration experiment isolates the practical issue: within its worker, the eight-box group-sum loop took 0.381 s. In the sign-norm worker, coefficient construction plus norm products took 7.593 s, a 19.915 ratio for those core stages. The sign-norm worker also spent 14.479 s on direct determinant and group audits; its full 27.115 s monitored wall includes that audit and startup. These are ordinary-host component diagnostics on frozen boxes, not isolated one-target IC timings. They show that this implementation creates a compact certificate at a higher cost than directly checking the enumerated assignments.

The independent replay reconstructs the W33 source points from the selected codes, checks subgroup and folded-column conditions, replays each group sum, multiplies every saved sign factor, and checks all public mask values. [The terminal verifier](verify_terminal.py) checks the frozen source hashes, receipts, counts, and the direct comparison. The terminal status is `PASS_N131_SIGN_NORM_TRANSFER_AND_BASELINE_AUDIT`.

The next algorithmic step is a constraint on code variables that rejects a family *before* its root tuples are generated. The current norm mask is computed after all 32 tuples in a box; increasing box size alone does not remove this cost. A useful follow-up should freeze a source-code family, derive an exact low-cost upper-level constraint, and measure rejected tuples per construction operation against the same direct enumeration baseline. `candidate_id: null` until a complete IC method is specified and measured.
