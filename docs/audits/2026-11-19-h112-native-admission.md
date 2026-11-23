# H112 source-bound maintained native admission

[pcc:unverified] The corpus job on commit `9ba637e851d8408e8c0fc116f105372fce87e114` refused the unchanged recovered H112 proof because its study-root path had no reviewed native admission. This change registers exactly that path and SHA-256, preserves every original proof, build receipt and empirical record, and adds a separate maintained replay context. The provenance reports Lean 4.34.1 without identifying its historical Mathlib revision in the reviewed bundle. The new replay uses Lean 4.35.0-rc4 and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`; it does not establish historical build reproduction.

[pcc:unverified] Local native compilation checks the eight original declaration printouts, then audits all twelve noninternal theorems, including four generated equations. All twelve identities and elaborated types are required. Source, auditor, project inputs and compiled objects are checked at phase boundaries. The original bytes are compiled directly. The static escape-token check uses the existing nested-comment lexer, avoiding a refusal caused by the documentation word `axiom`; active escape tokens remain visible, and the native transitive-axiom audit still runs.

## Semantic scope

| Original theorem | What its statement establishes |
| --- | --- |
| `carry_mem_reduction_kernel` | Kernel membership follows from the reduction/section and halving assumptions. |
| `homomorphic_section_carry_zero` | A homomorphic section gives zero carry under the halving equality. |
| `digit_recombination`, `highDigit_lt` | Natural-number division identities and a bound under positive modulus and bounded input. |
| `exact_predicate_supplies_parity` | Restates the supplied exact-predicate hypothesis at one point; it does not construct that predicate. |
| `reconstruct_eq` | A natural-number recursion reconstructs an integer given its exact remainder oracle; it does not implement public-point halving or prove an oracle's cost. |
| `verified_scalar_unique` | Injectivity and two image equalities imply equality of scalar inputs. |
| `totalCost_bound` | An assumed bound on the sum implies the same bound for the defined total; it does not supply measured costs. |

[pcc:unverified] The native result therefore covers these structural and conditional interfaces. It does not strengthen the original predicate screen or its empirical status. The four additional native theorems are generated equations for `carry` and `reconstruct`, not new empirical claims.

## Controls and delivery

[pcc:unverified] The local integration run passed 148 tests, including ten H112 controls. Changed source/build pins, incomplete or extra theorem inventories, same-count namespace substitutions and compiler failures are refused. The workflow now invokes unittest discovery: direct execution previously reached `unittest.main()` before two later classes, omitting 21 existing tests. No assertion or frozen record is removed.

[pcc:unverified] Failed and bounded local attempts are retained separately. The final integrated native run passed and its command-file hashes were rechecked. The adjacent JSON records its exact scope and input hashes. Full corpus CI and every applicable merge check remain required; a local result is not a signed PCC verdict.
