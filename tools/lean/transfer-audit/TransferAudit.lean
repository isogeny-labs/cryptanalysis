import Std

/-! Tool-certificate semantics only. Finite-group, Weil, Tate and algebraic-geometry
bridges remain written mathematics; none is silently introduced as a Lean axiom. -/
namespace TransferAudit

theorem size_obstruction (r n bound : Nat)
    (hinj : r ≤ n) (hbound : n ≤ bound) (hsmall : bound < r) : False := by
  omega

theorem divisibility_obstruction (r n bound : Nat)
    (hpos : 0 < n) (hdiv : r ∣ n) (hbound : n ≤ bound) (hsmall : bound < r) : False := by
  have hle := Nat.le_of_dvd hpos hdiv
  omega

/-- Replay must independently establish both enumerator completeness and test soundness. -/
theorem closed_coverage {α : Type} (domain visited : List α)
    (reject : α → Bool) (admissible : α → Prop)
    (cover : ∀ x, x ∈ domain → x ∈ visited)
    (sound : ∀ x, reject x = true → ¬ admissible x)
    (checked : visited.all reject = true) :
    ∀ x, x ∈ domain → ¬ admissible x := by
  intro x hx
  exact sound x ((List.all_eq_true.mp checked) x (cover x hx))

/-- A matching trace transports any property depending only on that trace.
This is not a formalization of Tate's theorem. -/
theorem invariant_transport {α β : Type} (invariant : α → β)
    (property : β → Prop) (x y : α) (heq : invariant x = invariant y)
    (hx : property (invariant x)) : property (invariant y) := by
  simpa only [heq] using hx

/-- Integer coefficients in (q+1+2√q)^g = A_g+B_g√q. -/
def weilPair (q : Nat) : Nat → Nat × Nat
  | 0 => (1, 0)
  | g+1 => let (a,b) := weilPair q g
           (a*(q+1)+2*b*q, 2*a+b*(q+1))

def integerWeilBound (q g : Nat) : Nat :=
  let (a,b) := weilPair q g
  a + Nat.sqrt (b*b*q)

def b163Prime : Nat := 5846006549323611672814742442876390689256843201587

theorem sqrt_upper (n u : Nat) (h : n < (u+1)*(u+1)) : Nat.sqrt n ≤ u := by
  by_cases hn : Nat.sqrt n ≤ u
  · exact hn
  have hle : u+1 ≤ Nat.sqrt n := by omega
  have hp := Nat.mul_le_mul hle hle
  have hs := Nat.sqrt_le n
  omega

theorem sqrt_lower (n l : Nat) (h : l*l ≤ n) : l ≤ Nat.sqrt n := by
  by_cases hn : l ≤ Nat.sqrt n
  · exact hn
  have hle : Nat.sqrt n + 1 ≤ l := by omega
  have hp := Nat.mul_le_mul hle hle
  have hs := Nat.lt_succ_sqrt n
  simp only [Nat.succ_eq_add_one] at hs
  omega

theorem pair63 : weilPair 2 63 = (848606505733840948241852054437801506505048644099, 600055414763419758512382581064986635475955641470) := by decide

theorem b163_genus63_bound : integerWeilBound 2 63 < b163Prime := by
  have hs : Nat.sqrt (600055414763419758512382581064986635475955641470*600055414763419758512382581064986635475955641470*2) ≤ 848606505733840948241852054437801506505048644098 := sqrt_upper _ _ (by decide)
  have hn : 848606505733840948241852054437801506505048644099 + 848606505733840948241852054437801506505048644098 < b163Prime := by decide
  simp only [integerWeilBound, pair63]
  omega

theorem pair64 : weilPair 2 64 = (4946041176255201878775086487573351061418968498177, 3497379255757941172020851852070562919437964212608) := by decide

theorem b163_genus64_bound : b163Prime ≤ integerWeilBound 2 64 := by
  have hs : 4946041176255201878775086487573351061418968498176 ≤ Nat.sqrt (3497379255757941172020851852070562919437964212608*3497379255757941172020851852070562919437964212608*2) := sqrt_lower _ _ (by decide)
  have hn : b163Prime ≤ 4946041176255201878775086487573351061418968498177 + 4946041176255201878775086487573351061418968498176 := by decide
  simp only [integerWeilBound, pair64]
  omega

theorem b163_obstruction (card : Nat) (hpos : 0 < card)
    (hdiv : b163Prime ∣ card) (hbound : card ≤ integerWeilBound 2 63) : False :=
  divisibility_obstruction b163Prime card (integerWeilBound 2 63)
    hpos hdiv hbound b163_genus63_bound

#print axioms size_obstruction
#print axioms divisibility_obstruction
#print axioms closed_coverage
#print axioms invariant_transport
#print axioms b163_genus63_bound
#print axioms b163_genus64_bound
#print axioms b163_obstruction
end TransferAudit
