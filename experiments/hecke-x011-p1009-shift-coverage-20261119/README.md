# Exact shift coverage of the prepared p1009 X011 fiber

The 84 logs derived from the certified relation lattice cover **every point of the order-1020 group within 49 additions** of `G=(2,155)`. The exact mean first-hit distance is `11189/1020`, about 10.97 additions. Two cyclic gaps between prepared logs have length 50, giving the maximum distance 49. The frozen public target `(75,527)` needs seven additions; 508 of the 1020 group points need seven or fewer.

`protocol.json` fixes the prepared-log and public-point hashes before enumeration. `run.py` computes the first-hit distance for each scalar `x=0..1019`, then checks the distribution against the independent cyclic-gap formula: for a gap of length `g`, its distances are `0..g-1` and contribute `g(g-1)/2` to the sum. The full 1020-entry distance vector, histogram, gap histogram, and digests are retained. `audit_sage.py` constructs the curve in the accepted Sage build and independently walks all 1020 points against the ordered 84-point fiber, checking every first hit and the cyclic-gap histogram.

| Quantity | Exact value |
| --- | ---: |
| Group points independently replayed | 1020 |
| Prepared fiber points | 84 |
| Direct hits | 84 |
| Longest cyclic gap | 50 |
| Worst first-hit shift | 49 |
| Mean first-hit shift | 11189/1020 |
| Frozen target shift | 7 |
| Points requiring at most seven shifts | 508/1020 |

This finite coverage result characterizes the prepared table's target movement. It uses the same relation-derived logs as the [one-target experiment](../hecke-x011-p1009-one-target-20261119/README.md); the earlier Lean `X011Target.shift_recovery` theorem proves log transport from a verified shift hit. The exact group walk and gap counts are computational certificates with independent Sage replay. Formalization of the concrete curve walk and finite histogram in Lean remains open.

## Reproduction

```sh
python3 experiments/hecke-x011-p1009-shift-coverage-20261119/run.py
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-p1009-shift-coverage-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p1009-shift-coverage-20261119/audit_sage.py
```

The run is an exact finite enumeration, not a CPU wall-time comparison. The next discriminating experiment is the same-point rho pair for the existing p20023 first-frontier table, with a frozen candidate manifest and benchmark envelope.
