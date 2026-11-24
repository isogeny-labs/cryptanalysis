import RectangleFree

namespace PointTriangles

abbrev P := Fin 64
abbrev L := Fin 68

def onLine (p : P) (l : L) : Bool := (RectangleFree.points l).contains p.val

private def joins := Array.ofFn fun a : P => Array.ofFn fun b : P =>
  (List.finRange 68).find? (fun l => onLine a l && onLine b l)

def joinLine (a b : P) : Option L := (joins[a.val]!)[b.val]!

theorem join_exact : ∀ a b : P, a ≠ b → ∀ l : L,
    (joinLine a b = some l ↔ onLine a l = true ∧ onLine b l = true) := by
  native_decide

inductive Kind | absent | same | cycle | mixed deriving DecidableEq, Repr

def classify (a b c : P) : Kind :=
  match joinLine a b, joinLine b c, joinLine c a with
  | some i, some j, some k =>
    if i = j ∧ j = k then .same
    else if i ≠ j ∧ j ≠ k ∧ k ≠ i then .cycle else .mixed
  | _, _, _ => .absent

def triangleSet (kind : Kind) : Finset (P × P × P) :=
  Finset.univ.filter fun (a,b,c) => a < b ∧ b < c ∧ classify a b c = kind

theorem partition_sizes :
    (triangleSet .same).card = 3808 ∧ (triangleSet .cycle).card = 31360 ∧
    (triangleSet .absent).card = 6496 ∧ (triangleSet .mixed).card = 0 := by
  native_decide

/-- The common-line lookup evaluates each off-diagonal Gram entry,
independently of the coefficients chosen on incidences. -/
theorem overlap (H : Matrix P L ℤ) (outside : ∀ a l, onLine a l = false → H a l = 0)
    {a b : P} (hab : a ≠ b) :
    (H * H.transpose) a b =
      (joinLine a b).elim 0 (fun l => H a l * H b l) := by
  have vanish (l : L) (h : joinLine a b ≠ some l) : H a l * H b l = 0 := by
    have hn := mt (join_exact a b hab l).mpr h
    cases ha : onLine a l <;> cases hb : onLine b l <;> simp_all
  rw [Matrix.mul_apply]
  cases he : joinLine a b with
  | none => exact Finset.sum_eq_zero fun l _ => vanish l (by simp [he])
  | some k =>
    apply Finset.sum_eq_single k
    · intro l _ hl
      exact vanish l (by simp [he, Ne.symm hl])
    · simp

/-- A same-line triple has weight one under every choice of incidence signs. -/
theorem same_weight (H : Matrix P L ℤ) (outside : ∀ a l, onLine a l = false → H a l = 0)
    (unit : ∀ a l, onLine a l = true → H a l ^ 2 = 1)
    {a b c : P} (ab : a < b) (bc : b < c) (kind : classify a b c = .same) :
    (H * H.transpose) a b * (H * H.transpose) b c * (H * H.transpose) c a = 1 := by
  have ca := (ab.trans bc).ne.symm
  rw [overlap H outside ab.ne, overlap H outside bc.ne, overlap H outside ca]
  cases x : joinLine a b with
  | none => simp [classify, x] at kind
  | some i =>
    cases y : joinLine b c with
    | none => simp [classify, x, y] at kind
    | some j =>
      cases z : joinLine c a with
      | none => simp [classify, x, y, z] at kind
      | some k =>
        have eqs : i = j ∧ j = k := by
          by_contra h
          simp [classify, x, y, z, h] at kind
          split at kind <;> contradiction
        obtain ⟨rfl,rfl⟩ := eqs
        have h₁ := (join_exact a b ab.ne i).mp x
        have h₂ := (join_exact b c bc.ne i).mp y
        change (H a i * H b i) * (H b i * H c i) * (H c i * H a i) = 1
        calc
          _ = H a i ^ 2 * H b i ^ 2 * H c i ^ 2 := by ring
          _ = 1 := by rw [unit a i h₁.1, unit b i h₁.2, unit c i h₂.2]; decide

#print axioms partition_sizes
#print axioms overlap
end PointTriangles
