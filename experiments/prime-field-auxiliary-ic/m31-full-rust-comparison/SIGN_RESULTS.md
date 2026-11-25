# Sign-packed full M31 collector result

The pre-measurement protocol and its later exact-map audit amendment are in
`SIGN_PROTOCOL.md`. The candidate hashes one x-coordinate per pair of point
signs and stores a separate first payload for each y parity. It uses a 6 MiB
index instead of the flat control's 8 MiB index. Both arms use the same
one-multiply slot hash, validated batch arithmetic, direct pair rows,
deterministic walk, checked relations, elimination and answer verification.

Two local panels of 24 matched blocks per frozen public fixture completed on
an Apple M4 Pro. Every arm regenerated the 500-point basis and ran in a fresh
process. All 96 matched pairs agreed on basis SHA-256, signed table-entry
count, trial count, relation count and scalar 123456789, which was checked by
generator multiplication. The second panel used a fresh block shuffle.
[pcc:unverified]

| Panel | Fixture | Flat wall median ms | Packed wall median ms | Median paired flat/packed wall ratio | Packed wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 173.510 | 158.830 | 1.0900 | 24/24 |
| Initial | Plain | 154.993 | 143.907 | 1.0809 | 24/24 |
| Repeat | Auxiliary | 178.939 | 165.931 | 1.0761 | 24/24 |
| Repeat | Plain | 161.319 | 149.716 | 1.0795 | 24/24 |

| Panel | Fixture | Flat CPU median ms | Packed CPU median ms | Median paired flat/packed CPU ratio | Packed wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 171.889 | 157.460 | 1.0954 | 24/24 |
| Initial | Plain | 153.894 | 142.779 | 1.0817 | 24/24 |
| Repeat | Auxiliary | 176.662 | 163.667 | 1.0827 | 24/24 |
| Repeat | Plain | 159.439 | 146.382 | 1.0822 | 24/24 |

Wall and parent-plus-child CPU timers charge basis regeneration, fixture
comparison, file writing, table build, relation collection, elimination and
answer verification. Compilation, frozen JSON loading and the later exact-map
audit are outside the clock. OS caches were not flushed. `sign-raw.csv` and
`sign-confirm.csv` retain all 192 arms. The paired ratios use individual
matched blocks and need not equal the ratio of displayed arm medians.

After the timing panels, an audit mode dumped both complete sorted maps of
`(encoded point key, first payload)` for each fixture and compared their bytes.
Both maps agreed exactly, including all duplicate pair sums. The matching
SHA-256 values were `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879`
for auxiliary and `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa`
for plain. Run `M31_AUDIT_ONLY=1 python3 sign_replay.py` to repeat the audit.

`SignPacked.lean` kernel-checks that the `(key / 2, key % 2)` representation
preserves first-inserted payload lookup for every insertion stream, and that
the encoded M31 point key splits and fits in a 32-bit word. This is a proof
of the logical map transformation. The Rust probe implementation is supported
by the exact fixture-map audit; the Lean file does not verify machine code or
the measured runtime. [pcc:unverified]

The measured gain is a same-target local collector improvement. Broader
target behavior, independent performance replay, and a causal breakdown of
table size versus hash distribution remain open.

Measurement CSV SHA-256: `e8c66700b24a36e4c2dadced01eca0a92cba3a83e5c41355b4c6ac2dc9e346e3`
and `5902d1d0d2d6a7cea2abc5ca1f4d1153a6388503b3fc9957cee16b94657ba985`.
