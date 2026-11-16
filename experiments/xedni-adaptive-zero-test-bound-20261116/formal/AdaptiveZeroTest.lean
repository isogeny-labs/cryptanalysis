import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Tactic

namespace XedniAdaptiveZeroTest

structure Query (F : Type*) where
  a : F
  b : F
  t₁ : F
  t₂ : F

def hit {F : Type*} [Ring F] (query : Query F) (w : F) : Prop :=
  query.a * (w - query.t₁) + query.b * (w - query.t₂) = 0

def candidate {F : Type*} [DivisionRing F] (query : Query F) : F :=
  (query.a * query.t₁ + query.b * query.t₂) / (query.a + query.b)

theorem hit_iff_candidate {F : Type*} [Field F] (query : Query F)
    (hs : query.a + query.b ≠ 0) (w : F) :
    hit query w ↔ w = candidate query := by
  unfold hit candidate
  constructor
  · intro h
    apply (eq_div_iff hs).2
    linear_combination h
  · intro h
    apply (eq_div_iff hs).1 at h
    linear_combination h

/-- The candidate equivalence holds for actual public group relations once
the scalar-to-point map is injective. The pinned p=313 order certificate in
the parent experiment establishes this premise for its generator. -/
theorem group_hit_iff_candidate {F A : Type*} [Field F]
    [AddCommGroup A] [Module F A] (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (query : Query F) (hs : query.a + query.b ≠ 0) (w : F) :
    query.a • ((w - query.t₁) • G) +
      query.b • ((w - query.t₂) • G) = 0 ↔ w = candidate query := by
  have hrewrite : query.a • ((w - query.t₁) • G) +
      query.b • ((w - query.t₂) • G) =
      (query.a * (w - query.t₁) + query.b * (w - query.t₂)) • G := by
    simp [add_smul, mul_smul]
  rw [hrewrite]
  have hzero : (query.a * (w - query.t₁) + query.b * (w - query.t₂)) • G = 0 ↔
      query.a * (w - query.t₁) + query.b * (w - query.t₂) = 0 := by
    constructor
    · intro h
      apply hinj
      simpa using h
    · intro h
      simp [h]
  exact hzero.trans (hit_iff_candidate query hs w)

/-- A strategy can choose its next query using all preceding zero-test answers.
Before the first hit, that transcript is necessarily a list of `false` values. -/
def negativeQuery {F : Type*} (strategy : List Bool → Query F) (i : ℕ) : Query F :=
  strategy (List.replicate i false)

def succeedsWithin {F : Type*} [Ring F] (strategy : List Bool → Query F)
    (N : ℕ) (w : F) : Prop :=
  ∃ i ∈ Finset.range N, hit (negativeQuery strategy i) w

noncomputable def successSet {F : Type*} [Fintype F] [DecidableEq F] [Ring F]
    (strategy : List Bool → Query F) (N : ℕ) : Finset F := by
  classical
  exact Finset.univ.filter (succeedsWithin strategy N)

theorem adaptive_zero_test_success_set {F : Type*} [Fintype F] [DecidableEq F] [Field F]
    (strategy : List Bool → Query F) (N : ℕ)
    (hs : ∀ i ∈ Finset.range N,
      (negativeQuery strategy i).a + (negativeQuery strategy i).b ≠ 0) :
    successSet strategy N = (Finset.range N).image
      (fun i => candidate (negativeQuery strategy i)) := by
  classical
  let candidates : Finset F := (Finset.range N).image
    (fun i => candidate (negativeQuery strategy i))
  have hsubset : successSet strategy N ⊆ candidates := by
    intro w hw
    have hw' : succeedsWithin strategy N w := by
      simpa [successSet] using hw
    rcases hw' with ⟨i, hi, hhit⟩
    exact Finset.mem_image.mpr ⟨i, hi,
      ((hit_iff_candidate (negativeQuery strategy i) (hs i hi) w).mp hhit).symm⟩
  have hreverse : candidates ⊆ successSet strategy N := by
    intro w hw
    rcases Finset.mem_image.mp hw with ⟨i, hi, hcandidate⟩
    apply Finset.mem_filter.mpr
    refine ⟨Finset.mem_univ w, i, hi, ?_⟩
    exact (hit_iff_candidate (negativeQuery strategy i) (hs i hi) w).mpr
      hcandidate.symm
  exact Finset.Subset.antisymm hsubset hreverse

theorem adaptive_zero_test_hit_bound {F : Type*} [Fintype F] [DecidableEq F] [Field F]
    (strategy : List Bool → Query F) (N : ℕ)
    (hs : ∀ i ∈ Finset.range N,
      (negativeQuery strategy i).a + (negativeQuery strategy i).b ≠ 0) :
    (successSet strategy N).card ≤ N := by
  rw [adaptive_zero_test_success_set strategy N hs]
  calc
    ((Finset.range N).image (fun i => candidate (negativeQuery strategy i))).card
      ≤ (Finset.range N).card := Finset.card_image_le
    _ = N := Finset.card_range N

#print axioms hit_iff_candidate
#print axioms group_hit_iff_candidate
#print axioms adaptive_zero_test_success_set
#print axioms adaptive_zero_test_hit_bound

end XedniAdaptiveZeroTest
