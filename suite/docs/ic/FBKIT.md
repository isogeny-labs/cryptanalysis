# `ca-ic fbkit`: the factor-base toolkit (user guide)

`ca-ic fbkit` (also `crax ic fbkit`) takes **one curve**, sweeps **factor-base
constructions** over it (every technique this project has tried plus new
leads), **measures** each construction at a chosen summand count `m` in
`2..=8` on construction, yield and downstream solver metrics, **ranks** them
under an explicit objective with a Pareto front, writes a reproducible **run
directory**, and uploads or downloads that directory to or from **S3**.

The design record (frozen 2026-10-18) is [`FBKIT_SPEC.md`](FBKIT_SPEC.md); this
file is the user guide. The library is `src/cryptanalysis/fbkit/`, the command
line `src/cli/tools/ic/fbkit.rs`, the tests `tests/ic_fbkit.rs` and
`tests/fbkit_store.rs`.

**Honesty rules.** Everything `fbkit` prints is a stage diagnostic. It is not
an `IC1` result, not an end-to-end cost and not a speedup. `fb<B>` is the
number of distinct usable (cofactor-projected, non-identity) subgroup points
**before** sign and Frobenius folding; the folded count is `effective_columns`
and is always recorded separately. A value that was not measured is `null`
with a sibling `reason`, never `0`. Ranking is relative within one sweep. A
cell may carry a `PS1N...` label; its `candidate_id` is always `null`. Every
report says so in `what_this_is_not`.

## Commands

```
ca-ic fbkit list      [--json]
ca-ic fbkit explain   <family> [--json]
ca-ic fbkit build     <curve> --family F[:k=v,..][;mod=v] [--m 3] [--metrics construction] [--dir D]
ca-ic fbkit sweep     <curve> (--manifest FILE | --families a,b,c [--dims 3-6] [--seeds 1,2] [--modifiers trace_zero=1 ...] [--cell RECIPE ...])
                      [--m 2,3] [--metrics construction,yield,f4,sat] [--targets 8] [--seed S]
                      [--budget-seconds 60] [--conflict-budget 20000] [--d-max 6] [--exact-cap N]
                      [--jobs N] [--dir D] [--resume] [--points] [--objective expected-ops]
ca-ic fbkit rank      --dir D [--objective expected-ops|solving-degree|sat-clauses|sat-conflicts|columns|composite] [--top 10] [--weights ops=1,dreg=1,clauses=0.5,conflicts=0.5,columns=0.5]
ca-ic fbkit export    --dir D --cell <cell-id> [--archive-out FILE]
ca-ic fbkit upload    --dir D [--s3 s3://bucket/prefix] [--dry-run] [--require]
ca-ic fbkit download  --s3 s3://bucket/prefix/fbkit/<curve_id>/<sweep_id> --dir D [--verify-only]
```

`--json` (print the machine-readable report, no progress text) and `--out FILE`
(save the JSON report to a new file; an existing path is refused) are the global
`ca-ic` flags. Progress goes to stderr and is suppressed by `--json`. The exit
code is 0 for `complete` (and for `skipped`), 1 for `incomplete` or `error`.

Every subcommand returns the house report: `schema_version: 1`, `operation`
(`fbkit-list`, `fbkit-explain`, `fbkit-build`, `fbkit-sweep`, `fbkit-rank`,
`fbkit-export`, `fbkit-upload`, `fbkit-download`), `status` (`complete`,
`skipped`, `incomplete`, `error`), `what_this_is`, `what_this_is_not`, `config`,
`elapsed_seconds`, `resources`, `markdown`, plus the rows. A sweep report has
`cells` (one summary row per cell: `cell_id`, `family`, `l`, `m`, `status`,
`fb_points`, `effective_columns`, `coverage`, `expected_trials`,
`solving_degree_mean`, `sat_clauses`, `conflicts_mean`, `expected_pdp_ops`),
`counts` (`total`, `run`, `skipped`, `by_status`), `slopes`, `errors`,
`warnings` and a `ranking` summary. A sweep is `complete` when no cell has
status `error`, else `incomplete` (the errors are listed).

