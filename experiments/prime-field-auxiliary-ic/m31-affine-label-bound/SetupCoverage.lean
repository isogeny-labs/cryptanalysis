import Mathlib

namespace M31SetupCoverage

-- x columns of the frozen field31_s5_base0/same_base.txt, in file order.
def coordinates : List ℕ := [3,98625645,308768278,536276641,753804470,975624154,
  985108144,1171458932,1213058799,1393679185,1685732321,1760557235,1896314920,
  1900239952,1900319349,1908835095,2084456163]

-- Every prime exponent of a positive integer below 2^31 is at most 30.
-- 47! contains every prime through 47 and no larger prime.
def hasSmoothRotation (x : ℕ) : Bool :=
  (List.range 31).any fun j => decide (((x * 2^j) % 2147483647) ∣ (47).factorial^30)

theorem soleCoordinate : coordinates.filter hasSmoothRotation = [3] := by native_decide

-- All candidate coordinates before lifting, in public.json order.
def rawRoots : List ℕ := [
  3,308768278,1213058799,1950178058,1620095117,1685732321,
  845665662,1760557235,1393679185,536276641,1896314920,1171458932,
  1533993268,1528659296,1851652048,987367763,1431655765,1908835095,
  1857409341,975624154,80168778,1101836261,985108144,2084456163,
  753804470,1900319349,1900239952,141165527,98625645,1491270739,
  2008905047,1560638367]

theorem rawCoverage : rawRoots.filter hasSmoothRotation = [3] := by native_decide

-- In microseconds: round total down and combined setup up separately per run.
-- t and s may be real times satisfying the conservative bounds.
theorem setupLimit (t s : ℝ)
    (run : (9685107 ≤ t ∧ s ≤ 2398) ∨ (5167235 ≤ t ∧ s ≤ 2204) ∨
           (11667566 ≤ t ∧ s ≤ 2391)) : t / (t-s) < 1.000427 := by
  rcases run with h | h | h <;> apply (div_lt_iff₀ (by linarith : 0 < t-s)).mpr <;> linarith

end M31SetupCoverage
