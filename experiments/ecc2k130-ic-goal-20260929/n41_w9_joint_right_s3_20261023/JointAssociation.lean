import Std

/-! A second five-point association yields a necessary S3 target link
whenever its reciprocal coordinates are defined. -/
namespace JointAssociation

variable {Point Coord : Type}
variable (add : Point → Point → Point)
variable (coord : Point → Option Coord)
variable (s3 : Coord → Coord → Coord → Prop)

theorem regroup_five
    (a b c d e : Point)
    (assoc : ∀ x y z : Point, add (add x y) z = add x (add y z)) :
    add (add (add (add a b) c) d) e =
      add (add (add a b) c) (add d e) := by
  exact assoc (add (add a b) c) d e

theorem joint_target_link_full
    (left d e target : Point) (z u v y t : Coord)
    (assoc : ∀ x y q : Point, add (add x y) q = add x (add y q))
    (chart : ∀ x y q : Point, ∀ ax ay aq : Coord,
      add x y = q → coord x = some ax → coord y = some ay →
      coord q = some aq → s3 ax ay aq)
    (hleft : coord left = some z)
    (hd : coord d = some u)
    (he : coord e = some v)
    (hright : coord (add d e) = some y)
    (htarget : coord target = some t)
    (hsum : add (add left d) e = target) :
    s3 u v y ∧ s3 z y t := by
  have hrightlink : s3 u v y :=
    chart d e (add d e) u v y rfl hd he hright
  have hgroup : add left (add d e) = target := by
    calc
      add left (add d e) = add (add left d) e := (assoc left d e).symm
      _ = target := hsum
  have htargetlink : s3 z y t :=
    chart left (add d e) target z y t hgroup hleft hright htarget
  exact ⟨hrightlink, htargetlink⟩

#print axioms regroup_five
#print axioms joint_target_link_full

end JointAssociation
