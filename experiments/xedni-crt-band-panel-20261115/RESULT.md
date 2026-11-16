# CRT xedni relation yield in a fixed subgroup-order band

The frozen subgroup-band panel reproduced the two sign-related rational
relations at `p=47`; its other seven fields produced zero rational
relations from 332 accepted reduced relations under the same deterministic
CRT policy. The fields were chosen as the first eight primes in `[43,499]`
whose largest subgroup prime `r` lies in `[43,80]`, using curve order alone
before examining any target relation. The selected primes are
`47,101,191,211,251,281,347,349`.

| Base prime `p` | `#E(F_p)` | Subgroup `r` | Target queries | CRT accepted | Accepted reduced relations | Rational relations | Coefficient probes at 7 and 11 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 47 | 43 | 43 | 1,849 | 1,344 | 34 | 2 | 308,314 |
| 101 | 106 | 53 | 2,809 | 2,072 | 44 | 0 | 482,190 |
| 191 | 212 | 53 | 2,809 | 2,096 | 40 | 0 | 506,986 |
| 211 | 237 | 79 | 6,241 | 4,648 | 60 | 0 | 1,117,054 |
| 251 | 244 | 61 | 3,721 | 2,664 | 50 | 0 | 676,358 |
| 281 | 292 | 73 | 5,329 | 3,928 | 46 | 0 | 946,022 |
| 347 | 329 | 47 | 2,209 | 1,608 | 38 | 0 | 394,458 |
| 349 | 355 | 71 | 5,041 | 3,736 | 54 | 0 | 851,452 |

The base curve is `y²=x³−x−2`. Each field uses the first eligible
cofactor-derived generator of its largest prime-order subgroup and public
fixture `Q=17G`. The run exhausts ordered `t₁,t₂∈[0,r)`, constructs
`Pᵢ=Q−tᵢG`, and applies the same 7/11 auxiliary orders, coefficient search,
CRT reconstruction, and rational relation check as the pinned parent panel.
The 40,000-query cap was frozen before field selection; the eight fields
required 30,008 queries. `selection.json` retains every prime and group
order screened until the eighth eligible field. Compressed raw shards retain
every target query and status.

The independent pure-Python audit recomputes the field selection, subgroup
generators, all target points, all 5,282,834 auxiliary coefficient probes,
and rational group relations for every accepted reduced event. It replayed
all 30,008 rows and reproduced the prior p=47 and p=101 counts, first-hit
records, and uncompressed row digests. The checked Sage run and audit exited
zero with empty stderr. `SEAL.sha256` pins the protocol, source, runtime,
selection, raw shards, results, and audit.

These are exact field-specific finite-panel counts. The selected subgroup
orders still range from 43 to 79, and relation events within each group are
correlated, so the zero rows do not establish an asymptotic probability or
a pooled independent-trial bound. Candidate probes omit target-point
generation, CRT assembly, rational group checks, and startup; this is an
operation-count diagnostic rather than a wall-time or rho comparison. The
next cost test needs a frozen larger subgroup band with resource caps and
full target-dependent phase timing on a calibrated host.

Reproduce from the repository root using the checked launcher:

```sh
./sage --runtime-info > experiments/xedni-crt-band-panel-20261115/sage-runtime-info.json
./sage -python experiments/xedni-crt-band-panel-20261115/run.py > experiments/xedni-crt-band-panel-20261115/result.json 2> experiments/xedni-crt-band-panel-20261115/run.stderr
python3 experiments/xedni-crt-band-panel-20261115/audit.py > experiments/xedni-crt-band-panel-20261115/audit.json 2> experiments/xedni-crt-band-panel-20261115/audit.stderr
```
