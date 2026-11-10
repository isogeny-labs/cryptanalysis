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

Both switches exist so an A/B run can build the baseline and the patched
solver from the same tree (`CPPFLAGS="-DM4GB_ARITH_KERNELS=0
-DM4GB_FIELDEQ_DECLARED_ONLY=0"`). Measurements and the protocol are in
crypto `research/m4gb_integration_20261110/`.

To regenerate a patch after editing a checkout at the pinned commit:
`git diff -- <files> > third_party/m4gb-patches/<nnnn>-<slug>.patch`.
