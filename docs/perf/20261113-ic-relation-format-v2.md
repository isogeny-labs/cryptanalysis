# Index-calculus relation records, format v2 (compact storage, versioned checkpoints)

Date: 2026-11-13. Base: `origin/main` `0d69fc552`. Change: `src/indexcalc.c`,
`tests/test_indexcalc.c`. Owner-approved task; background in
[`20261112-c-memory-pass.md`](20261112-c-memory-pass.md) §3.5.

Every number below is a local measurement on a shared VM (4 vCPU Intel Xeon @
2.10 GHz, Linux 6.18, gcc 13.3.0, Release `-DCA_BUILD_SHARED=OFF`) and is an
unverified assertion [pcc:unverified]. No pcc claim record was written. This
is a memory and format change. It is not an index-calculus speed result, and
it changes no IC leaderboard row or benchmark row.

## 1. What changed

- **In memory.** Before, the `relation` struct was 784 B: `n`, 96 fixed
  `col`/`val` slots, `rhs` and 4 B of padding. The relation list stored one
  struct per relation. Now the list is CSR-style (`rel_list`):
  - `off[n+1]` (uint32) marks where each relation starts;
  - `rhs[n]` (uint64) holds the right-hand sides;
  - the `col[]`/`val[]` arenas are packed.

  A relation therefore costs 12 B plus 8 B per nonzero. Measured relations
  average 6.2 to 7.4 nonzeros from 40 to 56 bits, with a maximum of 11 (§3).
  That is about 68 B at 48 bits, against 784 B: roughly 11x smaller.
  The fixed `relation` struct is kept only as the stack scratch that
  `trial_factor` fills.
- **Same rows in the same order.** Relations and the entries inside each
  one keep their append order, so `build_matrix` makes the same
  `ca_spmat_add_row` calls in the same order. Two other changes:
  - the matrix is now initialised with the exact nonzero count instead of
    the `16 * rows` hint (this changes capacity only);
  - the relation list is freed once the matrix copy is built, because
    nothing reads it after that.
- **Growth.** `rel_reserve` sizes the list for the target with 8 entries
  per relation, and the list grows by `realloc` (×2 for relations, ×1.5
  for entries).
- **Checkpoints.** Writers emit format v2. Readers accept v1 and v2, chosen
  by the magic *and* the `relation_size` field together. A file that
  matches neither is rejected with `CA_ERR_INVALID`, never reinterpreted.
- **Cleanup.** The two hot-loop `memset`s of the 784-byte scratch (sieve
  and random-exponent workers) are gone, because the scratch is no longer
  hashed or stored. A pre-existing leak of the reserved list is fixed: it
  happened on the two early returns after the zeta relation.

## 2. Format specification

All integers are native byte order, as in every other field of these files.
v1 is frozen and read only.

| | v1 (read only) | v2 (written) |
|---|---|---|
| journal magic | `"CAICJ1"` | `"CAICJ2"` |
| snapshot magic | `"CAICRX1"` | `"CAICRX2"` |
| header `relation_size` | 784 (`sizeof(ic_relation_v1)`) | 0 (variable length) |
| relation record | native struct `{u32 n; u32 col[96]; i32 val[96]; u64 rhs}`, 784 B with padding | packed `{u32 n; u64 rhs; u32 col[n]; i32 val[n]}`, 12 + 8n B |
| journal record header | `{u32 marker=0x43493152; u32 index; u32 count; (pad); u64 candidates; u64 checksum}`, 32 B | `{u32 marker=0x43493252; u32 index; u32 count; u32 entries; u64 candidates; u64 checksum}`, 32 B, payload `12·count + 8·entries` B |
| journal record checksum | FNV-1a 64 over index, count, candidates, then the `count` 784-B records | FNV-1a 64 over index, count, entries, candidates, then the payload |
| snapshot checksum | FNV-1a 64 over the header up to `checksum`, then the payload | same |
| snapshot length check | `size == 112 + 784·count` | `112 + 12·count ≤ size ≤ 112 + (12 + 768)·count`, and the records must fill the payload exactly |

The header layouts are unchanged (journal 56 B, snapshot 112 B). Only the
magic and the meaning of `relation_size` differ. Every decoded relation is
checked against the run, as before: `n ≤ 96`, `col < ncols`, `rhs < p − 1`,
and for snapshots `val ≥ 0`.

**Migration.**
- *Sieve journal.* A v1 journal of the same run is replayed, including the
  torn-tail repair, and then rewritten at once as v2 with the same units,
  relations, order and candidate counts. The rewrite goes to a temporary
  file, which is fsynced, renamed over the old journal, and followed by an
  fsync of the parent directory. A crash therefore leaves either the whole
  v1 journal or the whole v2 journal. New units are appended in v2.
- *Random-exponent snapshot.* A v1 snapshot is loaded, and the next save
  (the first one comes right after loading) writes v2 by an atomic rename.

## 3. Identity checks (base `0d69fc552` vs this change)

