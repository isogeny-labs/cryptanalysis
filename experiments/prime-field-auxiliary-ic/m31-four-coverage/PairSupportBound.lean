import Mathlib.Tactic

namespace M31PairSupportBound

variable {G : Type*} [AddCommGroup G] {n : Nat}

def signed (s : Bool) (x : G) := if s then -x else x

-- The upper triangle stores sums (including doubles); the lower stores differences.
def decode (b : Fin n → G) (code : Fin n × Fin n × Bool) : G :=
  let (i,j,s) := code
  signed s (if i ≤ j then b i + b j else b i - b j)

def represented (b : Fin n → G) (x : G) : Prop :=
  ∃ i j s t, x = signed s (b i) + signed t (b j)

theorem encodes (b : Fin n → G) {x : G} (hx : x ≠ 0) (h : represented b x) :
    ∃ c, decode b c = x := by
  obtain ⟨i,j,s,t,rfl⟩ := h
  rcases lt_trichotomy i j with hij | rfl | hji
  · cases s <;> cases t
    · exact ⟨(i,j,false), by simp [decode, signed, hij.le]⟩
    · exact ⟨(j,i,true), by simp [decode, signed, not_le.mpr hij]; abel⟩
    · exact ⟨(j,i,false), by simp [decode, signed, not_le.mpr hij]; abel⟩
    · exact ⟨(i,j,true), by simp [decode, signed, hij.le]; abel⟩
  · cases s <;> cases t
    · exact ⟨(i,i,false), by simp [decode, signed]⟩
    · simp [signed] at hx
    · simp [signed] at hx
    · exact ⟨(i,i,true), by simp [decode, signed]⟩
  · cases s <;> cases t
    · exact ⟨(j,i,false), by simp [decode, signed, hji.le]; abel⟩
    · exact ⟨(i,j,false), by simp [decode, signed, not_le.mpr hji]; abel⟩
    · exact ⟨(i,j,true), by simp [decode, signed, not_le.mpr hji]; abel⟩
    · exact ⟨(j,i,true), by simp [decode, signed, hji.le]⟩

theorem bound (b : Fin n → G) (points : Finset G)
    (h : ∀ x ∈ points, x ≠ 0 ∧ represented b x) : points.card ≤ 2*n^2 := by
  classical
  have sub : points ⊆ Finset.univ.image (decode b) := by
    intro x hx
    obtain ⟨nz,rep⟩ := h x hx
    obtain ⟨c,rfl⟩ := encodes b nz rep
    exact Finset.mem_image_of_mem _ (Finset.mem_univ c)
  calc
    points.card ≤ _ := Finset.card_le_card sub
    _ ≤ _ := Finset.card_image_le
    _ = 2*n^2 := by simp [pow_two]; ring

theorem seventeen (b : Fin 17 → G) (points : Finset G)
    (h : ∀ x ∈ points, x ≠ 0 ∧ represented b x) : points.card ≤ 578 :=
  bound b points h

end M31PairSupportBound
