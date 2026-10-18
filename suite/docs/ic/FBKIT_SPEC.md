# `ca-ic fbkit`: the factor-base toolkit (design specification, frozen 2026-10-18)

> The user guide is [`FBKIT.md`](FBKIT.md); this file is the design record.

Status: specification for implementation. Everything below is normative for the
implementing agents unless marked *optional*. Paths are relative to `suite/`.
Owner decisions already taken: Rust, inside the `cryptanalysis_suite` crate,
exposed as `ca-ic fbkit ...` (hence `crax ic fbkit ...`), binary/Koblitz curves
first-class, prime-field curves via the existing framework base only, no new
crates (`deny.toml`), S3 through the `aws` CLI exactly as
`experiments/fb-archive/fbarchive.py` does.

## 0. Purpose

One command that, for a chosen curve, **sweeps factor-base constructions**
(every technique this project has tried plus new leads), **measures** each one
at a chosen summand count `m` in `2..=8` on construction, yield and downstream
solver metrics (F4 solving degree / degree reached, Macaulay sizes, SAT
variables/clauses/XORs/conflicts/decisions/propagations, folded columns, expected
trials), **ranks** them under an explicit objective with a Pareto front, writes a
reproducible run directory, and **uploads/downloads** run directories to/from S3.

Research-rules reminders that the implementation must respect
(`AGENTS.md`, "Index-calculus candidate names and measurements"):
`fb<B>` is the number of distinct nonidentity subgroup-usable points *before*
sign/Frobenius folding; effective columns is recorded separately; a stage
diagnostic is never a speedup; unknown is `null`, not 0; every report carries
`what_this_is` / `what_this_is_not`; nothing here is an `IC1` result (a cell
may carry a `PS1N...` label with `candidate_id: null`).

## 1. Command surface

```
ca-ic fbkit list      [--json]                         # technique registry with prior verdicts
ca-ic fbkit explain <family> [--json]                  # definition, parameters, citations
ca-ic fbkit build     <curve> --family F[:k=v,..] [--m 3] [--metrics construction] [--dir D]
ca-ic fbkit sweep     <curve> (--manifest FILE | --families a,b,c --dims 3-6 --m 2,3) \
                      [--metrics construction,yield,f4,sat] [--targets 8] [--seed S] \
                      [--budget-seconds 60] [--jobs N] [--dir D] [--resume] [--objective ...]
ca-ic fbkit rank      --dir D [--objective expected-ops|solving-degree|sat-clauses|sat-conflicts|columns|composite] [--top 10] [--weights k=v,..]
ca-ic fbkit export    --dir D --cell <cell-id> [--archive-out FILE]   # ic-factor-base-archive/1 document + PS1 label
ca-ic fbkit upload    --dir D [--s3 s3://bucket/prefix] [--dry-run] [--require]
ca-ic fbkit download  --s3 s3://bucket/prefix/<sweep-id> --dir D [--verify-only]
```

`<curve>` is a group of flags shared by `build` and `sweep` (one clap `Args`
struct `CurveArgs`): `--koblitz-degree N --curve-a {0,1}` (Koblitz `K_a /
GF(2^N)`, N odd, 5..=62 for measured metrics; up to 131 for construction-only
metrics where the builders allow), or `--char2-degree N --seed S [--max-cofactor
8]` (random binary curve via `ic_boundary::random_binary_instance`), or
`--curve NAME` for a named profile from `params::NAMES` (inspection and
construction-only metrics only; solver metrics are `not_applicable`). Prime
curves: `--bits B` via `ic_boundary::roster_prime_instance`; only the
`prime-abscissa` family applies; everything else is `not_applicable`.

Global `--json` and `--out` behave like every other `ca-ic` subcommand
(`run_from` in `cli/tools/ic/mod.rs`). Exit code 0 for `complete`, 1 otherwise.

## 2. Run directory layout (`--dir D`)

