import HeightPigeonhole
import XedniObstruction

/-!
The rank-gap witness theorem and finite-field selected-sample count compose
without assuming the desired bounded witness. The arithmetic representation
and reduction compatibility remain explicit hypotheses for each admitted
sample.
-/

namespace XedniRankSampleBridge

variable {r q : ℕ}

/-- Conditional selected-sample obstruction derived from a rank drop and
bounded lattice coordinates for every dependent admitted lift. `L` is fixed
before sampling and `2L < q`; the torsion list and basis may depend on the
admitted tuple, but each must satisfy the same explicit radius threshold. -/
theorem selected_rank_gap_sample_count {H : Type*} [AddCommGroup H]
    [Fact q.Prime] (red : H →+ ZMod q)
    (s : Fin r → ZMod q) (w : ZMod q)
    (admissible : Finset (Fin r → ZMod q))
    (lifts : (Fin r → ZMod q) → Fin r → H)
    (hcompat : ∀ t ∈ admissible, ∀ i,
      red (lifts t i) = XedniObstruction.xedniSampleMap s w t i)
    (L : ℕ) (hbound : 2 * L < q)
    (hgeometry : ∀ t ∈ admissible,
      (∃ coeff, XedniObstruction.Nontrivial coeff ∧
        XedniObstruction.Relation (lifts t) coeff) →
      ∃ d : ℕ, ∃ basis : Fin d → H, ∃ torsion : Finset H,
      ∃ K c : ℕ,
        d < r ∧ K ≤ c * L ∧
        torsion.card * (2 * c + 1) ^ d < L ∧
        (∀ coeff ∈ XedniHeightPigeonhole.coefficientBox r L,
          ∃ τ ∈ torsion,
          ∃ a ∈ XedniHeightPigeonhole.coefficientBox d K,
            (∑ i, coeff i • lifts t i) =
              τ + ∑ j, a j • basis j))
    (candidates : Finset (Fin r → ℤ))
    (hcover : ∀ coeff, XedniObstruction.Nontrivial coeff →
      XedniObstruction.Bounded (2 * L) coeff → coeff ∈ candidates)
    (hvalid : ∀ coeff ∈ candidates,
      XedniObstruction.Nontrivial coeff ∧
      XedniObstruction.Bounded (2 * L) coeff) :
    (XedniObstruction.selectedDependentLiftSamples admissible lifts).card *
      Nat.card (ZMod q) ≤
      candidates.card * Nat.card (Fin r → ZMod q) := by
  apply XedniObstruction.selected_dependent_lift_sample_count red s w
    admissible lifts hcompat (2 * L) hbound ?_ candidates hcover hvalid
  intro t ht hdep
  obtain ⟨d, basis, torsion, K, c, hd, hK, hlarge, hrep⟩ :=
    hgeometry t ht hdep
  obtain ⟨small, hnon, hsmall, hrel⟩ :=
    XedniHeightPigeonhole.bounded_relation_of_rank_gap
      (lifts t) basis torsion L K c hd hK hlarge hrep
  exact ⟨small,
    by simpa [XedniHeightPigeonhole.Nontrivial,
      XedniObstruction.Nontrivial] using hnon,
    by simpa [XedniHeightPigeonhole.Bounded,
      XedniObstruction.Bounded] using hsmall,
    by simpa [XedniHeightPigeonhole.Relation,
      XedniObstruction.Relation] using hrel⟩

end XedniRankSampleBridge

#print axioms XedniRankSampleBridge.selected_rank_gap_sample_count
