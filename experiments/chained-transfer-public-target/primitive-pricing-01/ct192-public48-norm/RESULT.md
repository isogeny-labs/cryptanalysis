# CT192 — source result and native measurement handoff

Date 2026-11-17 UTC. **[pcc:unverified]**. Work tracked in [PR #1735](https://github.com/isogeny-labs/cryptanalysis/pull/1735), stacked on [CT191 #1734](https://github.com/isogeny-labs/cryptanalysis/pull/1734).

## What changed

CT191 instrumented `N2_actual` on five CT126 scalar-generated nonexceptional forward operands. This derivative instead prepares **96 real pre-norm operands** from the 48 original public class packets × 2 physical transfer routes, covering both directions, all four cofactor sectors and the 8 exceptional/identity packets. A separately generated, exact-source guarded CT125 Rust library exposes the hidden `gamma(corrected_lift(...))` pre-norm point **without any known-scalar reconstruction**. Every operand is checked against the original CT125 route's `norm_point` and complete public target verification. The isolated binary replays complete original 21-counter route objects and canonical 19-word public outputs before recording timings.

The prospective warm comparator uses the exact CT125 `norm_point`, i.e. `descend_point(pmul(target.f,target.curve,P,2))`, including its existing counter bump, versus CT126's historical `padd(P,P)` proxy. The raw timing records have block, slot, treatment, repetition count, physical route, source/target, cofactor sector, exceptional scalar *label only*, setup time and RSS. Each sample is a four-slot ABBA/BAAB block; 4 warmup and 12 measured blocks, 64 repetitions per slot, planned **4,608 measured slots**. A/A, physical crossover and block-fixed-effect diagnostics remain distinct external requirements (CT189/CT190). This is still only primitive pricing, not a complete cold ECDLP solve.

No original CT125 core code, 48-vector JSON, CT172/CT189/CT190 source, CT126 measurements or 695/701 original corpus was modified. Only a new source derivative is materialized before a future admitted native build. The manifest references the same pinned crypto and generated source dependencies.

## Evidence available and validity

Source-only CI [run #44185526632](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44185526632), on code head `7945795b`, **passed** 11 Python tests normally and 11 with `-O`, including 48-vector hash/field checks and deliberate arithmetic, cohort, output, dependency and source-derivative mutations. The immediately previous [run #44185379268](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44185379268) **failed** because the first source guard mistakenly treated the Cargo *package name* as a dependency declaration; the guard was corrected without modifying Rust algorithm code or fixture. The added Rustfmt parser succeeded on both the generated library and driver in [run #44185689958](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44185689958), but that job failed because Cargo tried to resolve the *unavailable pinned sibling crypto checkout*. The source workflow now parses TOML without resolving dependencies; native Cargo typechecking remains unperformed. Cite the subsequent exact-head run separately before claiming complete source CI.

These test outcomes validate the **producer's source and fixture contract**, not compiled/native correctness. Their `[pcc:unverified]` standing remains unchanged. Actual native parity and timing numbers are **not available**. This code is not a verified new cryptanalytic technique and does not demonstrate lower solver cost.

## Reproduction / source-only

```sh
dir=experiments/chained-transfer-public-target/primitive-pricing-01/ct192-public48-norm
python3 -S "$dir/source_contract.py"
python3 -S "$dir/source_contract.py" --materialize
python3 -S -m unittest discover -s "$dir" -p test_source_contract.py -v
python3 -O -S -m unittest discover -s "$dir" -p test_source_contract.py -v
rustfmt --edition 2021 --emit stdout "$dir/derived/lib.rs" >/dev/null
rustfmt --edition 2021 --emit stdout "$dir/src/main.rs" >/dev/null
python3 -S -c 'import pathlib,sys,tomllib; tomllib.loads(pathlib.Path(sys.argv[1]).read_text())' "$dir/Cargo.toml"
```

**Not authorized for automatic execution:**

```sh
# Only AFTER independent owner/provider admission, original corpus custody,
# same-host controls, toolchain and dependency restoration, and budget checks:
# CT192_OWNER_ADMISSION_RECEIPT='<authenticated reference>' \
# cargo run --release --manifest-path "$dir/Cargo.toml" -- --run-admitted
```

This producer accepts an operator-provided admission reference; it cannot independently authenticate authorization. Do not interpret the environment variable as budget approval. Source-only `--plan` prints planned counts without constructing geometry. The authenticated full 695/701 raw corpus and native Rust compiled artifacts have not been recovered here.

## Interpretation and decisions

- **If** the true `N2_actual` timing exceeds CT126 `D_padd`, previous symbolic `min(C169,2C13)-D` headroom was optimistic by an unknown amount; reprice actual routes and full solves.
- **If** norm-price parity holds across all 16 direction×sector×identity classes, continue matched route and cold end-to-end comparison; it does not itself establish a single-target speedup.
- Any robust complete-cost disadvantage is a **negative result** to retain; switch to the next existing IC/transfer lead, not another synthetic speedup proxy.
- The source-prime model here is **p=223**, not the intended larger `2^31-1` source baseline or the frozen entire corpus. Scaling and independent same-target comparison remain separate proof/measurement obligations.

## Sources checked and non-overlap

[Root crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877) (merged); [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215); [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523); [CT172 native source](../ct172-replay/src/main.rs); [CT173 exact-operation audit](../CT173_NORM_POINT_PRICE_PATH_AUDIT.md); [CT189 randomized route collector #1729](https://github.com/isogeny-labs/cryptanalysis/pull/1729); [CT190 block control #1732](https://github.com/isogeny-labs/cryptanalysis/pull/1732); [CT191 exact norm arm #1734](https://github.com/isogeny-labs/cryptanalysis/pull/1734); [GPU IC crypto #4178](https://github.com/isogeny-labs/crypto/pull/4178). Research KB and autoresearcher lead-atlas CLI unavailable in this connector runtime; no novelty or broad negative claim.
