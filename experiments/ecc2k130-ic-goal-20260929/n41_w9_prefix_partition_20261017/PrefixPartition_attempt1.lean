import Std

namespace PrefixPartition

/-- Every eight-bit source code belongs to one of the eight high-three-bit
prefix classes. -/
theorem prefix_in_range (code : Nat) (h : code < 256) : code / 32 < 8 := by
  omega

/-- The quotient gives exactly the interval selected by the three unit
clauses, so the classes neither miss nor overlap source codes. -/
theorem prefix_interval (code prefix : Nat) :
    code / 32 = prefix ↔ 32 * prefix ≤ code ∧ code < 32 * (prefix+1) := by
  omega

/-- A satisfying assignment whose first source code lies in a prefix
retains its original predicate when that prefix is imposed. -/
theorem matching_restriction {α : Type} (base : α → Prop)
    (code : α → Nat) (assignment : α) (prefix : Nat)
    (hbase : base assignment) (hprefix : code assignment / 32 = prefix) :
    base assignment ∧ code assignment / 32 = prefix := by
  exact ⟨hbase,hprefix⟩

#print axioms PrefixPartition.prefix_in_range
#print axioms PrefixPartition.prefix_interval
#print axioms PrefixPartition.matching_restriction

end PrefixPartition
