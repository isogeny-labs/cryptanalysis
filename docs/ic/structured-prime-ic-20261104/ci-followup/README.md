# Transitive consumer lockfile CI repair

The native genus-2-cover job stopped at dependency resolution under `--locked`.
The structured backend added two dependency edges that were missing from this
separate tool lockfile: the bindings tensor's sha2 dependency and the older
suite tensor's explicit dependency on the bindings structured backend.
The failure was reproduced locally before Cargo regenerated those edges.
No registry package version, native source, fixture, test or gate changed.
[pcc:unverified]

After regeneration, `cargo metadata --locked` completed and the tool's all-target
compile completed. Both structured CLI consumer panels report three passing
controls; scoped six-file parity is retained. Full `check.sh` is left to its
existing hosted workflow; no new curve/solver campaign was run locally.
[pcc:unverified]

Local compilation initially exposed sparse-checkout prerequisites: include/src,
a shared CUDA header, and the tracked compile-time challenge corpus. Those source
bytes were materialized from Git; intermediate failures are retained alongside
the final compile output. `repair.json` records the locked graph summary and the
exact hosted failure. The full metadata JSON was inspected locally; its digest
is diagnostic, and the committed lock plus command reproduces the graph.
[pcc:unverified]

The other active package/application locks already contain these edges. The
historical nested bindings lock is ignored by its enclosing Cargo workspace
and was not substituted for the active workspace lock. Claim
PCC-20261104-f011a3 remains an unverified producer statement; these checks are
software integration evidence, not an independent signed execution verdict.
[pcc:unverified]

Before publication of this follow-up report, the branch advanced to
`2015e2303c86e8cad1c040390a5d36a3dae2eec3`, which contains exactly the same
two-edge lock repair. This checkout fast-forwarded to that published fix;
this follow-up adds the retained diagnostic and validation outputs. The current
base also introduces an append-only PCC ledger conflict; it is left unresolved
for a maintainer rather than rewritten or resolved by choosing a side.
[pcc:unverified]