`build` is a one-cell sweep. `rank` re-ranks an existing directory. `explain`
prints the definition, parameters, prior verdict and citations of one family.

### Curve selectors

Exactly one selector, shared by `build` and `sweep` (a manifest may carry it
instead, as its `curve` object):

| selector | meaning |
|:--|:--|
| `--koblitz-degree N --curve-a {0,1}` | Koblitz `K_a / GF(2^N)`, N odd; N in 5..=62 for measured metrics. `curve_tag` `kb<a>`. Not every `(a, N)` has a prime-order subgroup (`K_1` at N=13 and `K_0` at N=17 do not). |
| `--char2-degree N [--curve-seed S] [--max-cofactor 8]` | random binary curve with a prime-order subgroup (`ic_boundary::random_binary_instance`), N in 5..=62. `curve_tag` `rb`. Only the families that need no Frobenius apply. |
| `--curve NAME` | a named profile from `ca-ic list`. A binary Koblitz profile with N <= 63 is built as `K_a`; the real ones (`ecc2k-130`, `ecc2k-95`, `sect163k1`) are wider than the single-word arithmetic, so the sweep is reported as `skipped` with the reason (exit 0). Named prime profiles are inspection-only. |
| `--bits B` | prime-field curve of `B` bits from the bench roster. Only `prime-abscissa` applies; everything else is `not_applicable` ("prime regime"). `curve_tag` `p`. |

The curve is identified by `curve_id = EC1N<n>C<tag>h<12hex>` (canonical
SHA-256 over the field and curve records of
`experiments/pdp-degree-heuristics/toycurve.py`), recorded in `curve.json` and
in every cell.

### Recipes

`name:k=v,k=v;modifier=v` (`Recipe::parse`): integers stay integers, `a+b+c` is a
list, `true`/`false` are 1/0. Examples: `geometric:l=4,seed=3`,
`coordinate:l=5;trace_zero=1`, `divisor:indices=1+2`,
`two-torsion-saturated:parent=geometric,parent.l=4`. Set modifiers
(`trace_zero`, `shift`, `two_torsion`, `frobenius_union`) change the point set;
system modifiers (`tau-twist`, `per-summand-shift`, `symmetry-breaking`,
`trace-constraint`, `macaulay-implied`) change how the decomposition system is
built. In a sweep matrix `--modifiers` is repeatable and each occurrence is one
column of the matrix (`--modifiers none --modifiers trace_zero=1`).

## The technique registry

Generated by `ca-ic fbkit list` (41 entries: families, the four set modifiers
and the five system modifiers). Prior verdicts are quoted from earlier studies
with their citing path; `status` is `tried` (measured before), `proposed`
(specified, not measured) or `new-lead` (first implemented by this toolkit).

