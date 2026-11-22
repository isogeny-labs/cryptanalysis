# AES captured-corpus holdouts in `crax`

`crax aes-attack` accepts independent training and verification corpora for
the differential, linear, and Square techniques. Both files use the existing
versioned JSON corpus format. Each plaintext in the verification file must
be distinct from every training plaintext and every other verification
plaintext. The CLI rejects malformed model, technique, round-count, or block
fields before claiming acceptance.

Generate reproducible differential and linear training and holdout files:

```sh
crax --json aes-attack --technique differential --samples 24 \
  --export-pairs-file /tmp/differential-training.json \
  --export-verification-file /tmp/differential-holdout.json
crax --json aes-attack --technique linear --samples 64 \
  --export-pairs-file /tmp/linear-training.json \
  --export-verification-file /tmp/linear-holdout.json
```

Replay captured files, including checked artifact-store references:

```sh
crax --json aes-attack --technique differential \
  --pairs-file /tmp/differential-training.json \
  --verification-file /tmp/differential-holdout.json
crax --json aes-attack --technique linear \
  --pairs-file store:YOUR_TRAINING_NAME \
  --verification-file store:YOUR_HOLDOUT_NAME
```

For the two-round differential model, the command recovers four last-round
key bytes. `holdout_constraints_verified` checks their differential
constraints on the separate corpus; it does not turn those bytes into a full
AES-128 key. An external corpus without a supplied reference key retains
`status: candidate`. For the one-round linear model, the command recovers a
complete key and `holdout_verified` checks encryption of every separate
plaintext. `verification_pairs` is zero and the holdout field is null if no
verification file was supplied.

The [local and live S3 acceptance receipt](CRAX_AES_HOLDOUT_S3_ACCEPTANCE_20261023.json)
records generated and replayed corpora, fresh-cache store references, remote
download verification, changed-ciphertext rejection, plaintext-overlap
rejection, and exact S3 acceptance-prefix cleanup.
