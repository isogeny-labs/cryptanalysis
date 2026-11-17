# Storage route for these frozen runs

The root artifact configuration still names the absent legacy bucket. These
studies use the authenticated default profile and crypto-autoresearcher store in
us-west-2. Keep the override scoped to these inputs; this change does not migrate
unknown legacy objects or CI credentials.

```sh
env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_SESSION_TOKEN \
  -u ARTIFACTS_AWS_ACCESS_KEY_ID -u ARTIFACTS_AWS_SECRET_ACCESS_KEY \
  AWS_PROFILE=default AWS_REGION=us-west-2 AWS_DEFAULT_REGION=us-west-2 \
  ARTIFACTS_REMOTE=s3://crypto-autoresearcher/store \
  ARTIFACTS_CACHE=/tmp/ic-inverse-regression-cache \
  python3 tools/artifacts/artifacts.py pull --jobs 16 \
  experiments/ic-compact-pair-table-20261116
```

Use the same scoped route for experiments/ic-inverse-regression-20261116.
Every bundle receipt also records explicit object URIs and per-file SHA-256.
Closed benchmark records retain explicit URIs and uploaded flags. PDF/PNG bytes
are unchanged; current-tree pointers satisfy store policy. Historical PDF links
in the merged PR bodies remain pinned to the publication commits.

CI's configured AWS identity currently reports an invalid token and403 errors;
the local working profile does not refresh those GitHub secrets. No credentials
are copied into repository files, logs or CI settings. See ../ic-canonical-coeff-20261116/ci-parent-excerpts.json
for the separate CI failures. The source experiments remain unsigned and invalid
for qualified performance promotion. [pcc:unverified]
