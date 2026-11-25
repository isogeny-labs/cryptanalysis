# Can a curve equation or coordinate system bring a recorded IC row to parity with rho? (2026-11-03)

**Kind.** Derived record. No new run. Every input number is copied from a
frozen record and cited by path and line in `RESULTS.md` and `data.json`.
**Verdict.** No recorded row reaches parity through a coordinate change
alone, under the lab's own pricing of the alternatives. The closest row
misses by 1% under the most generous reading, so the question is not closed
by a wide margin and the deciding measurement is named below.

## Why this record exists

On 2026-11-03 the owner asked whether the statement "a coordinate win cannot
move those rows into parity" had been established. It had not: it was an
inference in chat with no data behind it. This record is the derivation,
with its assumptions exposed, and the inventory of what the lab has measured
about coordinates and curve shapes.

## Method

A coordinate system or curve model changes the cost of each elliptic-curve
group operation and nothing else: relation yield, factor-base size, linear
algebra and descent counts are unchanged. If a fraction `f_g` of a row's IC
cost is group operations and a coordinate change makes each one `c` times
cheaper, the whole-row speedup is Amdahl's

    speedup(c) = 1 / ((1 - f_g) + f_g / c)

and parity with the recorded gap `g` needs `c* = f_g / (1/g - (1 - f_g))`,
unreachable when `1/g <= 1 - f_g`.

Two inputs are needed per row. The gap is on every frozen row. The share
`f_g` is recorded on one row only (`ic_group` 315 of `ic_total` 537 GAE on
the a1 n29 Frobenius-orbit arm). For the other rows the record uses the
envelope `f_g = 1`, the assumption most favourable to coordinates, under
which `c*` equals the gap itself.

The available `c` comes from the lab's pricing of the alternatives to its
shipping arithmetic, which is batched affine on every measured row (the
n41 to n61 baselines are even priced in units of one batched affine
addition). In `ecc2k130/LAMBDA-PROJECTIVE.md` the shipping batch-16 affine
update costs 38.1 carry-less lane instructions, the batch-infinity limit
36.3, and every projective form more (lambda-projective mixed 60.5, full
78.5). The explicit-formula operation counts in the lab's EFD import say the
same for prime and binary curves: affine addition is 2M 1S 1I against 7M 4S
for Jacobian mixed addition or 9M 5S for Lopez-Dahab, and with the inversion
batched over k >= 16 points affine stays cheapest. So the realistic factor
still available is the batch-depth limit, `c = 1.05`; the generous reading
takes the ALU-count ratio of 1.30 as if a coordinate change could win it
rather than lose it.

## Result

See `RESULTS.md` for the full table and `bound.svg` for the figure. In
short:

| row | gap | f_g | c* for parity | available c |
|---|---:|---:|---:|---:|
| a1 n29 Frobenius orbit (measured f_g) | 1.566 | 0.587 | 2.61 | 1.05 to 1.30 |
| n41 disjoint cold panel | 1.314 | envelope 1 | 1.31 | 1.05 to 1.30 |
| p36 prime res2 | 2.59 | envelope 1 | 2.59 | 1.05 to 1.30 |
| n83 rank-finder (wall) | 3.92 | envelope 1 | 3.92 | 1.05 to 1.30 |
| rule v8 n47 | 4.67 | envelope 1 | 4.67 | 1.05 to 1.30 |
| baselines n41, n53, n61 | 7.66, 13.2, 21.0 | envelope 1 | same as gap | 1.05 to 1.30 |
| tournament round 0026 n19a0 | 11.5 | envelope 1 | 11.5 | 1.05 to 1.30 |

Every required factor sits above the available one. The n41 cold panel is
the exception that keeps the question alive: it needs 1.314 against a
generous 1.30, a 1% margin, and that row's true `f_g` is unrecorded.

## What the lab has measured about coordinates and shapes

The inventory is in `RESULTS.md`. In one line each: the only controlled
coordinate arm against matched rho is the genus-2 weighted-projective state
versus its affine wrapper at 1.10 pooled, both arms 3.8 to 4.2 times behind
rho; the P-256 Jacobian seed ladder is 17.4 times faster per seed but is
setup only; the ECC2K-130 lambda-projective pricing favours affine by 1.59
and was never built; the Curve25519 Edwards and Montgomery factor-base
coordinates give F4 costs within 1% of the Weierstrass frame at k = 20 with
no DLP arm. No experiment in either repository has treated the coordinate
system of an elliptic-curve IC or rho run as the variable at the DLP level
with an A/A arm.

## Claim limits

- Derived, not measured. The envelope `f_g = 1` overstates what coordinates
  can do on eight of nine rows; the true shares are smaller (the n83 row's
  dominant cost is an index build, not group operations).
- The available `c` is an operation-count bound. Cache behaviour, batching
  depth and instruction mix on a given host can move it; that is exactly
  what catalogue idea H097 measures.
- The gaps are each record's own unit and reference; they are compared here
  only through the dimensionless ratio each record states.

## The measurement that decides it

H097 in `research/handbook-ff-ic-ideas-20261103/IDEAS.md`: batch-affine
versus projective candidate generation, binary and prime split, 10^7
additions per scheme with matched tables and seeds on isolab-eks, an A/A
arm, `perf-ipc` cycles. Its outcome replaces the `c` column above with a
measured number; the n41 panel row is where that number matters.

## Files

`data.json` (inputs with sources), `bound.py` (derivation and figure),
`RESULTS.md` (table, sources, inventory), `bound.svg`, `report.html`
(self-contained). `report.pdf` (6 pages, 83,891 bytes, sha256 `f23b43596f26daa36ae167180dc80b07d245a0467f4c4c9f1d7642f1609e84d0`) is built by `node render_pdf.js` from
`report.html` and is **not in Git**: the store policy assigns a PDF over 64 KiB
to the artifact store and this session's AWS token was rejected, so
`python3 tools/artifacts/artifacts.py push research/coordinate-leverage-bound-20261103/report.pdf`
is still to be run from a session holding the `ARTIFACTS_AWS_*` credentials.
