import Mathlib.Data.Finset.Card
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Int.Interval
import Mathlib.Data.Fintype.BigOperators

/-!
The finite pigeonhole step in the bounded-witness argument of Jacobson,
Koblitz, Silverman, Stein, and Teske, Analysis of the Xedni Calculus Attack,
Lemma 4.1. The arithmetic estimate for the lifted height ball is an explicit
input; it is not encoded as a claim-specific axiom.
-/

namespace XedniHeightPigeonhole

variable {r K : ℕ} {H : Type*} [AddCommGroup H]

def Relation (points : Fin r → H) (coeff : Fin r → ℤ) : Prop :=
  ∑ i, coeff i • points i = 0

def Nontrivial (coeff : Fin r → ℤ) : Prop :=
  ∃ i, coeff i ≠ 0

def Bounded (bound : ℕ) (coeff : Fin r → ℤ) : Prop :=
  ∀ i, (coeff i).natAbs ≤ bound

/-- The full integer coefficient box of radius `K`. -/
def coefficientBox (r K : ℕ) : Finset (Fin r → ℤ) :=
  Fintype.piFinset fun _ => Finset.Icc (-(K : ℤ)) (K : ℤ)

theorem coefficientBox_card (r K : ℕ) :
    (coefficientBox r K).card = (2 * K + 1) ^ r := by
  classical
  rw [coefficientBox, Fintype.card_piFinset_const]
  simp only [Int.card_Icc]
  congr 1
  omega

theorem coefficientBox_bounded {r K : ℕ} {coeff : Fin r → ℤ}
    (h : coeff ∈ coefficientBox r K) : Bounded K coeff := by
  classical
  intro i
  have hi := (Fintype.mem_piFinset.mp h) i
  simp only [Finset.mem_Icc] at hi
  omega

/-- More short coefficient vectors than possible sum values force a
nontrivial relation whose coordinate magnitudes are at most twice the box
radius. The finite `values` set can be a certified canonical-height ball. -/
theorem bounded_relation_of_card_lt
    (points : Fin r → H)
    (box : Finset (Fin r → ℤ)) (values : Finset H)
    (hcard : values.card < box.card)
    (hvalues : ∀ coeff ∈ box, (∑ i, coeff i • points i) ∈ values)
    (hbox : ∀ coeff ∈ box, Bounded K coeff) :
    ∃ coeff, Nontrivial coeff ∧ Bounded (2 * K) coeff ∧
      Relation points coeff := by
  classical
  let eval : (Fin r → ℤ) → H := fun coeff => ∑ i, coeff i • points i
  have hmap : Set.MapsTo eval (box : Set (Fin r → ℤ)) (values : Set H) := by
    intro coeff hc
    exact hvalues coeff hc
  obtain ⟨a, ha, b, hb, hab, heq⟩ :=
    Finset.exists_ne_map_eq_of_card_lt_of_maps_to hcard hmap
  have hcoord : ∃ i, a i ≠ b i := by
    by_contra h
    push Not at h
    apply hab
    funext i
    exact h i
  obtain ⟨i, hi⟩ := hcoord
  refine ⟨fun j => a j - b j, ⟨i, sub_ne_zero.mpr hi⟩, ?_, ?_⟩
  · intro j
    calc
      (a j - b j).natAbs ≤ (a j).natAbs + (b j).natAbs :=
        Int.natAbs_sub_le _ _
      _ ≤ K + K := Nat.add_le_add (hbox a ha j) (hbox b hb j)
      _ = 2 * K := by omega
  · unfold Relation
    dsimp [eval] at heq
    calc
      (∑ j, (a j - b j) • points j) =
          (∑ j, a j • points j) - (∑ j, b j • points j) := by
            simp_rw [sub_smul]
            rw [Finset.sum_sub_distrib]
      _ = 0 := sub_eq_zero.mpr heq

