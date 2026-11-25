import ArchiveRoots
import ArchiveData
import FiberLift

namespace M31ArchiveAuxiliaryDomain
open M31FiberLift

abbrev I := Fin 32
def x (j : I) : F31 := M31ArchiveRoots.roots[j.val]!
private def ordinates : List Nat := [615668188, 1077420386, 1490088935, 1594985392, 1780860533, 2016418512, 365919857, 1720022756, 916671559, 1861824312, 2134968279, 2119781404, 1166339106, 1782926342, 1005101518, 779577064, 886029600, 954833449, 174624862, 913852932, 2068573131, 107554392, 226085110, 1322607477, 915622983, 620411215, 2068932458, 264286050, 391425997, 1230405636, 2095264276, 1485308939]
def y (j : I) : F31 := ordinates[j.val]!

def chord (j : I) : Prop :=
  let u := x j
  let v := y j
  let dx := u-1965083199
  let dy := v-1854403464
  v^2 = u^3+u ∧ dx ≠ 0 ∧
    dy^2 = (x (j+1)+u+1965083199)*dx^2 ∧
    (y (j+1)+v)*dx = dy*(u-x (j+1))

instance (j : I) : Decidable (chord j) := by unfold chord; infer_instance

theorem closed_orbit : x 0 = 3 ∧ y 0 = 615668188 ∧
    M31ArchiveRoots.roots.length = 32 ∧ M31ArchiveRoots.roots.Nodup ∧
    (1854403464 : F31)^2 = (1965083199 : F31)^3+1965083199 ∧
    ∀ j, chord j := by native_decide

def rhs (j : I) : F31 := (x j)^3 + 2*x j + 14
def mask : Nat := 399118247

private theorem bits : ∀ j : I, mask.testBit j.val =
    decide ((squares rhs 29 j)^2 = rhs j) := by native_decide

theorem mask_spec (j : I) : mask.testBit j.val = true ↔ ∃ z : F31, z^2 = rhs j := by
  rw [bits]
  simpa using lift_exact rhs j

def selected : List Nat := ((List.finRange 32).filter
  (fun j => mask.testBit j.val)).map (fun j => (x j).val)

theorem matches_basis : selected.mergeSort = M31ArchiveData.archived.map Prod.fst ∧
    selected.length = 17 ∧ ∀ pt ∈ M31ArchiveData.archived,
      pt.2 ≤ 1073741823 ∧ (pt.2 : F31)^2 = (pt.1 : F31)^3 + 2*pt.1 + 14 := by
  native_decide

end M31ArchiveAuxiliaryDomain