```
D/
  manifest.json          # frozen sweep manifest actually used (schema ic-fbkit-manifest/1), with sweep_id
  curve.json             # curve record + curve_id (EC1N<n>C<tag>h<12hex>) via canonical sha256
  cells/<cell-id>.json   # one per (family, params, m): recipe + metrics + status; written atomically
  points/<cell-id>.jsonl # optional point lists (sorted [x,y] hex) when --points is given or |F| <= 65536
  ranking.json           # output of rank (rewritten by `rank`)
  report.json            # the ca-ic report (house shape) of the last sweep/rank
  report.md              # markdown table
  receipts/upload-<utc>.json, receipts/download-<utc>.json
```

`sweep_id` = first 12 hex of sha256 over the canonical manifest without
`seed`-independent measurement fields; `cell-id` = `<family>-<params-slug>-m<m>-l<l>` plus 8 hex of the
canonical recipe digest. `--resume` skips cells whose file has `status` in
{complete, not_applicable} and re-runs others. Atomic writes: temp + `sync_all`
+ rename (copy `workflow::write_atomic`).

Canonical JSON for hashing: `serde_json::Value` with sorted keys (default
BTreeMap), compact, no floats (measurements are never in a hash input).
SHA-256 from `crate::hash::sha256::sha256`. The curve record follows
`experiments/pdp-degree-heuristics/toycurve.py` (`field`: characteristic, degree,
representation "polynomial_basis", modulus_exponents, element_encoding;
`curve`: model, a2, a6, order, trace, subgroup_order, cofactor, generator,
target_group) so that `curve_id` agrees with the Python tools for the same
curve. Add a unit test that pins one known curve_id computed by
`tools/curve_identity.py` (run it once with python3 -I and hard-code the value).

## 3. The technique registry (`fbkit::registry`)

Every family is a `Family` with `name`, `regime` (koblitz | binary | prime |
any), `kind` (subspace | koblitz-structured | torsion-symmetry | non-subspace |
selection | system-modifier | lead), `parameters` (name, type, default,
range), `definition` (one sentence of mathematics), `prior_verdict`
(free text, with the citing path), `status` (tried | proposed | new-lead).
`fbkit list` prints it. Families marked system-modifier do not change the point
set; they change how the decomposition system is built and are combined with a
base family through `modifiers=`.

### 3.1 Subspace shapes (binary and Koblitz; `V ⊂ F_{2^n}`, points with `x ∈ V`)
| name | definition | params |
|---|---|---|
| `coordinate` | `V=⟨1,z,…,z^{l-1}⟩` polynomial-basis window | `l` |
| `random` | uniformly random full-rank basis | `l, seed` |
| `geometric` | `c·⟨1,g,…,g^{l-1}⟩`, random `c,g` (attains Kneser `dim V^(2)=2l-1`) | `l, seed` |
| `gp-scaled` | `a·⟨1,z,…,z^{l-1}⟩` | `l, seed` |
| `gp-symmetric` | `⟨g^{-k},…,g^{k}⟩` inversion-closed (l odd) | `l, seed` |
| `gp-order` | ratio `g` of small multiplicative order `o` | `l, order, seed` |
| `frobenius-progression` | `⟨α,α^2,…,α^{2^{l-1}}⟩` | `l, seed` |
| `normal` | first `l` elements of a normal basis (when one exists; else not_applicable) | `l` |
| `subfield` | `F_{2^l}` (requires `l | n`) and `scaled-subfield` `α·F_{2^l}` | `l, seed` |
| `sparse-descent` (**new lead**) | basis vectors of Hamming weight ≤ `w` in the polynomial basis chosen to minimise the ANF term count of the Weil descent (greedy over weight classes, seeded) | `l, w, seed` |
Modifiers applicable to any subspace family: `trace_zero=1` (intersect with
`ker Tr`, dimension drops by ≤1), `shift=<hex>` or `shift=invariant` (affine
coset `V+c`, `affine_factor_base::frobenius_invariant_shifts` for Koblitz),
`two_torsion=1` (saturate `B ∪ 1/B`, `saturate_factor_base_two_torsion` for
Koblitz; for b=1 generic binary use `x ↦ √b/x`), `frobenius_union=1` (`∪_j σ^j V`,
`build_frobenius_union_factor_base`).

