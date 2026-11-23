# CT318 — joint cold-cost and source-group replay gate (preregistered 2026-11-22)

**Standing:** [pcc:unverified]. Owner: draft PR #1920; successor of merged #1912. No new model execution.

## Decision and rationale

CT315 (source-only seven-arm cost/RSS audit) and CT317 (source-only independent short-Weierstrass Q=[k]P group replay and raw-output hashes) currently require separate manual invocations. A cost-ratio report can therefore be produced without the independent group checker, and a valid group replay can be reported without a matched fully charged cost panel. CT318 composes **the original two auditors without modifying or bypassing their gates**, always using exactly the same raw input panel object for both. A passing joint source-admission object is neither independent execution authentication nor a signed speedup.

Before writing CT318 code, freeze these checks:

1. Required CLI: `--panel` one exact file, `--witness` one exact public curve/target manifest, `--raw-root` one read-only per-run raw evidence directory. Parse each JSON with CT315/CT317 strict duplicate-key and NaN/Infinity rejection; do not rewrite source files or emit them as performance evidence. Report SHA-256 of the exact raw panel and manifest **bytes** and each checker result.
2. Invoke `ct315_complete_cold_panel.audit(panel)` and `ct317_group_replay.audit(panel,witness,raw_root)` on the *same* parsed panel. Any error in either fails the combined admission; never replace a failed checker with a synthetically constructed or adapted panel. Do not trust supplied `verified` booleans, roundtrip serialization or user-reported process timestamps.
3. Return only `ct318-joint-source-admission/v1` and descriptive CT315 provisional exact baseline/candidate ratio plus CT317 recovered Q=[k]P count. Hard-code independent execution, complete cost reproduction, signed speedup and PCC as false/unverified. A printed provisional ratio >1 is not an advantage claim.
4. Self-test materializes a completely **synthetic** 28-run four-block ABBA panel (retained, candidate, candidate, retained, rho, BSGS, IC) over the actual tiny group E/F97:y²=x³+2x+3, P=(3,6) prime order 5, Q=(80,10)=[2]P, with fabricated wall/RSS/phase/receipt data. Test both a synthetic positive provisional ratio and a synthetic negative ratio. Sabotage must reject a valid CT315 panel with false Q, valid CT317 rows with invalid cold phase, single forged raw stdout hash, missing raw receipt, different target, and duplicate JSON key. Repeat normal Python and `python3 -O`.
5. No edits to CT315, CT317, six original S3 models, native Rust, historical 695/701 fixture, recorded counters, shared PCC ledger or protected branches. This new gate is *pre-native* source custody only; does not price C169/C13a/C13b/D/N2_actual.

## Prior art and scope boundaries

Earlier gates: CT315_COMPLETE_COLD_PANEL_PROTOCOL.md and CT317_INDEPENDENT_PRIMEFIELD_GROUP_REPLAY_PROTOCOL.md in this directory; original #3877; symbolic #4215; merged #1912. NIST SP 800-56A Rev.3 §5.6.2.3.3 treats point/subgroup validation; CT317 adds direct source equation replay. The Diem 2012 J. Théorie Nombres Bordeaux article DOI:10.5802/jtnb.815 addresses nonhyperelliptic genus-3 IC, not an automatic elliptic-to-Jacobian transfer. This task claims no new cryptanalytic mechanism. Shared research-KB server was not exposed in the current connector runtime and crypto-autoresearcher AGENTS/lab-contract failed GitHub UTF-8 decode; literature and cross-repo novelty searches are nonexhaustive.

## Next real scientific gate

Restore *authorized* coherent six-object S3 custody and artifact-tool/STS pairing; reproduce original and norm-reuse 695/701 native source maps (including 672 exceptions) under a preregistered same-host budget; directly meter C169/C13a/C13b/D/N2_actual and actual cold solver processes. Charge complete cold setup/transfer/precompute/relation/LA/descent/recovery/verification/teardown, memory and uncertainty versus strongest retained lift, optimized rho, BSGS and frontier IC. Independent validator and signed PCC must verify a measured complete-solve baseline/candidate >1; a slower result is recorded, not omitted.

[pcc:unverified]
