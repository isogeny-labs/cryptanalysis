# Fresh per-run dependency-cache reuse after failed full01

Additive implementation notes,2026-11-12,before the cache-path change or
full02. Original protocol75eacc and every scientific acceptance criterion
remain unchanged. Full01/4a80d5 is NOT accepted:its checker five-minute
guard expires while rebuilding the existing isogeny_algos release library.
All original sources/logs/receipts are preserved in one intact79644-byte
archive;its S3 publication is pending. [pcc:unverified]

The completed native phase and failed checker build use the same exact
isogeny_algos fingerprint f3ae16f7bbabf025,source path,toolchain,empty feature
set,profile and rustflags. The completed native cache already contains its
release rlib. Use the fresh per-run native target directory for the checker
as well,so Cargo can reuse that exact existing engine dependency. The checker
source and algorithm remain independently encoded;it intentionally reuses
the same old arithmetic engine,as the original protocol already states.

The target directory is still isolated from the workspace,other replay
attempts and other CI jobs. No external/preexisting binary is substituted.
Keep the outer30-minute bound,native/algebra15-minute bounds,proof10-minute
bound,checker5-minute test and CLI bounds,all41/23ten/39module224compiled/
198written0trusted/checker4+CLI/hash/no-rg/byte-comparison conditions.
Run a complete full02,including all earlier phases and final guards;do not
promote full01 partial phases or its late hashes as complete acceptance.
[pcc:unverified]

Storage review: docs/artifacts.md explicitly documents same-repository PR
artifact-autofix migration using the trusted base tool/policy. The current
crypto artifact-autofix run43299290714 succeeds including push-token and S3
upload/replay checks. Local AWS CLI is absent. Use that existing documented
route for intact oversized archives;keep artifact gates pending until the
workflow has uploaded,replayed and committed real manifests. Do not invent
an S3 pointer,split/prune the raw archive,change the policy,add a bypass
label or treat a pending migration as complete. [pcc:unverified]