/-- A rank or height estimate may establish the cardinal inequality only
when dependence holds. In that form the pigeonhole result supplies the
bounded witness needed by the reduction-map obstruction. -/
theorem bounded_witness_of_card_lt_on_dependence
    (points : Fin r → H)
    (box : Finset (Fin r → ℤ)) (values : Finset H)
    (hcard : (∃ coeff, Nontrivial coeff ∧ Relation points coeff) →
      values.card < box.card)
    (hvalues : ∀ coeff ∈ box, (∑ i, coeff i • points i) ∈ values)
    (hbox : ∀ coeff ∈ box, Bounded K coeff) :
    (∃ coeff, Nontrivial coeff ∧ Relation points coeff) →
      ∃ witness, Nontrivial witness ∧ Bounded (2 * K) witness ∧
        Relation points witness := by
  intro hdep
  exact bounded_relation_of_card_lt points box values (hcard hdep)
    hvalues hbox

/-- The exact coefficient-box threshold for the finite height-ball step. -/
theorem bounded_relation_of_height_ball_count
    (points : Fin r → H) (values : Finset H)
    (hcard : values.card < (2 * K + 1) ^ r)
    (hvalues : ∀ coeff ∈ coefficientBox r K,
      (∑ i, coeff i • points i) ∈ values) :
    ∃ coeff, Nontrivial coeff ∧ Bounded (2 * K) coeff ∧
      Relation points coeff := by
  apply bounded_relation_of_card_lt points (coefficientBox r K) values
  · simpa [coefficientBox_card] using hcard
  · exact hvalues
  · intro coeff hc
    exact coefficientBox_bounded hc

/-- Values expressible with one of the recorded torsion elements and a
bounded coordinate vector in a rank-`d` free part. The basis need not be
independent for the upper bound. -/
noncomputable def latticeValues {d : ℕ} (basis : Fin d → H)
    (torsion : Finset H) (K : ℕ) : Finset H := by
  classical
  exact (torsion.product (coefficientBox d K)).image
    (fun pair => pair.1 + ∑ j, pair.2 j • basis j)

theorem latticeValues_card_le {d : ℕ} (basis : Fin d → H)
    (torsion : Finset H) (K : ℕ) :
    (latticeValues basis torsion K).card ≤
      torsion.card * (2 * K + 1) ^ d := by
  classical
  unfold latticeValues
  calc
    ((torsion.product (coefficientBox d K)).image
      (fun pair => pair.1 + ∑ j, pair.2 j • basis j)).card ≤
        (torsion.product (coefficientBox d K)).card := Finset.card_image_le
    _ = torsion.card * (2 * K + 1) ^ d := by
      simp [coefficientBox_card]

/-- A bounded-coordinate representation of all short lifted sums, together
with a strict rank-and-torsion count, yields a bounded relation. The
arithmetic height argument must establish `hrep` and `hcount` for its lift
family. -/
theorem bounded_relation_of_lattice_representation {d : ℕ}
    (points : Fin r → H) (basis : Fin d → H)
    (torsion : Finset H) (L K : ℕ)
    (hrep : ∀ coeff ∈ coefficientBox r L,
      ∃ τ ∈ torsion, ∃ a ∈ coefficientBox d K,
        (∑ i, coeff i • points i) = τ + ∑ j, a j • basis j)
    (hcount : torsion.card * (2 * K + 1) ^ d <
      (2 * L + 1) ^ r) :
    ∃ coeff, Nontrivial coeff ∧ Bounded (2 * L) coeff ∧
      Relation points coeff := by
  classical
  apply bounded_relation_of_height_ball_count points
    (latticeValues basis torsion K)
  · exact (latticeValues_card_le basis torsion K).trans_lt hcount
  · intro coeff hc
    obtain ⟨τ, hτ, a, ha, heq⟩ := hrep coeff hc
    rw [heq]
    unfold latticeValues
    exact Finset.mem_image.mpr
      ⟨(τ, a), Finset.mem_product.mpr ⟨hτ, ha⟩, rfl⟩