### 3.2 Koblitz-structured
| name | definition | params |
|---|---|---|
| `divisor` | `V_f = ker L_f`, `f | T^n−1`, by factor indices | `indices` |
| `frobenius-union` | union of Frobenius images of a seed subspace | `seed_dim, seed` |
| `explicit-orbits` | listed signed-orbit representatives | `reps` |
| `compact-orbit-scan` | first `K` cofactor-projected signed orbits of a raw-x scan | `K, start_x` |
| `greedy-coverage` | greedy orbit selection maximising exact `m`-coverage at equal columns | `K, pool, m` |
| `pruned` | parent base with orbits dropped while `(U+1)/p_m` falls (`greedy_prune`) | `parent` |
| `two-torsion-saturated` | parent `∪ 1/parent` | `parent` |
| `subgroup-orbits` | `build_subgroup_orbit_factor_base` seed/points | `seed, points` |
| `cyclotomic` | `{Σ_{k∈S} γ^k : |S|=w}`, `γ` primitive `(2n+1)`-th root (only when `2n+1` prime and 2 generates) | `w` |
| `index-set` (**lead K3**) | cyclotomic base over an arbitrary index set `S ⊂ Z/(2n+1)` (random or listed) | `size, seed` or `set` |
| `hamming-weight` | normal-basis Hamming ball `1 ≤ HW(x) ≤ w` | `w` |
| `maxmin-column-rate` (**new lead**) | pick `K` orbits greedily maximising the *minimum* column hit rate over sampled m-sums (the rarest-column rate was the best observed yield predictor) | `K, pool, samples, seed` |
| `ztau-norm` | `Z[τ]` multiplier closure of a seed base, `N(a+bτ) ≤ N` | `parent, norm` |

### 3.3 Torsion and symmetry
| name | definition | params |
|---|---|---|
| `symmetrised-u` | `{P : 1/(x+1) ∈ V}` (FGHR frame), via `koblitz_symmetrised` | `l` |
| `dual-frobenius-u` | `u=x+1/x`, trace-aligned affine seed `v_0+V`, `Tr v_0=1`, `V⊂ker Tr` | `l, seed` |
| `mobius-pole` | `{(x+β)^{-1} ∈ V}` | `l, pole, seed` |
| `trace-form` (**lead G4**) | non-subspace Frobenius-stable `{x : Tr(c_j x^{2^{e_j}+1}) = 0, j ≤ k}` | `k, seed` (c_j, e_j drawn) |
| `gauss-period` (**lead K1**) | window in `s=x+1/x` over a type-II ONB when `2n+1` prime | `l` |
| `power-sum` (**lead**) | subspace `V` filtered so `V·V^2` satisfies a quadratic power-sum condition (see fb-search/ABOVE_LIMIT.md §5); report the filtered dimension | `l, seed` |

### 3.4 System modifiers (change the decomposition system, not the set)
`tau-twist` (lead G2: summand `i` is `τ^i P_i`; implemented by Frobenius-shifting
the summand's base `σ^i(V)` in `build_decomposition_system`'s per-summand basis
when the builder supports it, else `not_applicable`), `per-summand-shift`
(summand `i` ranges over `σ^i V`, GGMP §3.1), `symmetry-breaking` (lex order on
summands in SAT), `trace-constraint` (Kosters–Yeo trace row on/off),
`macaulay-implied=D` (add degree-D implied rows to SAT).

### 3.5 Prime field
`prime-abscissa` (`ic_boundary::prime_factor_base(inst, size)`), only
construction+yield metrics via the framework. Everything else
`not_applicable` with reason `"prime regime"`.

Where a family exists only in the sibling `crypto` repo (greedy-coverage,
compact-orbit-scan, ztau-norm, cyclotomic, maxmin), implement it here from the
definition using the suite's `FrobeniusFactorBase` builders
(`build_explicit_frobenius_orbit_factor_base` is the universal sink: compute
the point set, fold to signed orbits, hand over representatives).

## 4. Metrics (`fbkit::metrics`)

Every cell records `metrics` as a JSON object with the groups below; any
value that was not measured is `null` with a sibling `reason` string
(`"caps_hit"`, `"not_applicable: n_vars 70 > 64"`, `"budget"`, ...). Floats are
allowed in measurements (never in hash inputs).

