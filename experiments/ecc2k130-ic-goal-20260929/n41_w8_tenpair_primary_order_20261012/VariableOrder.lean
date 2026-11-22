/- Exact satisfaction preservation when wire names are permuted. -/

import Std

namespace VariableOrder

abbrev Lit := Nat × Bool
abbrev Assignment := Nat → Bool

structure WirePerm where
  fwd : Nat → Nat
  bwd : Nat → Nat
  left_inv : ∀ n, bwd (fwd n) = n
  right_inv : ∀ n, fwd (bwd n) = n

def evalLit (a : Assignment) (l : Lit) : Bool :=
  if l.2 then a l.1 else !(a l.1)

def renameLit (p : WirePerm) (l : Lit) : Lit :=
  (p.fwd l.1, l.2)

def evalClause (a : Assignment) (l : List Lit) : Bool :=
  (l.map (evalLit a)).any id

def evalXor (a : Assignment) (l : List Lit) : Bool :=
  (l.map (evalLit a)).foldl Bool.xor false

def evalFormula (a : Assignment) (cnf xors : List (List Lit)) : Prop :=
  (∀ c ∈ cnf, evalClause a c = true) ∧
  (∀ x ∈ xors, evalXor a x = true)

theorem evalLit_rename (p : WirePerm) (a : Assignment) (l : Lit) :
    evalLit a (renameLit p l) = evalLit (a ∘ p.fwd) l := by
  cases l with
  | mk wire sign => cases sign <;> rfl

theorem evalClause_rename (p : WirePerm) (a : Assignment) (l : List Lit) :
    evalClause a (l.map (renameLit p)) = evalClause (a ∘ p.fwd) l := by
  simp [evalClause, List.map_map, Function.comp_def, evalLit_rename]

theorem evalXor_rename (p : WirePerm) (a : Assignment) (l : List Lit) :
    evalXor a (l.map (renameLit p)) = evalXor (a ∘ p.fwd) l := by
  simp [evalXor, List.map_map, Function.comp_def, evalLit_rename]

theorem formula_rename (p : WirePerm) (a : Assignment)
    (cnf xors : List (List Lit)) :
    evalFormula a (cnf.map (List.map (renameLit p)))
      (xors.map (List.map (renameLit p))) ↔
    evalFormula (a ∘ p.fwd) cnf xors := by
  simp [evalFormula, evalClause_rename, evalXor_rename]

theorem satisfiable_rename (p : WirePerm) (cnf xors : List (List Lit)) :
    (∃ a : Assignment, evalFormula a cnf xors) ↔
    (∃ a : Assignment,
      evalFormula a (cnf.map (List.map (renameLit p)))
        (xors.map (List.map (renameLit p)))) := by
  constructor
  · rintro ⟨a, ha⟩
    refine ⟨a ∘ p.bwd, ?_⟩
    rw [formula_rename]
    simpa [Function.comp_def, p.left_inv] using ha
  · rintro ⟨a, ha⟩
    exact ⟨a ∘ p.fwd, (formula_rename p a cnf xors).mp ha⟩

theorem n131_onehot_memory_gate :
    (34482792912 * 10 + 7) / 8 = 43103491140 ∧
    43103491140 > 4 * 1024 ^ 3 := by
  decide

#print axioms evalLit_rename
#print axioms evalClause_rename
#print axioms evalXor_rename
#print axioms formula_rename
#print axioms satisfiable_rename
#print axioms n131_onehot_memory_gate

end VariableOrder