/-- An explicit rank-gap threshold: if the lattice coordinate radius is at
most `c * L`, then `L > T(2c+1)^d` suffices for the strict count whenever
`d < r`. -/
theorem rank_gap_count (T d r c K L : ℕ)
    (hdegree : d < r) (hcoord : K ≤ c * L)
    (hlarge : T * (2 * c + 1) ^ d < L) :
    T * (2 * K + 1) ^ d < (2 * L + 1) ^ r := by
  have hL : 0 < L := by omega
  have hbase : 2 * K + 1 ≤ (2 * c + 1) * L := by
    calc
      2 * K + 1 ≤ 2 * (c * L) + 1 := by omega
      _ ≤ (2 * c + 1) * L := by
        calc
          2 * (c * L) + 1 ≤ 2 * (c * L) + L := by omega
          _ = (2 * c + 1) * L := by simp [add_mul, mul_assoc]
  have hpow : (2 * K + 1) ^ d ≤ ((2 * c + 1) * L) ^ d := by
    gcongr <;> omega
  have hstrict : (T * (2 * c + 1) ^ d) * L ^ d < L * L ^ d :=
    Nat.mul_lt_mul_of_pos_right hlarge (pow_pos hL d)
  have hexp : L ^ (d + 1) ≤ (2 * L + 1) ^ r := by
    calc
      L ^ (d + 1) ≤ (2 * L + 1) ^ (d + 1) := by gcongr <;> omega
      _ ≤ (2 * L + 1) ^ r := pow_le_pow_right₀ (by omega) (by omega)
  calc
    T * (2 * K + 1) ^ d ≤ T * ((2 * c + 1) * L) ^ d :=
      Nat.mul_le_mul_left T hpow
    _ = (T * (2 * c + 1) ^ d) * L ^ d := by rw [mul_pow]; ac_rfl
    _ < L * L ^ d := hstrict
    _ = L ^ (d + 1) := by rw [pow_succ]; ac_rfl
    _ ≤ (2 * L + 1) ^ r := hexp

/-- A rank drop and linear coordinate bound produce a bounded relation at
the explicit radius in `rank_gap_count`. -/
theorem bounded_relation_of_rank_gap {d : ℕ}
    (points : Fin r → H) (basis : Fin d → H)
    (torsion : Finset H) (L K c : ℕ)
    (hdegree : d < r)
    (hcoord : K ≤ c * L)
    (hlarge : torsion.card * (2 * c + 1) ^ d < L)
    (hrep : ∀ coeff ∈ coefficientBox r L,
      ∃ τ ∈ torsion, ∃ a ∈ coefficientBox d K,
        (∑ i, coeff i • points i) = τ + ∑ j, a j • basis j) :
    ∃ coeff, Nontrivial coeff ∧ Bounded (2 * L) coeff ∧
      Relation points coeff := by
  exact bounded_relation_of_lattice_representation points basis torsion L K
    hrep (rank_gap_count torsion.card d r c K L hdegree hcoord hlarge)

end XedniHeightPigeonhole

#print axioms XedniHeightPigeonhole.coefficientBox_card
#print axioms XedniHeightPigeonhole.coefficientBox_bounded
#print axioms XedniHeightPigeonhole.bounded_relation_of_card_lt
#print axioms XedniHeightPigeonhole.bounded_witness_of_card_lt_on_dependence
#print axioms XedniHeightPigeonhole.bounded_relation_of_height_ball_count
#print axioms XedniHeightPigeonhole.latticeValues_card_le
#print axioms XedniHeightPigeonhole.bounded_relation_of_lattice_representation
#print axioms XedniHeightPigeonhole.rank_gap_count
#print axioms XedniHeightPigeonhole.bounded_relation_of_rank_gap
