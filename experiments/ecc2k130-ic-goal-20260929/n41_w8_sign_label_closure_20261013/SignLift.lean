import Std

/-! Lifting a tree of point classes modulo negation through sign-closed leaves. -/
namespace SignLift

structure CommNegAdd (G : Type) where
  add : G → G → G
  neg : G → G
  neg_add : ∀ x y, neg (add x y) = add (neg x) (neg y)
  neg_neg : ∀ x, neg (neg x) = x

inductive Expr (G : Type) where
  | leaf (point : G)
  | node (left right : Expr G) (claimed : G)

variable {G : Type} (R : CommNegAdd G)

def anchor : Expr G → G
  | .leaf point => point
  | .node _ _ claimed => claimed

def classEq (x y : G) : Prop := x = y ∨ x = R.neg y

inductive Reachable : Expr G → G → Prop where
  | leaf_pos (point : G) : Reachable (.leaf point) point
  | leaf_neg (point : G) : Reachable (.leaf point) (R.neg point)
  | node {left right : Expr G} {claimed x y : G}
      (hl : Reachable left x) (hr : Reachable right y) :
      Reachable (.node left right claimed) (R.add x y)

def Compatible : Expr G → Prop
  | .leaf _ => True
  | .node left right claimed =>
      Compatible left ∧ Compatible right ∧
      (classEq R claimed (R.add (anchor left) (anchor right)) ∨
       classEq R claimed (R.add (anchor left) (R.neg (anchor right))))

theorem reachable_neg {expr : Expr G} {point : G}
    (h : Reachable R expr point) : Reachable R expr (R.neg point) := by
  induction h with
  | leaf_pos point => exact Reachable.leaf_neg point
  | leaf_neg point => simpa only [R.neg_neg] using (Reachable.leaf_pos point)
  | node hl hr ihl ihr =>
      rw [R.neg_add]
      exact Reachable.node ihl ihr

theorem anchor_reachable (expr : Expr G) (h : Compatible R expr) :
    Reachable R expr (anchor expr) := by
  induction expr with
  | leaf point => exact Reachable.leaf_pos point
  | node left right claimed ihl ihr =>
      rcases h with ⟨hleft, hright, hstep⟩
      have hl : Reachable R left (anchor left) := ihl hleft
      have hr : Reachable R right (anchor right) := ihr hright
      have hplus : Reachable R (.node left right claimed)
          (R.add (anchor left) (anchor right)) := Reachable.node hl hr
      have hminus : Reachable R (.node left right claimed)
          (R.add (anchor left) (R.neg (anchor right))) :=
        Reachable.node hl (reachable_neg R hr)
      change Reachable R (.node left right claimed) claimed
      rcases hstep with hsum | hdiff
      · rcases hsum with heq | heq
        · simpa only [heq] using hplus
        · simpa only [heq] using (reachable_neg R hplus)
      · rcases hdiff with heq | heq
        · simpa only [heq] using hminus
        · simpa only [heq] using (reachable_neg R hminus)

theorem target_reachable (expr : Expr G) (h : Compatible R expr)
    (target : G) (same_class : classEq R target (anchor expr)) :
    Reachable R expr target := by
  rcases same_class with heq | heq
  · rw [heq]; exact anchor_reachable R expr h
  · rw [heq]; exact reachable_neg R (anchor_reachable R expr h)

#print axioms target_reachable
end SignLift
