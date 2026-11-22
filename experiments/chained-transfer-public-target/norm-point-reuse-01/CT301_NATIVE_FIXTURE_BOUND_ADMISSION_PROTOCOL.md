# CT301 — bind native timing admission to the authentic frozen 48 vectors

**Preregistered 2026-11-21 before implementation. Standing: [pcc:unverified].** Child of [CT300 #1904](https://github.com/isogeny-labs/cryptanalysis/pull/1904), [CT299 #1899](https://github.com/isogeny-labs/cryptanalysis/pull/1899), and native-owner [CT244 #1871](https://github.com/isogeny-labs/cryptanalysis/pull/1871).

## Observed admission gap

The production `ct248_scoped_sample_audit.py --log ...` path checks exact 144 directed primitive calls, lifetime reconciliation, 48 ordered source-vector schemas, scalar schedule, each 19-word class-key width and all 21 selected route counters. It does **not** bind the values of the actual `input` and `whole_outputs_equal` class keys or unchanged nonprimitive call fields to the previously frozen 48 records. A same-shape changed key can therefore pass structural admission. CT300 independently authenticates the true fixture in a separate *mock-clock* source test, but the native `--log` path does not invoke that binding. This is an evidence-integrity weakness, not a demonstrated malicious native result.

Frozen record: `evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json`, Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`. The original archive uses the pre-CT125 counter name `transported_norm_doubling`; the native CT125/CT244 selected-vector schema names that *same count* `norm_point_doubling`. All class keys and other 20 counters must match exactly; no additional transformations are allowed.

## Acceptance contract

1. Require a `--fixture` argument whenever invoking production `--log`; missing/unreadable/wrong-blob original 48-row fixture is a hard failure, not an optional check. Synthetic `--self-test` does not assert native performance.
2. Check fixture bytes against the pinned Git blob *before* parsing. Normalize only the archived norm counter's name, rejecting unknown/missing/duplicate call fields. Keep exactly the original 48-row order, scalar/cofactor/direction, all 19 `u32` words per key and all 21 fields per route.
3. After existing structural auditor `audit(raw)` succeeds, compare the **entire** logged selected-vector envelope against the normalized pinned fixture using recursive exact type/value equality, not Python's bool/integer aliasing. Reject even shape-preserving class-key or nonprimitive-counter substitutions. No normalization of raw clock events, generator data or source values.
4. Source-only CI on the exact feature head must use the authentic immutable fixture and **explicitly synthetic** mock clocks. Positive: 144 synthetic samples plus original 48 rows accepted. Negative: a same-shape mutated `input`, a mutated `whole_outputs_equal`, a changed otherwise-unchecked call counter, altered fixture bytes, and missing `--fixture` rejected. Run in Python normal and `-O`; retain failed runs.
5. Preserve CT244 Rust producer, original 695/701 population, native signed fixture, ledger and prior source gates byte-identical. This change is *not* an independent arithmetic proof, native test, physical C169/C13/D pricing, cold source ECDLP benchmark, or signed PCC.

## Execution rule and stop conditions

Native operator (only after six-object artifact custody and normal budget/provider admission) must use:

```sh
root=experiments/chained-transfer-public-target
python3 -S "$root/norm-point-reuse-01/ct248_scoped_sample_audit.py" --log <unfiltered-native-stdout-stderr> --fixture "$root/evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json"
```

Any failure in original fixture identity, genuine vector parity, CT248/249 clocks, full original 695/701 source-model replay, or same-host complete cold solver validation **halts** admission. Source-level correctness is not evidence of a speedup. No unapproved EKS/Spot, credential substitution, force-push, ledger rechain or protected merge. [pcc:unverified]
