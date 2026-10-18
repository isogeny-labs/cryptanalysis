# N41 widened source and shared-inverse root controls

An exact census gives **281 valid canonical source codes and 1,124 signed
pair outputs** for the N41 width-11 fixed-seed source. The archived width-9
source has 71 codes and 284 signed outputs, so widening increased the source
state count by 3.96 times. The width-11 circuit accepts the complete,
independently verified public-relation assignment. On the same public point,
the one-worker 600-second ordinary query reached its frozen wall cap with
status `BOUNDED_UNKNOWN`.

The diagnostic sequence localizes the search cost. Fixing all five verified
source codes in the original circuit did not produce a terminal SAT result
in 120 seconds. A corrected shared-inverse root section also accepted the
complete assignment, but its five-code control reached the same cap. Even
after fixing all five pair outputs, the three S3 intermediate variables
remained unresolved at the 60-second cap. Direct characteristic-two S3
quadratic resolution on those same fixed pair outputs enumerated eight
middle tuples and retained exactly one against the public target, matching
the archived witness in 0.00581 seconds of checked-Sage computation.
These controls use planted assignments to isolate circuit components; they
are not natural relation yield measurements.

## Exact method and measured records

The field is `GF(2^41)` in the polynomial basis with modulus
`x^41+x^3+1`, on the binary Koblitz `b=1` curve represented by
`EC1N41Ckb1h7d5e80d3c4d0`, with subgroup order 549,756,390,943 and
cofactor four. The source uses seed mask 56, 10 free code
bits, and five pair rotations `[0,0,12,12,24]`. The [frozen public
fixture](../n41_n131_w29_rotation_alignment_20261017/n41_model_fixture.json)
fixes the target point, reciprocal representation, five factor-base pair
outputs, and complete relation witness. The exact census checked all
1,024 canonical codes through the repository's checked Sage launcher.

| Arm | Frozen inputs | Circuit or search result | Wall bound / observed time | Peak sampled combined RSS |
| --- | --- | --- | ---: | ---: |
| Width-11 original build | Complete archived relation witness | `PASS_N41_W11_ALIGNED_CONSTRUCTED_CONTROL`; 19,365 variables, 48,374 CNF clauses, 2,859 XOR rows | 1.474 s build | See build record |
| Ordinary width-11 query | Public point; all codes and roots free | `BOUNDED_UNKNOWN`, `WALL_CAP` | 600.104 s query; 601.578 s build plus query | 266,813,440 B |
| Original five-code control | Five verified codes fixed; roots and S3 middles free | `BOUNDED_UNKNOWN`, `WALL_CAP` | 120.095 s | 107,888,640 B |
| Original first-three-code control | First three verified codes fixed | `BOUNDED_UNKNOWN`, `WALL_CAP` | 120.107 s | 93,585,408 B |
| Shared-inverse root build | Complete archived relation witness | `PASS_N41_W11_SHARED_INVERSE_ROOT_CONTROL`; 20,030 variables, 48,734 CNF clauses, 3,469 XOR rows | 1.793 s build | See build record |
| Shared-inverse five-code control | Five verified codes fixed; roots and S3 middles free | `BOUNDED_UNKNOWN`, `WALL_CAP` | 120.269 s | 237,633,536 B |
| Shared-inverse fixed-output control | Five verified codes and five pair outputs fixed; three S3 middles free | `BOUNDED_UNKNOWN`, `WALL_CAP` | 60.013 s | 92,143,616 B |
| Direct S3 resolution | Same five pair outputs, Frobenius rotated; three middles solved explicitly | `PASS_N41_W11_DIRECT_S3_TARGET_FILTER`; 8 tuples, 1 target-compatible | 0.00581 s internal checked-Sage computation | Not sampled |

All solver controls used CryptoMiniSat 5.14.7, one worker, and a 4 GiB
RSS cap on an ordinary host. These are circuit diagnostics, not isolated
CPU performance comparisons. The natural query's clock begins with solver
work on the frozen public point; structural build is recorded separately.
Each run retains command, protocol and source hashes, terminal-status flags,
cap reason, sampled RSS, stdout, and stderr in its JSON result. The
checked Sage runtime receipt is [sage_runtime_info.json](sage_runtime_info.json).

## Circuit change and proof

The prior source circuit already constrains `p v = 1` for each source
product `p`. The shared-root variant reuses that `v` and adds a two-branch
functional root for the pair equation. In characteristic two, with
`q = C H v²`, the normalized root is `h = halftrace(q)` when `Tr(q)=0`;
the two output roots are `(p/C) h` and `(p/C)(h+1)`.

The first frozen root implementation failed before producing a formula:
coefficientwise half-trace was called on an individual trace-one basis
coefficient. The [failure receipt](shared_root_build_failure_0.json)
preserves its source and protocol hashes. The corrected implementation
uses `L(y)=halftrace(y+Tr(y))` on each coefficient and enforces zero trace
on the complete `q`. [PROOF_MAP.md](PROOF_MAP.md) gives the readable proof,
Lean declarations, hypotheses, and concrete implementation bridge. The
corrected circuit's archived positive assignment satisfies all 48,734
CNF clauses and 3,469 native XOR rows.

For fixed pair outputs, each S3 link is the quadratic
`A z²+B z+D=0`, with `A=(ab)²+1`, `B=ab`, and `D=(a+b)²`.
The [direct resolver](resolve_s3_v2_n41.py) applies the normalized
Artin-Schreier two-root formula, follows the three-link tree, and checks
the final target equation. Its first frozen version omitted the specified
Frobenius rotations and failed the archived-witness check; the
[failure receipt](s3_resolution_failure_0.json) retains the original
source hash. The corrected version freezes the rotations in its input
protocol and recovers exactly the archived middle tuple. The S3
coefficient identity is also kernel checked in [SharedRootTrace.lean](SharedRootTrace.lean).

## Decision and next experiment

The N41 width-11 natural query and every bounded solver diagnostic remain
`BOUNDED_UNKNOWN`. The prepared N131 width-33 builder was not promoted:
its frozen gate requires a SAT model on the ordinary N41 query and
independent group replay. It has `candidate_id: null` and no measured
N131 result.

The direct S3 result removes a concrete solver bottleneck for fixed pair
outputs. An earlier [N41 six-pair native join](../n41_w8_sixpair_mitm_20261011/RESULT.md)
already demonstrates explicit partial-sum tables and independent relation
replay at this field size. The next algorithmic test should therefore
derive a **compact, exact target-conditioned filter over families of pair
outputs**, rather than materialize another full half-list. The filter
should certify that it retains every solution and measure rejection and
cost on frozen N41 public-point queries; only a successful ordinary N41
relation with independent replay can open the N131 promotion gate.
The complete target-dependent cost and a same-point rho comparison remain
the eventual online performance test.
