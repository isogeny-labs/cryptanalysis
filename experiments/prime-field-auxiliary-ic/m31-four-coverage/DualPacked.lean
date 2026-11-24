import CanonicalLift

namespace M31DualPacked

open M31FiberLift M31CanonicalLift M31PairedCubic

def splitOrd (r : F31) : Option F31 × Option F31 :=
  let z := r^(2^29 : Nat)
  (if z^2 = r then some (lower z) else none,
   if z^2 ≠ r ∨ r = 0 then some (lower z) else none)

theorem split_exact (r : F31) : splitOrd r = (ordinate r, ordinate (-r)) := by
  have he : Even (2^29 : Nat) := ⟨2^28, by norm_num⟩
  obtain ⟨either, both⟩ := twist_split r
  have route : (r^(2^29 : Nat))^2 = -r ↔ (r^(2^29 : Nat))^2 ≠ r ∨ r = 0 := by
    constructor
    · intro h
      by_cases pos : (r^(2^29 : Nat))^2 = r
      · exact Or.inr (both.mp ⟨pos,h⟩)
      · exact Or.inl pos
    · rintro (h | zero)
      · exact either.resolve_left h
      · exact (both.mpr zero).2
  simp only [splitOrd, ordinate, he.neg_pow, route]

theorem paired_curve (a b x : F31) :
    splitOrd (rhs a b x) = (ordinate (rhs a b x), ordinate (rhs a (-b) (-x))) := by
  rw [split_exact]
  congr 2
  unfold rhs
  ring

/-- Filtering and sorting preserve the pointwise twist identity, including duplicates. -/
theorem sorted_twist {X Y : Type*} (neg : X → X) (xs : List X)
    (closed : (xs.map neg).Perm xs) (shared : X → Option Y × Option Y)
    (direct : X → Option Y) (encode : X → Y → Nat)
    (route : ∀ x, (shared x).2 = direct (neg x)) :
    (xs.filterMap (fun x => (shared x).2.map (encode (neg x)))).mergeSort =
      (xs.filterMap (fun x => (direct x).map (encode x))).mergeSort := by
  let k := fun x => (direct x).map (encode x)
  have point : (fun x => (shared x).2.map (encode (neg x))) = k ∘ neg := by
    funext x
    exact congrArg (Option.map (encode (neg x))) (route x)
  rw [point, ← List.filterMap_map]
  have perm := closed.filterMap k
  exact ((List.mergeSort_perm _ _).trans (perm.trans (List.mergeSort_perm _ _).symm)).eq_of_pairwise'
    (List.pairwise_mergeSort' (· ≤ ·) _) (List.pairwise_mergeSort' (· ≤ ·) _)

end M31DualPacked
