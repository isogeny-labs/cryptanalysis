import Std

/-! A source pair is retained by the product-span relaxation, and every
target S3 match between two source pairs survives the joint filter. The
field-specific halftrace implementation and curve-coordinate S3 bridge are
separate obligations recorded in PROOF_MAP.md. -/
namespace PairRelaxation

variable {F : Type} [Zero F] [One F] [Add F] [Mul F]

def pairEquation (c p s : F) : Prop :=
  ((1 + p * p) * c * c + p * c + s * s) = 0

def exactPair (usable : F → Prop) (c : F) : Prop :=
  ∃ a b : F, usable a ∧ usable b ∧ a ≠ b ∧
    pairEquation c (a * b) (a + b)

def relaxedPair (W D : F → Prop) (c : F) : Prop :=
  ∃ p s : F, D p ∧ W s ∧ pairEquation c p s

theorem exact_pair_in_product_span
    (usable W D : F → Prop) (c : F)
    (hW : ∀ a, usable a → W a)
    (hWadd : ∀ a b, W a → W b → W (a + b))
    (hD : ∀ a b, W a → W b → D (a * b))
    (hExact : exactPair usable c) : relaxedPair W D c := by
  obtain ⟨a, b, ha, hb, _hne, heq⟩ := hExact
  exact ⟨a * b, a + b,
    hD a b (hW a ha) (hW b hb),
    hWadd a b (hW a ha) (hW b hb), heq⟩

theorem exact_two_pair_target_survives
    (usable W D : F → Prop) (S3 : F → F → F → Prop)
    (c d target : F)
    (hW : ∀ a, usable a → W a)
    (hWadd : ∀ a b, W a → W b → W (a + b))
    (hD : ∀ a b, W a → W b → D (a * b))
    (hc : exactPair usable c) (hd : exactPair usable d)
    (hlink : S3 c d target) :
    relaxedPair W D c ∧ relaxedPair W D d ∧ S3 c d target := by
  exact ⟨exact_pair_in_product_span usable W D c hW hWadd hD hc,
         exact_pair_in_product_span usable W D d hW hWadd hD hd,
         hlink⟩

#print axioms PairRelaxation.exact_pair_in_product_span
#print axioms PairRelaxation.exact_two_pair_target_survives
end PairRelaxation
