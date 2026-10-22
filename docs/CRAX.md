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
| sibling crypto integration | `ic solve-prime \| solve-cubic`, `icx solve-prime \| solve-cubic`, `isogeny-walk`, `store`, `crypto` |
| curves and challenges | `curve names \| info`, `challenge list \| show \| solve \| rho-job` |
| symmetric and hash | `aes-attack`, `hash`, `list-ciphers`, `auto`, `boomerang`, `rectangle`, `sbox`, `aes-related-key`, `hash-auto`, `length-extension` |
| lattice and post-quantum | `mlwe` |
| isogenies | `isogeny` |
| distributed rho | `rho-collab` |
| demos and research bench | `visual-all`, `aes-visual-demo`, `bench`, `ec-challenges` |

The symmetric, lattice, isogeny, distributed rho, and demo rows, plus native
`ic`/`icx`, are the older research command lines:
`ca-suite`, `ca-ic` and `ca-icx`. `crax` passes their arguments through to
them unchanged, and their `--help`, flags and report formats are their own.
The old binary names still work.

The sibling crypto commands above execute the corresponding installed
`ic`, `icx`, `isogeny_walk`, or `crypto` binary. Set `CRAX_IC_BIN`, `CRAX_ICX_BIN`,
`CRAX_ISOGENY_WALK_BIN`, or `CRAX_CRYPTO_BIN` to an explicit path when those
executables are not on `PATH`. `crax` forwards arguments directly, preserves
the child exit status, and wraps its JSON or text report when `--json` is
requested. In JSON mode, child diagnostics also stream to stderr while the
command runs and remain in the final `diagnostics_text` field. The native
`crax icx` catalog and run commands remain in the suite.

`crax icx run ... --verbose --json` prints stage progress to stderr and one
final JSON document to stdout. Add `--state-dir DIR` to select the sibling
`icx` binary's completed-repeat checkpoint; `--resume` continues local state
or restores it from `--s3-uri s3://BUCKET/PREFIX`. The sibling executable
must be on `PATH` or selected with `CRAX_ICX_BIN`. In this mode, `crax --json`
nests the sibling report under `report`. `crax gnfs`, `snfs`, and `qs` also support
`--verbose` stage reports. GNFS, SNFS, and SIQS save relation-sieve checkpoints
with `--state-dir`, continue with `--resume`, and mirror the run directory with
`--s3-uri`. The [restart guide](cli_progress_resume.md) lists each command's
checkpoint boundary and the remaining gaps. The sibling commands retain their
own artifact and recovery options.

`crax ic workflow` uses `--dir` for its stage and work-unit artifacts. Add
`--verbose --progress-every SECONDS` for live stderr, and
`--s3-uri s3://BUCKET/PREFIX --sync-every SECONDS` to commit checksummed
artifacts to S3. A fresh `--dir` plus `--resume` restores the last complete
S3 generation. Use a separate prefix for each worker or run.

For example, a capped GNFS run can be continued from local or S3 state:

```sh
crax gnfs '1000000016000000063' --verbose --progress-every 5 --max-b 1 \
  --state-dir ./runs/gnfs-001 --checkpoint-every 60 \
  --s3-uri s3://my-bucket/cryptanalysis/gnfs-001 --sync-every 60
crax gnfs '1000000016000000063' --verbose --max-b 5 \
  --state-dir ./runs/gnfs-001 --resume \
  --s3-uri s3://my-bucket/cryptanalysis/gnfs-001
```

The first command exits with an incomplete result at the requested sieve cap
and leaves its checkpoint for the second command.

The same options apply to `snfs`; repeat its polynomial or form arguments on
resume. The checkpoint records completed sieve batches and relations with a
checksum and input binding. A run interrupted during one batch repeats that
batch. Resume can raise `--max-b` or change `--threads`; changes to the sieve
parameters or polynomial are rejected. The matrix and square-root stages run
again after interruption. `manifest.json`, `nfs.ckpt`, `progress.json`, and
`result.json` are kept in the state directory. An S3-only restore uses a fresh
local directory and the same prefix. Use a distinct directory and prefix for
each run; the local directory is locked against another writer. With
`--verbose`, a heartbeat reports the active stage every five seconds by
default; `--progress-every` changes that interval. S3 syncs use completed
checkpoints and publish `result.json` last. A successful managed command
requires the final S3 upload to succeed.

SIQS uses the same state and S3 flags with `crax qs`. Its cap is
`--max-a-values`; raise that cap on resume. `--threads` and checkpoint cadence
may also change, while the input, seed, factor-base and sieve parameters must
match. The `qs.ckpt` file holds completed polynomial batches and deduplicated
relations. On resume, the accepted polynomial choices are replayed to restore
the seeded generator. An interrupted batch is repeated; matrix and square-root
work is recomputed after interruption. For example:

```sh
crax qs 100000000003900003000000000117 --max-a-values 4 \
  --state-dir ./runs/qs-001 --checkpoint-every 0 --verbose
crax qs 100000000003900003000000000117 --max-a-values 40 \
  --state-dir ./runs/qs-001 --resume --threads 2 --verbose
```

For an explicit public EC target, install the sibling `ic` executable or
set `CRAX_IC_BIN`, then run:

