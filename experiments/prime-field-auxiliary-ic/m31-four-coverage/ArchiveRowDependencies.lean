import Mathlib.Tactic

namespace M31.ArchiveRowDependencies

/- Each left side lists the nonempty factor-base columns in index order.
The variable rK is the coefficient of the Kth archived row, starting at one.
Entries come from the i,j,si,sj fields in v2_batch_seed{0,1,2}.relations.jsonl
at commit 9a1d8a6cf. The final row coefficient parametrizes every dependency. -/

theorem seed0 (r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12 r13 r14 r15 : ℤ) :
    (r6 + r12 = 0 ∧
     r10 = 0 ∧
     -r3 = 0 ∧
     r1 = 0 ∧
     r2 -r13 = 0 ∧
     -r4 + r5 = 0 ∧
     r3 + r13 + r14 = 0 ∧
     -r9 - r11 = 0 ∧
     r11 -r12 - r15 = 0 ∧
     r1 = 0 ∧
     r4 + r14 = 0 ∧
     -r8 + r10 = 0 ∧
     r7 = 0 ∧
     -r6 - r8 = 0 ∧
     r2 + r5 + r9 -r15 = 0 ∧
     -r7 = 0) ↔
    (r1 = 0 ∧
     r2 = r15 ∧
     r3 = 0 ∧
     r4 = r15 ∧
     r5 = r15 ∧
     r6 = 0 ∧
     r7 = 0 ∧
     r8 = 0 ∧
     r9 = -r15 ∧
     r10 = 0 ∧
     r11 = r15 ∧
     r12 = 0 ∧
     r13 = r15 ∧
     r14 = -r15) := by
  omega

theorem seed1 (r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12 r13 r14 : ℤ) :
    (-r1 + (2) * r6 - r13 = 0 ∧
     r5 -r13 = 0 ∧
     r3 = 0 ∧
     r5 -r9 = 0 ∧
     (-2) * r7 -r8 = 0 ∧
     r11 = 0 ∧
     -r3 - r4 = 0 ∧
     -r9 + r12 = 0 ∧
     r10 -r11 - r14 = 0 ∧
     -r8 = 0 ∧
     -r2 - r4 = 0 ∧
     -r1 - r2 + r10 = 0 ∧
     -r12 - r14 = 0) ↔
    (r1 = r14 ∧
     r2 = 0 ∧
     r3 = 0 ∧
     r4 = 0 ∧
     r5 = -r14 ∧
     r6 = 0 ∧
     r7 = 0 ∧
     r8 = 0 ∧
     r9 = -r14 ∧
     r10 = r14 ∧
     r11 = 0 ∧
     r12 = -r14 ∧
     r13 = -r14) := by
  omega

theorem seed2 (r1 r2 r3 r4 r5 r6 r7 r8 r9 : ℤ) :
    (r2 + r9 = 0 ∧
     -r3 = 0 ∧
     r3 -r5 = 0 ∧
     r2 + r6 -r8 = 0 ∧
     -r7 = 0 ∧
     r1 + r4 = 0 ∧
     -r1 - r5 + r7 - r8 = 0 ∧
     r4 + r6 + r9 = 0) ↔
    (r1 = r9 ∧
     r2 = -r9 ∧
     r3 = 0 ∧
     r4 = -r9 ∧
     r5 = 0 ∧
     r6 = 0 ∧
     r7 = 0 ∧
     r8 = -r9) := by
  omega

end M31.ArchiveRowDependencies
