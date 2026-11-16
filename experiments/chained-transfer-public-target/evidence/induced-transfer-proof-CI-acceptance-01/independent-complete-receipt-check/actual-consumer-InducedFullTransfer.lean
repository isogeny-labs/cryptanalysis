import Std.Tactic
import Init.Grind.Module.Basic
set_option autoImplicit false
set_option genInjectivity false

namespace InducedFullTransfer
open Lean.Grind

/-- A geometric quotient presentation with an arbitrary section. The section
is not assumed additive, integer-linear, equivariant or rational. -/
structure Presentation (A J : Type) [IntModule A] [IntModule J] where
  phi : A → J
  lift : J → A
  phi_add : ∀ a b, phi (a+b)=phi a+phi b
  phi_sub : ∀ a b, phi (a-b)=phi a-phi b
  phi_linear : ∀ z : Int, ∀ a, phi (z • a)=z • phi a
  phi_zero : phi 0=0
  lift_image : ∀ x, phi (lift x)=x

/-- Only source-map identities and transport of the full quotient kernel.
No identity concerning the induced transfer is stored in this structure. -/
structure CompatibleEdge {A J B K : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    (source : Presentation A J) (target : Presentation B K) where
  map : A → B
  map_add : ∀ a b, map (a+b)=map a+map b
  map_sub : ∀ a b, map (a-b)=map a-map b
  map_linear : ∀ z : Int, ∀ a, map (z • a)=z • map a
  map_zero : map 0=0
  kernel_transport : ∀ a, source.phi a=0 → target.phi (map a)=0

def transfer {A J B K : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    {source : Presentation A J} {target : Presentation B K}
    (edge : CompatibleEdge source target) (x : J) : K :=
  target.phi (edge.map (source.lift x))

/-- The existing equal-images kernel argument, specialized to targetPhi∘g. -/
theorem representative_independence {A J B K : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    (source : Presentation A J) (target : Presentation B K)
    (edge : CompatibleEdge source target) (a b : A)
    (same : source.phi a=source.phi b) :
    target.phi (edge.map a)=target.phi (edge.map b) := by
  have kernel : source.phi (a-b)=0 := by
    rw [source.phi_sub, same]
    grind
  have transported := edge.kernel_transport (a-b) kernel
  rw [edge.map_sub, target.phi_sub] at transported
  exact AddCommGroup.sub_eq_zero_iff.mp transported

/-- The commuting source identity is derived from the section and kernel
transport; it is not a hypothesis about the desired quotient map. -/
theorem induced_on_source {A J B K : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    (source : Presentation A J) (target : Presentation B K)
    (edge : CompatibleEdge source target) (a : A) :
    transfer edge (source.phi a)=target.phi (edge.map a) := by
  unfold transfer
  exact representative_independence source target edge
    (source.lift (source.phi a)) a (source.lift_image (source.phi a))

/-- An arbitrary nonlinear section still gives an additive induced map. -/
theorem induced_additive {A J B K : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    (source : Presentation A J) (target : Presentation B K)
    (edge : CompatibleEdge source target) (x y : J) :
    transfer edge (x+y)=transfer edge x+transfer edge y := by
  have same : source.phi (source.lift (x+y))=
      source.phi (source.lift x+source.lift y) := by
    rw [source.lift_image, source.phi_add, source.lift_image, source.lift_image]
  have image := representative_independence source target edge
    (source.lift (x+y)) (source.lift x+source.lift y) same
  rw [edge.map_add, target.phi_add] at image
  exact image

/-- Integer linearity supplies the DLP relation, without linear section. -/
theorem induced_integer_linear {A J B K : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    (source : Presentation A J) (target : Presentation B K)
    (edge : CompatibleEdge source target) (z : Int) (x : J) :
    transfer edge (z • x)=z • transfer edge x := by
  have same : source.phi (source.lift (z • x))=
      source.phi (z • source.lift x) := by
    rw [source.lift_image, source.phi_linear, source.lift_image]
  have image := representative_independence source target edge
    (source.lift (z • x)) (z • source.lift x) same
  rw [edge.map_linear, target.phi_linear] at image
  exact image

/-- Both individual quotient reverse norms are conclusions derived from
the two source elliptic dual identities and the two kernel conditions. -/
theorem induced_reverse_norms {A J B K : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    (source : Presentation A J) (target : Presentation B K)
    (forward : CompatibleEdge source target)
    (reverse : CompatibleEdge target source) (n : Int)
    (source_elliptic_dual : ∀ a, reverse.map (forward.map a)=n • a)
    (target_elliptic_dual : ∀ b, forward.map (reverse.map b)=n • b) :
    (∀ x, transfer reverse (transfer forward x)=n • x) ∧
      (∀ y, transfer forward (transfer reverse y)=n • y) := by
  constructor
  · intro x
    change transfer reverse (target.phi (forward.map (source.lift x)))=n • x
    rw [induced_on_source target source reverse, source_elliptic_dual,
      source.phi_linear, source.lift_image]
  · intro y
    change transfer forward (source.phi (reverse.map (target.lift y)))=n • y
    rw [induced_on_source source target forward, target_elliptic_dual,
      target.phi_linear, target.lift_image]

/-- A literal two-quotient chain collapses to one initial section, the
factored source maps and the final quotient. No commuting square is assumed. -/
theorem induced_chain_collapse {A J B K C L : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    [IntModule C] [IntModule L]
    (source : Presentation A J) (middle : Presentation B K)
    (target : Presentation C L)
    (first : CompatibleEdge source middle)
    (second : CompatibleEdge middle target) (x : J) :
    transfer second (transfer first x)=
      target.phi (second.map (first.map (source.lift x))) := by
  exact induced_on_source middle target second (first.map (source.lift x))

/-- Recovery assumes annihilation only for this input. The reverse norm
is derived inside the proof, not supplied as a desired transfer hypothesis. -/
theorem recover_on_annihilator {A J B K : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    (source : Presentation A J) (target : Presentation B K)
    (forward : CompatibleEdge source target)
    (reverse : CompatibleEdge target source) (n order inverse quotient : Int)
    (source_elliptic_dual : ∀ a, reverse.map (forward.map a)=n • a)
    (target_elliptic_dual : ∀ b, forward.map (reverse.map b)=n • b)
    (bezout : inverse*n+quotient*order=1)
    (x : J) (annihilated : order • x=0) :
    inverse • transfer reverse (transfer forward x)=x := by
  have norm := (induced_reverse_norms source target forward reverse n
    source_elliptic_dual target_elliptic_dual).1 x
  rw [norm]
  calc
    inverse • (n • x) = (inverse*n+quotient*order) • x := by
      rw [IntModule.add_zsmul, IntModule.mul_zsmul, IntModule.mul_zsmul,
        annihilated, IntModule.zsmul_zero]
      grind
    _ = x := by rw [bezout, IntModule.one_zsmul]

/-- Full-annihilator injectivity is a recovery consequence. No finite
annihilator is imposed on every point of the geometric group. -/
theorem injective_on_annihilator {A J B K : Type}
    [IntModule A] [IntModule J] [IntModule B] [IntModule K]
    (source : Presentation A J) (target : Presentation B K)
    (forward : CompatibleEdge source target)
    (reverse : CompatibleEdge target source) (n order inverse quotient : Int)
    (source_elliptic_dual : ∀ a, reverse.map (forward.map a)=n • a)
    (target_elliptic_dual : ∀ b, forward.map (reverse.map b)=n • b)
    (bezout : inverse*n+quotient*order=1)
    (x y : J) (annihilated_x : order • x=0) (annihilated_y : order • y=0)
    (same : transfer forward x=transfer forward y) : x=y := by
  have first := recover_on_annihilator source target forward reverse n order
    inverse quotient source_elliptic_dual target_elliptic_dual bezout x annihilated_x
  have second := recover_on_annihilator source target forward reverse n order
    inverse quotient source_elliptic_dual target_elliptic_dual bezout y annihilated_y
  have equal := congrArg (fun z : K => inverse • transfer reverse z) same
  rw [first, second] at equal
  exact equal

/-- Published original values, recertified by ordinary kernel reduction;
these are not a certificate of an actual field or Jacobian order. -/
theorem actual_original_witnesses :
    (3413013*13+(-4)*11092292 : Int)=1 ∧
    (9648325*169+(-147)*11092292 : Int)=1 ∧
    Nat.gcd 13 11092292=1 ∧ Nat.gcd 169 11092292=1 := by
  decide

end InducedFullTransfer
