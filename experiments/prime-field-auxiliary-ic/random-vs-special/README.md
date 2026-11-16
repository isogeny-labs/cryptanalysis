# Three-arm random/special IC controls

Claim `PCC-20261116-8d7a97`, unverified standing. All results below are unsigned
producer assertions. This implementation adds the requested comparison;
it does not establish a runtime advantage. [pcc:unverified]

The three arms are special auxiliary-map IC, direct IC on exactly the same
special base, and ordinary IC on a separate random equal-column subgroup base.
The old same-base control remains useful for isolating the maps' contribution;
it is not relabeled as a random-base comparison. The full comparison and cost
requirements are in [COMPARISON.md](COMPARISON.md).

Current engineering follow-up: [exclusive core phase accounting and projective
scalar arithmetic](phase-projective-20261116/README.md), source `59524758`,
and [joint projective row validation](joint-row-20261116/README.md), source
`d95d582c`, retain separate unsigned receipts and claims `PCC-20261116-992167`
and `PCC-20261116-c1df99`. The later source has 32 core checks on each
toolchain and eight CLI checks passing. Phase accounting is implemented for
the core interval, while upstream/cold costs and independent replay remain
outside it. No fresh benchmark or runtime gain is established. Historical
observations below retain their original source scopes. [pcc:unverified]

Algorithm/CLI source `5e3a4202` adds `FactorBase::random_control`, separate base
and relation-search seeds, preparation rejection counters, and CLI
`--random-base-columns K`. It checks the generator order and derives the
cofactor only when the Hasse interval has a unique multiple of that order.
The cofactor must be coprime to the subgroup order. Coordinates are lifted,
cofactor cleared, negation folded and deduplicated. Unsupported certification
cases and exhausted draw budgets fail explicitly. No target is accepted by the
base constructor and no base logarithms are generated. Both requested-field
fixtures have checked usable random bases; the archived 61-bit example clears
cofactor 14,627,932. [pcc:unverified]

`PreparedSolver::relation_yield` and CLI `--relation-yield-only` reuse the full
solver's public target sampler but skip graph recovery and early stopping on
a solution. Completed prefixes have exactly the requested processed-query
count; unused generated lanes remain in a separate counter. Time/storage caps
remain incomplete results. Full certificate-producing solves are unchanged in
purpose and remain a separate comparison. No fixed-prefix stage timing can
stand in for end-to-end recovery cost. [pcc:unverified]

| Local check on source `5e3a4202` | Producer outcome |
| --- | --- |
| Core stable | 25 checks including one doctest pass |
| Core Rust 1.78 | The same 25 checks including one doctest pass |
| Targeted CLI | Six checks pass |
| Formatting, strict core/CLI lint and rustdoc | Pass |

The toolchain and CLI scopes are separate. New controls check random-base
membership at both requested fields, exact small-subgroup coverage after
cofactor clearing, explicit preparation refusals, complete small-field query
panels against all signed sums, three-arm public scalar recovery, matched
fixed prefixes and capped/incomplete collection. Five new core checks and two
new CLI checks add to the existing suites. The old archived replay stays
labeled as replay. Commands, exit statuses, full logs and source hashes are in
[the scoped validator](evidence/comparison-validator.json) and
[the source record](evidence/source-and-checks.json). [pcc:unverified]

Source `76a941c2` separately adds the hosted `Auxiliary IC CLI comparison`
job. Existing stable/1.78 core and archived Python jobs remain unchanged.
That later workflow definition has not yet been established passing by these
local source checks. The workflow wiring check emits its existing nonfatal
Sage checkout note and exits zero; its raw output is retained. The snapshot's
exact tree and 2,473 files are unchanged. [pcc:unverified]

Additive hosted follow-up: on head `e24a3a3e`, both core jobs completed their
test suites and then failed strict rustdoc because a newly added bare
`[pcc:unverified]` marker was interpreted as an intra-doc link. Source
`a4976ed5` renders that same marker literally. Strict documentation generation
passes locally on stable and Rust 1.78, with all warning flags intact. Both
exact decoded failure logs are retained as compressed files in
[rustdoc-followup](rustdoc-followup/), along with source-scoped checks and
validator. Claim `PCC-20261116-76c3e0` is unverified. Earlier passing rustdoc
observations remain scoped to `5e3a4202`, before the later annotation; no
earlier receipt is rewritten. Current-head hosted qualification remains
separate. [pcc:unverified]

No fresh benchmark was launched. Actual base/target freeze, checkpoint upload,
admitted GPU/host, phase accounting, benchmark records and independent signed
replay remain outstanding. The existing GLV binding and CodeQL merge blockers
are separate from these comparison controls. Earlier evidence is retained.
[pcc:unverified]

## Additive report-alignment controls

Source `3ddc3238` adds `factor_base.columns_blake3` and the standard-library
`compare_reports.py` helper. The fingerprint identifies actual canonical
columns independently of the decomposition encoding or target. The helper
checks reported public inputs, source labels, binary identity, matching A/B
columns, base sizes, sampler/limits and lane/draw accounting. It retains
incomplete arms but refuses derived fractions on mismatched or censored
prefixes. Replay/full-solve modes, mixed arithmetic, malformed counters,
duplicate JSON keys and nonfinite constants are refused. Matching metadata
does not prove execution; no time ratio or qualified speedup is emitted.
Claim `PCC-20261116-f8615b` remains unverified. [pcc:unverified]

Seven targeted CLI checks and twelve checker test methods pass on that source,
along with strict CLI formatting/lint, strict stable/1.78 documentation and
workflow wiring. The CLI fixture exports its three actual public reports;
the helper accepts them on identical 129-query prefixes at **p=127**. This
existing correctness fixture is not a new 31/61-bit research panel. CI now
exercises both the Rust-to-checker hand-off and the synthetic refusal cases.
The [scoped validator](alignment-evidence/alignment-validator.json), source
pins and complete logs are retained. [pcc:unverified]

The first negative-test fixture shortened its query count while retaining
larger circuit/hit counters. The checker correctly rejected it earlier than
the test's expected diagnostic. The exact failed fixture and failing output
are retained; its counters were corrected and every guard kept. This was
pre-commit development, not a fully pinned research execution. The admission
presence probe read no credential bytes and attempted no upload/allocation;
it found no local checkpoint token or `nvidia-smi`. An admitted allocation,
frozen actual bases/targets, exclusive phase accounting and independent signed
replay remain outstanding. [pcc:unverified]
