# Prospective cross-run comparison contract02

This operational contract is published before implementing the new cross-run verifier or running retry03. It follows preserved failure02; it does not convert that run into a passing CI result. Frozen scientific protocols3da7fe/abf432, original solvers, same-run auditors and both complete historical100/101-record fixtures remain unchanged. [pcc:unverified]

## Full records and strict comparison

Run each unchanged original auditor --freeze on the entire fresh native output, then --compare against that same-run frozen file. This requires literal equality of every raw record field, including all times and counters, and retains the complete raw/frozen/compared files. Run the separate new Rust historical verifier on the full published historical fixture and the full fresh frozen population. [pcc:unverified]

The historical verifier permits differences only in numeric nonnegative elapsed-time values at these exact record/report locations:

| Record kind | Report object | Permitted elapsed fields |
|---|---|---|
| N4_ORIGINAL_MODEL_IC_ATTEMPT | data.report | phases[i].wall and the second value of the single stats entry named wall_total |
| N4_ORIGINAL_FIXED_SAMPLER_ATTEMPT | data.original, data.candidate | phases[i].wall and the second value of the single stats entry named wall_total |

Each report must contain exactly the seven original phase names fb, relations, matrix, linear_algebra, log_recovery, descent, verify, in that order, with one numeric elapsed wall value per phase and exactly one well-formed wall_total statistic. Every other byte-represented JSON value, record kind/order/count, model/field/base-point/input/target/scalar/correctness/rejection value, parameter, seed, counter and non-time statistic must compare exactly. Extra fields remain compared; missing/malformed timing schema fails. This rule does not omit the seven descent counters used only by the distinct original-vs-assisted within-run comparison. [pcc:unverified]

## Controls and boundaries

Require an actual whole-input timing-only variation to pass the historical verifier. Require four whole-input modified controls to fail without accepted output: remove a complete record class; change a recovered scalar; change a primitive counter; add an unexpected report field. Preserve all whole modified inputs and actual subprocess outputs/exits. The existing fifteen entire-class same-run omission controls remain mandatory. [pcc:unverified]

The new comparator produces an unsigned equality receipt and hashes of both complete inputs; it never rewrites, replaces or truncates the historical or fresh scientific records. Failures outside the explicit elapsed-time contract stay failures. The CI driver must retain actual source/runtime/prepared-library custody, all original source guards and both original proof gates/bindings. A full CI result requires every declared phase and final original.exit0. Raw elapsed times remain available and unpriced. [pcc:unverified]

## Sources checked

Read the unchanged original IC/sampler Rust auditors, full failure02 inputs/output, independent Rust all-literal-differences result and existing paired-comparison protocol. The original auditor explicitly labels its equality assertion whole same-run records differ and does not normalize timing. The KB wrapper remains unavailable127; no novelty or absence claim is made. [pcc:unverified]
