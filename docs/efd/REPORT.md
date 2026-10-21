# EFD binary formula integration — 2026-10-21

Engineering implementation of established formulas. Requested destinations:
`aburan28/crypto` and `aburan28/cryptanalysis` (the latter's Rust suite).

Checkout baselines: `crypto` at `51e8742ae95e0c11aea10c7db7575b380225f2c7`,
`cryptanalysis` at `df69c0c3c35d6c30ad7f9b96e43c91b2be90b89e`.
The delivered EFD sources are pinned separately in `validation/source-sha256.txt`.

## Requirement-to-evidence record

| Requested capability | Status | Evidence and exact boundary |
| --- | --- | --- |
| Bring in the linked formula collection | Verified complete for the linked snapshot | 135/135 programs; original records, assumptions, source URLs and hashes in `binary_ecc/efd/catalogue.json` |
| Cover the different coordinate formats | Verified for finite charts | All 19 encode/project; full, X and W projections remain distinct; roundtrip and group-law checks |
| Execute the different mechanisms | Verified on bounded reference fixtures | ADD, DBL, TPL, DADD, LADD and SCALE all run through the native evaluator; 270 per-formula/per-field coverage rows |
| Interoperate with existing point arithmetic | Verified for full-point Weierstrass ADD/DBL | Checked adapters, explicit exceptional affine fallback, and independent existing-law comparisons |
| Put the work in both repositories | Verified locally; paired PR delivery | Identical core, catalogue, importer and tests; byte comparison script and source hash inventory |
| Make it inspectable and reproducible | Verified | Native importer replay reproduces the pinned catalogue; list/show/demo example; source-linked report and inspected PDF |

The original URL is specifically the binary-field EFD section. Prime-field
formulas, automatic curve-model conversion, optimized GPU kernels and changing
the production rho walk are outside this implementation. The imported formulas
are available for follow-up kernel and walk experiments; no performance result
or default-routing change is implied.

## Observed validation

The common source is tested separately against each repository's actual field
and curve modules. The focused native target compiles those existing modules in
place rather than copying or replacing their arithmetic.

| Check | crypto | cryptanalysis/suite |
| --- | --- | --- |
| EFD-specific tests | 8 passed | 8 passed |
| Native field/curve/EFD target | 48 passed, 1 existing ignored test | 36 passed, 1 existing ignored test |
| Successful formula/input comparisons over GF(2^4), GF(2^5) | 8,640 | 8,640 |
| Checked full-point ADD/DBL against existing affine law | Passed at `a2=0,1,z` | Passed at `a2=0,1,z` |
| Public known-scalar fixtures over 113-, 131-, 163-bit fields | Passed for applicable formulas | Passed for applicable formulas |
| Core/catalogue/importer byte parity | Passed | Passed |
| Importer replay | Exact catalogue match | Same pinned catalogue |
| Strict lint of native tooling and included EFD code | Passed | Passed |
| Current library EFD integration tests | 8 passed | 8 passed |
| Example test and demo/list/show commands | Passed | Passed |
| Broader library run | 4,471 passed, 119 ignored | 3,152 passed, 7 missing-fixture failures, 92 ignored; all affected tests passed after fixture materialization |

The per-formula records in `validation/coverage.json` retain attempted and
successful comparisons, excluded singular affine charts, and each field's
exact polynomial. Each formula has 32 successful comparisons in each field.
The expected optimized outputs are checked against the unoptimized affine
group law from the EFD model record. Full-point Weierstrass results receive an
additional independent check against the pre-existing library law.

The broad crypto run began before the final large-field regression test was
added; its runtime implementation is unchanged, and the current eight EFD tests
were then replayed through the actual library target. The initial cryptanalysis
failures were five missing `gpu/certicom` emulator-source checks and two missing
`challenges/ecc/catalog.json` checks. After materializing those tracked paths,
the complete six-test device group and both catalogue tests passed through
Cargo. The original failed broad run and successful targeted replays are kept;
a second complete cryptanalysis run was not performed.

Exception tests cover infinity, equal/opposite points, lambda's x=0 chart,
invalid points in the checked adapter, zero inversion, wrong field widths,
incorrect cached powers/parameters and mixed-input specialization violations.
All source records are hash-checked. These checks do not prove the formulas
universally. The upstream Sage proof scripts are linked but were not replayed;
no new mathematical theorem or Lean proof is claimed.

Commands, complete local execution status, source hashes and raw outputs are in
`validation/`. The environment was a Linux x86-64 cloud container on an exposed
AMD EPYC 9V74 CPU, Rust 1.99.1. This was correctness validation, with no hardware
isolation or timing claim. The two repositories have different field/curve
implementations and different numbers of existing unit tests.

## Source review and implementation decisions

The [README's source inventory](README.md#sources-checked) records the EFD
primary records and existing repository work checked before implementation.
In particular, `crypto:ecc2k130/LAMBDA-PROJECTIVE.md` already discusses lambda
coordinates and the invariant-selector problem. The implementation adds the
whole linked source collection and interoperable reference APIs; it makes no
novelty or speed claim and does not rewrite the earlier study.

Derived parameters are prepared from their recorded field equations and
verified when supplied. Point coordinates are never invented to satisfy a
missing mixed-input restriction. Coordinate-cache relations are checked before
the program runs. Model equations, model changes, quotient semantics and
differential-input relations stay explicit.

The complete binary catalogue has 41 addition, 47 doubling, 2 tripling,
16 differential-addition, 16 ladder and 13 scaling programs. The eight Edwards,
one Hessian and ten Weierstrass representations are listed in README.md.
This is a collection of reference straight-line arithmetic programs, not a JIT
or an optimized CUDA code generator.

## Failures and setup observations retained

The first local all-formula check used output index 4 for differential addition.
EFD uses index 5 (shared with the sum output of LADD); the test and API comments
were corrected, without changing any imported formula. The initial failed log
is retained as `validation/initial-native-failure.log`.

Initial broad-build attempts encountered off-disk fixtures in the sparse
checkouts. The source paths were materialized, rather than reported absent or
replaced. One cryptanalysis invocation was launched at the repository root
 instead of `suite/`; it was corrected. These setup attempts established no test
result. The native tool also needed the parent crates' existing two lint-policy
exceptions for the included legacy field/curve modules; the importer pointer
argument was fixed and strict lint then passed.

`conductor check` was attempted before edits, but the binary/control plane is
unavailable in this fresh environment. `crypto:docs/CONDUCTOR.md` documents the
installation-free, warning-only behavior; `.conductor/WORKFLOW.md` is not tracked.
No shared reservation or Conductor task is claimed. Work is isolated on a new
feature branch and primarily in the new EFD paths.

## Visual record and follow-up boundary

The [architecture source](architecture.dot), [SVG](architecture.svg),
[Typst source](report.typ) and [inspected PDF](report.pdf) accompany this record.
The existing `crypto:docs/index-calculus-scoreboard.html`,
`crypto:docs/ic/progress-timeline.json` and `crypto:docs/performance-gains/`
inventory were checked. They remain unchanged: this change supplies no new
performance observation, curve/isogeny edge, solver result or leaderboard value.

A subsequent optimization comparison needs complete-step timings, conversion
and parameter/cache maintenance costs, memory/register pressure, a compatible
walk selector and distinguished-point predicate, and the relevant batched-affine
reference. Those measurements and GPU/backend activation have not been done.
