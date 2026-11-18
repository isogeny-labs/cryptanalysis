# CT189 — v3 physical A/B crossover cold-transfer producer and evidence reader

2026-11-17 UTC · [pcc:unverified] · [draft PR #1729](https://github.com/isogeny-labs/cryptanalysis/pull/1729)

## Source implementation and exact-scope checks

The new `ct189_native_physical_crossover_panel.py` imports the already merged CT188 randomized **physical** treatment roster instead of relabeling a fixed route. It preserves all 48 original literal Jacobian packets and 48 × 8 × 6 = **2,304 planned** fresh child positions, with 1,536 physically A/B treatment slots and 768 physical A/A controls. Ordered SHA-256: `1bc8c26a01e7952e57d944fd535c9832607f2ab7bcc910342ad704171ab67af1`. This is a plan, NOT 2,304 native measurements.

**Crucial boundary:** the CT189 cold-route child still uses CT175's **original 21-counter route contract**. It is not the 22-counter norm-point-reuse derivative, does not instrument a genuine `N2_actual` or `D` microprice, and cannot claim to have timed the optimized derivative. Native derivative compilation/parity and cost instrumentation must be treated as distinct admission gates. An optimized binary that emits a different counter schema must be **rejected**, not silently coerced to this frozen fixture. [pcc:unverified]

The runner is plan-only unless explicit execution/admission flags, owner/provider permission, a pinned native executable SHA256, positive child timeout and an aggregate wall budget are satisfied. On admitted execution only, it uses CT176's bounded child stdout/stderr capture and process-group termination, exact actual-arm argv, stable host/affinity comparison, crash/failure/censorship retention, and exclusive output creation. Physical B is never silently changed to a sham A. The offline reader validates the complete original 19-word and 21-counter native evidence, child base64/raw SHA256, wall-time nesting, exact host/executable/roster/terminal claims and memory reporting *before* calling CT188's conditional first-order carryover model. It refuses all legacy v1/v2/sham schemas as v3.

The prospective implementation contract was committed first at `bf4e5f10160a5b626a1a985ec03f5c125c0a1551`; source at `39d5bec127698e323443245bf49f00538571546b`; tests at `7768894c9303fcd42ac73f35d911c776dd33c139`. The source CI workflow was added at **`7a395ea9f2daf91f4815bf521c34e7f3241ac814`**. [Exact-head source workflow #44152752027](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44152752027), job 134285222236, completed **success** on that code/workflow SHA. Its decoded log shows **5/5 Python normal and 5/5 Python -O** tests passing, including a complete mocked 2,304-child producer→reader JSONL roundtrip, physical-arm argv fidelity, admission/budget/hash refusals, deliberately corrupted arm/argv/stdout/counter/native-time/terminal and truncation controls. All child transcripts were **synthetic mocks**; no Rust native executable or measured hardware cost was involved.

Reproduce in an exact-source repository checkout:

```sh
root=experiments/chained-transfer-public-target/primitive-pricing-01
python3 -S -m unittest discover -s "$root" -p 'test_ct189_native_physical_crossover_panel.py' -v
python3 -O -S -m unittest discover -s "$root" -p 'test_ct189_native_physical_crossover_panel.py' -v
python3 -S "$root/ct189_native_physical_crossover_panel.py" plan \
  --fixture experiments/chained-transfer-public-target/evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json
```

No execution command is given as authorized; owner/provider approval, native 48-case Rust parity and original full-corpus custody still need external checks.

## Scientific standing and next decision

This is **producer-origin source/synthetic validation [pcc:unverified]**, not independent signed PCC, physical native timing, a Jacobian ECDLP solver, or a measured improvement. In particular, the seven-term log-time model is conditional on its nuisance specification; observed route differences can still reflect higher-order/inter-packet carryover. A clean physical crossover is insufficient by itself to claim a complete solver speedup.

The highest-value next unit is the original 695/701 whole-corpus authentication and CT172 native full 48-packet parity on an admitted matched host, followed by native C169/C13a/C13b/N2_actual/D pricing and **complete cold single-target** source-prime transfers and log recovery against strongest optimized rho/BSGS/IC. Preserve negative/null costs, timing uncertainty, memory, setup, transfer, inversion, linear algebra and final public logarithm verification. Signed independent PCC and ordinary review/merge gates remain mandatory. No paid compute, protected merge, original fixture mutation or result promotion occurred.
