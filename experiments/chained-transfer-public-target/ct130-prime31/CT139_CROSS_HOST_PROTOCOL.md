# CT139 independent-host replay and break-even diagnostic — prospective 2026-11-15 [pcc:unverified]

Parent cryptanalysis PR #1550, rooted in crypto #3877. This preregisters a second-host repeat of the *unchanged* 3,840-solve CT138 experiment and a transfer overhead sensitivity threshold. NOT an original-prime Jacobian-chain test. No source or frozen scientific fixture changes. [pcc:unverified]

## Sources and nonduplication

Inspected repository AGENTS, latest session logs, CT138 head 6ec7925ccaca1eff8fc8c50821b177ded0293b32, CT137 #1549, CT126 #1534, root crypto #3877, norm-reuse #4215, consumer #1523 and GPU IC #4178, plus the autoresearcher active PR register. Shared research KB MCP and Conductor are unavailable in this runtime; literature/novelty claims are not made. CT138 already reviews the negation-map rho literature. Original CT138 archived evidence SHA-256: 4fadd60f98c72b571dc1683bd030695a7527eafa19a508524e9fbcd96e2823fe.

## Precommitted protocol

1. Source from that immutable archive: native CT135 SHA256 5422e02524850bfb0f595901c063a07326079e9dd82a483e6085996ce97bbdb0, CT136 20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921, generator af0ad4688457821293a96acd8af9ebf2e399ea9fd45c93f058a03669fa91d489; independent CT136 verifier ce3a9e5af959ad5ec3a81ce78151587a099fa8f86029bc7fa059bf9a384abc2f, CT138 verifier 9b16c910b633102c13067ce53a6b205fdc46bd45035376804d51e0bc5b2c3385. Rebuild via g++ -O3 -std=c++17 -Wall -Wextra -Werror -I ., and retain hashes/host/compiler receipt.
2. No-cost local container only; never launch EKS, Spot, or unapproved hosted benchmark. Existing exact cohort 4 seeds 20261340..43, each 32 public targets, widths 16/32/64; 5 algorithms x 2 repeats => 3840 scalar recoveries. Same 12 process sequence from original sequence.txt; no exclusions, replacements or favorable reruns. Timeout 120s each, /usr/bin/time peak RSS, stdout/stderr archived.
3. Run unchanged independent arithmetic verifier in normal and optimized Python; require both to agree byte-for-byte, require all prior mutation controls. Recompute only fixed whole-cohort best-source vs fixed whole-cohort best-target ratio. Report A/A medians and descriptive paired-bootstrap bounds, not an independent-sample confidence claim.
4. New sensitivity diagnostic, not timed primitive measurement: allowed extra *per-single-target* cold transfer/setup cost that would make candidate no faster, in nanoseconds = max(0, (best_source_total_ns - best_target_total_ns)/128). Include width-specific and overall values, and state that repeated source initialization/known precomputation could change this margin. Strictly do not extrapolate to original 695/701 Jacobian records or claim that CT126 C169/C13/D has been priced.
5. Preserve failures and timing reversals. Independent host timing is a second platform measurement, not a controlled paired same-host delta against previous host. [pcc:unverified].

Reproduction: python3 -S ct138_generate.py generated2; g++ as above for three variants; run each in original sequence with arguments '32 SEED'; python3 -S ct138_verify.py results; python3 -O -S ct138_verify.py results. Record hashes and source/time/host/measurement evidence. [pcc:unverified]

Remaining main goal unchanged: actual CT126 original-prime C169/C13a/C13b/D, 695/701 parity, complete cold original-prime rho/BSGS/IC incl setup, transfer, LA, verification and memory; independent PCC signing and merge gates.