import Mathlib.Data.Sym.Card
import Mathlib.Algebra.BigOperators.Group.Multiset.Basic
import Mathlib.Data.Fintype.Prod
import Mathlib.Data.Fintype.Card
/-! Upper bound for the number of distinct sums of three signed entries from a list of
500 representatives. Repetitions are allowed. The group and the representatives are arbitrary. -/

set_option maxRecDepth 16000
namespace CountSigned
abbrev Label (k : ℕ) := Fin k × Bool
def tri {k : ℕ} (v : Fin k × Label k) : Multiset (Label k) :=
  (v.1, true) ::ₘ (v.1, false) ::ₘ {v.2}

theorem inj {k : ℕ} : Function.Injective (@tri k) := by
  rintro ⟨i,r⟩ ⟨j,s⟩ h
  have e : i = j := by
    by_contra hij
    have hp : (i,true) ∈ tri (j,s) := h ▸ (by simp [tri] : (i,true) ∈ tri (i,r))
    have hm : (i,false) ∈ tri (j,s) := h ▸ (by simp [tri] : (i,false) ∈ tri (i,r))
    simp [tri,hij] at hp hm
    exact Bool.noConfusion (congrArg Prod.snd (hp.trans hm.symm))
  subst j
  simpa [tri] using h

example : (Finset.univ.image (@tri 500)).card = 500000 := by
  rw [Finset.card_image_of_injective _ inj, Finset.card_univ]
  simp [Label, Fintype.card_prod]
abbrev L := Label 500
abbrev T := Sym L 3
def triple (v : Fin 500 × L) : T := ⟨tri v, by simp [tri]⟩

theorem capacity {G : Type*} [AddCommGroup G] [DecidableEq G] (v : Fin 500 → G) :
    let val : L → G := fun (i,b) => if b then v i else -(v i)
    let ev : T → G := fun t => (t.val.map val).sum
    (Finset.univ.image ev).card ≤ 166668000 := by
  classical
  dsimp only
  let val : L → G := fun (i,b) => if b then v i else -(v i)
  let ev : T → G := fun t => (t.val.map val).sum
  change (Finset.univ.image ev).card ≤ _
  let c := Finset.univ.image triple
  have hc : c.card = 500000 := by
    have it : Function.Injective triple := fun a b e => inj (congrArg Subtype.val e)
    simp [c, Finset.card_image_of_injective _ it, L, Label, Fintype.card_prod]
  have he : (c.image ev).card ≤ 1000 := by
    have sub : c.image ev ⊆ Finset.univ.image val := by
      intro x hx
      obtain ⟨t,ht,et⟩ := Finset.mem_image.mp hx
      rw [← et]
      obtain ⟨u,_,eu⟩ := Finset.mem_image.mp ht
      rw [← eu]
      exact Finset.mem_image.mpr ⟨u.2, Finset.mem_univ _, by simp [ev,triple,tri,val]⟩
    calc
      _ ≤ _ := Finset.card_le_card sub
      _ ≤ (Finset.univ : Finset L).card := Finset.card_image_le
      _ = _ := by simp [L, Label, Fintype.card_prod]
  have ht : (Finset.univ : Finset T).card = 167167000 := by
    rw [Finset.card_univ, Sym.card_sym_eq_choose]
    simp only [L, Label, Fintype.card_prod, Fintype.card_fin, Fintype.card_bool]
    rw [Nat.choose_eq_descFactorial_div_factorial]
    decide
  have hu := Finset.sdiff_union_of_subset (Finset.subset_univ c)
  calc
    _ = (((Finset.univ \ c).image ev) ∪ c.image ev).card := by rw [← Finset.image_union, hu]
    _ ≤ _ := Finset.card_union_le _ _
    _ ≤ (Finset.univ \ c).card + 1000 := Nat.add_le_add Finset.card_image_le he
    _ = _ := by rw [Finset.card_sdiff_of_subset (Finset.subset_univ c), ht, hc]
end CountSigned
