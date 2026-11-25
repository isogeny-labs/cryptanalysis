import Std

namespace M31SparseWindow

variable {Key Slot : Type} [DecidableEq Slot]

-- A write changes exactly one address. None represents the reserved empty word.
def write (table : Slot → Option Key) (slot : Slot) (value : Option Key) :=
  fun i => if i = slot then value else table i

def build (addr : Key → Slot) (keys : List Key) (table : Slot → Option Key) :=
  keys.foldl (fun t k => write t (addr k) (some k)) table

def clear (addr : Key → Slot) (keys : List Key) (table : Slot → Option Key) :=
  keys.foldl (fun t k => write t (addr k) none) table

theorem clear_at (addr : Key → Slot) (keys : List Key) (table : Slot → Option Key) (i : Slot) :
    clear addr keys table i = if i ∈ keys.map addr then none else table i := by
  induction keys generalizing table with
  | nil => simp [clear]
  | cons k ks ih =>
    simp only [clear, List.foldl_cons, List.map_cons, List.mem_cons]
    rw [← clear, ih]
    by_cases h : i ∈ ks.map addr <;> simp [h, write]

theorem untouched (addr : Key → Slot) (keys : List Key) (table : Slot → Option Key) (i : Slot)
    (h : i ∉ keys.map addr) : build addr keys table i = table i := by
  induction keys generalizing table with
  | nil => rfl
  | cons k ks ih =>
    simp only [List.map_cons, List.mem_cons, not_or] at h
    exact (ih _ h.2).trans (ite_eq_right h.1)

theorem reset (addr : Key → Slot) (keys : List Key) :
    clear addr keys (build addr keys (fun _ => none)) = fun _ => none := by
  funext i
  rw [clear_at]
  split
  · rfl
  · exact untouched _ _ _ _ ‹_›

theorem stored (addr : Key → Slot) (keys : List Key) (table : Slot → Option Key)
    (unique : (keys.map addr).Nodup) (k : Key) (hk : k ∈ keys) :
    build addr keys table (addr k) = some k := by
  induction keys generalizing table with
  | nil => simp at hk
  | cons x xs ih =>
    simp only [List.map_cons, List.nodup_cons] at unique
    rcases List.mem_cons.mp hk with rfl | ht
    · exact (untouched addr xs _ _ unique.1).trans (ite_eq_left rfl)
    · exact ih _ unique.2 ht

theorem origin (addr : Key → Slot) (keys : List Key) (table : Slot → Option Key)
    (i : Slot) (x : Key) (h : build addr keys table i = some x) :
    x ∈ keys ∨ table i = some x := by
  induction keys generalizing table with
  | nil => exact Or.inr h
  | cons k ks ih =>
    rcases ih _ h with ht | hw
    · exact Or.inl (List.mem_cons_of_mem _ ht)
    · simp only [write] at hw
      split at hw
      · cases hw
        exact Or.inl List.mem_cons_self
      · exact Or.inr hw

theorem lookup_exact (addr : Key → Slot) (keys : List Key) (unique : (keys.map addr).Nodup)
    (x : Key) : build addr keys (fun _ => none) (addr x) = some x ↔ x ∈ keys := by
  constructor
  · intro h
    exact (origin _ _ _ _ _ h).resolve_right (by simp)
  · exact stored _ _ _ unique _

-- A build passes the collision test precisely when every overwrite saw an empty slot.
def passes (addr : Key → Slot) : List Key → (Slot → Option Key) → Prop
  | [], _ => True
  | k :: ks, t => t (addr k) = none ∧ passes addr ks (write t (addr k) (some k))

theorem passes_iff (addr : Key → Slot) (keys : List Key) (t : Slot → Option Key) :
    passes addr keys t ↔ (keys.map addr).Nodup ∧ ∀ k ∈ keys, t (addr k) = none := by
  induction keys generalizing t with
  | nil => simp [passes]
  | cons k ks ih =>
    simp only [passes, ih, List.map_cons, List.nodup_cons]
    constructor
    · rintro ⟨empty, distinct, rest⟩
      have apart : ∀ j ∈ ks, addr j ≠ addr k := by
        intro j hj eq
        simpa [write, eq] using rest j hj
      refine ⟨⟨?_, distinct⟩, ?_⟩
      · intro h
        obtain ⟨j, hj, eq⟩ := List.mem_map.mp h
        exact apart j hj eq
      · intro j hj
        rcases List.mem_cons.mp hj with rfl | ht
        · exact empty
        · simpa [write, apart j ht] using rest j ht
    · rintro ⟨⟨fresh, distinct⟩, empty⟩
      refine ⟨empty _ List.mem_cons_self, distinct, ?_⟩
      intro j hj
      have apart : addr j ≠ addr k := fun eq => fresh (List.mem_map.mpr ⟨j, hj, eq⟩)
      simpa [write, apart] using empty j (List.mem_cons_of_mem k hj)

theorem with_fallback (addr : Key → Slot) (keys : List Key) (x : Key)
    [Decidable (passes addr keys (fun _ => none))] :
    (if _ : passes addr keys (fun _ => none) then
      build addr keys (fun _ => none) (addr x) = some x else x ∈ keys) ↔ x ∈ keys := by
  classical
  split
  · exact lookup_exact _ _ ((passes_iff _ _ _).mp ‹_›).1 _
  · rfl

end M31SparseWindow