The workload was `ca ic --g 5 --h 5^987654321987 mod p --seed 7`. p was the
largest prime below 2^40, 2^44 and 2^52, plus the earlier notes' 48-bit
281474976705359 and 56-bit 72057594037925687. Both lsieve and rexp were run;
rexp was run up to 48 bits. Results [pcc:unverified]:

| check | result |
|---|---|
| `--threads 1 --verbose`: stdout JSON (x, check, factor_base, unknowns, relations, verified_logs, lanczos_iterations) and the stderr log, with times removed | 8/8 runs identical |
| `--threads 1 --state-dir` (checkpointed) JSON | 8/8 identical |
| `--threads 4` x | 8/8 identical |
| checkpoint content: the base's v1 file and the new v2 file decoded by an independent Python decoder (checksums verified, header identity, `(index, count, candidates)` of every journal record, every relation's rhs/col/val in order) | 8/8 identical |
| checkpoint size v1 → v2 | journal 832,440 → 71,056 B (40-bit), 2,166,216 → 190,436 B (48-bit), 5,236,584 → 475,052 B (56-bit); snapshot 452,480 → 38,460 B (48-bit rexp) |
| 62-bit p = 4611686018427387847, `--B 200000 --C 40000 --threads 1`: JSON and log | identical (x = 987654321987, 105,037 relations, 97,985 unknowns, 45,424 Lanczos iterations, 17,473 verified logs) |
| `ca_perfbench run --samples 1 --min-samples 1 --warmup-seconds 0 --max-seconds 1`, base build vs new build | 31/31 fingerprints identical (`perf-base.jsonl` sha256 `2bd048cd…`, `perf-new.jsonl` `fc72374c…`) |
| ctest (Release) | 20/20 passed |

Average nonzeros per relation, from the decoded journals: 6.71, 6.89, 7.05,
7.25 and 7.36 for lsieve at 40, 44, 48, 52 and 56 bits; 6.22, 6.55 and 6.81
for rexp at 40, 44 and 48 bits; at most 11. The §3.5 estimate of about 16
used slots was high.

### Resume from journals written by the pre-change binary

Fixtures were written by the base `ca` binary at 48 bits; they are not
committed (they are binary data, and the in-repo tests synthesise v1 files
instead):

- `ls-v1-partial/relations.ckpt` is a CAICJ1 journal cut at 1,000,000 bytes,
  inside a record. sha256 `74fb4a57…f9d8`.
- `rx-v1-partial/relations.ckpt` is a CAICRX1 snapshot from
  `--max-relation-tries 40000`, holding 181 relations. sha256
  `00fb9cf4…1f9c`.

Each fixture was resumed with `--resume` by the base binary and by the new
one [pcc:unverified]:

- lsieve: both runs replayed 22 units and 1,267 relations. The JSON and the
  log were identical: x = 987654321987, 2,762 relations, 1,105 Lanczos
  iterations. The new run left a CAICJ2 journal that decodes identically to
  the base's finished v1 journal. It is also **byte-identical** to the v2
  journal of an uninterrupted new run (sha256 `4e3a20c9…6152`).
- rexp: both runs resumed 181 relations and 40,001 tests. The JSON and the
  log were identical (565 relations, 346 Lanczos iterations). The new run
  left a CAICRX2 snapshot that decodes identically to the base's.

### New unit tests (`tests/test_indexcalc.c`, 195 → 236 checks)

The tests write the two formats out from the spec in §2, independently of
the library:

- `journal_v1_migration` converts a run's v2 journal to v1 and recomputes
  the v1 and v2 checksums along the way. Then:
  - a complete v1 journal resumes with the same x, relations and candidates,
    and is rewritten **byte-identical** to the original v2 journal;
  - a v1 journal torn inside its last record resumes, and ends up v2 again
    with the same length;
  - a `CAICJ1` header with `relation_size` 0, and a `CAICJ2` header with
    784, are both rejected.
- `rexp_v1_migration` checks that an interrupted run's snapshot, converted
  to v1, resumes to a correct log and is saved as v2. It also checks that a
  `CAICRX1` magic over a v2 payload is rejected.

### Sanitizers and static analysis

- ASan + LSan + UBSan (`-DCA_SANITIZE=ON`, RelWithDebInfo,
  `detect_leaks=1:detect_stack_use_after_return=1:halt_on_error=1`):
  - `test_indexcalc`: 236/236 checks, no reports;
  - `ca ic` resumes from both v1 fixtures, with identical answers;
  - lsieve and rexp at 48 bits, 4 threads, with a state dir;
  - lsieve at 56 bits, 4 threads.
  All were clean.
