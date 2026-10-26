import Std

/- Finite arithmetic core of the written CM/polarization argument.
   Elliptic curves, CM Hom-spaces, norm bounds and Torelli are not formalized. -/
set_option maxRecDepth 1000000
set_option maxHeartbeats 0
namespace CubicCM53

def normMember (n : Nat) : Bool :=
  (List.range 21).any fun i => (List.range 11).any fun j =>
    let x : Int := (i : Int)-10
    let y : Int := (j : Int)-5
    8*x*x+3*x*y+26*y*y == (n : Int)

def heron (a b c : Nat) : Int :=
  2*(a : Int)*b*c*53 - ((a : Int)*b)^2 - ((b : Int)*c)^2 - ((c : Int)*a)^2

def valid (a b c : Nat) : Bool :=
  decide (0<a ∧ a≤b ∧ b≤c ∧ a+b+c=53 ∧ 0≤heron a b c ∧ heron a b c % 823=0) &&
  normMember (a*b) && normMember (a*c) && normMember (b*c)

theorem sorted_bounds (a b c : Nat)
    (h : 0<a ∧ a≤b ∧ b≤c ∧ a+b+c=53) : a<18 ∧ b<27 := by omega

theorem finite_exclusion :
    ∀ a : Fin 18, ∀ b : Fin 27, valid a.val b.val (53-a.val-b.val) = false := by decide

theorem no_admissible_partition (a b c : Nat)
    (h : 0<a ∧ a≤b ∧ b≤c ∧ a+b+c=53)
    (hab : normMember (a*b)=true) (hac : normMember (a*c)=true)
    (hbc : normMember (b*c)=true)
    (hh : 0≤heron a b c) (hd : heron a b c % 823=0) : False := by
  have bounds := sorted_bounds a b c h
  have hc : c=53-a-b := by omega
  have bad := finite_exclusion ⟨a,bounds.1⟩ ⟨b,bounds.2⟩
  have good : valid a b c=true := by
    simp [valid,h.1,h.2.1,h.2.2.1,h.2.2.2,hab,hac,hbc,hh,hd]
  have : valid a b c=false := by simpa [←hc] using bad
  simp_all

theorem no_cube_trace :
    ∀ u : Fin 11, let n : Int := (u.val : Int)-5
      n^3-24*n ≠ 35 ∧ n^3-24*n ≠ -35 := by decide

#print axioms sorted_bounds
#print axioms finite_exclusion
#print axioms no_admissible_partition
#print axioms no_cube_trace
end CubicCM53
