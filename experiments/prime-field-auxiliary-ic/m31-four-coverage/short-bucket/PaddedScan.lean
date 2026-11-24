import Mathlib.Tactic

namespace PaddedScan

/-- The scan performs a first load even for an empty bucket. -/
def loads (lo hi : Nat) := max 1 ((hi-lo+3)/4)

theorem last_load (lo hi : Nat) (doneHere : hi-lo ≤ 4) : loads lo hi = 1 := by
  unfold loads
  omega

theorem next_load (lo hi : Nat) (more : 4 < hi-lo) :
    loads lo hi = 1 + loads (lo+4) hi := by
  unfold loads
  omega

def address (lo block lane : Nat) := lo+4*block+lane

theorem within_allocation (lo hi n block lane : Nat) (ordered : lo ≤ hi)
    (endpoint : hi ≤ n) (hb : block < loads lo hi) (hk : lane < 4) :
    address lo block lane < n+4 := by
  unfold address loads at *
  omega

theorem covers (lo hi j : Nat) (hj : lo ≤ j ∧ j < hi) :
    ∃ block < loads lo hi, ∃ lane < 4, address lo block lane = j := by
  refine ⟨(j-lo)/4, ?_, (j-lo)%4, Nat.mod_lt _ (by decide), ?_⟩
  · unfold loads
    omega
  · unfold address
    omega

/-- Offset construction brackets all real keys having the query prefix.
The four trailing words are filled with UINT32_MAX. -/
theorem exact (keys : Nat → Nat) (x lo hi n : Nat) (canonical : x < 2^31)
    (ordered : lo ≤ hi) (endpoint : hi ≤ n)
    (offsets : ∀ j < n, keys j / 65536 = x / 65536 → lo ≤ j ∧ j < hi)
    (padding : ∀ j, n ≤ j → j < n+4 → keys j = 4294967295) :
    (∃ b < loads lo hi, ∃ k < 4, keys (address lo b k) = x) ↔
      ∃ j < n, keys j = x := by
  constructor
  · rintro ⟨b,hb,k,hk,hit⟩
    let j := address lo b k
    have bounded : j < n+4 := within_allocation lo hi n b k ordered endpoint hb hk
    by_cases real : j < n
    · exact ⟨j,real,hit⟩
    · have pad := padding j (by omega) bounded
      change keys j = x at hit
      omega
  · rintro ⟨j,hj,eq⟩
    obtain ⟨b,hb,k,hk,idx⟩ := covers lo hi j (offsets j hj (by rw [eq]))
    exact ⟨b,hb,k,hk,idx ▸ eq⟩

end PaddedScan
