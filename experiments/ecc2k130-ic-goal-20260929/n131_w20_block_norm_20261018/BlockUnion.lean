import Std

/-! Exact union of finite source blocks under a zero-detecting block norm. -/
namespace BlockUnion

variable {Q K : Type}

theorem zero_iff_some_block_zero
    (source : List Q) (blocks : List (List Q)) (f : Q → K) (zero : K)
    (normZero : List Q → Prop)
    (cover : ∀ q, q ∈ source ↔ ∃ block ∈ blocks, q ∈ block)
    (normCorrect : ∀ block ∈ blocks,
      normZero block ↔ ∃ q ∈ block, f q = zero) :
    (∃ q ∈ source, f q = zero) ↔
      ∃ block ∈ blocks, normZero block := by
  constructor
  · rintro ⟨q, hq, hz⟩
    obtain ⟨block, hb, hqb⟩ := (cover q).mp hq
    exact ⟨block, hb, (normCorrect block hb).mpr ⟨q, hqb, hz⟩⟩
  · rintro ⟨block, hb, hn⟩
    obtain ⟨q, hqb, hz⟩ := (normCorrect block hb).mp hn
    exact ⟨q, (cover q).mpr ⟨block, hb, hqb⟩, hz⟩

#print axioms BlockUnion.zero_iff_some_block_zero
end BlockUnion
