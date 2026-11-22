import Std

namespace HalfBranchClasses

/-- Four-torsion-class counts in residues 0, 1, 2, 3. -/
structure Counts where
  c0 : Nat
  c1 : Nat
  c2 : Nat
  c3 : Nat
  deriving DecidableEq

/-- Exact class-count convolution for addition modulo four. -/
def conv (a b : Counts) : Counts :=
  ⟨a.c0*b.c0 + a.c1*b.c3 + a.c2*b.c2 + a.c3*b.c1,
   a.c0*b.c1 + a.c1*b.c0 + a.c2*b.c3 + a.c3*b.c2,
   a.c0*b.c2 + a.c1*b.c1 + a.c2*b.c0 + a.c3*b.c3,
   a.c0*b.c3 + a.c1*b.c2 + a.c2*b.c1 + a.c3*b.c0⟩

def original : Counts := ⟨2160, 2067, 1974, 2067⟩
def image : Counts := ⟨4134, 0, 4134, 0⟩
def union : Counts := ⟨6294, 2067, 6108, 2067⟩

/-- One even original-source position followed by one odd union-source position. -/
def pairStep (v : Counts) : Counts := conv (conv v original) union

/-- Ordered twelve-position count, starting from the zero class. -/
def sixPairs : Nat → Counts
  | 0 => ⟨1, 0, 0, 0⟩
  | n + 1 => pairStep (sixPairs n)

theorem union_classes :
    union = ⟨original.c0 + image.c0, original.c1 + image.c1,
             original.c2 + image.c2, original.c3 + image.c3⟩ := by
  decide

/-- The exact ordered tuple counts conditional on the enumerated one-position
    source and image class vectors. The curve-to-vector census is a separate
    executable audit. -/
theorem twelve_position_counts :
    sixPairs 6 =
      ⟨1632772202848539815248204491379559103260383217664,
       1632772202848539815247347206162321352120982306816,
       1632772202848539815246489920945083600981581395968,
       1632772202848539815247347206162321352120982306816⟩ := by
  decide

#print axioms union_classes
#print axioms twelve_position_counts

end HalfBranchClasses
