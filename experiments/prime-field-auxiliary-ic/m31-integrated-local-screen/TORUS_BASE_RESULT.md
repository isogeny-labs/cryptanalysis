# Norm-one torus factor-base full M31 comparison

The pre-existing `FactorBase::torus` constructs x coordinates from a norm-one
torus trace fiber and then lifts them onto the same M31 elliptic curve. The
`m31-fast` command took the first 384 representatives from its complete
depth-10 fiber. This is a structured factor-base choice, not point transport
from an auxiliary elliptic curve or a quadratic twist. All arms used the same
integrated signed m2 pair-index solver at commit `48306253e`, with the
size-limited bitmap enabled for every 384-column base. [pcc:unverified]

## Pilot and full panel

The frozen pilot target 0, seed 0 solved under all three bases. Torus charged
CPU was 21.134 ms versus interval 36.393 ms and random 24.198 ms; torus
used 930,412 queries versus 1,816,655 interval queries. This passed the
protocol's 2x pilot admission gate but was only one target/seed.

The full panel then ran five previously published public targets × three
seeds × four arms: interval, torus, random and archived C++ rho. All 60
fresh-process arms solved, independently verified `[scalar]G=Q`, and exited
within the 20s deadline. No arm failed, was censored, or was replaced. The
separate `torus_base_analyze.py` reopened every local process report, checked
its CSV digest and public group equation, and reproduced the summaries below.
The fifteen cells reuse five independent public targets. [pcc:unverified]

| Base or solver | Median charged wall ms | Median charged CPU ms | Median base build ms | Median pair-index build ms | Median online ms | Median queries/steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Interval B384 | 30.149 | 29.668 | 0.099 | 3.061 | 22.103 | 1,483,386 |
| Torus B384 | 31.799 | 31.247 | 0.326 | 3.085 | 23.565 | 1,597,789 |
| Random B384 | 31.225 | 30.819 | 0.112 | 3.116 | 23.274 | 1,594,977 |
| Matched rho | 11.643 | 11.269 | — | — | — | 67,542 |

| Median paired numerator/torus ratio | Wall | Torus wall wins | CPU | Torus CPU wins |
| --- | ---: | ---: | ---: | ---: |
| Interval / torus | 0.9639 | 6/15 | 0.9467 | 6/15 |
| Random / torus | 0.9907 | 7/15 | 0.9949 | 7/15 |
| Rho / torus | 0.4125 | 1/15 | 0.4107 | 0/15 |

Target-level interval/torus CPU median ratios were 1.063, 0.867, 0.947,
0.895 and 1.026. The torus condition did not meet the predeclared
four-of-five-target criterion against interval, random or rho. Its pilot
advantage did not generalize to this panel. The pair table had 147,453
distinct signed x classes for torus, versus 147,450 for interval and 147,444
for random, consistent with similar pair-sum diversity at equal base size.
The panel does not isolate whether individual walk luck, useful-cycle
formation or base geometry caused each target's query-count variation.
It provides no evidence for a cold performance breakthrough from this
particular torus base and first-witness graph policy. [pcc:unverified]

## Timing, custody and launch correction

The charged wall and parent-plus-child CPU interval starts before each
process launch and ends after exit, parsing and public group-equation
verification. Basis generation, index construction, search, elimination,
certificate replay and teardown are included; compilation and frozen public
fixture loading are excluded. Arm order rotates within target/seed and block
order is frozen by `TORUS_BASE_PROTOCOL.md`. Host: shared Apple M4 Pro; OS
cache state and background load were not controlled. The IC binary SHA-256
was `e5f13b960f620e6aaae3c99ca17ee82963b4df981d89585688b8bbe9a35b4804`.

The first full launch stopped after two successful IC arms because the runner
attempted to parse rho's text stdout as JSON before reading rho's metrics
file. Its partial CSV is preserved as `torus-aborted-raw.csv`; it is excluded
from the full-panel statistics. The runner was corrected to parse JSON only
for IC, then the entire frozen 60-arm panel was run once. This was a runner
error, not a failed mathematical solve or a replacement of a censored arm.

SHA-256: full raw CSV
`0aee126e9380dfbdd932236d7a3bc217b2ae6a29fc7555d2752085debbb5d69a`,
pilot CSV `0e3062f47a5e3d3f976129fb4efe326c6f92e6a2b56c15273aa0c6393698d857`,
aborted partial CSV `c7dc695210a9a7cd83d5e4cf9e09dba62fdd0f57150f77d6700b6eab77593153`,
corrected runner `a0d52c5aa0c002f21453e5ccedc6bf5d6ae0107c02d4b5cc22e03a45869cabcb`,
analyzer `18ebe4db3abf292051306746f7322b035faa1531f93ff77155c816740b4eebbb`.
Per-process stdout, stderr and rho metrics remain local with their hashes
recorded in the raw CSV; they are not asserted independently archived.
