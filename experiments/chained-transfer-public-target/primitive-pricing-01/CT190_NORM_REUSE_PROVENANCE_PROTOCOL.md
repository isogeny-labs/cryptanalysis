# CT190 — prospective audit of the CT189 norm-reuse executable contract

2026-11-17 UTC · continuation of [cryptanalysis #1729](https://github.com/isogeny-labs/cryptanalysis/pull/1729) · [pcc:unverified]

## Exact question

CT189 calls its 21-counter fixture an "original" rather than norm-reuse counter
contract, and states a separate 22-counter derivative is not represented. Test
that claim against the **actual** default-branch Rust crates, frozen fixture and
Python producer/adjudicator before making another costly instrument.

Historical references to original 695/701 custody, original full populations,
CT126 prices and CT143 envelopes remain unchanged.

## Prospective source-only checks (NO native workloads)

1. Verify original evaluator file blob `8016634385d76207b23a3eb3a4dae9b0366ac68d`
   has 20 `Calls` fields and norm-reuse evaluator derived file blob
   `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc` has exactly 21, with
   exactly the additional `transported_norm_doubling` counter.
2. Verify `ct172-replay/Cargo.toml` depends on
   `chained-n4-fixed-jacobian-chain-norm-reuse`; `src/main.rs` imports
   that crate's `Runtime`, implements `--cold-route` for original two physical
   arms and checks `runtime.calls() == row[arm]`.
3. Verify the derived `Runtime::norm_point` executes actual
   `descend_point(curve::pmul(..., point, 2))` and increments that exact counter.
   Check `transfer_entry` and `retained_lift_entry` use this norm computation;
   do not claim the derivative was executed on this host.
4. Verify the original pinned 48-row *optimized* selected-call fixture
   Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`, all 48 row identities,
   all 21 counters in each route, and norm counts direct=1, retained=1,
   sequential=2. Check expected degree-169 and degree-13 counts separately.
5. Verify CT176 and CT179's checked fixture/schema and CT189's delegated native
   transport are consistent. Deliberately mutate counter, import, and fixture
   data in source-only tests. Produce only a source-code audit; do not infer
   actual compiler/linkage, executable identity, performance or cost.
6. Correct *prospective descriptions* in PR/report/ACTIVE, not the already
   frozen CT189 protocol, original evidence, or historical code. Keep explicit
   source-to-binary provenance and all 695/701, admission, measured N2_actual/D,
   full cold single-target solve, uncertainty, memory and PCC gates unresolved.

## Scope

One independently re-readable source consistency guard and report, Python
normal and optimized-mode tests. No git replacement of original data; no EKS,
Spot, paid capacity, lock bypass, protected merge or speculative advantage.
A `--executable-sha256` provided by the producer does **not** authenticate
its source tree or compiler; an authorized native build attestation is separate.

Sources checked: CT173_NORM_POINT_PRICE_PATH_AUDIT.md, CT172_SESSION_LOG.md,
original and derived Rust evaluators, CT175 cold-route source,
CT176/179 collectors/readers, frozen selected vectors, crypto #4215,
cryptanalysis #1523, GPU IC #4178, root crypto #3877 and live queue #3904.
Research KB server/wrapper unavailable in this connector runtime; no novelty
or negative literature claim is made. [pcc:unverified]
