# `ca m4gb`: Gröbner bases and roots through M4GB

`ca m4gb` runs the external Gröbner-basis solver
[M4GB](https://github.com/cr-marcstevens/m4gb) (Makarim and Stevens, *M4GB: An
efficient Groebner-basis algorithm*, ISSAC 2017) on a polynomial system over a
small finite field and reports the result as JSON. M4GB is GPL-3 and is never
linked into this library: the subcommand starts a solver binary as a child
process, with a wall-clock limit, and reads what it wrote.

## Building a solver

```sh
scripts/m4gb_build.sh n32_gf2 n20_gf31          # into ./.m4gb/bin
scripts/m4gb_build.sh --prefix /opt/m4gb n64_gf2 n128_gf2
```

The script clones upstream at a pinned commit, applies
[`third_party/m4gb-patches/`](../third_party/m4gb-patches/README.md) (arithmetic
`GF(p)` dense kernels; field equations for declared variables only), builds one
binary per `(MAXVARS, FIELDSIZE)` pair and writes `MANIFEST.json` with the
commit, patch and binary hashes. `FIELDSIZE` is a prime below `2^16` or a power
of two up to `2^16`; `MAXVARS` is a compile-time upper bound on the variable
count. A binary much wider than the system costs memory (about 7 GB resident for
a 35-variable system under a 128-variable binary), so build a ladder of widths
and point the subcommand at the directory.

## Usage

```
ca m4gb --input FILE [--field Q] [--vars N] [--format default|mqchallenge]
        [--bin PATH | --bin-dir DIR] [--threads T] [--timeout SEC] [--out FILE]
        [--keep] [--verbose]
```

- `--input`: M4GB's default text format (`$fieldsize Q`, `$vars N X` or
  `$vars a b c`, then one polynomial per line, terms joined by `+`, factors by
  `*`, `#` comments) or the Fukuoka MQ-challenge format. The field size, the
  variable count and the format are read from the file; `--field`, `--vars` and
  `--format` override or supply them.
- Solver selection, in order: `--bin PATH`; `--bin-dir DIR` or `CA_M4GB_DIR`
  (the narrowest `solver_m4gb_n<N>_gf<Q>` in the directory with `N ≥` the
  variable count and the right field); `CA_M4GB_BIN`. None of these: exit 2.
- `--threads` is passed to the solver (`--nrthreads`; default 1). `--timeout`
  kills the solver after that many seconds (default 0: none). `--out` keeps the
  basis file at that path. `--keep` keeps the solver's log and basis files and
  names them in the JSON.

## Output and exit status

Exit 0 is a decided answer, exit 1 undecided, exit 2 a usage error.

```json
{"status":"ok","solver":".../solver_m4gb_n20_gf31","field":31,"vars":12,
 "unit_ideal":false,"basis_size":12,"basis":["X11 + 7","X10 + 8", "..."],
 "basis_truncated":false,"solution":{"X11":24,"X10":23,"...":0},
 "max_degree":4,"cpu_seconds":0.15,"peak_mib":13.0,"wall_seconds":0.21,"threads":1}
```

- `basis`: the reduced degrevlex basis, monic, one polynomial per line (at
  most 256 lines are listed; `basis_truncated` says so). Upstream prints
  `^2 + ` lines for the field equations of variables the input never declared;
  they are dropped.
- `solution`: present when every basis element is `V` or `V + c`, i.e. the
  ideal is one point: `V = −c mod q`. A basis with free variables or
  non-linear elements has `"solution": null` and `basis_size`.
- `unit_ideal: true`: the system has no solution. M4GB signals this by exit
  status 1 and `contradiction: …` on stderr with no basis file; the subcommand
  reports it as a decided answer with exit 0.
- `max_degree`: the highest critical-pair degree the solver processed
  (`lcmdegree=` in its log); `cpu_seconds` and `peak_mib` are the solver's own
  figures; `wall_seconds` is measured here, process start included.
- `{"status":"timeout"}` (exit 1) after `--timeout`; `{"status":"error"}`
  (exit 1) when the solver exits non-zero without a contradiction.

## Accounting

The subcommand reports wall time and the solver's own counters only: no
operation count in a shared unit exists for M4GB, so by the lab's accounting
rules it is a reference arm, never a leaderboard row. Measurements of the
patched kernels against upstream and of `m4gb-f2` inside crypto's
index-calculus framework are in crypto `research/m4gb_integration_20261110/`
and `research/m4gb_descent_ladder_20261110/`.

## Tests

`scripts/cli_smoke.sh` exercises the subcommand through stub solvers;
`python3 -m unittest tests.test_m4gb_cli -v` covers binary selection, basis and
point parsing, the unit-ideal path, the timeout and the MQ-challenge header.
