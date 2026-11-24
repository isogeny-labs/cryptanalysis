import FiberLift
import Mathlib.Data.List.FinRange
import Mathlib.Data.List.Chain

namespace M31PrefixWidth

abbrev F := ZMod 2147483647
abbrev Prefix := Fin 32768
abbrev Suffix := Fin 31

def coordinate (h : Prefix) (s : Suffix) : Nat := h.val * 65536 + s.val
def rhs (h : Prefix) (s : Suffix) : F :=
  let x : F := coordinate h s
  x^3 + 2*x + 14

def label (h : Prefix) (s : Suffix) : Bool :=
  let a := rhs h s
  decide ((M31FiberLift.squares (fun _ : Unit => a) 29 ())^2 = a)

theorem label_exact (h : Prefix) (s : Suffix) :
    label h s = true ↔ ∃ y : F, y^2 = rhs h s := by
  simpa [label] using M31FiberLift.lift_exact (fun _ : Unit => rhs h s) ()

def signature (row : Suffix → Bool) :=
  let phase := row 0
  (List.ofFn (fun s => row s ^^ phase)).foldl (fun (a : Nat) b => 2*a + b.toNat) 0

theorem signature_phase (phase : Bool) (row : Suffix → Bool) :
    signature (fun s => phase ^^ row s) = signature row := by
  have h (s : Suffix) : ((phase ^^ row s) ^^ (phase ^^ row 0)) = (row s ^^ row 0) := by
    cases phase <;> cases row s <;> cases row 0 <;> rfl
  simp only [signature, h]

def signatures := List.ofFn fun h : Prefix => signature (label h)

-- Native evaluation sorts and checks adjacent signatures, avoiding a quadratic
-- comparison over all prefix pairs. The remaining reasoning is symbolic.
theorem ordered : signatures.mergeSort.IsChain (· < ·) := by native_decide

theorem prefix_injective : Function.Injective (fun h : Prefix => signature (label h)) := by
  apply List.nodup_ofFn.mp
  have h := List.isChain_iff_pairwise.mp ordered
  exact (List.mergeSort_perm signatures _).nodup_iff.mp (h.imp (fun lt => ne_of_lt lt))

theorem width {State : Type*} [Fintype State] (readPrefix : Prefix → State)
    (finish : State → Suffix → Bool) (phase : Prefix → Bool)
    (exactLabel : ∀ h s, (phase h ^^ finish (readPrefix h) s) = label h s) :
    32768 ≤ Fintype.card State := by
  have inj : Function.Injective readPrefix := by
    intro a b eq
    apply prefix_injective
    have key (h : Prefix) : signature (label h) = signature (finish (readPrefix h)) := by
      rw [show label h = (fun s => phase h ^^ finish (readPrefix h) s) from
        funext (fun s => (exactLabel h s).symm)]
      exact signature_phase _ _
    exact (key a).trans ((congrArg (fun t => signature (finish t)) eq).trans (key b).symm)
  simpa using Fintype.card_le_of_injective readPrefix inj

end M31PrefixWidth