- `construction`: `fb_points` (B, before folding), `geometric_points`,
  `usable_points`, `effective_columns` (signed-orbit count, `FrobeniusFactorBase::unknowns()` or
  `projected_signed_orbit_count`), `fold_ratio`, `dimension` (nominal), `dim_v2`
  (`dim V·V`), `linearization_excess` `e = n − dim V − dim V^(2)`, `trace_class`
  (`all_zero` | `mixed`), `basis_weight` (sum of Hamming weights of the echelon
  basis), `build_ms`, `point_set_sha256` (sorted `[x,y]` hex pairs, canonical JSON, as in
  `pdp-degree-heuristics/factor_base.py`), `factor_base_sha256` (over the recipe record).
- `yield` (per `m`): `coverage` (exact when `|F|^(m-1) ≤ --exact-cap`
  (default 2^24) via enumeration or pair tables, else sampled over `--targets`
  random subgroup points with a Wilson 95% interval), `expected_trials
  = (U+1)/coverage`, `min_column_rate`, `achievable_rank` (rank of the
  relation rows collected over the sample), `rows_per_target`.
- `system`: `n_vars`, `n_equations`, `degrees`, `semi_regular_degree`
  (`ic_descent_degrees::semi_regular_degree`), `anf_terms`.
- `f4` (engine `f4-f2` via `ic_framework` `SystemSolver`, or `koblitz_groebner::solving_degree`): per target class (sat/unsat)
  `solving_degree_{mean,max}`, `degree_reached_max`, `degree_over_bound`,
  `matrix_rows_max`, `matrix_cols_max`, `word_ops_mean`, `ms_mean`,
  `refuted`, `solved`, `timed_out`.
- `sat` (`sat-cdcl` via `encode_boolean_system_with` + `sat::Solver`, native XOR):
  `variables`, `clauses`, `xors`, `conflicts_{mean,max}`, `decisions_mean`,
  `propagations_mean`, `learnt_clauses_mean`, `ms_mean`, `sat/unsat/unknown` counts,
  `conflict_budget`.
- `xl` *(optional)*: degree reached via `pq_xl::boolean_xl`.
- `derived`: `expected_pdp_ops = expected_trials × ops_per_attempt`
  (ops from f4 `word_ops` or sat `conflicts`, named in `op_unit`),
  `la_cost_estimate = effective_columns^2 × avg_row_weight` (label as estimate),
  `composite` (§5).
- `slope` (sweep-level, per family and m): `sigma = ΔD*/Δlog2|V|` across the
  dims swept (lead 15: an interior optimum needs σ ≲ 1/4); `null` with fewer than two dims.

Applicability rule for `m`: the chained Semaev-S3 system has
`n_vars = m·l + (m−2)·n` and the `F2BoolPoly` monomial mask caps it at 64
(`koblitz_groebner::MAX_VARS`). For every `m` in `2..=8` the sweep still runs
construction and yield (enumeration handles any `m`; cost `|F|^(m−1)` gated by
`--exact-cap`, otherwise sampled), and marks f4/sat `not_applicable` with the
exact `n_vars` in the reason. `m=3` with a union base may route through the S4
system; `m=4` may route through `KIC_M4_DESCENT`-style S5 when available. Never
silently drop a requested `m`.

Budgets: `--budget-seconds` per cell per metric group, `--conflict-budget`
(default 20_000), `--d-max` (default 6), F4 caps from `F4_F2_MAX_ROWS/COLS`.
Cell `status`: `complete` (all requested groups measured or
not_applicable), `caps_hit`, `budget`, `error` (message kept, sweep continues).

## 5. Ranking (`fbkit::rank`)

Objectives (`--objective`): `expected-ops` (default; `expected_pdp_ops`),
`solving-degree` (f4 `solving_degree_mean` for unsat class, then max), `sat-clauses`,
`sat-conflicts`, `columns` (effective columns, lower is better at equal
coverage), `composite`: weighted geometric mean of normalised
(`value / best_in_sweep`) `expected_pdp_ops`, `solving_degree_mean`,
`clauses`, `conflicts_mean`, `effective_columns`, with `--weights
ops=1,dreg=1,clauses=0.5,conflicts=0.5,columns=0.5` defaults. Cells with a
`null` objective rank last and are listed under `unranked` with the reason.
Always emit the Pareto front over (`expected_trials`, `solving_degree_mean`,
`clauses`, `effective_columns`) (minimise all), the top-k table, and per-family
best. The report says in `what_this_is_not` that ranking is a stage diagnostic
and not an `IC1` result or a speedup.

