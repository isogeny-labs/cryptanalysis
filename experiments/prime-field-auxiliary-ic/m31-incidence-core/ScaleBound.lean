import Mathlib

namespace ArchivedScale

abbrev bound : ℕ := 8388608
abbrev modulus : ℕ := 2147505293

/-- First five distinct nonzero centered magnitudes in archive order, auxiliary then plain. -/
def witnesses : List (List ℕ) := [[918521277, 150976700, 938940779, 93623696, 413302589], [908140804, 1054377987, 288649646, 994121923, 207391523], [756661381, 880410899, 215996138, 75853188, 973159540], [440624821, 351356337, 1, 70732535, 592728324], [851364803, 303084331, 943305603, 158374722, 500550159], [774975565, 254661741, 525950555, 1064746870, 238127105]]

def excluded (c w : ℕ) : Bool := decide <|
  bound < (c*w)%modulus ∧ (c*w)%modulus < modulus-bound

private theorem chunks : ∀ b : Fin 2048, ∀ i : Fin 4096,
    witnesses.all (fun ws => ws.any (excluded (b.val*4096+i.val+1))) = true := by
  native_decide

/-- A positive scale compatible with the final coordinate always violates the
centered magnitude bound on at least one selected coordinate of every case. -/
theorem excludesPositiveScale {c : ℕ} (hp : 0 < c) (hb : c ≤ bound)
    {ws : List ℕ} (hw : ws ∈ witnesses) :
    ∃ w ∈ ws, excluded c w = true := by
  have hq : (c-1)/4096 < 2048 := by unfold bound at hb; omega
  have hr : (c-1)%4096 < 4096 := Nat.mod_lt _ (by decide)
  have h := chunks ⟨_,hq⟩ ⟨_,hr⟩
  have he : (c-1)/4096*4096+(c-1)%4096+1 = c := by omega
  simp only [he] at h
  exact List.any_eq_true.mp (List.all_eq_true.mp h _ hw)

end ArchivedScale