| family | regime | kind | status | prior verdict |
|---|---|---|---|---|
| `coordinate` | binary | subspace | tried | Product law flat in l; 2^71.77x rho at n=131 (crypto-autoresearcher KN-FIND-aa2efc). |
| `random` | binary | subspace | tried | D* about 4.0 at 2l=n; +0.4..2.0 degrees above coordinate in 31/90 pairs (crypto/research/fb_hyperparam_sweep_20261014). |
| `geometric` | binary | subspace | tried | Attains Kneser dim V^(2)=2l-1, D = 2+[e<-3.5]+[e<-8.5] with e = n - dim V - dim V^(2); 15-40x cheaper per query than random at equal yield (cryptanalysis/experiments/pdp-degree-heuristics/README.md). |
| `gp-scaled` | binary | subspace | tried | Geometric-progression variants behave like the random band once the trace class is controlled (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4). |
| `gp-symmetric` | binary | subspace | tried | Random band once the trace class is controlled (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4). |
| `gp-order` | binary | subspace | tried | Random band once the trace class is controlled (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4). |
| `frobenius-progression` | binary | subspace | tried | Random-like (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4). |
| `normal` | binary | subspace | tried | Random-like (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 6.4). |
| `subfield` | binary | subspace | tried | D* about 2 but the yield collapses on b=1 and the base is empty at prime n (cryptanalysis/experiments/fb-search/README.md). |
| `scaled-subfield` | binary | subspace | tried | As subfield: D* about 2, yield collapses on b=1, empty at prime n (cryptanalysis/experiments/fb-search/README.md). |
| `sparse-descent` | binary | subspace | new-lead | New lead, never measured: the aim is fewer clauses and ANF terms at equal dimension (this toolkit, spec 3.1). |
| `trace_zero` | binary | set-modifier | tried | Yield doubles, but class-1 targets refute at degree 2 by the trace identity; geomtraceu is the best fb-search family at 2.8x prefix but 3.9e3-4.4e4x rho (cryptanalysis/experiments/fb-search/README.md). |
| `shift` | binary | set-modifier | tried | Affine descent 2.7x (m=2) / 6.3x (m=3) faster than the hull, but enumeration still wins (suite/src/cryptanalysis/affine_factor_base.rs doc). |
| `two_torsion` | binary | set-modifier | tried | Columns unchanged, coverage never falls (n=15: 150 -> 210/210) (crypto/research/sat_factor_base_review_20260908/MATHEMATICS.md). |
| `frobenius_union` | binary | set-modifier | tried | 3.8-30.3x rho over n=13..47; ECC2K-130 floor 2^124.99 (crypto/research/ic_frontier_campaign_20261015). |
| `divisor` | koblitz | koblitz-structured | tried | 7.9-13x fewer relations and 62-168x cheaper LA on toys; 300x rho at n=41; empty at n=131/163 (crypto-autoresearcher KN-FIND-b9a41d). |
| `frobenius-union` | koblitz | koblitz-structured | tried | 3.8-30.3x rho over n=13..47; ECC2K-130 floor 2^124.99 (crypto/research/ic_frontier_campaign_20261015). |
| `explicit-orbits` | koblitz | koblitz-structured | tried | The universal sink of the builders; no verdict of its own (suite/src/cryptanalysis/koblitz_index_calculus.rs). |
| `compact-orbit-scan` | koblitz | koblitz-structured | tried | 3.8-30.3x rho over n=13..47; ECC2K-130 floor 2^124.99 (crypto/research/ic_frontier_campaign_20261015). |
| `greedy-coverage` | koblitz | selection | tried | Expected trials 1.08-1.18x better; the gain vanishes at saturation (crypto/research/greedy_factor_base_yield_20261014). |
| `pruned` | koblitz | selection | tried | Expected trials 1.08-1.18x better; vanishes at saturation (crypto/research/greedy_factor_base_yield_20261014). |
| `two-torsion-saturated` | koblitz | torsion-symmetry | tried | Columns unchanged, coverage never falls (n=15: 150 -> 210/210) (crypto/research/sat_factor_base_review_20260908/MATHEMATICS.md). |
| `subgroup-orbits` | koblitz | koblitz-structured | tried | No separate verdict; the pair-table oracle needs no structure (suite/src/cryptanalysis/koblitz_factor_base_search.rs). |
| `cyclotomic` | binary | non-subspace | tried | Yield-neutral in 15/15 null tests, 1.02-1.12x costlier (crypto/research/cyclotomic_falsifier_20261015). |
| `index-set` | binary | lead | new-lead | New lead, never measured; non-subspace bases are dominated for linear oracles, d_lin >= 3log2/F/ - n - 2 (cryptanalysis/experiments/fb-search/nonsubspace.py). |
| `hamming-weight` | binary | non-subspace | tried | Calls grow /F/^(1.9-2.5): rejected (crypto/research/hamming_ideal_pdp_20260930/RESULT.md). |
| `maxmin-column-rate` | koblitz | selection | new-lead | New lead: the rarest-column hit rate was the best observed yield predictor, Spearman -0.83..-0.95 (cryptanalysis/experiments/fb-search/online.py). |
| `ztau-norm` | koblitz | koblitz-structured | tried | 4.5x rho at norm 64; a precompute trade, not a yield lever (crypto/research/ic_leads_20261010/RESULTS_ROUND2.md). |
| `symmetrised-u` | binary | torsion-symmetry | tried | S_sym/S_x 0.84/0.76/4.0 at n=17/23/31, refuted at 31 (crypto/research/koblitz_symmetrised_e2e_20260927). |
| `dual-frobenius-u` | binary | torsion-symmetry | tried | Coverage 6101/6909, below the orbit-picked 6165/6909 (crypto/research/sat_factor_base_review_20260908/continuation-01). |
| `mobius-pole` | binary | torsion-symmetry | tried | Killed: beta-spread 0.06-0.19 (crypto/research/shape_search_g1_g6_20261015). |
| `trace-form` | binary | lead | proposed | Never built (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md section 7). |
| `gauss-period` | binary | lead | proposed | Proposed, not measured (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md). |
| `power-sum` | binary | lead | proposed | Proposed (cryptanalysis/experiments/fb-search/ABOVE_LIMIT.md section 5); dim V*V^2 = min(n, 3l-2) for a progression, so no extra conditions above the limit. |
| `tau-twist` | koblitz | system-modifier | proposed | Survives n <= 9; yield promised x m! (not measured at scale) (crypto/research/notes/index-calculus/RESEARCH_FACTOR_BASE_SHAPE_SEARCH.md). |
| `per-summand-shift` | koblitz | system-modifier | tried | Coverage 4-73x with unchanged columns; Lean `patterns_neutral`: k patterns cost k solves (cryptanalysis/experiments/shifted-base-geometry, crypto/research/factor_base_designs_20261015). |
| `symmetry-breaking` | any | system-modifier | tried | No help: the degree-2 Macaulay and trace rows already break the symmetry (crypto/RESEARCH_KOBLITZ_INDEX_CALCULUS.md). |
| `trace-constraint` | binary | system-modifier | tried | Degree-2 Macaulay plus trace rows already break the symmetry (crypto/RESEARCH_KOBLITZ_INDEX_CALCULUS.md). |
| `macaulay-implied` | any | system-modifier | proposed | Proposed; compare conflicts against the plain encoding (suite/src/cryptanalysis/koblitz_groebner.rs matrix_f4_f2). |
| `slope-sigma` | any | lead | proposed | Proposed (crypto/research/ic_leads_20261010/RESULTS_ROUND2.md). |
| `prime-abscissa` | prime | subspace | tried | Only construction and yield apply to a prime field (suite/src/cryptanalysis/ic_boundary.rs prime_factor_base). |


