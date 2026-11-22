# Gröbner reference table: `f4_fp` vs msolve on the lab's F_p systems

Workspace goal "Faster Gröbner bases for the lab's F_p systems" (owner,
pinned 2026-11-21; workspace PR #51), items GB-1 (freeze the system set) and
GB-2 (reference table). Status: exploratory; nothing here is a claim
`[pcc:unverified]`.

## Question

How far is the lab's degree-bounded F4 (`f4_fp`, the registry's PKM
baseline arm) from msolve on the exact systems the PKM lead-testing protocol
measures, in matrix width (`max_cols`, the registry cost metric) and in time
and memory? This sets the bar every later Gröbner lead is measured against.

## Systems (GB-1)

**Set A, PKM tower (chain presentation).** The registry phase-1 baseline
commands, unchanged, plus `--export DIR`: `pkm_tower_pilot --p 786433
--kinds kummer,dickson,isogeny --controls tower,null,naive --t-min {1|2|3}
--max-t 8 --max-t-m3 8 --max-t-m4 8 --budget 60 --seed 1347112276
--planted 3 --random 3 --ladder-t none --m {m}`, m = 2..9 (exact commands:
`python3 tools/lead_sweep.py plan` in the workspace trunk). `--export`
writes each input system before it is solved, in msolve's format, with the
planted solution beside it, and adds `export_id` / `export_sha256` to the
`f4_fp` row, so both engines are joined on identical bytes.

**Set B, generic (direct) Semaev.** For each Set A system with m ≥ 3, the
chain's auxiliary abscissae u_0..u_{m−3} are eliminated by successive
resultants in Singular (`direct_semaev.py`), giving S_{m+1}(x_1..x_m, x_R)
in the same variables with the same tower equations. m = 3, 4, 5 give
S_4, S_5, S_6; the planted solution is checked to vanish on the derived
polynomial before the file is written. Derivations that exceed the
Singular budget are recorded as resource limits.

## Engines and metrics (GB-2)

| engine | how | order | output |
|:--|:--|:--|:--|
| `f4_fp` | the pilot itself (registry baseline arm) | grevlex, degree bound n + d + 6 | `max_cols`, `max_rows`, wall, solving degree, planted check |
| msolve 0.6.5 (Ubuntu 24.04 package) | `run_msolve.py`: `msolve -g 2 -t 1 -v 2` under the trunk watchdog (`lead_sweep.watched_run`, 12 GiB, 600 s) | grevlex (DRL) | reduced GB, `max. matrix data` rows × cols, zero reductions, wall, peak RSS, planted check |

Correctness: a row counts only if the planted solution vanishes on every
element of the engine's basis (`planted_ok`), and random targets agree on
consistency between engines. The run_msolve planted check was tested with a
wrong solution (rejected) and a right one (accepted) on a toy system.

Not comparable directly: `f4_fp` reports a *degree-truncated* basis and
stops at its bound; msolve computes the full reduced basis. `max_cols` is
reported for both but msolve's is the widest matrix of a different
algorithm (with Gebauer–Möller pruning, which `f4_fp` lacks).

## Host

Claude cloud VM: 4 vCPU, 15 GiB, no isolation. All times are exploratory
(AGENTS.md "CPU performance isolation gate"); `max_cols` is
host-independent. Any timing used for the goal's pass criterion is re-run
on isolab.

## Files

- `direct_semaev.py`: Set B derivation.
- `run_msolve.py`: msolve runner and planted check.
- Data (systems, logs, rows) go to the artifact store, not Git.
