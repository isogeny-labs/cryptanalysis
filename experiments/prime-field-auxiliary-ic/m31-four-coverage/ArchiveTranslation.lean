import ArchiveData
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.Algebra.Field.ZMod
import Mathlib.Data.Finset.Card
import Mathlib.Tactic

namespace M31ArchiveTranslation

abbrev F := ZMod 2147483647
private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

abbrev I := Fin 17
abbrev Choice := I × I × Bool

def x (i : I) : F := (M31ArchiveData.archived[i.val]!).1
def y (i : I) : F := (M31ArchiveData.archived[i.val]!).2

/-- Identify a pair up to exchange, and both ordinates up to simultaneous negation. -/
def domain : Finset Choice := Finset.univ.filter (fun c => c.1 < c.2.1)

def signed (flip : Bool) (v : F) := if flip then -v else v

def translationX (c : Choice) : F :=
  let i := c.1
  let j := c.2.1
  ((y i - signed c.2.2 (y j)) / (x i - x j))^2 - x i - x j

theorem distinct_inputs : ∀ i j : I, i < j → x i ≠ x j := by native_decide

theorem census : domain.card = 272 ∧ (domain.image translationX).card = 272 := by
  native_decide

theorem separates : Set.InjOn translationX domain :=
  Finset.card_image_iff.mp (census.2.trans census.1.symm)

/-- Arbitrary orientations of the two points reduce to their relative sign. -/
theorem orientation (i j : I) (a b : Bool) :
    ((signed a (y i) - signed b (y j)) / (x i - x j))^2 - x i - x j =
      translationX (i,j,xor a b) := by
  cases a <;> cases b <;> simp [signed, translationX, div_pow] <;> ring

end M31ArchiveTranslation
