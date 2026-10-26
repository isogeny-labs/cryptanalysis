# The D=-39, f=6 relation matrix is stable under repeated-root recovery

The complete 64-point scan found no repeated rational roots in the degree-2 or degree-3 neighbor polynomials. The validated degree-2 multiplicity-aware routine therefore adds zero rows to the frozen D=-39, f=6 matrix, and its rank remains 40 over three separately replayed moduli. This closes a concrete producer-coverage concern for the exact class in [PR #1191](https://github.com/isogeny-labs/cryptanalysis/pull/1191).

| Degree | Rational-root multiplicity patterns over 64 source points | Complete rational fibers |
| ---: | --- | ---: |
| 2 | 32 with `[1]`; 32 with `[1,1,1]` | 32 |
| 3 | 48 with `[1]`; 16 with `[1,1,1,1]` | 16 |

The [protocol](PROTOCOL.md) fixed the source matrix and both kernel hashes before the scan. [scan.py](scan.py) reconstructs every saved point on `X_0(11)/F_367`, counts rational neighbor roots with multiplicity, and compares the original and multiplicity-aware complete degree-2 multisets point by point. Its recovery branch checks class membership, all three available y-moments, and the elliptic-curve group identity before admitting a row. It found zero differing multisets. Its sparse rank replay gives `40 -> 40` modulo 23, 1009, and 1000000007. The full [scan receipt](scan.json) preserves root-pattern counts, hashes, additions, and ranks.

The checked repository Sage launcher saved [runtime information](runtime-info.json) before the job. The [launch receipt](launch.json) records exit 0 under the 120-second cap, with [stdout](scan.stdout) and [stderr](scan.stderr) retained. The script compares the exact matrix committed in PR #1191 by SHA-256; that PR remains the source of the 64-point class and relation-stage result. This audit establishes coverage of repeated **rational** roots for this field and degree set; it does not assign a result to a different class or Hecke degree.
