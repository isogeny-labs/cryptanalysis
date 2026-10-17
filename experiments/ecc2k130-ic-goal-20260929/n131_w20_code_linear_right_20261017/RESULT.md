# A 19-bit linear solve for the target-conditioned N131 right pair

## Contribution

The right W20 pair product can be recovered as a **19-bit binary linear
solve**, before extracting either target S3 root. The solver scanned all
264,090 left roots on each of two frozen N131 points and returned exactly
the archived right-source decisions: the constructed control has one
distinct-column hit at codes `(3,16722)`, and the ordinary raw public point
has zero two-pair hits. Both scans had full 19-bit image rank at every left
root and took no exceptional fallback.

In an alternating same-point comparison with the preceding batched
quadratic-algebra oracle, the batched/code child-CPU ratio was **1.320 on
the constructed control and 1.310 on the ordinary point** (ratio of summed
CPU across two runs per arm). The native
peak was 16,465,920 bytes for the code solver and 88,375,296–88,391,680
bytes for the batched oracle. This is an implementation result for an exact
two-pair point-decomposition component; `candidate_id: null`.

## Algebra and source

The source is `GF(2)[t]/(t^131+t^13+t²+t+1)` on the binary Koblitz model
`y²+xy=x³+1`, curve ID `EC1N131Ckb1heb5f1998f20b`. The W20 pair seed mask
is 898618, with source slots at Frobenius rotations 0 and 18. The frozen
support table has 524,493 rows; the validity bitmap admits 132,045 codes,
each giving two left roots. The point fixture supplies a constructed
first-two-pair control and an ordinary raw preimage of the public point.

For one left reciprocal root `c` and target reciprocal `t`, the right root
`d` satisfies `A d²+B d+D=0`, where `A=1+(ct)²`, `B=ct`, and `D=c²+t²`.
The right pair product `p` satisfies `C d²+p d+H=0`. Put `U=C D+H A` and
`V=H B`. These equations give `D p=U d+V`. When `D,U` are nonzero,
eliminating `d` gives

`A D² p² + B U D p + A V² + B U V + D U² = 0`.

Because `p` is an F₂-linear combination of 19 rotated product-basis
elements, the equation gives 131 binary rows in the 19 source-code bits.
The implementation reduces those columns with a high-pivot XOR basis,
then checks the recovered code against the source bitmap, reconstructs
`d=(D p+V)/U`, and verifies both quadratics and four distinct folded
columns. It uses the exact root fallback when `D=0`, `U=0`, or the image
rank is below 19. The [proof map](PROOF_MAP.md) gives a readable derivation
and four checked Lean implications, including the reverse reconstruction.

The preceding [batched quadratic-algebra oracle](../n131_w20_batched_quadratic_20261017/RESULT.md)
already used the affine product identity but tested the entire product
span through a 19-step linearized-polynomial recurrence. This experiment
solves directly for its 19 binary code coordinates instead.

## Frozen runs and independent replay

The [producer protocol](protocol.json) binds exact input, source, binary,
and runner hashes before execution. Its one worker had a 590-second native
cap, 600-second parent cap, and 4-GiB RSS cap. The [producer result](native_result.json)
recorded 4.086 seconds setup, 2.961 seconds constructed query, and 3.405
seconds ordinary query, with 15,925,248 bytes native peak. The
[parent receipt](receipt.json) recorded 10.749 seconds wall and 35,012,608
bytes sampled combined RSS, with exit zero and no monitor failures.

The separate [full-candidate audit](audit_result.json) rebuilt all
264,090 right roots into the archived hash index, used a low-pivot code
basis, and compared the code equation and exact root membership for each
left root. It checked the eliminant on **1,056,360 S3 roots** across both
points. Its [receipt](audit_receipt.json) records PASS in 176.520 seconds
of parent wall, 57,769,984 bytes sampled combined RSS, and no cap stop.

| Frozen point | Code child CPU, two runs | Batched child CPU, two runs | Batched/code CPU | Code native peak | Batched native peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| Constructed control | 6.165, 6.245 s | 8.171, 8.206 s | 1.320 | 16,465,920 B | 88,375,296–88,391,680 B |
| Ordinary raw point | 6.286, 6.265 s | 8.196, 8.251 s | 1.310 | 16,465,920 B | 88,375,296–88,391,680 B |

The [paired protocol](benchmark_protocol.json) fixed eight single-point
processes in alternating `code,batch,batch,code` order for each point, using
the same fixture, source table, cap, compiler family, and one-worker
envelope. Each result retained the exact hit set. The [paired CPU result](paired_cpu_result.json)
records child user and system CPU, parent wall, setup and query time,
process status, and per-run hashes. Parent wall ranged 6.728–7.154 seconds
for the code solver and 8.780–10.014 seconds for the batched oracle on this
ordinary shared host. The code binary used `clang++ -O3 -std=c++17 -Wall
-Wextra`; the archived batched binary used `clang++ -O3 -std=c++17 -DNDEBUG`.
Both exact binaries are hash-pinned in the protocols. These local CPU and wall records are component
measurements under the observed host envelope; an isolated single-target
IC/rho comparison requires the remaining pipeline stages.

## Next experiment

The linear code equation solves a **supplied two-pair residual** in time
linear in the left source size. The next test should leave two or more pair
code products free, compose their equations with the public target, and
reject code families before their Cartesian combinations are formed. An
unpinned N41 seven-pair relation is the first full-search control; only a
source-bound configuration fitting one worker, 600 seconds and 4 GiB should
advance to the frozen N131 ordinary relation query. Relation rank, unseen
single-target recovery, and matched isolated rho remain later measured
stages of the active goal.

Run `python3 verify.py` from the repository root to recheck all frozen
hashes, statuses, source counts, paired result equalities, and Lean audit
output. The [terminal verification](verification.json) records PASS.
