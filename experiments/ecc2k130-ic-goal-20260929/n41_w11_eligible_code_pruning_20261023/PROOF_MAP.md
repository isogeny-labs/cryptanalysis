# Proof map: ten-bit source-code exclusion clauses

The new logical result is the exactness of the generated mismatch clauses, independently of any curve equation. All declarations are in `EligibleCodeClauses.lean`, checked with the pinned `leanprover/lean4:v4.34.1` toolchain.

| Result | Lean declaration | Hypotheses and conclusion | Status |
| --- | --- | --- | --- |
| One exclusion clause | `forbids_iff_ne` | For any two functions `Fin 10 → Bool`, at least one differing bit is equivalent to inequality of the complete code words. | Checked |
| Whole eligible-code list | `all_forbidden_iff_eligible` | For any list of ten-bit words and candidate word, all clauses against words outside the list hold exactly when the candidate belongs to the list. Duplicates in the list are allowed. | Checked |
| Four source slots | `four_slots_iff_eligible` | For any four ten-bit words, the clause family in each slot holds exactly when each slot word is in the eligible list. | Checked |

The application bridge is the exhaustive Python assertion in `schedule.py`: all 1,024 code words were evaluated by `FixedSeed.source_valid`, and the resulting set equaled the 281-code archived input table. The four-slot SAT clause generation uses the same bit order as the source-code wires. The Lean statements do not assume this finite table or formalize `GF(2^41)` point eligibility; that bridge is checked by enumeration and the archived independent group census. All 32 census relations had source codes in the eligible set, so the added clauses retain their assignments.

`lean EligibleCodeClauses.lean` exited zero. The saved `lean_check.stdout` contains `#print axioms` output for each theorem: `propext`, `Classical.choice`, and `Quot.sound`. The module contains no `sorry`, `admit`, custom axiom, or native evaluation. `lean4checker --fresh` was not installed.
