# `crax`: the command line

`crax` is the toolkit's single entry point. It has one subcommand per attack.
The generic discrete-logarithm solvers run on the C library in `src/`. They
work over 64-bit groups and are the source of the measured constants in
[BENCHMARKS.md](BENCHMARKS.md). Everything else runs on the Rust attack suite
in [`suite/`](../suite/README.md), which uses arbitrary precision.

```sh
cd suite && cargo build --release --bin crax
./target/release/crax --help
```

The same binary is built by `make suite`.

**Conventions:**

- Every command accepts `--json`. Native `crax` commands return structured
  fields. Older research commands return one JSON envelope with their native
  output in `report_text`, diagnostics in `diagnostics_text`, and an exit code.
- Native solver commands check any answer they mark solved independently of
  the solver that produced it. For a discrete log, one scalar multiplication
  or exponentiation checks it. For a factor, a multiplication checks it. For a
  message, re-encryption checks it. Their report says `"verified": true`, and
  an unverified answer exits non-zero. Older research commands retain their
  own report and verification conventions.
- Problems can be given completely (`--g`, `--h`, `--q`), or generated from a
  planted secret (`--x`). With a planted secret, the report also says whether
  the planted value was recovered.
- Integers are decimal or `0x` hex. The factoring commands also accept
  expressions such as `2^227-1`, `(2^239+1)/3` or `3*10^40+7`.
- A size that an implementation cannot finish in reasonable time is refused,
  with the measured numbers, instead of being started. `--force` overrides
  this for the sieves and `--max-log2-ops` for the curve solvers.

## The command tree

| family | commands |
|---|---|
| discrete logs, generic (C library, p < 2^64) | `bsgs`, `rho`, `kangaroo`, `grumpy`, `precomp`, `glv`, `pohlig-hellman` (`ph`, `dlog`), `cheon`, `gpu-rho` |
| weak curves, any size | `ecdlp` (singular, Smart anomalous, Pohlig–Hellman, MOV/Frey–Rück) |
| ECDSA signature attacks | `ecdsa nonce-reuse \| hnp \| audit \| invalid-curve` |
| factoring | `factor`, `gnfs`, `snfs`, `qs`, `ecm`, `pm1` (`--pp1`), `rho-factor` |
| RSA | `rsa fermat \| wiener \| from-d \| hastad \| common-modulus \| small-e \| batch-gcd` |
| index calculus | `ic zp` ((Z/pZ)^*, C library), `ic prime \| run \| compare \| fixed \| workflow \| boundary \| bench \| rho \| descent \| corpus \| budget \| ...`, `icx` |
| sibling crypto integration | `ecdlp-nist`, `ic` / `icx` `solve-prime \| solve-prime-file \| solve-cubic \| prime-route-generate \| cubic-graph \| cubic-route-generate`, `isogeny-walk`, `store`, `crypto` |
| curves and challenges | `curve names \| info`, `challenge list \| show \| solve \| rho-job` |
| symmetric and hash | `aes-attack`, `aes-sbox-table`, `hash`, `list-ciphers`, `auto`, `boomerang`, `rectangle`, `sbox`, `aes-related-key`, `hash-auto`, `length-extension` |
| lattice and post-quantum | `mlwe` |
| isogenies | `isogeny` |
| distributed rho | `rho-collab` |
| demos and research bench | `visual-all`, `aes-visual-demo`, `bench`, `ec-challenges` |

The symmetric, lattice, isogeny, distributed rho, and demo rows, plus native
`ic`/`icx`, are the older research command lines:
`ca-suite`, `ca-ic` and `ca-icx`. `crax` passes their arguments through to
them unchanged, and their `--help`, flags and report formats are their own.
The old binary names still work.

The sibling crypto commands above execute the corresponding
`ecdlp-nist`, `ic`, `icx`, `isogeny_walk`, or `crypto` binary. `crax` first uses an explicit
`CRAX_ECDLP_NIST_BIN`, `CRAX_IC_BIN`, `CRAX_ICX_BIN`, `CRAX_ISOGENY_WALK_BIN`, or `CRAX_CRYPTO_BIN`
path, then a binary beside its own executable, then `PATH`. A release bundle
can therefore put all six binaries in one directory without extra setup.
`crax` forwards arguments directly, preserves
the child exit status, and wraps its JSON or text report when `--json` is
requested. The native `crax icx` catalog and run commands remain in the suite.
The [co-located release-bundle acceptance](CRAX_SIBLING_BRIDGE_ACCEPTANCE_20261023.json)
checks all four sibling executables, public prime and cubic EC solves, an S3
completion-marker lookup, and a fresh-cache S3 artifact read through `crax hash`.

