# CT125: native norm-point reuse, implementation gate

**Standing:** [pcc:unverified]. This branch implements a source-guarded, *sibling*
Rust evaluator derivative, not a verified full native replay, measured cost,
cold single-target ECDLP solve, or speedup. It is stacked on cryptanalysis
[#1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), without edits
to the original 695-record producer, the crypto root
[#3877](https://github.com/isogeny-labs/crypto/pull/3877), the prospective
counter audit [#4215](https://github.com/isogeny-labs/crypto/pull/4215),
or crypto-autoresearcher.

## What changed and what is held fixed

The original complete-chain evaluator is
\`fixed-jacobian-chain-evaluator-01/src/lib.rs\`, Git blob
\`8016634385d76207b23a3eb3a4dae9b0366ac68d\`. The published
[NORM_POINT_REUSE_PROTOCOL_01.md](../NORM_POINT_REUSE_PROTOCOL_01.md) precedes
this derivative. The prior full-population output and all original fixture
bytes stay immutable.

The new generator copies that package into sibling
\`fixed-jacobian-chain-reuse-01\` (never overwrites), then modifies exactly
four guarded source locations. Its \`norm_from_target_point(to,Z)\` evaluates
\`Z+Z\` on the actual target quadratic elliptic curve, checks admissibility
and descent to the prime-field target, and counts the one doubling. The
existing \`check_final\` **still recomputes the actual target Jacobian norm**
and verifies \`N(class) == transported_norm\`; it is not replaced by a claimed
identity. The literal two-hop route uses the optimized one-hop function twice.
The complete \`diagnose_half\` routine, all original source/cofactor/exceptional
cases, and the original source-to-target map code remain untouched.

The generator refuses a changed Git blob, missing source blocks, changed
whole norm check or altered diagnostic control. A receipt records the original
and derivative Git blob hashes, exact changes and standing.

## Reproduction without paid compute

From the *cryptanalysis* repository root (after the original
\`fixed-jacobian-chain-evaluator-01/materialize.py\` has prepared literal
helpers, as required by its existing README):

\`\`\`sh
python3 -S experiments/chained-transfer-public-target/norm-point-reuse-01/build_norm_reuse.py \
  --original experiments/chained-transfer-public-target/fixed-jacobian-chain-evaluator-01 \
  --out experiments/chained-transfer-public-target/fixed-jacobian-chain-reuse-01

python3 -S experiments/chained-transfer-public-target/norm-point-reuse-01/compare_norm_reuse.py --self-test
python3 -O -S experiments/chained-transfer-public-target/norm-point-reuse-01/compare_norm_reuse.py --self-test
\`\`\`

Native evaluation must then use the existing pinned Rust 1.99.1 source and
prepared-library/custody protocol with separately captured **original and
optimized** unfiltered logs, retained failures, and a strict 900-second/2 GiB
attempt cap. Do not run a new EKS job without budget and isolation admission.
The additive comparison is:

\`\`\`sh
python3 -S experiments/chained-transfer-public-target/norm-point-reuse-01/compare_norm_reuse.py \
  --original /path/to/original-native.txt \
  --optimized /path/to/reuse-native.txt
\`\`\`

Only the original 48 selected-call vectors may change, with exact counts:
direct map169 2→1 and norm doubling 0→1; literal map13 4→2 and
doubling 0→2; retained map13 4→2 and doubling 0→1. **Every other field in
each of the 695 whole ordered event records must compare exactly.**
It checks all 672 standalone exceptional records, both directions and all
four cofactor sectors. Six synthetic sabotage controls exercise omitted,
modified, misordered and miscounted records. These synthetic checks do not
substitute for running the actual native evaluator.

## Acceptance and cost frontier

1. Exact-source derivative: static generator + six negative comparator
   controls pass. Native compilation and full 695-record parity **pending**.
2. Same-host prices for \`C169\`, \`C13\` and elliptic norm doubling \`D\`;
   cold setup, Jacobian corrections/Phi/halving, memory, and complete primitive
   counters **not yet measured**.
3. Matched cold source ECDLP: optimize against the strongest same-curve
   rho/BSGS and published IC; all public logs checked equal, setup and
   linear algebra included, paired isolated timings and uncertainty with A/A
   and negative control. **Not yet performed**.

Conditional selected-call savings cannot be promoted to an ECDLP advantage.
The actual transfer can still lose once full costs are included. An elliptic
isogeny chain preserves the generic square-root DLP hardness of its elliptic
factor; beating rho requires a genuine additional algorithmic or arithmetic
advantage, not mere multiplication by a lower map degree.

## Literature and coordination

Prior work checked: cryptanalysis [CT35 #1500](https://github.com/isogeny-labs/cryptanalysis/pull/1500)
(exact cold toy negative comparison), crypto [#4215](https://github.com/isogeny-labs/crypto/pull/4215)
(selected-call prospective counts), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178)
(measured wall-clock component improvement but still far above rho in S),
and classical Vélu/Bostan–Morain–Salvy–Schost 2008
(https://arxiv.org/abs/cs/0609020). The shared research-KB MCP and
checkout-local wrapper and Conductor are unavailable in this runtime;
no novelty or absence is inferred. No EKS job, paid compute, protected
merge, signed PCC verdict or benchmark promotion is claimed.