```sh
crax --json ic solve-prime --p 271 --a 1 --b 19 --n 281 \
  --gx 3 --gy 7 --qx 231 --qy 54
```

The bridge also accepts `solve-cubic`; `crax icx` accepts both commands too. Use
`crax store` for the content-addressed S3 push, verify and pull commands, and
`crax isogeny-walk` for route enumeration and verification.

## SHA and AES commands

```sh
crax --json hash --algorithm sha256 --text abc
crax --json hash --algorithm sha3-384 --hex 616263
crax hash --algorithm shake256 --text abc --output-bytes 32
crax --json aes-attack --technique differential --samples 4096
crax --json aes-attack --technique linear --samples 4096
crax --json aes-attack --technique square
crax --json hash-auto --hash sha256
crax --json hash-auto --hash sha3-256
```

`hash` accepts a single `--text`, `--hex`, or `--file` input and supports
SHA-1, SHA-2, SHA-3, SHAKE, MD4, and MD5. `--output-bytes` is required for
SHAKE and bounded to 1 MiB. `hash-auto` runs a length-extension demonstration
against SHA-256; SHA-3 uses a sponge, so that particular attack is not
applicable. Its truncated birthday and differential-bias measurements remain
available. `aes-attack` runs verified key recovery on the implemented
AES-128 reduced-round differential (2), linear (1), or integral (4) models.
These commands do not imply key recovery against full-round AES-128 or a
collision against full-output SHA-2 or SHA-3.

## Coverage of the cross-repository CLI path

| Requested surface | Available command | Current boundary |
| --- | --- | --- |
| SHA-256, SHA-3, and related digests | `crax hash` | Native byte, text, and file inputs; SHA-1, SHA-2, SHA-3, SHAKE, MD4, and MD5. SHAKE output is limited to 1 MiB per call. |
| Hash cryptanalysis | `crax hash-auto`, `crax length-extension` | SHA-256 length extension, 32-bit truncated birthday search, and differential-bias measurements. SHA-3 has the generic measurements but no Merkle-Damgård length-extension step. |
| AES differential and linear analysis | `crax aes-attack`, `crax sbox`, `crax auto` | Key-recovery examples use the implemented one-, two-, or four-round AES-128 models; other AES research commands retain their own flags and reports. |
| Explicit EC index calculus | `crax ic solve-prime`, `crax ic solve-cubic`; `crax icx` aliases | These delegate to the sibling `ic` or `icx` executable and inherit its checked field-size and work-budget limits. The cubic Gaudry factor base requires a counted full prime-order curve. `crax ic zp` remains multiplicative-group index calculus. |
| Isogeny graph enumeration and route checks | `crax isogeny-walk`; `crax ic solve-prime --route-file ... --route-id ...` | The sibling walker enumerates and verifies prime-field routes; the prime IC command checks point transport along a selected route. Cubic-field route transport is not implemented. |
| Artifact upload, existence verification, and retrieval | `crax store push`, `crax store verify --remote`, `crax store pull`; `crax isogeny-walk publish/fetch` | Sibling `crypto` store and walker require configured AWS credentials. Small public-artifact round trips passed on `setec-astronomy-artifacts`; live multipart recovery is unverified. |

The native cryptanalysis commands and the sibling bridges have separate build
dependencies. Install the sibling `crypto`, `ic`, and `isogeny_walk` binaries
or set their `CRAX_*_BIN` paths before using the corresponding rows. The
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

The generic `crax bsgs`, `rho`, `kangaroo`, `grumpy`, `precomp`, `glv`,
`pohlig-hellman`, `cheon`, and `gpu-rho` commands accept `--verbose`,
`--progress-every`, `--state-dir`, `--resume`, `--checkpoint-every`, `--s3-uri`,
and `--sync-every`. These options run the matching native `cryptanalysis`
solver and retain its exact checkpoint. Install that binary beside `crax` or
set `CRAX_NATIVE_BIN`. For example:

```sh
crax rho --p 2000000579 --order 1000000289 --x 123456789 \
  --verbose --state-dir ./runs/rho-001 --s3-uri s3://my-bucket/crax/rho-001
crax rho --p 2000000579 --order 1000000289 --x 123456789 \
  --state-dir ./runs/rho-001 --s3-uri s3://my-bucket/crax/rho-001 --resume
```

The native process writes live diagnostics to stderr even with `--json`;
`crax` still verifies each returned answer. See the
[restart guide](cli_progress_resume.md) for checkpoint and S3 rules.

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

`crax factor` accepts `--verbose --progress-every SECONDS` for live ladder
and sieve output. Add `--state-dir DIR --s3-uri s3://BUCKET/PREFIX` to save
cofactor, ECM-curve, and sieve checkpoints; repeat the command with `--resume`
to continue. `--checkpoint-every` controls inner sieve batch writes and
`--sync-every` controls S3 uploads. `crax rho-factor` also accepts
`--verbose --progress-every`, `--state-dir --resume`, and `--s3-uri` to retain
each completed Brent attempt; `--attempts` may increase on resume. The
`crax pm1` command supports the same progress, local resume, and S3 options;
`--pp1 --seeds N` selects the p+1 seed budget. The
[restart guide](cli_progress_resume.md)
describes the exact boundaries and artifacts.

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
