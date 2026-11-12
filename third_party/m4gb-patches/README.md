# M4GB patches

Patches applied by [`scripts/m4gb_build.sh`](../../scripts/m4gb_build.sh) on top
of the pinned upstream commit of
[cr-marcstevens/m4gb](https://github.com/cr-marcstevens/m4gb) (GPL-3.0). M4GB
is built as a separate binary and only ever run as a subprocess
(the `ca m4gb` subcommand, `tools/ca_cli.c`); no M4GB source is linked into this
crate. The patches are published here under the same GPL-3.0 terms as the
code they modify.

| patch | what it changes | switch |
|:--|:--|:--|
| `0001-gf_p-arithmetic-vector-kernels.patch` | `lib/gf_p_simple.hpp`: the dense-row kernels `add_to`, `mul_to`, `substract_to` compute `l + c·r mod p` with plain integer arithmetic on a compile-time modulus instead of one table gather per coefficient, so the compiler vectorizes them (16 or 32 lanes per AVX2 operation). Scalar table operations are unchanged. | `-DM4GB_ARITH_KERNELS=0` restores upstream |
| `0002-field-equations-declared-variables-only.patch` | `lib/parser.hpp`, `src/m4gb.hpp`: over `GF(2)` the field equations `x_i² + x_i` are added for the variables the input declares (`$vars`) or uses, not for all `MAXVARS`, so one binary compiled for 128 variables does not drag 93 unused variables through a 35-variable computation. | `-DM4GB_FIELDEQ_DECLARED_ONLY=0` restores upstream |
| `0003-serve-mode-persistent-solver-process.patch` | `src/common.hpp`: a `--serve` mode. One solver instance reads `SOLVE <inputfile> <outputfile>` lines from stdin, solves each with the same `solve()` entry point (which re-initialises its state), writes the output file and answers `OK`, `UNSAT` (unit ideal) or `ERR <what>` on stdout; `QUIT` or end of input ends it. The process start, the field tables and the thread pool are paid once per process instead of once per system. The one-shot `--solve` path is untouched. Run it with `--loglevel 1` so the logger (which writes to stdout) does not interleave with the protocol; the client ignores lines that are not protocol words. | none; the mode is opt-in (`--serve`), crypto's `m4gb-f2-server` engine uses it; `ca m4gb` runs the one-shot `--solve` path |
| `0004-divisibility-signatures-in-update.patch` | `lib/monomial_base.hpp`, `lib/monomial_degrevlex.hpp`, `src/m4gb.hpp`: a 64-bit signature per monomial (variables present, variables with exponent 2, and whether every exponent is at most 2). Divisibility and lcm between monomials whose exponents are all at most 2 (every monomial over GF(2) with the field equations) are decided from the signatures, exactly, instead of decoding the degrevlex rank one variable at a time; other monomials use the signature as a prefilter and then the exponent walk. Integer-monomial signatures come from a thread-local cache; `update()` computes the new leading monomial's signature once and stores each critical pair's lcm signature. Bases are byte-identical. | `-DM4GB_SUPPORT_MASK=0` restores 0001–0003 |

The compile-time switches exist so an A/B run can build the baseline and the patched
solver from the same tree (`EXTRA_CPPFLAGS="-DMAXVARS=<N> -DFIELDSIZE=<q> -DM4GB_ARITH_KERNELS=0
-DM4GB_FIELDEQ_DECLARED_ONLY=0 -DM4GB_SUPPORT_MASK=0"`; overriding `EXTRA_CPPFLAGS` drops the Makefile's own `-DMAXVARS`/`-DFIELDSIZE`, so restate them). Measurements and the protocol are in crypto
`research/m4gb_integration_20261110/` (0001, 0002),
`research/m4gb_persistent_server_20261111/` (0003) and
`research/m4gb_update_signatures_20261112/` (0004).

To regenerate a patch after editing a checkout at the pinned commit:
`git diff -- <files> > third_party/m4gb-patches/<nnnn>-<slug>.patch`.
