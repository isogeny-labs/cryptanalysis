import Std

/-! Exact labeled four-pair tuple count before column and chart filtering. -/
namespace FourPairSupport

universe u v

private theorem flatMap_length_const {A : Type u} {B : Type v}
    (xs : List A) (f : A → List B) (n : Nat)
    (hlen : ∀ a, (f a).length = n) :
    (xs.flatMap f).length = xs.length * n := by
  induction xs with
  | nil => simp
  | cons a rest ih =>
      simp only [List.flatMap_cons, List.length_append, hlen a,
        List.length_cons, ih, Nat.succ_mul]
      omega

def fourTuples {S : Type u} (states : List S) : List (S × S × S × S) :=
  states.flatMap fun a =>
    states.flatMap fun b =>
      states.flatMap fun c =>
        states.map fun d => (a,b,c,d)

theorem fourTuples_length {S : Type u} (states : List S) :
    (fourTuples states).length =
      states.length * (states.length * (states.length * states.length)) := by
  unfold fourTuples
  have hinner (a b : S) :
      (states.flatMap fun c => states.map fun d => (a,b,c,d)).length =
        states.length * states.length := by
    apply flatMap_length_const
    intro c
    simp
  have hmiddle (a : S) :
      (states.flatMap fun b =>
        states.flatMap fun c => states.map fun d => (a,b,c,d)).length =
        states.length * (states.length * states.length) := by
    apply flatMap_length_const
    intro b
    exact hinner a b
  rw [flatMap_length_const states _
    (states.length * (states.length * states.length)) hmiddle]

theorem filtered_fourTuples_bound {S : Type u}
    (states : List S) (valid : S × S × S × S → Bool) :
    ((fourTuples states).filter valid).length ≤
      states.length * (states.length * (states.length * states.length)) := by
  rw [← fourTuples_length]
  exact List.length_filter_le _ _

#print axioms FourPairSupport.fourTuples_length
#print axioms FourPairSupport.filtered_fourTuples_bound

end FourPairSupport
