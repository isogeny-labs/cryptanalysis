# Rational elliptic curve height-cover control

The checked Sage run constructs 13 rational metric centers from the frozen
point multipliers before coefficient enumeration. They cover all 27 ordered
coefficient triples for the curve and points below. The strict count
`13 × 1 < 27` supplies an exact finite-cover collision, with the relation
`P + 2P − 3P = O` checked directly. All 27 sums commute with reduction at
101, and the canonical-height quadratic identity meets the frozen residual
cap.

| Item | Frozen value or measured result |
| --- | --- |
| Curve and field | `E/Q: y² + y = x³ − x`, `[0,0,1,-1,0]`, discriminant 37 |
| Points | `P=(0,0)`, `2P=(1,0)`, `3P=(-1,-1)` |
| Input law | Full ordered cube `[-1,1]^3`, 27 triples |
| Metric | `sqrt(ĥ(Q−R))` on the generated subgroup; radius zero |
| Centers | `kP` for `−6 ≤ k ≤ 6`, fixed from `L Σ|m_i|` before enumeration |
| Rational torsion labels | 1 |
| Distinct sums and covered triples | 13 and 27 |
| Canonical height of `P` | `0.051111408239968840235886099756942021610` at 128-bit precision |
| Minimum positive center difference height | `0.051111408239968840235886099756942021610` |
| Height quadratic residual, v1 | `5.8774717541114375398436826861112283891e-39` |
| PARI/Sage height crosscheck residual, v1 | 0 |
| Reduction | Good at 101; 27 compatible sums; reduced point order 33 |

`protocol.json` and `result.json` retain the first frozen run. Its center list
was chosen from the observed sums. `protocol-v2.json` records the amendment:
the center interval is built only from the frozen multipliers `[1,2,3]` and
coefficient radius 1. `run_v2.py` constructs those points before coefficient
enumeration, then tests coverage. The v1 output remains available for its
height and reduction checks, while v2 is the constructive cover control.

The exact interval uses the rank-one identity
`a(P)+b(2P)+c(3P)=(a+2b+3c)P`; `|a+2b+3c|≤6` follows from
`|a|,|b|,|c|≤1`. This is a chosen dependent rational-point panel. The next
mathematical step is a center bound for the actual selected-lift family,
including its rank and torsion fibers, with the center construction fixed
before target sampling. The finite-cover structural implication is formalized
separately in the labelled metric-cover Lean module (PR #1565).

Reproduce from the repository root with the checked launcher:

```sh
./sage --runtime-info > experiments/xedni-rational-height-cover-20261115/sage-runtime-info-v2.json
./sage -python experiments/xedni-rational-height-cover-20261115/run_v2.py > experiments/xedni-rational-height-cover-20261115/result-v2.json 2> experiments/xedni-rational-height-cover-20261115/run-v2.stderr
python3 experiments/xedni-rational-height-cover-20261115/audit.py
```

The saved runtime receipt includes the accepted source and native binary
manifest. Both Sage runs exited zero with empty stderr. `audit.py` checks the
receipt hashes and independently enumerates the integer cube and center
interval; Sage checks the elliptic-curve identities, height and reduction.
