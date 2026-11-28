# Static x lookup development screen

The six matched cells in `STATIC_LOOKUP_PROTOCOL.md` completed on the frozen
public auxiliary M31 target. Every arm solved and generator multiplication
verified the reported scalar. Within each seed and basis size, both arms had
identical base points, certificates, work counters, signed-pair counts and
answers. There were no failures, censored arms or replacements. The full
per-process JSON reports remain local; `static-lookup-raw.csv` retains their
SHA-256 digests. [pcc:unverified]

| Base | Metric | Control median ms | Static median ms | Median paired control/static | Static wins |
| --- | --- | ---: | ---: | ---: | ---: |
| B384 | Charged wall | 30.874 | 55.681 | 0.5545 | 0/3 |
| B384 | Charged CPU | 30.533 | 54.780 | 0.5397 | 0/3 |
| B384 | Index build | 3.313 | 5.303 | 0.6291 | 0/3 |
| B384 | Online | 22.272 | 46.132 | 0.4828 | 0/3 |
| B768 | Charged wall | 37.669 | 78.085 | 0.4539 | 0/3 |
| B768 | Charged CPU | 37.405 | 76.627 | 0.4486 | 0/3 |
| B768 | Index build | 14.585 | 26.906 | 0.5421 | 0/3 |
| B768 | Online | 16.369 | 45.105 | 0.3143 | 0/3 |

The candidate failed its frozen screen. The exact fixed table preserved the
algorithmic workload but regressed both setup and online time. It was removed
from production source after measurement. The control binary SHA-256 was
`a4c7faf8a50671c8b88712d2a4e9a217b243e1739a451416708eec594510f585`;
candidate binary SHA-256 was
`6ccb8b00b6b88f2a450be71b2a01abe9cfe66873c971386f9ed4c103000b3c66`.
Candidate source is archived in `static_lookup_candidate.rs` with the three
call-site substitutions documented there. Both were release builds on the
same Apple M4 Pro host. Compilation was excluded; setup through process exit,
including result parsing and independent public group-equation verification,
was charged. The small single-target screen is a reason to reject this
implementation, not a general statement about open-addressing schemes.

The static table used `size + 1` rounded up to a power of two, full x keys,
linear probing and a multiplicative initial slot. Its larger indexed setup
and substantially slower misses are consistent with extra random-access
probes; that is a hypothesis, not measured cache telemetry. Next focus on the
query path's repeated membership check or batch addition while keeping the
existing integer-key HashMap control.