Build `ecdlp-nist` in the sibling crypto checkout with
`cargo build --release --bin ecdlp-nist`. The bridge forwards `list`, `audit`,
`solve`, `smart`, and `bench` directly, including checked `--point-file`
references and the native feasibility bounds. For example:

```sh
crax --json ecdlp-nist solve P-256 --secret 12345 --interval-bits 16
```

With `--json`, the verified solve result is in `report.report`; the outer
envelope records the child exit code and diagnostics.

For an explicit public EC target, install the sibling `ic` executable or
set `CRAX_IC_BIN`, then run:

```sh
crax --json ic solve-prime --p 271 --a 1 --b 19 --n 281 \
  --gx 3 --gy 7 --qx 231 --qy 54
```

The bridge also accepts `prime-route-generate`, `cubic-graph`, and
`cubic-route-generate` through either `crax ic` or `crax icx`. Route generation
returns the native JSON route file inside the `report` field when `crax --json`
is used; save that field as a JSON file before passing it to `--route-file`.
It accepts `solve-prime-file --input FILE`, including checked
`store:NAME` and `sha256:DIGEST` inputs, and `solve-cubic`; `crax icx` accepts
all three commands too. Use
`crax store` for the content-addressed S3 push, verify and pull commands, and
`crax isogeny-walk` for route enumeration and verification.
The [current-head S3 bridge receipt](CRAX_PRIME_ROUTE_S3_ACCEPTANCE_20261024.json)
checks `crax store` upload, remote HEAD and byte verification, and fresh-cache
pull for both a public prime target and certified route. `crax --json ic
solve-prime-file` then consumes their `store:` names and returns scalar 190,
`verified: true`, and two verified route edges in its child report. The
isolated acceptance prefix was empty after exact-object cleanup.
The sibling cubic solver also accepts a checked monic irreducible modulus.
For `p=11`, `"modulus": [1,0,4]` selects `F_11[t]/(t³+4t²+1)`.
`crax --json ic solve-cubic` and `crax --json icx solve-cubic` both return
verified scalar 5 on the sibling `cubic_f11_public_target.json` fixture,
including fresh-cache `store:` input replay. The [sibling release and S3
receipt](https://github.com/aburan28/crypto/blob/e34a4a66286/docs/store/CUBIC_GENERAL_MODULUS_S3_ACCEPTANCE_20261024.json)
records those runs. The sibling `ic` and `icx` now also enumerate cubic
isogeny j-graphs, generate checked degree-2 routes, and solve across those
routes for an explicit irreducible cubic modulus. The
[routed F11 S3 receipt](https://github.com/aburan28/crypto/blob/a273e3f558f/docs/store/CUBIC_ROUTED_GENERAL_S3_ACCEPTANCE_20261024.json)
records target and route upload, byte verification, fresh-cache `store:`
solves through both binaries, scalar 5 with IC and same-target rho, and
exact-object cleanup. Use `crax --json ic cubic-graph` and
`crax --json ic cubic-route-generate` to get the corresponding child reports;
save each child `report` JSON before using it as a graph or route file.

`crax aes` now exposes both sibling AES families. Block encryption and
decryption, CTR, CBC, and GCM commands go to `crypto aes`; AES attack and
analysis commands go to `crypto cryptanalysis`. For example,
`crax aes block-encrypt --help` and `crax aes aes-attack --help` show the
respective native options. `crax aes --help` lists both families, and
`CRAX_CRYPTO_BIN` selects the sibling `crypto` executable if it is not
adjacent to `crax` or on `PATH`. With `crax --json aes block-encrypt ...`,
the native hexadecimal result appears as `report.output_hex`, alongside
`report.operation` and the producer exit status.

```sh
CRAX_CRYPTO_BIN=/path/to/crypto crax --json aes block-encrypt \
  --key-hex 000102030405060708090a0b0c0d0e0f \
  --hex 00112233445566778899aabbccddeeff
```

For that AES-128 known-answer vector, `report.output_hex` is
`69c4e0d86a7b0430d8cdb78070b4c55a`.

`crax mac` forwards keyed digest commands to `crypto mac`, including
HMAC-SHA-256, KMAC128, KMAC256, and their XOF variants. Use `--key-file`
for a secret key or `--key-hex` for a public test vector. A successful
`crax --json mac kmac128 ...` result carries `report.algorithm` and
`report.tag_hex`; tag verification retains the native success or failure
exit code and its text report.

### Resumable isogeny experiment sweeps

`crax isogeny experiment` accepts `--state-dir` for a checkpoint after each
completed starting curve. Add `--s3-uri` to publish and resume that state in
S3. Use a unique run ID under the Setec production schema
`s3://setec-astronomy-artifacts/ic/v1/isogeny-experiments/<run-id>`. For a
bounded first run and restore into an empty local directory:

```sh
crax isogeny experiment --bits 9 --trials 2 --ell-list 2 --rho-cap 1024 \
  --state-dir /tmp/crax-isogeny-run --max-new-curves 1 \
  --s3-uri s3://setec-astronomy-artifacts/ic/v1/isogeny-experiments/YOUR_RUN_ID
crax isogeny experiment --bits 9 --trials 2 --ell-list 2 --rho-cap 1024 \
  --state-dir /tmp/crax-isogeny-restored --resume \
  --s3-uri s3://setec-astronomy-artifacts/ic/v1/isogeny-experiments/YOUR_RUN_ID
```

The first command reports `status: partial`; the second reports
`status: complete` and includes the full experiment report. Progress goes to
stderr. The checkpoint is atomically replaced under a local writer lock and
binds the complete configuration, generated curve sequence, and running
executable's BLAKE3 digest. S3 uploads immutable
`generations/<N>/checkpoint.json` objects, then conditionally publishes
`_isogeny_head.json` last. The head names the generation, size, BLAKE3 digest,
and an explicit `complete` marker. Resume checks the head and downloaded bytes
before accepting remote state, ignores unpublished generations, and rejects
changed inputs, binaries, corrupt state, or concurrent head changes. A local
checkpoint one generation ahead of the remote head can be published on resume
after matching the remote prefix. Set `AWS_PROFILE` and `AWS_REGION` for the
bucket (`us-east-2` for Setec). `--s3-uri` requires `--state-dir`; omitting it
keeps checkpoints local.
The [release CLI acceptance receipt](CRAX_ISOGENY_RESUME_ACCEPTANCE_20261023.json)
records a partial run, an exact-match resume versus a fresh sweep, the
`crax --json` envelope, and rejection of changed configuration, changed
executable, and damaged checkpoint bytes.
The [live Setec S3 receipt](CRAX_ISOGENY_S3_RESUME_ACCEPTANCE_20261023.json)
records the isolated prefix, partial and complete heads, fresh-local restores,
stray-generation rejection, exact report replay, and object cleanup.

Native `crax rho-collab work/status --job` accepts a local public job document
or a checked `store:NAME` or `sha256:DIGEST` reference. Store references are
resolved through `CRAX_CRYPTO_BIN` and limited to 64 KiB of JSON. Mutable
mailbox and Cairn state stay in local paths; with a store job, the default
Cairn state directory is `--mailbox` if set, otherwise the current directory.
The live round trip is recorded in
[`CRAX_RHO_JOB_S3_ACCEPTANCE_20261023.json`](CRAX_RHO_JOB_S3_ACCEPTANCE_20261023.json).

## SHA and AES commands

```sh
crax --json hash --algorithm sha256 --text abc
crax --json hash --algorithm sha3-384 --hex 616263
crax hash --algorithm shake256 --text abc --output-bytes 32
crax hash --algorithm streebog-256 --text abc
crax hash --algorithm skein512 --file ./message.bin --output-bytes 64
crax hash --algorithm cshake256 --text abc --output-bytes 32 --custom-hex 637573746f6d
crax --json hash --algorithm sha256 --file store:public/message.bin
crax --json aes-attack --technique differential --samples 4096
crax --json aes-attack --technique linear --samples 4096
crax --json aes-attack --technique square
crax aes --help
crax aes aes-distinguisher --help
crax aes aes-dfa --help
crax --json aes-attack --technique differential --samples 24 \
  --export-pairs-file /tmp/aes-differential.json
crax --json aes-attack --technique differential \
  --pairs-file /tmp/aes-differential.json
crax --json aes-attack --technique linear --samples 64 \
  --export-pairs-file /tmp/aes-linear.json
crax --json aes-attack --technique linear --pairs-file /tmp/aes-linear.json
crax --json aes-attack --technique square --square-sets 3 \
  --export-pairs-file /tmp/aes-square-training.json \
  --export-verification-file /tmp/aes-square-heldout.json
crax --json aes-attack --technique square \
  --pairs-file /tmp/aes-square-training.json \
  --verification-file /tmp/aes-square-heldout.json
crax --json hash-auto --hash sha256
crax --json hash-auto --hash sha3-256
crax --json hash-auto --hash sha-3-512
crax --json hash-auto --hash blake2s --output-bytes 1
crax --json hash-auto --hash cshake256 --output-bytes 1 --custom-hex 74657374
crax --json aes-sbox-table --kind ddt --row 1
crax --json aes-sbox-table --kind lat > aes-lat.json
crax --json aes-sbox-table --kind bct --row 1
crax --json aes-sbox-table --kind dlct > aes-dlct.json
```

`crax aes` forwards the sibling `crypto cryptanalysis` command family. Its
[bridge acceptance](CRAX_AES_BRIDGE_ACCEPTANCE_20261024.json) checks that the
help lists the observed differential and linear, DFA, power, cache, trail,
and distinguisher commands; DDT, LAT, BCT, and DLCT row reports match the
producer exactly; a zero-correlation command succeeds; and an unknown
command exits unsuccessfully.
The separate [observed AES bridge receipt](CRAX_AES_OBSERVED_BRIDGE_ACCEPTANCE_20261024.json)
uses the committed differential and linear statistics fixtures. Both measured
reports match the direct producer command exactly, with input and report
digests recorded.

For `hash --file`, a local path or indexed `store:NAME` and `sha256:DIGEST`
reference is accepted. The latter uses the sibling `crypto store pull`
command through `CRAX_CRYPTO_BIN` (or `crypto` on `PATH`), so the artifact is
fetched and digest-checked before `crax` hashes it. Set the sibling store's
remote, index, cache, and AWS profile as needed. A public Setec S3 acceptance
receipt is in [`CRAX_HASH_STORE_S3_ACCEPTANCE_20261023.json`](CRAX_HASH_STORE_S3_ACCEPTANCE_20261023.json).
The 16 native digest names process file input incrementally in 64 KiB
chunks. The additional 14 digest names use the sibling `crypto` file reader,
which also reads in 64 KiB chunks. The [native streaming hash acceptance receipt](CRAX_HASH_STREAM_S3_ACCEPTANCE_20261023.json)
records 272 local cross-implementation comparisons and a fresh-cache S3
push, existence check, download, and hash round trip for every digest.

`hash` accepts a single `--text`, `--hex`, or `--file` input. `sha-3-*` and
`shake-*` names are accepted. `--output-bytes` is required for SHAKE and
cSHAKE, and bounded to 1 MiB. It is optional for BLAKE2 and Skein.
`hash-auto` runs length-extension demonstrations for hashes with an implemented
adapter (MD4, MD5, SHA-1, SHA-256, SHA-512). It runs bounded truncated birthday
searches and differential-bias measurements for the supported unkeyed digests.
These searches concern up to 32 output bits and do not claim a full-output
collision. Each found pair includes both input messages as hex, the shared
digest prefix, the search seed, and the trial cap so it can be replayed.
The [CLI replay receipt](CRAX_HASH_AUTO_REPLAY_ACCEPTANCE_20261024.json)
checks reported pairs for all 30 supported unkeyed names through the
independent `crax hash` command, including cSHAKE customization.
SHAKE, cSHAKE, and Skein require `--output-bytes` in 1..=64;
BLAKE2b and BLAKE2s allow 1..=64 and 1..=32 respectively, defaulting to their
maximum digest sizes. cSHAKE also accepts `--function-name-hex` and
`--custom-hex`, and the report records both inputs. SHA-3 uses a sponge, so
Merkle-Damgård length extension does not apply. `aes-sbox-table` exports exact 256-by-256 AES S-box DDT, LAT, BCT, and DLCT tables, or one input row. DDT counts XOR transitions, LAT gives signed linear imbalance, BCT counts boomerang switches, and DLCT gives half the signed differential-linear parity sum. `aes-attack` runs verified key recovery on the implemented
AES-128 reduced-round differential (2), linear (1), or integral (4) models.
For captured reduced-round data, `--pairs-file` accepts a JSON object with
`schema_version: 1`, `cipher_model: "aes128-reduced-final-no-mixcolumns/v1"`,
`technique: "differential"` and `rounds: 2`, or `technique: "linear"` and
`rounds: 1`. The differential `pairs` array contains objects with `p0`, `p1`,
`c0`, and `c1`; linear pairs use `plaintext` and `ciphertext`. Every block is
exactly 32 hex digits. Differential input pairs must differ by `--alpha` in
byte 0 only. The file is capped at 64 MiB and one million pairs.
`--export-pairs-file` writes generated data in the same schema to a new file.
`--pairs-file` also accepts a checked `store:NAME` or `sha256:DIGEST` reference
through the sibling `crypto store pull` command; publish an exported file
with `crypto store push` first. On imported linear data, the recovered master
key is checked against every supplied ciphertext. Imported differential data
yields four last-round key bytes with a whole-corpus difference check; it
does not yield the other 12 key bytes. Supply `--key-hex` only if a reference
key is available for an additional check. Square accepts the same versioned
corpus envelope with `technique: square`, `rounds: 4`, and `plaintext` /
`ciphertext` pairs. It requires 1–6 complete 256-value lambda sets with
distinct training plaintexts, recovers the four-round key without an oracle,
and replays the recovered key against every pair. `--verification-file`
accepts separate held-out pairs and reports `verified` only when all replay
and the plaintexts are distinct. `--square-sets` controls generated training
sets; `--export-verification-file` writes one separate held-out set.
The [AES corpus acceptance receipt](CRAX_AES_CORPUS_ACCEPTANCE_20261023.json)
records local differential and linear round trips and a fresh-cache Setec S3
retrieval through the checked store resolver, followed by exact-object cleanup.
The [Square corpus acceptance receipt](CRAX_AES_SQUARE_CORPUS_ACCEPTANCE_20261023.json)
records cross-CLI recovery, malformed-corpus controls, and a checked S3
artifact round trip.
These commands do not imply key recovery against full-round AES-128 or a
collision against full-output SHA-2 or SHA-3.
The [AES S-box cross-check](CRAX_AES_SBOX_CROSSCHECK_20261022.json) compares
all 65,536 entries of each DDT, LAT, BCT, and DLCT export with the sibling
`crypto` release CLI and checks selected one-row exports against full tables.

## Coverage of the cross-repository CLI path

| Requested surface | Available command | Current boundary |
| --- | --- | --- |
| SHA-256, SHA-3, and related digests | `crax hash` | Native text, hex, local-file, and checked `store:` file inputs for SHA-1, SHA-2, SHA-3, SHAKE, BLAKE3, MD4, and MD5. BLAKE2b/s, cSHAKE128/256, SM3, RIPEMD-160, Streebog-256/512, Whirlpool, Tiger/Tiger2, and Skein-256/512/1024 use the sibling `crypto` executable through `CRAX_CRYPTO_BIN` or `PATH`. The sibling file path streams input in bounded chunks. SHAKE and cSHAKE output is limited to 1 MiB per call. |
| Hash cryptanalysis | `crax hash-auto`, `crax length-extension` | MD4/5, SHA-1/256/512 length extension where implemented; bounded truncated birthday search and differential-bias measurements for supported unkeyed hashes, including SHA-2/3, SHAKE/cSHAKE, BLAKE2/3, Skein, SM3, RIPEMD-160, Streebog, Whirlpool, and Tiger. A missing length-extension adapter is reported explicitly. |
| AES differential and linear analysis | `crax aes-attack`, `crax aes-sbox-table`, `crax sbox`, `crax auto`, `crax aes <command>` | The full AES S-box DDT, LAT, BCT, and DLCT or a selected row are exported as JSON. Key-recovery examples use the implemented one-, two-, or four-round AES-128 models. `crax aes` exposes the sibling `crypto cryptanalysis` AES command family, including observed differential and linear analysis, distinguishers, power and cache analyses, DFA, trail checks, and related-key experiments, with the producing executable's parameter and evidence limits. |
| Standardized-curve ECDLP | `crax ecdlp-nist list/audit/solve/smart/bench` | Delegates to the sibling `ecdlp-nist` executable. External points and checked target artifacts follow its bounded interval and feasibility rules. |
| Explicit EC index calculus | `crax ic solve-prime`, `crax ic solve-prime-file`, `crax ic solve-cubic`; `crax icx` aliases | These delegate to the sibling `ic` or `icx` executable and inherit its checked field-size and work-budget limits. Prime and cubic target files may be checked store references. The cubic command accepts either a noncube binomial or a checked irreducible monic cubic modulus, counts the full curve order, and requires a cofactor invertible modulo the target subgroup order. `crax ic zp` remains multiplicative-group index calculus. |
| Isogeny graph enumeration and route checks | `crax isogeny-walk`; `crax ic solve-prime --route-file ... --route-id ...`; `crax ic solve-cubic --route-file ... --route-id ...` | The sibling walker enumerates and verifies prime-field routes; the prime and cubic IC commands check point transport along selected certified routes within their documented degree and field bounds. |
| Collaborative rho job artifacts | `crax rho-collab work/status --job store:NAME` | Native job loading uses the sibling `crypto store pull` to check the indexed digest before parsing; job JSON is limited to 64 KiB. Mutable worker state is local. |
| Artifact upload, existence verification, and retrieval | `crax store push`, `crax store verify --remote --download`, `crax store pull`; `crax isogeny-walk publish/exists/fetch` | Sibling `crypto` store and walker require configured AWS credentials. Public-artifact round trips and the `crypto` store's live multipart upload, HEAD, downloaded-byte verification, and cleanup have Setec S3 receipts in the sibling repository. |

The release CLI matrix for SHA-256, SHA-3, SHAKE, BLAKE3, bounded hash
analysis, AES recovery modes, distinguishers, and DDT/LAT/BCT/DLCT row
agreement is recorded in
[`CRAX_HASH_AES_ACCEPTANCE_20261023.json`](CRAX_HASH_AES_ACCEPTANCE_20261023.json).
The [extended hash bridge receipt](CRAX_HASH_BRIDGE_S3_ACCEPTANCE_20261023.json)
compares all 14 additional digest names with the sibling `crypto` release
binary on a 1,048,577-byte file. The checked input was fetched through a
fresh S3-backed cache; upload, remote downloaded-byte verification, exact
object cleanup, and empty-prefix listing passed. CRAx's native Streebog
library implementation was corrected and separately passed both RFC 6986 M1
known-answer tests after converting the RFC's displayed bit-string order to
the conventional byte-oriented API.

The native cryptanalysis commands and the sibling bridges have separate build
dependencies. Put the sibling `crypto`, `ic`, `icx`, `isogeny_walk`, and `ecdlp-nist` binaries
beside `crax`, install them on `PATH`, or set their `CRAX_*_BIN` paths before
using the corresponding rows. The
explicit field ranges and reproducible public inputs are documented in the
sibling `crypto:docs/ic/EXTERNAL_TARGET_CLI.md`; its
`crypto:docs/store/README.md` defines the Setec S3 prefix and receipts.

## Discrete logarithms on the C library

```text
$ crax rho --p 2000000579 --order 1000000289 --x 123456789 --threads 2
rho: x = 123456789  (verified: g^x = h)
  group    Z_p^* p=2000000579 order=1000000289
  g        1422302461
  h        1216411080
  planted  recovered
  work     38523 group ops, 1063 table entries, 0.017 s, 2 thread(s), 1.218 ops/sqrt(width)

$ crax glv --curve glv-j0-26 --x 999999
glv-rho: x = 999999  (verified: g^x = h)
  group    E(F_p) p=67108933 a=0 b=7 order=16773703
  ...
  note     endomorphism J0: walk folded by an automorphism group of order 6 (rho speed-up 2.4495)

$ crax kangaroo --p 2000000579 --order 1000000289 --x 500123 --lo 500000 --hi 600000
$ crax cheon --p 2000000579 --order 1000000289 --alpha 987654321
$ crax ic zp --p 1099511627791 --g 3 --x 99
$ crax curve info --name glv-j0-26
```

Every solver checks on entry that both elements lie in the order-n subgroup.
A target outside ⟨g⟩ is refused at once; previously it made rho, glv, gpu-rho
and Pohlig–Hellman run forever. `kangaroo` bounds its walk at 128·√width
unless `--max-ops` is given, because a target outside the interval never
meets the tame herd.

## Weak curves of any size: `crax ecdlp`

`ecdlp` analyses a prime-field curve and then runs the cheapest attack whose
preconditions hold:

- the singular-cubic map to (F_p, +), F_p^\* or the norm-one torus;
- Smart's p-adic attack on anomalous curves;
- Pohlig–Hellman with BSGS / rho in each prime subgroup;
- on request, MOV / Frey–Rück to F_{p^k}^\* with a Tate pairing.

A curve without any of these weaknesses is refused, and the report gives the
reason for each check:

```text
$ crax ecdlp --curve p256 --x 5 --analyze-only
ecdlp on a 256-bit prime field: not solved
  Singular       no  4a³ + 27b² ≢ 0 (mod p): the curve is non-singular
  Smart          no  ord(G) ≠ p: not anomalous
  PohligHellman  no  ... largest prime factor 256 bits; Pohlig–Hellman needs ≈2^128.3 group operations (exceeds the 2^34 budget)
  Mov            no  embedding degree of the largest prime factor exceeds 12: MOV/Frey–Rück gives no usable transfer
```

MOV really does move the logarithm into F_{p^k}^\*. The finite-field solver
here is generic, though, not index calculus, so MOV is reported as a weakness
but never chosen on cost.

## ECDSA signature attacks: `crax ecdsa`

These are *implementation* attacks: they exploit how the per-message nonce
`k` is produced, not the ECDLP on the curve. Every command reconstructs the
private scalar and then **verifies it independently** — `d·G == Q`, or by
re-deriving the signatures — and reports `"verified": true` only on success.
Each takes a named curve (`--curve secp256k1|p256|sm2`) or a full custom curve
(`--p --a --b --gx --gy --order`), and a `--demo` mode that plants a key with
the stated weakness and recovers it (so there is always something runnable).

**`nonce-reuse`** — two signatures that reused one nonce `k` on hashes
`z1, z2` share the same `r`; then `k = (z1−z2)/(s1−s2)` and
`d = (s1·k−z1)/r`, both mod `n`. Give `--r --s1 --s2 --z1 --z2` (and optional
`--q x,y` for a `d·G == Q` check; otherwise the two signatures are re-derived
from the recovered `(k, d)`):

```text
$ crax ecdsa nonce-reuse --demo
ecdsa nonce-reuse on secp256k1
  r        55778340832446138752524611825738996659700884378540138182536574743701968198492
  nonce k  16045690984503098046
  key d    1311768467463790320 (d·G == Q)
```

**`hnp`** — biased-nonce key recovery through the hidden number problem,
driving `cryptanalysis::hnp_ecdsa` and the lattice reduction in
`cryptanalysis::lattice`. The supported leak model is *known high bits are
zero*: each nonce satisfies `k < 2^k_bits`, stated with `--k-bits`. Give a
transcript as repeated `--sig r,s,z` plus `--q x,y`; pick the reduction with
`--reduction lll|bkz|lll-hp` (`--bkz-beta` for BKZ). `--demo` plants a
64-bit-bias P-256 stream and recovers `d`:

```text
$ crax --json ecdsa hnp --demo
{"status":"ok","curve":"P-256","signatures":8,"k_bits":192,"bias_bits":64,"reduction":"lll","d":"…","verified":true}
```

**`audit`** — run the `cryptanalysis::ecdsa_audit` transcript auditor: a
chi-squared bias score, then a `k_bits` sweep that recovers the key if a bias
is present. Reports `no_bias`, `bias_suspected`, or `key_recovered`
(verified). A well-implemented RFC 6979 stream scores near zero and returns
`no_bias`.

**`invalid-curve`** — the real oracle invalid-curve attack (see
`cryptanalysis::invalid_curve_attack`). Against a black-box scalar-multiply
oracle `d·P`, it crafts points of small prime-power order on the weak sextic
twists of a j-invariant-0 base curve, queries the oracle, solves each small
subgroup DLP, CRTs the residues, and confirms `d·G == Q`. The attack code
never sees `d` — `--secret` feeds only the honest oracle. Twist enumeration is
`O(p)`, so the base prime must be small; `--demo` uses a built-in 16-bit
curve:

```text
$ crax --json ecdsa invalid-curve --demo
{"status":"ok","base_curve":"j0-demo-16bit","n_base":"65521","twists_total":6,"twists_used":6,"bits_recovered":26.0,"d":"12345","d_partial":"12345","verified":true}
```

## The challenge corpus: `crax challenge`

`challenge solve <id>` reads what a record in
[`challenges/ecc/`](../challenges/ecc/README.md) says about its curve. That
includes the trace, embedding degree, endomorphism and subgroup order. From
that it picks an attack:

- the C library's GLV or Pohlig–Hellman solvers below 2^64;
- Smart for anomalous curves;
- the arbitrary-precision attacks above 2^64.

It then verifies the answer. On `check`-tier records it also compares the
answer with the stored log.

```text
$ crax challenge solve fp-anomalous-b128
fp-anomalous-b128 (open): x = 95065309868721090666590822693085299358 (verified: [x]G = target)
  curve    128-bit field, 128-bit subgroup = 170141183460469232383923901789557442567
  checks   anomalous=true embedding_degree=large endomorphism=anomalous
  method   Smart (0.062 s)
```

Measured over all 98 prime-field records in the corpus (release build, one
core, 180 s cap):

- **All 47 `check`-tier records with p > 3 solve** and match their stored logs.
- **Nine `open`-tier records solve.** None of these has a published answer.
  - Smart's attack handles the anomalous curves at 64, 96, 128 and 192 bits,
    in 0.02–0.15 s each.
  - Pohlig–Hellman handles a 160-bit class-number-2 CM curve (67 s) and two
    small ones.
  - GLV rho handles two 61-bit j = 0 curves.
- **The rest are refused, with reasons.** They have no structural weakness and
  their largest prime subgroup exceeds the budget.
- **One record, `fp-j0-b64-volcano5-h2`, has no answer.** Its target is not in
  ⟨G⟩: the C library and the weak-curve attacks agree independently. The two
  characteristic-3 records are outside the prime-field solver.

The budget is 2^44 group operations on the C library and 2^28 on the
arbitrary-precision attacks; raise it with `--max-log2-ops`.

## Factoring

```text
$ crax factor '2^128+1'
340282366920938463463374607431768211457 (39 digits) = 59649589127497217 * 5704689200685129054721
  complete, product verified (1.800 s)

$ crax snfs '2^227-1'
snfs: 2156795733...3727 (69 digits) = 26986333437777017 * 79921777382...8631  (verified)
  polynomial  x^4 - 2 (degree 4, m = 144115188075855872, skewness 1.19, alpha 1.92)
  factor base rational 6611 primes (B = 66289), algebraic 6605 ideals (B = 66289), 48 quadratic characters
  sieve       5808 lines, 134201 relations (5733 full, 128468 from partials)
  matrix      134201 x 165810 -> 22632 x 22599 after filtering, 32 dependencies; 3 square roots tried
  time        polyselect 0.00 s, sieve 5.76 s, linear algebra 0.79 s, sqrt 0.43 s, total 7.14 s

$ crax gnfs '1000000000000000000000007*100000000000000000000000000031'   # 54 digits, 11.8 s
$ crax qs <n>        # SIQS: 50 digits ~1 s, 60 digits ~16 s
$ crax ecm <n> --b1 11000 --curves 64
$ crax pm1 <n> --b1 100000 --b2 10000000      # --pp1 for Williams p+1
$ crax rho-factor <n>
```

These sieves are **educational scale**. They have no lattice sieve, no double
large primes, no Block Lanczos and no Kleinjung polynomial selection. At every
size both can reach, the quadratic sieve here beats GNFS, so `factor` uses the
QS up to 100 digits. Sizes where a sieve is impractical are refused unless
`--force` is given: GNFS above 65 digits, SNFS above 90 and the QS above 75.
The measured timings and the full list of limitations are in the module
documentation of `suite/src/cryptanalysis/factoring/`.

## RSA

```text
$ crax rsa wiener <n> --e <e>
wiener: n = 100838969382656946560373176440817955492681622693031250224486320217033755381847 * 105521954077741822635373266291794581792811894718351891228448572712095560074597 (verified) (38 iterations, 0.000 s)
  d = 3339107582246289661

$ crax rsa hastad --e 3 <c1>:<n1> <c2>:<n2> <c3>:<n3>
hastad-broadcast: m = 1976620216402300889624482718775150 (verified: re-encrypts to the ciphertext) (0.001 s)
  as text: attack at dawn

$ crax rsa fermat <n>
$ crax rsa batch-gcd <n1> <n2> ... | @moduli.txt
$ crax rsa from-d <n> --e <e> --d <d>
$ crax rsa common-modulus --n <n> --e1 .. --c1 .. --e2 .. --c2 ..
$ crax rsa small-e --n <n> --e 3 --c <c>
```
