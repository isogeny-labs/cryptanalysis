import FiberOrbit
import PanelInitializer
import Mathlib.FieldTheory.IsAlgClosed.Basic

namespace M31PanelInitializer

open M31FiberRecurrence

private theorem trace_exists {K : Type*} [Field K] [IsAlgClosed K] [NeZero (2 : K)] (a : K) :
    ∃ z : K, z ≠ 0 ∧ tr z = a := by
  obtain ⟨s, hs⟩ := IsAlgClosed.exists_pow_nat_eq (a^2-4) (by decide : 0 < 2)
  let z := (a+s)/2
  have rel : z^2 - a*z + 1 = 0 := by
    dsimp [z]
    field_simp
    linear_combination hs
  have nz : z ≠ 0 := by intro h; simp [h] at rel
  refine ⟨z, nz, ?_⟩
  unfold tr
  field_simp
  linear_combination rel

private theorem map_generated {K : Type*} [Field K] (ι : M →+* K) (s a b : M)
    (i : Nat) : ι (generated s a b i) = generated (ι s) (ι a) (ι b) i := by
  induction i using Nat.twoStepInduction with
  | zero => rfl
  | one => rfl
  | more i ih jh => simp only [generated, map_sub, map_mul, ih, jh]

/-- All generated slots are distinct and account for every geometric root. -/
theorem panel_exact {K : Type*} [Field K] [IsAlgClosed K] [NeZero (2 : K)]
    (ι : M →+* K) (n : Nat) (row : n ∈ terminals) :
    let t := (n : M)
    let slots := fun j : Fin 128 => ι (generated (step t) (leaf t) (neighbor t) j.val)
    Function.Injective slots ∧
      ∀ x, (doublingPoly K 7).eval x = ι t ↔ ∃ j, slots j = x := by
  dsimp only
  let t : M := n
  obtain ⟨down, terminal, disc, second⟩ := panel_valid n row
  obtain ⟨z, hz, trace⟩ := trace_exists (ι (leaf t))
  have two : ι 2 = 2 := by change ι (2 : Nat) = (2 : Nat); exact map_natCast ι 2
  have four : ι 4 = 4 := by change ι (4 : Nat) = (4 : Nat); exact map_natCast ι 4
  have commute : Function.Semiconj ι forward M31TorusOrder.step := by
    intro x
    simp [forward, M31TorusOrder.step, two, sq]
  have travel (k : Nat) : tr (z^(2^k)) = ι (forward^[k] (leaf t)) := by
    calc
      _ = M31TorusOrder.step^[k] (tr z) := (M31TorusOrder.trace_iter hz k).symm
      _ = _ := by rw [trace, (commute.iterate_right k).eq]
  have endpt : tr (z^128) = ι t := (travel 7).trans (congrArg ι down)
  have stride : tr (z^16777216) = ι (step t) := travel 24
  have order : orderOf z = 2147483648 := by
    apply M31TorusOrder.order_from_trace hz 30
    change M31TorusOrder.step^[23+7] (tr z) = -2
    rw [Function.iterate_add_apply, trace, ← (commute.iterate_right 7).eq, down,
      ← (commute.iterate_right 23).eq, terminal, map_neg, two]
  have hd : (ι (squareRoot (delta t)))^2 = ((tr z)^2-4)*((tr (z^16777216))^2-4) := by
    rw [trace, stride, ← map_pow, disc]
    simp [delta, four, t]
  have hy : 2 * ι (neighbor t) = tr z * tr (z^16777216) + ι (squareRoot (delta t)) := by
    rw [trace, stride, ← two, ← map_mul, second, map_add, map_mul]
  have result := generated_exact hz order hd hy
  simp only [map_generated]
  simpa only [trace, stride, endpt] using result

end M31PanelInitializer
