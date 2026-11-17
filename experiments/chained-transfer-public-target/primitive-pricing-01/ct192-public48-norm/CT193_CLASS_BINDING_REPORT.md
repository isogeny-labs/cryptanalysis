# CT193 — full-class binding audit and source amendment

Date 2026-11-17 UTC · [draft PR #1737](https://github.com/isogeny-labs/cryptanalysis/pull/1737), stacked on [CT192 #1735](https://github.com/isogeny-labs/cryptanalysis/pull/1735). Scientific standing: **[pcc:unverified]**.

## Mechanism and identified risk

The CT192 diagnostic reconstructs each true candidate pre-norm elliptic point from a public class, then checks the point only by recomputing its doubled/descent norm. The native route result separately passes `check_final`, but that does **not** establish `target_phi(to, candidate) == result.class`.

The deficiency is algebraic: doubling has a 2-torsion kernel. A concrete counterexample is `E(F_5): y^2=x^3-x`, `P=(2,1)`, `T=(0,0)`, `Q=P+T=(2,4)`. Here `2T=O`, `P!=Q` but `[2]P=[2]Q=(0,0)`. Therefore the doubled norm alone is not a unique binding to an elliptic point. The risk applies to CT192's validation contract; no actual CT192 native corruption, nor a distinct Jacobian image for these specific F5 points, is alleged.

CT193 keeps the original norm check and additionally enforces **`self.target_phi(to, operand)? == result.class`**, before the existing `check_final(&result)`. Both directions and both physical routes remain bound by the frozen public 48 case fixture and original complete 19-word/21-counter replay. The extra diagnostic target-phi call occurs only during the untimed preflight; CT192 resets its operation counters before each original native route replay.

## Implementation and tests

The change is confined to the CT192 *generated diagnostic derivative* at `source_contract.py`: original CT125 code Git blob `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc` and original frozen 48 public vector blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3` remain untouched. A new fail-closed validator inspects the generated Rust method and requires, in order, norm equality, complete target class equality, and the native final check.

Three additional source-only regressions (in the existing test file so the pinned workflow discovers them) check the injected class binding, reject norm-only / misordered validation, and independently calculate the F5 2-torsion double collision. Existing CT192 source tests remain in the suite, including frozen source/fixture guards and deliberate mutations. The prospective protocol was committed at `e7bc031d` before the implementation.

Reproduce source-only:
```bash
dir=experiments/chained-transfer-public-target/primitive-pricing-01/ct192-public48-norm
python3 -S "$dir/source_contract.py"
python3 -S "$dir/source_contract.py" --materialize
python3 -S -m unittest discover -s "$dir" -p test_source_contract.py -v
python3 -O -S -m unittest discover -s "$dir" -p test_source_contract.py -v
rustfmt --edition 2021 --emit stdout "$dir/derived/lib.rs" >/dev/null
```

**Validation boundary:** a passing source workflow establishes source-contract tests and Rust parsing, not native typechecking, 48-case native arithmetic, independent PCC, or a complete ECDLP solve. No real timings, paid compute, or signed verifier verdict was generated in this amendment. A native failure at any public packet must be preserved, not papered over.

## Exact next gate

Restore and independently authenticate original 695/701 custody and pinned sibling crypto source dependencies; then perform owner-admitted native typecheck and full 48 packet output/counter arithmetic parity, including this new class binding. Only after that run paired same-host `C169,C13a,C13b,N2_actual,D_padd` prices under CT189/190 sham/physical crossover/block fixed-effect controls. Complete cold single-target rho, BSGS, IC and transferred target solves, with initialization, geometry, inverse, transfer, relation collection, LA, recovery, verification, peak memory and uncertainty charged, remain the success gate. An absolute speedup claim requires signed independent PCC and `baseline/candidate > 1`.

## Sources checked

CT192 #1735; CT191 #1734; original CT125 `fixed-jacobian-chain-evaluator-02/derived/lib.rs`; crypto #3877 and #4215; CT189 #1729, CT190 #1732. Prior literature on group homomorphism kernels is elementary; this is a measurement-input validity correction, **not a novelty claim**. Research-KB service and original authenticated raw custody were not accessible in the connector environment.

**[pcc:unverified]**
