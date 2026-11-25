import Mathlib.Data.Finset.Basic

namespace M31Filter

def passes {K B : Type*} (index : K → B) (keys : Finset K) (query : K) : Prop :=
  ∃ key ∈ keys, index key = index query

theorem passes_of_mem {K B : Type*} (index : K → B) (keys : Finset K)
    {query : K} (h : query ∈ keys) : passes index keys query :=
  ⟨query, h, rfl⟩

theorem coarsen {K B C : Type*} (fine : K → B) (forget : B → C)
    (keys : Finset K) (query : K) (h : passes fine keys query) :
    passes (fun k => forget (fine k)) keys query := by
  obtain ⟨key, hk, heq⟩ := h
  exact ⟨key, hk, congrArg forget heq⟩

theorem passes_mod_of_dvd {small large : Nat} (h : small ∣ large)
    (keys : Finset Nat) (query : Nat)
    (hp : passes (fun k => k % large) keys query) :
    passes (fun k => k % small) keys query := by
  have hc := coarsen (fun k : Nat => k % large) (fun r => r % small) keys query hp
  simpa only [Nat.mod_mod_of_dvd _ h] using hc

end M31Filter
