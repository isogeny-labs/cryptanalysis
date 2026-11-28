# Same-target cold orbit/rho distance

The protocol in `RHO_PROTOCOL.md` was fixed before this panel. The signed-pair
orbit Rust collector and archived C++ `comparison/compare_rho.cpp` used the
same frozen public M31 curve, generator and target. The auxiliary and plain
bases share that target. The runner checked all public identity fields against
the rho fixture before measurement. Both paths returned scalar 123456789 in
all 96 fresh-process arms; the Rust collector checks `[k]G=Q`, and the C++
rho program asserts the same identity with assertions enabled. There were no
failed, timed-out, or censored arms. [pcc:unverified]

| Basis | Orbit wall median ms | Rho wall median ms | Median paired orbit/rho wall ratio | Orbit CPU median ms | Rho CPU median ms | Median paired CPU ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 49.114 | 7.224 | 6.809 | 48.377 | 6.759 | 7.197 |
| Plain | 39.117 | 7.445 | 5.194 | 38.538 | 6.933 | 5.558 |

Each basis has 24 balanced-order pairs using seeds 0,1,2 and eight repeats
per seed. The wall and parent-plus-child CPU windows include factor-base
regeneration, input writing, orbit table/bitmap setup, relation collection,
elimination, generator check and fresh-process exit for IC; for rho they
include writing the frozen input, its complete fresh process, metrics parsing
and exit. Compilation and fixture JSON loading are excluded, and OS caches
were not flushed. Ratios are medians of paired ratios, not ratios of displayed
medians. Raw `rho-raw.csv` SHA-256 is
`a252e965932dcaa57db54911092ad32bcae94476c2899286af180757daa82b69`;
`rho_replay.py` SHA-256 is
`d41650c6d60488f65673623e2249f99f894cc700eeffce9b5b775724e0f9a32a`.
Run `M31_REPLAY_TMPDIR=/Volumes/SSD990 python3 rho_replay.py > rho-raw.csv`.

The orbit hash improves this IC implementation against its paired IC control,
but it does not close the same-target distance to archived rho. Source
language, arithmetic and optimization differ, so this is a direct wall/CPU
distance indicator, not an operation-normalized comparison or a strongest
possible rho implementation. One public target and one Apple M4 Pro host
limit generalization. [pcc:unverified]
