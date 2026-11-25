import Mathlib.Tactic
import ArchiveData

namespace M31ArchiveHash
open M31ArchiveData

def offsets : Vector Nat 8 := #v[0,1,7,5,2,3,6,16]
def slot (x : Nat) : Fin 17 :=
  ⟨(x / 128 + offsets[x % 8]) % 17, Nat.mod_lt _ (by decide)⟩

def keys : Vector Nat 17 := #v[1900239952,975624154,985108144,1685732321,
  1896314920,3,1171458932,98625645,2084456163,308768278,1393679185,
  1900319349,536276641,1213058799,753804470,1760557235,1908835095]

theorem occupied : ∀ i : Fin 17, keys[i] ∈ archived.map Prod.fst ∧
    slot keys[i] = i := by decide +kernel

theorem stored : ∀ x ∈ archived.map Prod.fst, keys[slot x] = x := by decide +kernel

-- Reading the full key makes the decision exact even outside the training set.
theorem lookup_exact (x : Nat) : keys[slot x] = x ↔ x ∈ archived.map Prod.fst := by
  constructor
  · intro h
    exact h ▸ (occupied (slot x)).1
  · exact stored x

-- No injective indexing of these distinct keys uses fewer slots.
theorem minimum_slots {n : Nat} (index : Nat → Fin n)
    (inj : Set.InjOn index (↑(archived.map Prod.fst).toFinset : Set Nat)) : 17 ≤ n := by
  have size : (archived.map Prod.fst).toFinset.card = 17 := by decide +kernel
  rw [← size, ← Finset.card_image_of_injOn inj]
  simpa using (Finset.card_le_univ ((archived.map Prod.fst).toFinset.image index))

def slice (x : Nat) : Fin 64 := ⟨(x / 1024) % 64, Nat.mod_lt _ (by decide)⟩
def sliced (i : Fin 64) : Nat :=
  ((archived.map Prod.fst).find? (fun x => slice x == i)).getD 2147483647

private theorem slice_entries : ∀ i : Fin 64, sliced i = 2147483647 ∨
    sliced i ∈ archived.map Prod.fst := by decide +kernel

theorem slice_exact (x : Nat) (hx : x < 2147483647) :
    sliced (slice x) = x ↔ x ∈ archived.map Prod.fst := by
  constructor
  · intro eq
    rcases slice_entries (slice x) with empty | key
    · omega
    · exact eq ▸ key
  · exact (show ∀ a ∈ archived.map Prod.fst, sliced (slice a) = a by decide +kernel) x

end M31ArchiveHash
