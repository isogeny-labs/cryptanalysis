# CLI progress and resume

The native `cryptanalysis` (also installed as `ca`) command prints its final
JSON result on stdout. With `--verbose`, it also prints periodic progress to
stderr. Run state is kept in a dedicated directory and can be mirrored to an
S3 prefix with the AWS CLI installed and configured on the host.

## Pollard rho

```sh
cryptanalysis rho --group zp --p 1019 --order 509 --g 4 --h 818 \
  --seed 1984 --verbose --progress-every 5 \
  --state-dir ./runs/rho-001 --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/rho-001 --sync-every 60
```

After interruption, repeat the same group, base, target, seed, and walk
parameters with `--resume`. The operation cap can be increased:

```sh
cryptanalysis rho --group zp --p 1019 --order 509 --g 4 --h 818 \
  --seed 1984 --state-dir ./runs/rho-001 --resume --max-ops 1000000 \
  --s3-uri s3://my-bucket/cryptanalysis/rho-001
```

`solve --alg rho` accepts the same options. `--verbose` also works without a
state directory. The durable flags are currently available for native rho and
kangaroo; other `solve` algorithms reject them.

For a walking run, the directory contains `manifest.json`, `rho.dp` (a
versioned, checksummed distinguished-point table),
`rho.dp.progress.json`, and `result.json`. Trivial inputs resolved before
the walk have the manifest and result, and can be recomputed on resume. The
checkpoint binds the full group identity, base, target, resolved walk settings,
and effective seed. Resume starts fresh worker lanes against saved
distinguished points; it does not preserve lane positions. Group-operation
and elapsed-time counters accumulate across resumed runs, including setup on
each invocation. The local checkpoint is written atomically and completed
before the final result is reported. A checkpoint or progress write failure
ends the run with an error.

The S3 prefix is an asynchronous copy of the local directory at
`--sync-every` intervals. The command also attempts a final sync and reports
failure if that upload fails. If a process or host stops before the next sync,
local state may be newer than S3. Resume prefers an existing local checkpoint;
if it is absent, the command restores from S3 after checking any local run
manifest. Use one run per directory and S3 prefix. The state directory is
locked against concurrent local writers.

## Pollard kangaroo

For interval searches, use `kangaroo` or `solve --alg kangaroo`:

```sh
cryptanalysis kangaroo --group zp --p 1019 --order 509 --g 4 --h 818 \
  --lo 0 --hi 508 --seed 17 --verbose --progress-every 5 \
  --state-dir ./runs/kangaroo-001 --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/kangaroo-001 --sync-every 60
```

Repeat the group, base, target, interval, seed, herd, jump, and distinguished
point settings with `--resume`. The saved `kangaroo.ckpt` includes exact herd
positions, RNG state, distinguished points, cumulative counters, and a
checksum. A resumed run recreates the jump table and continues the same
herds. `kangaroo.ckpt.progress.json` and `result.json` provide readable
status. Tiny intervals handled by a direct scan have only the manifest and
result; resume recomputes them. The local/S3 sync and locking rules above
apply to kangaroo as well.

## Index calculus

The linear-sieve `ic` command also accepts `--verbose`, `--progress-every`,
`--state-dir`, `--resume`, `--s3-uri`, and `--sync-every`. Its run state is a
relation journal and precomputation artifact. Its random-exponent method does
not support durable state. See the `ic` section of the CLI help for arguments.