## Metrics

Every cell records `metrics` as groups; a value that was not measured is `null`
with a `reason` (`caps_hit`, `not_applicable: n_vars 66 > 64`, `budget`, ...).
Select groups with `--metrics`; `yield` or a solver group also computes
`derived`, and `f4`/`sat` also compute `system`.

| group | contents |
|:--|:--|
| `construction` (always) | `fb_points` (B, before folding), `geometric_points`, `usable_points`, `strict_subgroup_points`, `effective_columns` (signed-orbit count), `fold_ratio`, `dimension`, `dim_v2` (dim V.V), `linearization_excess` `e = n - dim V - dim V.V`, `trace_class`, `basis_weight`, `build_ms`, `point_set_sha256`, `notes` |
| `yield` (at the cell's `m`) | `coverage` (exact when `|F|^(m-1) <= --exact-cap`, else sampled over `--targets` points with a Wilson 95% interval `coverage_ci95`), `expected_trials = (U+1)/coverage`, `min_column_rate`, `achievable_rank`, `rows_per_target`, `mode` |
| `system` | `n_vars`, `n_equations`, `degrees`, `semi_regular_degree`, `anf_terms` |
| `f4` | per class (`random`, `planted`): `solving_degree_mean/max`, `degree_reached_max`, `matrix_rows_max`, `matrix_cols_max`, `word_ops_mean`, `ms_mean`; capped by `--d-max` and `--budget-seconds` |
| `sat` | `variables`, `clauses`, `xors`, per class `conflicts_mean/max`, `decisions_mean`, `propagations_mean`, `ms_mean`, sat/unsat/unknown counts; capped by `--conflict-budget` |
| `derived` | `expected_pdp_ops = expected_trials x ops per attempt` (`op_unit` names the unit), `la_cost_estimate` (an estimate, labelled), `composite` (computed by `rank`) |

Cell `status`: `complete` (every requested group measured or not applicable),
`caps_hit`, `budget`, `not_applicable` (the family does not apply: reason
kept), `error` (message kept, the sweep continues).

### The `m`-applicability rule

The chained Semaev S3 system for `m` summands over a subspace of dimension `l`
has `n_vars = m*l + (m-2)*n`, and the boolean polynomial type caps variables at
64. For every `m` in `2..=8` the sweep still measures **construction and
yield** (enumeration handles any `m`; cost `|F|^(m-1)` is gated by
`--exact-cap`, otherwise sampled), and marks `system`, `f4` and `sat`
`not_applicable` with the exact `n_vars` in the reason. A requested `m` is never
silently dropped. `docs/ic/sweeps/fbkit-m2-8-n7.json` demonstrates it: at n = 7
and `l = 3`, `m = 7` has 56 variables (measured) and `m = 8` has 66 (not
applicable).

### The slope sigma

Per `(family, m)` across the swept dimensions, `sigma = dD*/d dim V`, the
least-squares slope of the mean solving degree against `dim V` (lead 15: an
interior optimum needs sigma at most 1/4). `null` with fewer than two measured
dimensions.

## Ranking

`--objective` (lower is better) at sweep time or with `fbkit rank`:

| objective | value |
|:--|:--|
| `expected-ops` (default) | `derived.expected_pdp_ops` |
| `solving-degree` | `f4.random.solving_degree_mean`, then max |
| `sat-clauses` | `sat.clauses` |
| `sat-conflicts` | `sat.random.conflicts_mean` |
| `columns` | `effective_columns` |
| `composite` | weighted geometric mean of each component divided by the best in the sweep; `--weights ops=1,dreg=1,clauses=0.5,conflicts=0.5,columns=0.5` |

Cells whose objective is `null` rank last and are listed under `unranked` with
the reason. The ranking also emits the **Pareto front** over
(`expected_trials`, `solving_degree_mean`, `clauses`, `effective_columns`),
minimising all, and the best cell per family. `ranking.json` is rewritten by
every `rank`. Ranking is a stage diagnostic over one sweep: not an `IC1` result,
not a speedup.

## The run directory

```
D/
  manifest.json          frozen manifest (ic-fbkit-manifest/1) with sweep_id
  curve.json             field + curve records, curve_id, curve_tag, selector
  cells/<cell-id>.json   one per (family, params, m); written atomically as each cell finishes
  points/<cell-id>.jsonl sorted ["x","y"] lowercase hex lines (cells with <= 65536 points, or all with --points)
  ranking.json           last ranking
  report.json, report.md the report of the last sweep or rank
  inventory.json         path, bytes, sha256, blake3 of every file (not receipts)
  receipts/upload-<utc>.json, receipts/download-<utc>.json
```

`sweep_id` is the first 12 hex of the SHA-256 of the canonical manifest (without
`jobs`, `budget_seconds`, `dir`, `resume`, `progress`); `cell-id` is
`<family>-<params>-m<m>-l<l>-<8hex>`. Without gzip in the crate the files are
plain `.json` and `.jsonl`. Writes are atomic (temp file, `sync_all`, rename).

`--resume` opens an existing directory of the **same** manifest (a different
`sweep_id` is refused) and skips cells whose stored status is `complete`,
`not_applicable` or `caps_hit` (a cap is deterministic for one manifest); `budget`
and `error` cells run again. `--jobs` defaults to all cores, at most 8 when the
1-minute load average exceeds half the cores. Per-cell seeds derive from
`(--seed, cell-id)`, so a cell is reproducible on its own.

### Manifests

`--manifest FILE` is an `ic-fbkit-manifest/1` JSON: `curve` (a selector object
such as `{"koblitz_degree": 13, "curve_a": 0}`), `m`, `cells` (explicit recipes
`{"family", "params", "modifiers"}`), `matrix` (`families`, `dims`, `seeds`,
`modifiers`, `params`), `metrics` (`groups`, `targets`, `exact_cap`,
`budget_seconds`, `conflict_budget`, `d_max`), `seed`, `jobs`. Keys starting
with `_` are comments. Explicit flags (`--seed`, `--jobs`, `--m`, `--metrics`,
`--targets`, ...) override the file; `--families`/`--dims`/`--seeds`/`--modifiers`
cannot be combined with a manifest. Shipped manifests (`docs/ic/sweeps/`):

| file | curve | what it shows |
|:--|:--|:--|
| `fbkit-shapes-n13.json` | `K_0 / GF(2^13)` | six subspace shapes x l=3..5 x m=2,3, with and without `trace_zero` |
| `fbkit-koblitz-n17.json` | `K_1 / GF(2^17)` | divisor, frobenius-union, compact-orbit-scan, greedy-coverage, maxmin-column-rate, two-torsion-saturated, pruned |
| `fbkit-leads-n13.json` | `K_0 / GF(2^13)` | trace-form, power-sum, sparse-descent, maxmin-column-rate, geometric with tau-twist / per-summand-shift, symmetrised-u, dual-frobenius-u, mobius-pole |
| `fbkit-m2-8-n7.json` | `K_1 / GF(2^7)` | coordinate and geometric, l=2..4, m=2..8: the applicability rule |

## S3

`upload`/`download` use the `aws` CLI through an argument vector (no shell).
The binary is `FBKIT_AWS_BIN` (default `aws`); the destination is `--s3`, else
`FBKIT_S3_URI`, else `IC_ARCHIVE_S3_URI`, and must match `^s3://[^/]+/.+`.
Credentials come from the usual AWS environment and are never read from the
tree or printed.

Keys are `<prefix>/fbkit/<curve_id>/<sweep_id>/<relative path>` for every file
of the inventory, then `inventory.json`, then `manifest.json` **last**: a remote
run is complete only once `manifest.json` landed. Each object carries `sha256`
metadata; unchanged objects (`head-object` with the same `sha256`) are skipped.

- `upload` with no destination, or with unusable credentials, returns status
  `skipped` and exit 0; with `--require` it fails (exit 1). `--dry-run` lists
  the objects without transferring. A receipt is written to `receipts/`.
- `download` writes into a new or empty `--dir`, verifies size, SHA-256 and
  BLAKE3 of every file against `inventory.json`, refuses to overwrite, and
  fails on any mismatch. `--verify-only` re-checks an existing directory
  without network access.

## Archive export

`fbkit export --dir D --cell ID [--archive-out FILE]` writes the
`ic-factor-base-archive/1` document of one cell as
[`experiments/fb-archive`](../../../experiments/fb-archive/README.md) documents
it (`builder`, `recipe{n,family,l,seed,extra}`, `field`, `curve`, `factor_base`,
`factor_base_sha256`, sorted `points`) and its `ps1_label`
`PS1N<n>C<tag>fb<B>PDP<m><solver>h<12hex>` with `candidate_id: null`. The points
come from `points/<cell>.jsonl`, else are re-materialised deterministically
from the recipe and checked against the cell's `point_set_sha256`. Deviations
from the Python archive: points are lowercase hex strings, and `point_columns`
and `column_representatives` are `null` (not computed here).

**The fb-archive is append-only** (`appendonly.py`, CI `fb-refs`): never remove
or rewrite an archived row or file; a correction is a new entry. `fbkit export`
only produces a document; copying it into `experiments/fb-archive/` and adding
the index row is a deliberate, append-only act.

## Examples

```
ca-ic fbkit list
ca-ic fbkit explain geometric
ca-ic fbkit sweep --koblitz-degree 11 --curve-a 1 --families coordinate,geometric --dims 3-4 --m 2,3 \
    --metrics construction,yield,f4,sat --targets 4 --budget-seconds 5 --dir runs/k11
ca-ic fbkit sweep --manifest docs/ic/sweeps/fbkit-m2-8-n7.json --dir runs/m2-8 --jobs 8
ca-ic fbkit rank --dir runs/k11 --objective composite --weights dreg=2 --top 5
ca-ic fbkit export --dir runs/k11 --cell <cell-id> --archive-out geometric-k11.json
ca-ic fbkit upload --dir runs/k11 --s3 s3://bucket/prefix --dry-run
```
