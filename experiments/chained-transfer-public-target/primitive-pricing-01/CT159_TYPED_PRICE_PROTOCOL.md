# CT159 — Typed CT126 primitive-price evidence protocol

2026-11-16. Frozen **before the CT159 validator implementation**. Standing: [pcc:unverified]. Root crypto #3877; existing pricing PR cryptanalysis #1534; related CT128 on this branch and distinct CT157 695-record parity fix in #1533. No complete ECDLP or speedup claim.

## Target and observed fail-open mechanism

CT126 `check_pair.py` (Git blob `1caf31daadc71b30be45e8e8e46224c03c6650a2`) validates four ABBA raw primitive-pricing JSON reports. After CT128's removal of `assert`, it still compares all `identity_checks` with ordinary Python `==`. Thus a JSON public coordinate `1` can silently change to `true` or `1.0` across arms while equality succeeds; metadata `223` can become `223.0`; `scalar_fixture_only: 1` can become `1.0`. The reader uses default `json.loads`, admitting duplicate member names, NaN, Infinity and `1e999` decoded as infinity. These are evidence-integrity failures, **not** evidence that any actual native scientific run was altered.

## Acceptance criteria and modifications

1. Preserve all eight CT128 negative controls, five scalar fixtures, four ABBA arms, six primitive labels, timing/size bounds, A/A and report output shape, and original Rust/fixture/code hash guards. No native scientific source changes.
2. Require `type(v) is int` and exact value for source prime, subgroup order, full group order, fixture count, rounds, warmups and every public fixture scalar. Do not accept JSON `true` or `223.0` as integers.
3. Recursively compare public identity fields with identical Python JSON-node types (dict keys/values, list length/elements, ints, bools, finite floats, strings/null). Reject changes only hidden by Python coercive equality. Do not claim that cross-arm equality independently proves elliptic arithmetic.
4. Decode every raw input with a duplicate-key rejection hook, `parse_constant` rejection of nonstandard NaN/Infinity/-Infinity, and `parse_float` rejection of nonfinite large-exponent numbers. No permissive parser fallback.
5. Exercise CT128's eight original mutations plus at least four newly recognized typed-alias controls and four parser controls: duplicate key, NaN, Infinity, and overflowed 1e999. Run normal `python3 -S` and `python3 -O -S`, compare outputs byte-for-byte; a valid synthetic ABBA directory must still pass.
6. Source-only CI must validate the exact updated source under both Python modes. Hosted CI, local diagnostics and hashes remain [pcc:unverified] absent independent PCC signatures. Failures must remain failures.

## Prior art and scope

Existing separate CT157 `compare_norm_reuse.py` already guards exact typed equality and JSON constants for **whole 695-record parity**, but this does not protect the **CT126 primitive-timing auditor**. CT128 fixed a different `assert`-under-`-O` failure. See Python JSON documentation https://docs.python.org/3/library/json.html and RFC 8259 https://www.rfc-editor.org/rfc/rfc8259; source history in #1534/#1533; cost plan #4215 and source comparator #1589. Research-KB MCP/CLI unavailable; do not infer novelty or prior-art absence.

## Unchanged decisive performance requirement

This source integrity repair does not price actual C169/C13a/C13b/D. Approved same-host native execution, complete original/reuse 695/701 parity, matched optimized rho/BSGS/IC, all setup/transport/correction/LA/verification/RSS/uncertainty and signed PCC are still mandatory before claiming any single-target transfer advantage. CT141 owner/budget admission is not bypassed. No paid compute or protected merge is authorized by this protocol.
