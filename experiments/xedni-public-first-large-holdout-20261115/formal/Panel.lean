import FamilyCount

namespace XedniPublicFirstLargeHoldout

set_option maxRecDepth 4096

/-- The frozen selected coefficient vectors, in their experiment order. -/
def selected (F : Type*) [Ring F] : Fin 13 → F × F :=
  ![(1, -6), (2, -1), (6, 5), (5, 4), (6, 1), (5, 3), (4, -5),
    (6, -1), (5, -1), (6, -5), (1, 5), (4, -1), (4, 1)]

def PanelPremises (q : ℕ) [NeZero q] : Prop :=
  (∀ i, (selected (ZMod q) i).1 ≠ 0) ∧
  (∀ i, (selected (ZMod q) i).2 ≠ 0) ∧
  (∀ i, (selected (ZMod q) i).1 + (selected (ZMod q) i).2 ≠ 0) ∧
  (∀ i j, i ≠ j →
    (selected (ZMod q) i).1 * (selected (ZMod q) j).2 -
    (selected (ZMod q) i).2 * (selected (ZMod q) j).1 ≠ 0)

theorem panel293 : PanelPremises 293 := by
  unfold PanelPremises
  decide
theorem panel313 : PanelPremises 313 := by
  unfold PanelPremises
  decide
theorem panel331 : PanelPremises 331 := by
  unfold PanelPremises
  decide
theorem panel353 : PanelPremises 353 := by
  unfold PanelPremises
  decide
theorem panel419 : PanelPremises 419 := by
  unfold PanelPremises
  decide
theorem panel439 : PanelPremises 439 := by
  unfold PanelPremises
  decide
theorem panel571 : PanelPremises 571 := by
  unfold PanelPremises
  decide
theorem panel599 : PanelPremises 599 := by
  unfold PanelPremises
  decide

instance prime293 : Fact (Nat.Prime 293) := ⟨by decide⟩
instance prime313 : Fact (Nat.Prime 313) := ⟨by decide⟩
instance prime331 : Fact (Nat.Prime 331) := ⟨by decide⟩
instance prime353 : Fact (Nat.Prime 353) := ⟨by decide⟩
instance prime419 : Fact (Nat.Prime 419) := ⟨by decide⟩
instance prime439 : Fact (Nat.Prime 439) := ⟨by decide⟩
instance prime571 : Fact (Nat.Prime 571) := ⟨by decide⟩
instance prime599 : Fact (Nat.Prime 599) := ⟨by decide⟩

/-- The checked panel premises instantiate the general distinct-pair theorem. -/
theorem panel_card (q : ℕ) [Fact (Nat.Prime q)]
    (h : PanelPremises q) (w : ZMod q) :
    Fintype.card (FamilyHitPair (selected (ZMod q)) w) = 13 * (q - 1) := by
  rcases h with ⟨ha, hb, hs, hd⟩
  simpa using family_hit_pair_count (selected (ZMod q)) w ha hb hs hd

theorem count293 (w : ZMod 293) :
    Fintype.card (FamilyHitPair (selected (ZMod 293)) w) = 13 * (293 - 1) := by
  exact panel_card 293 panel293 w

theorem count313 (w : ZMod 313) :
    Fintype.card (FamilyHitPair (selected (ZMod 313)) w) = 13 * (313 - 1) := by
  exact panel_card 313 panel313 w

theorem count331 (w : ZMod 331) :
    Fintype.card (FamilyHitPair (selected (ZMod 331)) w) = 13 * (331 - 1) := by
  exact panel_card 331 panel331 w

theorem count353 (w : ZMod 353) :
    Fintype.card (FamilyHitPair (selected (ZMod 353)) w) = 13 * (353 - 1) := by
  exact panel_card 353 panel353 w

theorem count419 (w : ZMod 419) :
    Fintype.card (FamilyHitPair (selected (ZMod 419)) w) = 13 * (419 - 1) := by
  exact panel_card 419 panel419 w

theorem count439 (w : ZMod 439) :
    Fintype.card (FamilyHitPair (selected (ZMod 439)) w) = 13 * (439 - 1) := by
  exact panel_card 439 panel439 w

theorem count571 (w : ZMod 571) :
    Fintype.card (FamilyHitPair (selected (ZMod 571)) w) = 13 * (571 - 1) := by
  exact panel_card 571 panel571 w

theorem count599 (w : ZMod 599) :
    Fintype.card (FamilyHitPair (selected (ZMod 599)) w) = 13 * (599 - 1) := by
  exact panel_card 599 panel599 w

#print axioms panel293
#print axioms panel313
#print axioms panel331
#print axioms panel353
#print axioms panel419
#print axioms panel439
#print axioms panel571
#print axioms panel599
#print axioms panel_card
#print axioms count293
#print axioms count313
#print axioms count331
#print axioms count353
#print axioms count419
#print axioms count439
#print axioms count571
#print axioms count599

end XedniPublicFirstLargeHoldout
