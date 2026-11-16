# Native field-fiber identity admission

2026-11-15. Follow-up to [the field-fiber report](REPORT.md), source
`df1564ab593d14a5dd75bfc0b819f9eb27f1b21c`. Claim
`PCC-20261115-8cb342` records unsigned producer build/admission evidence;
`PCC-20261115-496600` binds the universal torus coefficient identity.
Both have unverified PCC standing. [pcc:unverified]

The missing-toolchain status in the earlier report is superseded: Lean 4.35.0
was installed, the pinned Mathlib dependencies were fetched, and all six
identity declarations compiled. Each printed only the standard foundations
`propext` and `Quot.sound`. The initial source record, commands and failed
attempts remain retained. No Rust arithmetic or performance result changes
in this follow-up. [pcc:unverified]

| Lean declaration in AuxiliaryIC.FieldFibers | Exact scope |
|---|---|
| opposite_pair | Product of the quadratic at opposite roots |
| cube_trace | Cubic power-sum recurrence |
| seventh_trace | Seventh-power sum recurrence |
| torus_push | Homogeneous coefficient update for x^2-2 |
| terminal_pair | Explicit product of the quadratic at two roots |
| orbit_discriminant | Discriminant identity for adjacent trace selection |

Every declaration is quantified over arbitrary commutative rings. These are
polynomial identities; none assumes division by the leading coefficient or
claims a complete finite-field/DLP construction. The [proof source](formal/FieldFibers.lean)
and [native receipt](formal-validation/producer-checks.json) pin the exact
statements, project, commands and raw outputs. [pcc:unverified]

The corpus gate now registers the exact identity source and its Lake
configuration through pinned checkers. Both admissions execute the native
project check; the configuration entry declares no mathematical theorems.
The identity entry requires exactly the six names above and their foundation
outputs. Source/checker changes, a missing/extra theorem, a nonstandard axiom
or a failed native command are rejected. Six synthetic-output refusal/plumbing
controls pass; the separate real native admissions also pass. Mocked outputs
are not proof evidence. Existing frozen corpus pins and checks are unchanged.
[pcc:unverified]

The metadata audit reports 194 Lean files, zero missing toolchain pins, all
14 existing receipt hashes matching, and no forbidden-token files. The
configuration's lack of local theorem printouts is informational: it is
compiled by the project checker and contains no theorems. [pcc:unverified]

Reproduce with `python3 formal/check_native.py` from this report's directory,
or use the source-bound corpus gate for the two registered files. The
project pins Lean 4.35.0, Mathlib revision
`cfc55fc58714a59dc06e6e79edc6d1d95140d3c2`, all transitive package revisions,
and both source/configuration hashes. Bootstrap requires the module argument
`Mathlib.Tactic.Ring`; the initial project-relative file argument failed and
its original log is retained. The first development checker was edited while
that failed process ran, so traceback source-line excerpts can reflect later
line positions; the final pinned checker was run separately and passed.
[pcc:unverified]

Generated native command captures were moved, without changing their bytes,
into `formal-validation/corpus-evidence/`; the old-to-new prefix mapping is
retained. The original source at `facaac33` remains in Git history; the only
identity-source edit changes a header comment from “axiom-audit” to
“foundation-audit” for compatibility with the admission filter. Statements
and proof terms are unchanged. [pcc:unverified]

The [existing pipeline diagram](pipeline.svg) remains current: these checks
add no curve/isogeny edge or transport. The corresponding flow is included
in the [PDF](FORMAL_ADMISSION.pdf).

Still open: formal cyclic norm-one group construction, primitive-trace
criterion, complete fibers, trace-orbit enumeration and the target-group
relation bridge. No full mathematical attack theorem, independently signed
verdict, fresh large-field recovery, runtime gain or advantage over rho is
established. Fresh performance work still requires checkpoint/runner access
and the admitted panel/accounting/replay protocol. [pcc:unverified]
