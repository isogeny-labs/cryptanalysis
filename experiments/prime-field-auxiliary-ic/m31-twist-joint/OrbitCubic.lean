import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic.Ring
/-! Products of the two cubics over a full 31-step doubling orbit in M31.
The coefficient recurrence computes the product as a polynomial in the seed.
Only degrees 0, 31, 62, and 93 survive. -/

namespace OrbitCubic
abbrev F := ZMod 2147483647
def eval (x : F) : List F → F
  | [] => 0
  | c :: cs => c+x*eval x cs
/-- Multiply a coefficient list by b + aX + hX³, carrying the next three terms. -/
def step (b a h : F) : List F → F → F → F → List F
  | [], u,v,w => [u,v,w]
  | c::cs,u,v,w => (b*c+u)::step b a h cs (a*c+v) w (h*c)
theorem eval_step (x b a h : F) (cs : List F) (u v w : F) :
    eval x (step b a h cs u v w) =
    (b+a*x+h*x^3)*eval x cs+u+x*v+x^2*w := by
  induction cs generalizing u v w with
  | nil => simp [eval,step]; ring
  | cons c cs ih => simp only [step,eval,ih]; ring
def coeff (b : F) : ℕ → List F
  | 0 => [1]
  | n+1 => step b (2*(2^n)) ((2^n)^3) (coeff b n) 0 0 0
def orbit (b x : F) : ℕ → F
  | 0 => 1
  | n+1 => ((2^n*x)^3 + 2*(2^n*x)+b)*orbit b x n
theorem relation (b x : F) (n : ℕ) : orbit b x n = eval x (coeff b n) := by
  induction n with
  | zero => simp [orbit,eval,coeff]
  | succ n ih => rw [orbit,coeff,eval_step,ih]; ring
def sparse (a b c : F) := a :: (List.replicate 30 0 ++ b :: (List.replicate 30 0 ++ c :: (List.replicate 30 0 ++ [1])))
theorem zeros (n : ℕ) (x : F) (cs : List F) : eval x (List.replicate n 0 ++ cs) = x^n * eval x cs := by
  induction n with
  | zero => simp
  | succ n ih => simp [List.replicate_succ, eval, ih, pow_succ]; ring
theorem sparse_eval (a b c x : F) :
    eval x (sparse a b c) = a+x^31*(b+x^31*(c+x^31)) := by
  simp only [sparse,eval,zeros]; ring
set_option maxRecDepth 100000
set_option maxHeartbeats 20000000
theorem curve (x : F) : orbit 14 x 31 =
    1143995257+x^31*(1828106314+x^31*(1903309697+x^31)) := by
  rw [relation, show coeff 14 31 = sparse 1143995257 1828106314 1903309697 by decide, sparse_eval]
theorem twist (x : F) : orbit (-14) x 31 =
    1003488390+x^31*(1828106314+x^31*(244173950+x^31)) := by
  rw [relation, show coeff (-14) 31 = sparse 1003488390 1828106314 244173950 by decide, sparse_eval]

/-- Both orbit products from the same odd and even polynomial parts. -/
theorem shared (x : F) :
    let u := x^31
    let odd := u * (u^2 + 1828106314)
    let even := 1903309697 * u^2 + 1143995257
    (orbit 14 x 31, orbit (-14) x 31) = (odd + even, odd - even) := by
  dsimp only
  rw [curve, twist]
  have hc : (1003488390 : F) = -1143995257 := by decide
  have hq : (244173950 : F) = -1903309697 := by decide
  rw [hc, hq]
  have parts {R : Type} [CommRing R] (u a b c : R) :
      (a+u*(b+u*(c+u)), -a+u*(b+u*(-c+u))) =
      (u*(u^2+b)+(c*u^2+a), u*(u^2+b)-(c*u^2+a)) := by
    apply Prod.ext <;> dsimp <;> ring
  exact parts (x^31) 1143995257 1828106314 1903309697

end OrbitCubic
