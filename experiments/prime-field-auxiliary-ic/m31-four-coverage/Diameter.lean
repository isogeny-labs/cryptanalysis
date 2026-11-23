import Mathlib.Data.Finset.Card
import Mathlib.Algebra.BigOperators.Group.List.Basic
import Mathlib.Algebra.Group.Basic
import Mathlib.Data.Fintype.Card
import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace M31FourCoverage

variable {G : Type*} [AddCommGroup G] [Fintype G] [DecidableEq G]

theorem dense_sum (s t : Finset G) (h : Fintype.card G < s.card + t.card) (g : G) :
    ∃ a ∈ s, ∃ b ∈ t, a + b = g := by
  classical
  by_contra miss
  have hd : Disjoint s (t.image (fun b => g-b)) := by
    rw [Finset.disjoint_left]
    intro a ha hi
    obtain ⟨b,hb,rfl⟩ := Finset.mem_image.mp hi
    exact miss ⟨_,ha,b,hb,sub_add_cancel g b⟩
  have cap := Finset.card_le_univ (s ∪ t.image (fun b => g-b))
  rw [Finset.card_union_of_disjoint hd, Finset.card_image_of_injective _ (by
    intro x y he
    simpa using he)] at cap
  omega

def reachable (basis : Finset G) (n : Nat) (x : G) :=
  ∃ terms : List G, terms.length ≤ n ∧ (∀ a ∈ terms, a ∈ basis) ∧ terms.sum = x

theorem diameter_bound (basis s t : Finset G) {r k : Nat}
    (hs : ∀ x ∈ s, reachable basis r x) (ht : ∀ x ∈ t, reachable basis k x)
    (h : Fintype.card G < s.card + t.card) (g : G) : reachable basis (r+k) g := by
  obtain ⟨a,ha,b,hb,rfl⟩ := dense_sum s t h g
  obtain ⟨u,hu,hbu,rfl⟩ := hs a ha
  obtain ⟨v,hv,hbv,rfl⟩ := ht b hb
  refine ⟨u++v, by simpa using Nat.add_le_add hu hv, ?_, List.sum_append⟩
  intro x hx
  exact (List.mem_append.mp hx).elim (hbu x) (hbv x)

/-- Count distinct first summands that can be completed, for any group element. -/
theorem fixture_overlap (s t : Finset G) (hn : Fintype.card G = 2147505293)
    (hs : s.card = 783104641) (ht : t.card = 1586841251) (g : G) :
    222440599 ≤ (s ∩ t.image (fun b => g-b)).card := by
  have cap := Finset.card_le_univ (s ∪ t.image (fun b => g-b))
  have total := Finset.card_union_add_card_inter s (t.image (fun b => g-b))
  rw [Finset.card_image_of_injective _ (by intro x y he; simpa using he)] at total
  omega

theorem fixture_nine (basis s t : Finset G) (hn : Fintype.card G = 2147505293)
    (cs : s.card = 783104641) (ct : t.card = 1586841251)
    (hs : ∀ x ∈ s, reachable basis 4 x) (ht : ∀ x ∈ t, reachable basis 5 x)
    (g : G) : reachable basis 9 g :=
  diameter_bound basis s t hs ht (by omega) g

omit [DecidableEq G] in
/-- A measured union of radius-four translates certifies exact diameter five
when it fills the group and the radius-four ball is strictly smaller. -/
theorem exact_five_of_translates (basis four cover : Finset G)
    (hfour : ∀ g, g ∈ four ↔ reachable basis 4 g)
    (small : four.card < Fintype.card G) (full : cover.card = Fintype.card G)
    (hcover : ∀ g ∈ cover, ∃ x ∈ four, g = x ∨ ∃ b ∈ basis, g = b + x) :
    (∀ g, reachable basis 5 g) ∧ ¬ ∀ g, reachable basis 4 g := by
  have hu := Finset.eq_univ_of_card cover full
  constructor
  · intro g
    have hg : g ∈ cover := by simp [hu]
    obtain ⟨x,hx,he⟩ := hcover g hg
    obtain ⟨terms,hlen,hm,hsum⟩ := (hfour x).mp hx
    rcases he with rfl | ⟨b,hb,rfl⟩
    · exact ⟨terms, by omega, hm, hsum⟩
    · refine ⟨b::terms, by simp only [List.length_cons]; omega, ?_, ?_⟩
      · intro z hz
        exact (List.mem_cons.mp hz).elim (fun e => e ▸ hb) (hm z)
      · simp [hsum]
  · intro hall
    have h : four = Finset.univ := by
      ext g
      simp [(hfour g).mpr (hall g)]
    simp [h] at small

/-- First and second differences for the independent full-curve abscissa scan. -/
theorem cubic_scan_step {R : Type*} [CommRing R] (x : R) :
    (x+1)^3+2*(x+1)+14 = (x^3+2*x+14)+(3*x^2+3*x+3) ∧
    3*(x+1)^2+3*(x+1)+3 = (3*x^2+3*x+3)+(6*x+6) ∧
    6*(x+1)+6 = (6*x+6)+6 := by
  constructor
  · ring
  constructor <;> ring

/-- Checking support by abscissa covers both affine ordinates when the
recorded point set is closed under reflection. -/
theorem affine_cover_of_abscissae {F : Type*} [Field F] (rhs : F → F)
    (covered : F → F → Prop)
    (reflect : ∀ x y, covered x y → covered x (-y))
    (abscissae : ∀ x, (∃ y, y^2 = rhs x) → ∃ w, w^2 = rhs x ∧ covered x w)
    (x y : F) (hy : y^2 = rhs x) : covered x y := by
  obtain ⟨w, hw, hc⟩ := abscissae x ⟨y, hy⟩
  rcases sq_eq_sq_iff_eq_or_eq_neg.mp (hy.trans hw.symm) with h | h
  · simpa [h] using hc
  · simpa [h] using reflect x w hc

theorem half_square_table (r : ZMod 2147483647) :
    (∃ y : ZMod 2147483647, y^2 = r) ↔
      ∃ y : ZMod 2147483647, y.val ≤ 1073741823 ∧ y^2 = r := by
  constructor
  · rintro ⟨y,hy⟩
    by_cases small : y.val ≤ 1073741823
    · exact ⟨y,small,hy⟩
    · have hn : y ≠ 0 := by intro he; simp [he] at small
      refine ⟨-y, ?_, by simpa using hy⟩
      simp only [ZMod.neg_val, hn, ↓reduceIte]
      omega
  · rintro ⟨y,_,hy⟩
    exact ⟨y,hy⟩

end M31FourCoverage
