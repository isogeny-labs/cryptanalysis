# Signed-pair orbit hash: frozen public M31 screen

## Question and construction

Can the sign involution of the factor base be combined with x-key hashing to
halve pair-table construction and storage without changing exact point-key
membership? The signed basis is `[B0,-B0,B1,-B1,...]`. The control computes
every `i <= j` pair and stores two first payloads per x in a 12-byte slot.
The candidate computes even-first rows only and stores one sign and pair
payload in an 8-byte slot per x. Opposite-sign lookup toggles the low bit of
both signed indices. Both use the same 512 KiB high-bit x bitmap, fused native
candidate scanner, Rust relation collector, elimination, and answer check.
The indexed 249,970/249,958 x keys occupy 4 MiB of candidate slots versus
6 MiB of control slots; both allocate the same bitmap.

## Proof and correctness

`OrbitHash.even_first_coverage` in `OrbitHash.lean` proves for any additive
structure obeying `-(a+b)=(-a)+(-b)` and any adjacent signed list satisfying
`signed(flip k)=-signed(k)` that each ordered full pair `i<=j` has an
even-first pair within bounds whose sum is equal or opposite. The exact
premises and quantifiers are in the Lean declaration. `lean OrbitHash.lean`
under pinned Lean 4.36.0 succeeded; `#print axioms` reported only `propext`
and `Quot.sound`. This theorem establishes row coverage conditional on the
group law. It does not refine the Rust or C++ code or prove a runtime bound.

Before each panel, the runner checked the *complete* sorted key sets of the
control and candidate on both frozen bases (1,000 point keys each), audited
every stored and reconstructed orbit payload by Rust curve addition, checked
the native scan against the Rust scan in the candidate, and compared first-hit
indices at every common walk state across full seed-0/1/2 or seed-3/4/5 solves.
The key digests are `669f5f3ac59dc1f4a017de4c5c3332c1f36c7f5fe77b66d011d87336651a4e7d`
(auxiliary) and `9c3827d3b408999d018a77c3272f1adea6b32030c7ed84f71bde8457d27c18b0`
(plain). All 192 timed arms returned scalar 123456789, checked against the
public generator and target; all 96 matched pairs agreed on basis digest,
entry count, trials, relations and answer. No timed arms failed or were
censored. [pcc:unverified]

## Complete charged timings

Each panel has 24 balanced-order pairs per basis, three seeds with eight
repeats each. The confirmation uses fresh seeds and a separately fixed order
seed. Wall and parent-plus-child CPU start before basis regeneration and end
after the fresh Rust process exits and its answer is parsed. They charge
table/bitmap setup, native scan, relation collection, elimination, and
generator verification. Compilation, frozen JSON loading, and OS cache
flushing are outside the timer. Ratios below are medians of *paired*
orbit/control ratios; they need not equal ratios of displayed medians.

| Panel | Basis | Control wall ms | Orbit wall ms | Paired wall ratio | Wall wins | Control CPU ms | Orbit CPU ms | Paired CPU ratio | CPU wins | Paired table ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| First | Auxiliary | 119.978 | 109.261 | 0.9144 | 20/24 | 114.961 | 104.437 | 0.9154 | 22/24 | 0.5394 |
| First | Plain | 94.802 | 87.798 | 0.9224 | 21/24 | 91.738 | 83.710 | 0.9115 | 22/24 | 0.5686 |
| Fresh seeds | Auxiliary | 87.209 | 81.852 | 0.9403 | 19/24 | 86.281 | 80.812 | 0.9433 | 19/24 | 0.5742 |
| Fresh seeds | Plain | 66.997 | 60.576 | 0.9075 | 22/24 | 66.006 | 58.748 | 0.9046 | 22/24 | 0.5466 |

Raw panels are `raw.csv` (SHA-256 `6bdfaa48612c280906a22b478da68565094f1fc0381aaabf2b081c6f9f2bdc23`)
and `confirm.csv` (SHA-256 `2edbb20db5e3d9298da0210908a7be0cdb81770a4b4365b4cddc68e87230fcb9`).
`analyze.py` validates paired identities and recomputes this table. The
protocols are `PROTOCOL.md` and `CONFIRM_PROTOCOL.md`. They were fixed locally
before the respective timing runs but published with the results, so this is
an exploratory producer panel rather than a pre-registered independent
confirmation. [pcc:unverified]

## Environment and decision

Apple M4 Pro, arm64 Darwin 27.2.0, Rust/cargo 1.93.1, Apple clang 21.0.0,
Python 3.13.1. Starting Git head `85395a80b`; candidate source `main.rs`
SHA-256 `b08876623e28e0cc58ac3df0599f9021f9c9f9e81a01332566bc2b952d4341c1`,
runner `replay.py` `7cd8b0cab1300bfde3d7b9b285b7e89ae7fdf38d0e2e220711d7f1c2aedb548c`,
native `m31.cpp` `6605965ea709bb8ed1c6b5ae1c9acf2389b0da7c45e6b5ba1cf0721a2d31d7cc`,
and `scan.cpp` `ddd19577d4c57741a290548d00a0daaafc6ce06cfc1491869ef6754761e42928`.
After measurement, the runner was changed only to pin its crate archive to
the measured `85395a80b` source because `main` advanced before publication.
The frozen fixture snapshot did not change across that rebase. This runner
change is outside the timed arms and is not part of the above source hash.
Run `M31_REPLAY_TMPDIR=/Volumes/SSD990 python3 replay.py > raw.csv`; for the
confirmation add `M31_SEEDS=3,4,5 M31_REPLAY_ORDER_SEED=2026112612` and
redirect to `confirm.csv`. The raw panels preserve phase timings and scanner
call/fallback counts. Native inverse and scanner tests ran before every panel.

The repeated local result supports a roughly 6–9% full-pipeline reduction
versus this fused-scan IC control on the two frozen public bases. The table
phase improves about 43–46%. The subsequent direct same-target cold comparison
in `RHO_RESULT.md` measured orbit/rho wall ratios of 6.809 auxiliary and
5.194 plain; the orbit path remains slower than that archived rho reference.
The IC/IC gain does not establish a rho crossover, a broad
target distribution result, x86/GPU performance, or novelty over existing
signed-point table representations. The next decisive comparison is a
second-host independent replay and a method change large enough to close the
remaining same-target gap. [pcc:unverified]
