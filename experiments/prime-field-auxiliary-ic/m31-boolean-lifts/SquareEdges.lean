import Mathlib

namespace M31SquareEdges

/-- Columns are destination labels, rows are source labels. -/
structure Counts where
  nn : ℕ
  nl : ℕ
  ln : ℕ
  ll : ℕ

def best (c : Counts) := max c.nn c.nl + max c.ln c.ll
def size (c : Counts) := c.nn + c.nl + c.ln + c.ll
def score (c : Counts) (rule : Bool → Bool) :=
  (if rule false then c.nl else c.nn) + (if rule true then c.ll else c.ln)

theorem upperBound (c : Counts) (rule : Bool → Bool) : score c rule ≤ best c := by
  unfold score best
  apply Nat.add_le_add <;> split <;> simp

theorem attainable (c : Counts) : ∃ rule, score c rule = best c := by
  use fun label => if label then decide (c.ln ≤ c.ll) else decide (c.nn ≤ c.nl)
  simp [score, best, max_def]

/-- The native census and independent reverse-edge replay verify these
contingency tables in increasing order of the 24 primes through 89. -/
def panel : List Counts := [
  ⟨492972, 493019, 493792, 494000⟩,
  ⟨329751, 329736, 330507, 331274⟩,
  ⟨196862, 196660, 196394, 197279⟩,
  ⟨139020, 138727, 139010, 138584⟩,
  ⟨86415, 85596, 86256, 85694⟩,
  ⟨71806, 72002, 71664, 71747⟩,
  ⟨53493, 53704, 53311, 53682⟩,
  ⟨47508, 47326, 47326, 47221⟩,
  ⟨38400, 38249, 38255, 38090⟩,
  ⟨29461, 29498, 29485, 29259⟩,
  ⟨27250, 27423, 27258, 27133⟩,
  ⟨22393, 22155, 22117, 22316⟩,
  ⟨19730, 19815, 19808, 19642⟩,
  ⟨18471, 18898, 18710, 18648⟩,
  ⟨16980, 16641, 16814, 16907⟩,
  ⟨14618, 14549, 14464, 14818⟩,
  ⟨12971, 12688, 12812, 12992⟩,
  ⟨12256, 12397, 12461, 12349⟩,
  ⟨11034, 11017, 11119, 11034⟩,
  ⟨10190, 10381, 10229, 10422⟩,
  ⟨9935, 9956, 9943, 10022⟩,
  ⟨8990, 9091, 8955, 9187⟩,
  ⟨8574, 8498, 8449, 8575⟩,
  ⟨7855, 7808, 7829, 7812⟩]

theorem panelCounts : (panel.map size).sum = 6748424 ∧
    (panel.map best).sum = 3379303 ∧
    (panel.map (fun c => max (c.nn+c.ln) (c.nl+c.ll))).sum = 3378048 ∧
    (panel.map (fun c => c.nn+c.ll)).sum = 3375622 := by decide

def cell (c : Counts) (src dst : Bool) : ℕ :=
  if src then (if dst then c.ll else c.ln) else (if dst then c.nl else c.nn)

theorem allPositive : panel.all (fun c =>
    decide (0 < c.nn ∧ 0 < c.nl ∧ 0 < c.ln ∧ 0 < c.ll)) = true := by decide

/-- Even an abstaining rule cannot certify any destination using only the
prime and the source label: each context has both destination labels. -/
theorem soundAbstains (c : Counts) (hc : c ∈ panel) (rule : Bool → Option Bool)
    (sound : ∀ src guess, rule src = some guess → cell c src (!guess) = 0)
    (src : Bool) : rule src = none := by
  have pos := of_decide_eq_true (List.all_eq_true.mp allPositive c hc)
  cases h : rule src with
  | none => rfl
  | some guess =>
    have bad := sound src guess h
    cases src <;> cases guess <;> simp [cell] at bad <;> omega

theorem ceiling : (3379303:ℚ)/6748424 < 50076/100000 := by norm_num

end M31SquareEdges
