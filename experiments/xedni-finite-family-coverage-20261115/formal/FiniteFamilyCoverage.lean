import Mathlib.Algebra.Field.Defs
import Mathlib.Data.Finset.Card
import Mathlib.Tactic

namespace XedniFiniteFamilyCoverage

variable {K : Type*} [Field K] [DecidableEq K]

/-- The reduced public relation equation for `R₁=dG`, `R₂=(d-t)G`. -/
def relation (c : K × K) (d t : K) : Prop :=
  (c.1 + c.2) * d = c.2 * t

/-- The single target scalar selected by one effective coefficient/offset pair. -/
def candidate (c : K × K) (t : K) : K :=
  c.2 * t / (c.1 + c.2)

/-- All targets selected by a fixed coefficient family and offset set. -/
def winners (C : Finset (K × K)) (T : Finset K) : Finset K :=
  (C.product T).image (fun ct => candidate ct.1 ct.2)

theorem relation_eq_candidate {c : K × K} {d t : K}
    (h : c.1 + c.2 ≠ 0) (hr : relation c d t) : d = candidate c t := by
  unfold candidate
  apply (eq_div_iff h).2
  simpa only [relation, mul_comm] using hr

theorem relation_mem_winners {C : Finset (K × K)} {T : Finset K}
    {c : K × K} {d t : K} (hc : c ∈ C) (ht : t ∈ T)
    (h : c.1 + c.2 ≠ 0) (hr : relation c d t) : d ∈ winners C T := by
  unfold winners
  apply Finset.mem_image.mpr
  refine ⟨(c,t), Finset.mem_product.mpr ⟨hc,ht⟩, ?_⟩
  exact (relation_eq_candidate h hr).symm

theorem card_winners_le (C : Finset (K × K)) (T : Finset K) :
    (winners C T).card ≤ C.card * T.card := by
  unfold winners
  calc
    ((C.product T).image (fun ct => candidate ct.1 ct.2)).card ≤
        (C.product T).card := Finset.card_image_le
    _ = C.card * T.card := Finset.card_product C T

theorem card_winners_le_cap (C : Finset (K × K)) (T : Finset K)
    (B L : ℕ) (hC : C.card ≤ B) (hT : T.card ≤ L) :
    (winners C T).card ≤ B * L := by
  exact (card_winners_le C T).trans (Nat.mul_le_mul hC hT)

/-- The one zero-sum vector is omitted from scalar-recovering coverage. -/
def integerFamily : Finset (ℤ × ℤ) :=
  {(1,-3), (1,-2), (1,-1), (1,1), (1,2), (1,3),
   (2,-3), (2,-1), (2,1), (2,3),
   (3,-2), (3,-1), (3,1), (3,2)}

theorem effective_integer_family_card :
    (integerFamily.filter (fun c => c.1 + c.2 ≠ 0)).card = 13 := by
  decide

#print axioms relation_eq_candidate
#print axioms relation_mem_winners
#print axioms card_winners_le
#print axioms card_winners_le_cap
#print axioms effective_integer_family_card

end XedniFiniteFamilyCoverage
