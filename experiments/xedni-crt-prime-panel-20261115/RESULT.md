# CRT xedni relation panel across six predetermined primes

The fixed two-point CRT curve-choice policy produced its two sign-related
rational relations over `F_47` and none over the other four eligible fields
in this predetermined panel. The p=47 arm exactly reproduces the earlier
fixed-target census. The base curve over `F_71` has largest prime-order
subgroup `r=3`, below the frozen minimum `r=5`, so its field record is
`subgroup_too_small` and has no target scan.

| Base prime `p` | `#E(F_p)` | Subgroup `r` | Target queries | Admissible pairs | CRT accepted | Accepted reduced relations | Rational relations | Coefficient probes at 7 and 11 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 47 | 43 | 43 | 1,849 | 1,722 | 1,344 | 34 | 2 | 308,314 |
| 59 | 60 | 5 | 25 | 12 | 8 | 4 | 0 | 1,092 |
| 71 | 81 | 3 | — | — | — | — | — | — |
| 83 | 88 | 11 | 121 | 90 | 64 | 8 | 0 | 15,674 |
| 101 | 106 | 53 | 2,809 | 2,652 | 2,072 | 44 | 0 | 482,190 |
| 127 | 114 | 19 | 361 | 306 | 216 | 14 | 0 | 44,722 |

The experiment freezes the six primes, the common curve
`y²=x³−x−2`, and the subgroup rule before running. For each field it chooses
the largest prime factor `r` of the group order and the lexicographically
first eligible cofactor multiple as `G`. The public fixture is `Q=17G` when
`r>17`, otherwise `Q=G`. It enumerates all ordered `t₁,t₂∈[0,r)` and sets
`Pᵢ=Q−tᵢG`. The coefficient search and auxiliary orders at 7 and 11 are
identical across fields. All statuses, including identity, duplicate,
same-`x`, and failed auxiliary searches, are retained in deterministic
compressed JSONL shards.

`audit.py` independently enumerates every finite-field curve and subgroup,
reconstructs all sampled points and query statuses, repeats each auxiliary
coefficient search, and evaluates each candidate rational relation with
exact fractions. It checks all 5,165 saved queries, the p=47 reference
counts, source and runtime hashes, and all raw-row digests. The checked
Sage run and independent audit both exited zero with empty stderr. The
initial producer failure from calling `.factor()` on a Python integer and
the two audit-development failures remain in the saved failure records.

These are field-specific exact counts under the fixed policy. Subgroup
orders and target counts vary, so the rows do not form independent trials
from one common distribution. Candidate probes count inspected auxiliary
coefficient triples; they omit reduced-point generation, rational curve
assembly, relation checks, and startup. The panel is a correctness and
yield diagnostic, with no wall-time or asymptotic comparison. The next
experiment is a larger panel with a frozen subgroup-order band and a
declared resource cap, so zero-yield and censored fields can be compared
without selecting curves after observing relations.

From the repository root, rerun with the checked Sage launcher:

```sh
./sage --runtime-info > experiments/xedni-crt-prime-panel-20261115/sage-runtime-info.json
./sage -python experiments/xedni-crt-prime-panel-20261115/run.py > experiments/xedni-crt-prime-panel-20261115/result.json 2> experiments/xedni-crt-prime-panel-20261115/run.stderr
python3 experiments/xedni-crt-prime-panel-20261115/audit.py > experiments/xedni-crt-prime-panel-20261115/audit.json 2> experiments/xedni-crt-prime-panel-20261115/audit.stderr
```