## 6. Store and S3 (`fbkit::store`)

- `Store::open(dir)`, `write_cell`, `read_cells`, `write_manifest`,
  `inventory() -> Vec<{path, bytes, sha256, blake3}>`, `write_receipt`.
- `export_archive_document(cell, points) -> Value` with schema
  `ic-factor-base-archive/1` exactly as `experiments/fb-archive/README.md`
  documents (`builder`, `recipe{n,family,l,seed,extra}`, `field`, `curve`,
  `factor_base{...}`, `factor_base_sha256`, `points` sorted, `points_encoding`,
  `point_columns`, `column_representatives`), and a `ps1_label` =
  `PS1N{n}C{tag}fb{B}PDP{m}{solver}h{12hex}` per `experiments/fb-archive/ps1.py`
  with `candidate_id: null`.
- S3: resolve the URI from `--s3`, else `FBKIT_S3_URI`, else
  `IC_ARCHIVE_S3_URI`; refuse anything not matching `^s3://[^/]+/.+`. Object
  keys: `<prefix>/fbkit/<curve_id>/<sweep_id>/<relative path>` for every file
  in the inventory plus `inventory.json` (list with sha256/blake3/bytes) and
  `manifest.json` last (upload is complete only when `manifest.json` landed).
  Transport is the `aws` CLI: `aws s3 cp <file> <uri> --only-show-errors
  --metadata sha256=<hex>` per object, `aws s3api head-object` to skip unchanged
  objects (same `sha256` metadata), `aws s3 cp <uri> <file>` and
  `aws s3 ls <uri>/` for download. The binary comes from `FBKIT_AWS_BIN`
  (default `aws`), so tests use a stub shell script that writes into a
  temp "bucket" directory; add such a stub under `tests/fixtures/fake_aws.sh`
  and integration tests for upload→download→verify round trip, dry-run, missing
  credentials (`--require` exit 1; without it, status `skipped` and exit 0),
  tampered object (hash mismatch fails download verify).
- `download` writes into an empty `--dir`, verifies every sha256 against
  `inventory.json`, and refuses to overwrite.
- Never read credentials from the tree; never print them.

## 7. Engineering constraints

- House style: clap derive, `Result<Value, String>`, report with
  `schema_version: 1`, `operation: "fbkit-<sub>"`, `status`, `what_this_is`,
  `what_this_is_not`, `config`, `elapsed_seconds`, `markdown`, rows; progress to
  stderr unless `--json`. `display()` arm in `ic/mod.rs` prints the markdown.
- `cargo fmt`, `cargo clippy --all-targets -- -D warnings`, `cargo doc`
  (`-D warnings`), `cargo deny check` (no new crates), `cargo test --release`
  must pass. `[lints.clippy]` allow list is frozen. Rust 1.87 MSRV.
- Parallelism: rayon over cells with `--jobs` (default: `available_parallelism`
  but never more than 8 on a box whose 1-minute load exceeds `nproc/2`;
  read `/proc/loadavg`); determinism per cell from `(seed, cell-id)`.
- Every metric path has a unit test on a toy cell (n ∈ {7, 9, 11, 13}) that
  runs in under a few seconds in release; the end-to-end CLI test in
  `tests/ic_fbkit.rs` runs a 2-family × 2-dim × m∈{2,3} sweep at n=11 with
  `--metrics construction,yield,f4,sat --budget-seconds 5`, then `rank`, then
  the S3 round trip with the stub.
- Documentation: `docs/ic/FBKIT.md` (user guide, from this spec), a section in
  `docs/ic/README.md`, one line in `suite/README.md`, `fbkit` in the `crax`
  OVERVIEW string, and shipped manifests in `docs/ic/sweeps/fbkit-*.json`
  (`fbkit-shapes-n13.json`, `fbkit-koblitz-n17.json`, `fbkit-leads-n13.json`,
  `fbkit-m2-8-n7.json`).
