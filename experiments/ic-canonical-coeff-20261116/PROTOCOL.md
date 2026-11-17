# Canonical walk coefficient arithmetic

User scope: continue frozen-anchor/current/SIMD profiling and source optimization toward lower complete IC cost. This successor preserves all previous panels and failed controls.

Hypothesis: reduced u64 coefficients in BatchedWalker::next need no general u128 remainder. Only its two lane coefficient updates change. The private add_canonical helper assumes nonzero m and 0<=a,b<m; constructors, jump/pool generation and induction preserve this. For gap=m-b, a>=gap gives a-gap=a+b-m; otherwise a+b<m fits u64. General addmod and initialization remain unchanged. RNG, restart/order/cap/counters, group operations and all pipeline boundaries remain identical.

Baseline is immutable direct-m2 binary9f3228e66f36a4c20fff834ddcf98c81086dcb4c8e0e01e3c9e48b250f2b9f38, preparation20261117-020802-ae70, sourcea87e6243562955e3521923c95b4e9fe6afc6f075. Frozen anchor1026bf74 remains a separate reference. No claim that the exploratory baseline is signed or qualified.

First bounded preparation: one L4/4CPU/8GiB/900s allocation, same Rust/compiler/environment as baseline; compile cap780s, worker unit cap180s, other controls unchanged. Existing175map,15loader,512-state×5 walker, actual SIMD positive controls and overlapping framework/inverse tests retained. Six batched-walk-filter tests expected (one new canonical-add test). Exhaustive moduli1..128 plus fixed and randomized full-width edge cases compare against u128 reference. Existing independent Python arithmetic must replay2560states. Source manifest must differ from baseline only in batched_walk.rs. Failure/cap remains evidence, no allocation replacement.

Native timing is a separate later frozen protocol, published before new inputs. Planned comparison: anchor, baseline ordinary/inverse, candidate ordinary/inverse; fresh fixtures510..539, ten balanced method orders repeated3, five fields, same-point rho, A/A, source/routing/count identity and scalar/state replay. No reuse/repricing of480..509. No benchmark launch until exact controller, receipt, input identities and analysis rules are committed. Post-timing profiles test removal of BatchedWalker-to-__umodti3 calls without asserting other remainder uses disappear. Record all costs/failures and native confidence intervals separately from guest instructions. No GPU arithmetic performance inference from CPU work on a CUDA host.

| Requirement | Evidence |
|---|---|
| Remove measured remainder overhead | Scoped source patch, exact native disassembly/call edges |
| Preserve coefficient and walk behavior | Exhaustive/reference tests, stream controls and independent arithmetic replay |
| Compare native pipeline and collector | Separate frozen fresh panel, matched rho and retained A/A failures |
| Retain custody | Gate before launch; raw hashes/S3; closed benchmark records/report before promotion |

Known arithmetic engineering, no new curve/isogeny mechanism. Prior canonical curve catalog and route graphs remain unchanged. No current performance result for this successor.

Preparation amendment before launch: refreshed main adds an unrelated prime-field path dependency while its suite lock is unchanged. Local --locked test refused an update; failure retained as local-main-locked-failure-001.log. Do not change that dependency or the lock to fit this experiment. Reconstruct the full immutable baseline suite from preparation job020802/src.tar.gz and overlay only batched_walk.rs, asserting all16 source hashes differ only there; local counterpart uses git archive of exact baselinea87. Receipt pins baseline source archive and overlay. Current source revision identifies controller and overlay, while controlled_source identifies actual compiled tree. This preserves the one-change comparison and leaves main dependency work untouched.

The frozen tree includes C sources/build metadata and all path dependencies, not only suite/. Two local layout failures (missing hashed dependency, then missing C sources) are retained; full baseline archive reconstruction is the declared preparation method.

Preparation amendment002, before a replacement launch or any fresh input: attempt20261117-032103-5b3e was terminated by the producer after suspecting an omitted CFLAGS. Its fetched partial receipt proves environment match had already passed, including inherited CFLAGS=-g0. That suspicion was incorrect; producer interruption censored compilation. Retain the original2files, job metadata, status(exit1/50s) and termination receipt(sandbox137), without calling the preparation successful. Original receipt has no final status. Permit exactly one corrected bounded preparation002, same L4/4CPU/8GiB/900s and build780s caps, explicit --env CFLAGS=-g0, initialized status field and distinct outputbuild-optimized-002. No scientific timing or fresh targets were produced in001; replacement is a documented interruption recovery, not host selection or filtering timing data. Any002 failure remains evidence; do not replace it automatically. [pcc:unverified]