- Locally with Ubuntu 24.04's tools, running CI's commands on the changed
  files, all exited 0:
  - clang-tidy 18.1.3 (`-p` on a Debug compile database);
  - cppcheck 2.13.0 (the workflow's flags);
  - `gcc -fanalyzer -Wall -Wextra -Werror` on `src/indexcalc.c`;
  - `git-clang-format --diff origin/main`, which reported no changes;
  - a Release `-DCA_WERROR=ON` build.
- CI uses clang-tidy ≥ 21 and cppcheck 2.19, which were not available
  here, so the PR's `analysis` run is the check for those versions.
  `src/curve.c` is untouched, so the Lean binding pin does not move.

## 4. Memory before → after [pcc:unverified]

### Peak RSS of the whole process

Peak RSS is `ru_maxrss` from `wait4` (`/usr/bin/time` is not installed). The
table gives three alternating runs per arm, and the median, in kB. The
process floor is about 5.26 MB, so below 48 bits the relation list is lost
in it.

| p (bits) | method | threads | base runs | new runs | base median | new median |
|---|---|---:|---|---|---:|---:|
| 1099511627689 (40) | lsieve | 1 | 5372/5264/5264 | 5260/5268/5364 | 5,264 | 5,268 |
| 1099511627689 (40) | lsieve | 4 | 5264/5272/5372 | 5268/5268/5364 | 5,272 | 5,268 |
| 1099511627689 (40) | rexp | 1 | 5264/5372/5272 | 5272/5368/5264 | 5,272 | 5,272 |
| 1099511627689 (40) | rexp | 4 | 5264/5372/5276 | 5272/5280/5372 | 5,276 | 5,280 |
| 281474976705359 (48) | lsieve | 1 | 5624/5692/5712 | 5264/5272/5280 | 5,692 | 5,272 |
| 281474976705359 (48) | lsieve | 4 | 6316/6172/6048 | 5248/5264/5272 | 6,172 | 5,264 |
| 281474976705359 (48) | rexp | 1 | 5264/5264/5264 | 5260/5268/5260 | 5,264 | 5,260 |
| 281474976705359 (48) | rexp | 4 | 5276/5268/5268 | 5364/5340/5364 | 5,268 | 5,364 |
| 4503599627370449 (52) | lsieve | 1 | 7496/7464/7504 | 5372/5368/5264 | 7,496 | 5,368 |
| 4503599627370449 (52) | lsieve | 4 | 8256/8280/8396 | 5368/5272/5368 | 8,280 | 5,368 |
| 72057594037925687 (56) | lsieve | 1 | 9976/9916/9988 | 5272/5280/5264 | 9,976 | 5,272 |
| 72057594037925687 (56) | lsieve | 4 | 11336/11300/11116 | 5272/5264/5288 | 11,300 | 5,272 |
| 4611686018427387847 (62), `--B 200000 --C 40000` | lsieve | 1 | 115,024 (one run) | 34,132 (one run) | 115,024 | 34,132 |

The 62-bit row has 105,037 relations. At about 7.5 nonzeros the compact list
is roughly 7.7 MB, where the 784-B records took about 82 MB. Two changes
make up the −70 % RSS: the record format, and freeing the list once the
matrix is built (the base held both during Lanczos). They were not
measured separately.

### Peak heap (valgrind 3.22 massif)

| workload | base | new |
|---|---:|---:|
| `ca ic` 48-bit lsieve, `--threads 1` | 3,678,705 B | 986,985 B (−73 %) |
| `ca ic` 56-bit lsieve, `--threads 1` | 8,664,813 B | 2,415,661 B (−72 %) |

## 5. Not done / limits

- The numbers come from one shared VM. RSS was measured one run per arm at
  62 bits and three runs per arm elsewhere. No wall-time claim is made: the
  62-bit linear algebra took 104.5 s (base) and 106.1 s (new) in one run
  each, with other jobs running on the VM.
- clang-tidy 21 and cppcheck 2.19 (CI's versions) were not run locally.
- The v1 fixtures from the pre-change binary are described here by
  sha256, not stored. The in-repo tests produce v1 files from the spec
  instead.
- Endianness is native in both versions, as before. A checkpoint does not
  move between machines with different byte orders, in either version.
- No `bench.record/v1` record and no `benchmarks/` entry were made: this is
  a local identity and memory check, not a benchmark row. The
  research-visuals graph and PDF were not produced either. The note follows
  the markdown-only precedent of `20261112-c-memory-pass.md`.

## Reproduce

Scratch scripts were used and are not committed. Each takes a build
directory:

- `ic_identity.sh` runs the identity matrix in §3, saving JSON, logs and
  checkpoints;
- `icdecode.py` decodes both formats with checksums and compares two files;
- `maxrss.py` reports a child's `ru_maxrss`;
- `rss.sh` runs the RSS table;
- `big.sh` runs the 62-bit row.

Massif ran as `valgrind --tool=massif ca ic … --threads 1`. Its peak is the
largest `mem_heap_B` snapshot.

## Sources checked

`research-kb` is not attached to this subagent session (KB unavailable). Files
read: `cryptanalysis:docs/perf/20261112-c-memory-pass.md` (§2, §3.5, §6),
`cryptanalysis:docs/perf/20261110-lanczos-spmv-threads.md` (the 48- and
56-bit IC workloads), `cryptanalysis:AGENTS.md` (sabotage rule, data files,
benchmark records), `cryptanalysis:.github/workflows/analysis.yml`.
