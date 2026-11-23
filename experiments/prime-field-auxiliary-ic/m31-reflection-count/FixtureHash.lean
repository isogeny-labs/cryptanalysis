import Correlation
import M31FixtureObstruction

namespace M31Reflection.FixtureHash

/-- Canonical coordinates from the archived depth-five public fixture. -/
def roots : List F := [
  3, 308768278, 1213058799, 1950178058,
  1620095117, 1685732321, 845665662, 1760557235,
  1393679185, 536276641, 1896314920, 1171458932,
  1533993268, 1528659296, 1851652048, 987367763,
  1431655765, 1908835095, 1857409341, 975624154,
  80168778, 1101836261, 985108144, 2084456163,
  753804470, 1900319349, 1900239952, 141165527,
  98625645, 1491270739, 2008905047, 1560638367]

abbrev Edge := F × F
def edges : List Edge := roots.flatMap fun x =>
  (roots.filter fun y => x.val < y.val).map fun y => (x,y)
def s (e : Edge) := e.1 + e.2
def t (e : Edge) := e.1 * e.2

theorem sums_unique : (edges.map s).Nodup := by native_decide

private theorem different_sums {e f : Edge} (he : e ∈ edges) (hf : f ∈ edges) (hne : e ≠ f) :
    s e ≠ s f := fun h => hne (List.inj_on_of_nodup_map sums_unique he hf h)

def incident (a b : F) (e : Edge) := t e = a*s e+b
instance (a b : F) (e : Edge) : Decidable (incident a b e) := inferInstanceAs (Decidable (_ = _))
def merged (a b : F) : Finset Edge := edges.toFinset.filter (incident a b)

/-- For x outside the pole this chord equation describes the fractional-linear map exactly. -/
theorem chord {K : Type*} [Field K] (a b x y : K) (hx : x ≠ a) :
    (a*x+b)/(x-a) = y ↔ x*y = a*(x+y)+b := by
  rw [div_eq_iff (sub_ne_zero.mpr hx)]
  constructor <;> intro h <;> linear_combination -h

def slope (e f : Edge) := (t f-t e)/(s f-s e)
def candidates (e : Edge) : List Edge := edges.filter fun f =>
  let a := slope e f
  let b := t e-a*s e
  decide (s f ≠ s e ∧ a^2+b ≠ 0 ∧ ¬(a=0 ∧ b=1))

private def keys (e : Edge) := ((candidates e).map (slope e)).map ZMod.val

/-- For each reference pair, no admissible slope leads to two further pairs. -/
theorem slope_certificate : ∀ e ∈ edges, ((candidates e).map (slope e)).Nodup := by
  have check : edges.all (fun e => decide ((keys e).mergeSort.IsChain (· < ·))) := by native_decide
  intro e he
  have inc := of_decide_eq_true (List.all_eq_true.mp check e he)
  have sorted : (keys e).mergeSort.Nodup := (List.isChain_iff_pairwise.mp inc).imp (fun h => ne_of_lt h)
  have dedup := (List.mergeSort_perm (keys e) _).nodup_iff.mp sorted
  exact List.Nodup.of_map _ dedup

private theorem recover {e f : Edge} {a b : F} (he : e ∈ edges) (hf : f ∈ edges)
    (ne : e ≠ f) (ie : incident a b e) (j : incident a b f) :
    slope e f = a := by
  apply (div_eq_iff (sub_ne_zero.mpr (different_sums hf he ne.symm))).mpr
  unfold incident at ie j
  rw [j, ie]
  ring

private theorem neighbor {e f : Edge} {a b : F} (he : e ∈ edges) (hf : f ∈ edges)
    (ne : e ≠ f) (ie : incident a b e) (j : incident a b f)
    (det : a^2+b ≠ 0) (exception : ¬(a=0 ∧ b=1)) : f ∈ candidates e := by
  apply List.mem_filter.mpr
  refine ⟨hf, ?_⟩
  simp only [recover he hf ne ie j, decide_eq_true_eq]
  have hb : t e-a*s e = b := sub_eq_of_eq_add' ie
  rw [hb]
  exact ⟨different_sums hf he ne.symm, det, exception⟩

theorem at_most_two (a b : F) (det : a^2+b ≠ 0) (exception : ¬(a=0 ∧ b=1)) :
    (merged a b).card ≤ 2 := by
  by_contra! bad
  obtain ⟨e,f,g,he,hf,hg,ef,eg,fg⟩ := Finset.two_lt_card_iff.mp bad
  have mem {u : Edge} (h : u ∈ merged a b) : u ∈ edges ∧ incident a b u := by
    simpa only [merged, Finset.mem_filter, List.mem_toFinset] using h
  obtain ⟨he,ie⟩ := mem he
  obtain ⟨hf,jf⟩ := mem hf
  obtain ⟨hg,jg⟩ := mem hg
  exact fg (List.inj_on_of_nodup_map (slope_certificate e he)
    (neighbor he hf ef ie jf det exception) (neighbor he hg eg ie jg det exception)
    ((recover he hf ef ie jf).trans (recover he hg eg ie jg).symm))

