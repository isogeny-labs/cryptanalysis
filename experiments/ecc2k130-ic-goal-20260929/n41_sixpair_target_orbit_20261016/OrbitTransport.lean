import Std

/-!
Conditional transport of a relation through an additive automorphism.
Here G is the binary elliptic-curve point group, f is Frobenius, g is inverse
Frobenius, cofactor is multiplication by four, and base is the signed-Frobenius
factor-base closure. The theorem applies to the six-pair relation list.
-/
namespace SixPairTargetOrbit

universe u
variable {G : Type u}

def sum (zero : G) (add : G → G → G) : List G → G
  | [] => zero
  | x :: xs => add x (sum zero add xs)

def forward (f : G → G) : Nat → G → G
  | 0, x => x
  | n + 1, x => f (forward f n x)

def backward (g : G → G) : Nat → G → G
  | 0, x => x
  | n + 1, x => backward g n (g x)

theorem backward_forward (f g : G → G)
    (hinv : ∀ x, g (f x) = x) :
    ∀ n x, backward g n (forward f n x) = x := by
  intro n
  induction n with
  | zero => intro x; rfl
  | succ n ih =>
      intro x
      simpa [forward, backward, hinv] using ih x

theorem sum_map (zero : G) (add : G → G → G) (g : G → G)
    (hzero : g zero = zero)
    (hadd : ∀ x y, g (add x y) = add (g x) (g y)) :
    ∀ xs, g (sum zero add xs) = sum zero add (xs.map g) := by
  intro xs
  induction xs with
  | nil => simpa [sum] using hzero
  | cons x xs ih => simp [sum, hadd, ih]

theorem backward_sum (zero : G) (add : G → G → G) (g : G → G)
    (hzero : g zero = zero)
    (hadd : ∀ x y, g (add x y) = add (g x) (g y)) :
    ∀ n xs, backward g n (sum zero add xs) =
      sum zero add (xs.map (backward g n)) := by
  intro n
  induction n with
  | zero => intro xs; simp [backward]
  | succ n ih =>
      intro xs
      calc
        backward g (n + 1) (sum zero add xs)
            = backward g n (g (sum zero add xs)) := rfl
        _ = backward g n (sum zero add (xs.map g)) := by
              rw [sum_map zero add g hzero hadd xs]
        _ = sum zero add ((xs.map g).map (backward g n)) := ih (xs.map g)
        _ = sum zero add (xs.map (backward g (n + 1))) := by
              simp [List.map_map, backward, Function.comp_def]

theorem backward_base (g : G → G) (base : G → Prop)
    (hclosed : ∀ x, base x → base (g x)) :
    ∀ n x, base x → base (backward g n x) := by
  intro n
  induction n with
  | zero => intro x hx; simpa [backward] using hx
  | succ n ih =>
      intro x hx
      simpa [backward] using ih (g x) (hclosed x hx)

theorem relation_pullback
    (zero : G) (add : G → G → G) (f g : G → G)
    (cofactor : G → G) (base : G → Prop)
    (hinv : ∀ x, g (f x) = x)
    (hzero : g zero = zero)
    (hadd : ∀ x y, g (add x y) = add (g x) (g y))
    (hclosed : ∀ x, base x → base (g x))
    (u q : G) (j : Nat) (points : List G)
    (hraw : cofactor u = q)
    (hrelation : sum zero add points = forward f j u)
    (hpoints : ∀ x ∈ points, base x) :
    cofactor (sum zero add (points.map (backward g j))) = q ∧
      ∀ x ∈ points.map (backward g j), base x := by
  have hpull : sum zero add (points.map (backward g j)) = u := by
    rw [← backward_sum zero add g hzero hadd j points,
        hrelation, backward_forward f g hinv j u]
  constructor
  · rw [hpull]
    exact hraw
  · intro x hx
    rcases List.mem_map.mp hx with ⟨y, hy, rfl⟩
    exact backward_base g base hclosed j y (hpoints y hy)

#print axioms SixPairTargetOrbit.relation_pullback

end SixPairTargetOrbit