def liftBit (x : F) := decide ((cubic x)^1073741823 = 1)

private theorem criterion {K : Type*} [Field K] [Fintype K] (n : Nat)
    (size : Fintype.card K = n) (odd : ringChar K ≠ 2) (v : K) (nz : v ≠ 0) :
    v^(n/2) = 1 ↔ IsSquare v := by
  rw [← size]
  exact (FiniteField.isSquare_iff odd nz).symm

theorem lift_correct (x : F) : liftBit x = true ↔ IsSquare (cubic x) := by
  have nz : cubic x ≠ 0 := M31FixtureObstruction.no_root x
  have odd : ringChar F ≠ 2 := (ZMod.ringChar_zmod_n _).trans_ne (by decide)
  exact decide_eq_true_iff.trans (criterion 2147483647 (ZMod.card _) odd (cubic x) nz)

def conflicts (a b : F) := (merged a b).filter fun e => liftBit e.1 ≠ liftBit e.2

theorem witnesses : roots.length = 32 ∧ roots.Nodup ∧ edges.length = 496 ∧
    (merged 0 1).card = 16 ∧ (conflicts 0 1).card = 7 ∧
    (merged 720732407 1078219647).card = 2 ∧ (conflicts 720732407 1078219647).card = 0 := by
  native_decide


theorem affine_at_most_one (k : F) : (edges.toFinset.filter (fun e => s e = k)).card ≤ 1 := by
  apply Finset.card_le_one.mpr
  intro e he f hf
  simp only [Finset.mem_filter, List.mem_toFinset] at he hf
  exact List.inj_on_of_nodup_map sums_unique he.1 hf.1 (he.2.trans hf.2.symm)

theorem lossless_at_most_two (a b : F) (det : a^2+b ≠ 0) (ok : (conflicts a b).card = 0) :
    (merged a b).card ≤ 2 := by
  apply at_most_two a b det
  rintro ⟨rfl,rfl⟩
  have counter := witnesses.2.2.2.2.1
  omega

/-- Squaring to a scalar matrix forces trace zero for every nonscalar matrix. -/
theorem trace_zero {K : Type*} [Field K] (a b c d : K)
    (up : a*b+b*d = 0) (down : c*a+d*c = 0)
    (diag : a^2+b*c = c*b+d^2) (nonscalar : ¬(b=0 ∧ c=0 ∧ a=d)) :
    d = -a := by
  by_contra h
  have hn : a+d ≠ 0 := fun z => h (by linear_combination z)
  have van (x : K) (hx : x*(a+d) = 0) := (mul_eq_zero.mp hx).resolve_right hn
  exact nonscalar ⟨van b (by linear_combination up), van c (by linear_combination down),
    sub_eq_zero.mp (van (a-d) (by linear_combination diag))⟩

theorem normalized_chord {K : Type*} [Field K] (a b c x y : K)
    (hc : c ≠ 0) (pole : c*x-a ≠ 0) :
    (a*x+b)/(c*x-a) = y ↔ x*y = (a/c)*(x+y)+b/c := by
  rw [div_eq_iff pole]
  field_simp
  constructor <;> intro h <;> linear_combination -h


def parity4 (x : F) := (x.val.testBit 7 ^^ x.val.testBit 12) ^^
    (x.val.testBit 18 ^^ x.val.testBit 22)

theorem parity_decode : ∀ i : Fin 32,
    liftBit (roots[i.val]!) = ((33987 : Nat).testBit (i.val % 16) ^^ parity4 (roots[i.val]!)) := by
  native_decide

theorem reciprocal_layout : ∀ i : Fin 16, roots[i.val]! * roots[i.val+16]! = 1 := by
  native_decide

/-- The signature has a bit wherever the supplied Boolean function differs
on the two coordinates of a reciprocal pair. -/
def signature (bit : F → Bool) : Nat := (List.range 16).foldl (fun acc i =>
  if bit (roots[i]!) != bit (roots[i+16]!) then acc + 2^i else acc) 0

/-- Bit 31 is identically zero, so it pads the cases of weight below three. -/
theorem no_three_bits : ∀ i j k : Fin 32,
    signature (fun x => x.val.testBit i.val) ^^^ signature (fun x => x.val.testBit j.val) ^^^
    signature (fun x => x.val.testBit k.val) ≠ signature liftBit := by
  let cols := (List.range 32).map fun i => signature (fun x => x.val.testBit i)
  let wanted := signature liftBit
  have lookup (i : Fin 32) : cols[i.val]! = signature (fun x => x.val.testBit i.val) := by
    simp [cols, i.isLt]
  have cert : ∀ i j k : Fin 32, cols[i.val]! ^^^ cols[j.val]! ^^^ cols[k.val]! ≠ wanted := by
    native_decide
  intro i j k
  simpa only [lookup] using cert i j k

end M31Reflection.FixtureHash
