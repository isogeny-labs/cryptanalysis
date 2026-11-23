import Mathlib

namespace M31TensorCuts

/-- Little-endian lift bits in the field31_s8_base0 structured_roots order. -/
def labels (second : Bool) : Nat := if second then
  115676677566673279785420824090728349230249939372380466152352527793085432411304
  else 13659445427536930535081474813143208749566494119185677463092623986750226938325

/-- Ordered coordinates from field31_s8_base0/public.json
(SHA-256 d9b37ebd239714b43c5495ab1d0fc9178f5d0362b4c9ffe775257f18b0b653ca). -/
def roots : Array Nat := #[
  3, 1203551522, 1536990316, 539070090, 908746428, 288435722, 2076622497, 556151870,
  308768278, 542722525, 965603179, 2126721692, 359948633, 128502619, 293222943, 381809933,
  1213058799, 1351369859, 266549023, 1654610866, 1991405496, 221609590, 505240220, 469398761,
  1950178058, 1778015464, 207117416, 1420109433, 535634841, 1372163765, 1686916870, 1458020002,
  1620095117, 1849409954, 709032129, 206033265, 974504375, 1223984705, 330248674, 724251205,
  1685732321, 550713455, 689045045, 502959564, 1919791429, 2044870429, 634883852, 1899316242,
  845665662, 1574268988, 949774795, 1109344772, 1347550901, 789883502, 877968933, 229780419,
  1760557235, 1298822968, 1836440738, 1210694610, 1964730219, 1076595796, 1577461604, 2076319201,
  1393679185, 1075338288, 1952044371, 940965991, 1316615191, 23153349, 1836549034, 2013417741,
  536276641, 1822024368, 2055943965, 1434153586, 1362264055, 1428243488, 802920906, 885173638,
  1896314920, 1739323829, 1308345839, 1952846158, 1220096672, 281340230, 1698407859, 124309447,
  1171458932, 283198404, 1952432603, 601502222, 1061464045, 249736899, 1328662907, 674867531,
  1533993268, 1053095001, 2066694777, 908651627, 663363933, 1998589667, 405177853, 1087343611,
  1528659296, 266065793, 857798499, 666317790, 147546915, 1284785398, 666647166, 870129920,
  1851652048, 1088602941, 2120299015, 1676136771, 316981566, 212742001, 683955466, 719040472,
  987367763, 1817398495, 283936717, 1812124617, 393503860, 363771846, 1914115906, 1052539396,
  1431655765, 699480731, 1435150362, 1855494706, 1890337495, 1250644656, 1371893784, 1306853747,
  1908835095, 2048915358, 938709049, 2080851001, 1045448707, 1601024036, 573622777, 1575903470,
  1857409341, 1959060526, 282813966, 384911225, 952446904, 1958785438, 1360861958, 1728706143,
  975624154, 1544708068, 912977784, 1553958982, 683025760, 930640529, 604834518, 985345071,
  80168778, 1834944232, 1586510496, 772637863, 953953111, 387230172, 1429422687, 1640461606,
  1101836261, 212959319, 1146975312, 512817870, 191729941, 648136595, 1385539725, 1996648649,
  985108144, 936498951, 693791372, 318011797, 552402987, 624584136, 1498473223, 1797180114,
  2084456163, 338376938, 460075151, 736709947, 1473375652, 1897914899, 1060062115, 262929395,
  753804470, 1723438002, 1402451289, 109281818, 1706471425, 1787997261, 1168479315, 1879995779,
  1900319349, 1507419522, 1830187144, 213687041, 1540858324, 2047309224, 775906403, 1317035274,
  1900239952, 1030062799, 167849932, 2007597026, 1078537248, 568966198, 357187202, 89414648,
  141165527, 2119240203, 2128001522, 705382376, 1572319414, 215978863, 180852104, 1506549564,
  98625645, 569039486, 1661715015, 1512802043, 232116925, 488173821, 373895537, 1142931561,
  1491270739, 1755784903, 1590385724, 1235973168, 1330202499, 1978119149, 1636962681, 1137373510,
  2008905047, 1048955606, 930602142, 649635604, 883608566, 1897199447, 1377431620, 407766740,
  1560638367, 1547274140, 1757720736, 566778278, 1343687786, 905929423, 2022821148, 370804213]

theorem labelAgreement : roots.size = 256 ∧ ∀ s : Bool, ∀ i : Fin 256,
    let x : ZMod 2147483647 := roots[i.val]!
    (labels s).testBit i.val = decide
      ((x^3 + 2*x + (if s then 36 else 14))^1073741823 = 1) := by native_decide

def axes (mask : Nat) := (List.range 8).filter (fun k => mask.testBit k)
def balanced (mask : Fin 256) : Bool := mask.val.testBit 0 && (axes mask).length == 4

def spread (bits : Nat) (positions : List Nat) : Nat :=
  (positions.zipIdx.map fun (pos,i) => if bits.testBit i then 2^pos else 0).sum

def cut (second : Bool) (mask : Fin 256) : Matrix (Fin 16) (Fin 16) ℚ :=
  fun i j => if (labels second).testBit
    (spread i (axes mask) + spread j (axes (255-mask.val))) then 1 else 0

/-- Candidate inverse by row reduction. Soundness only uses the subsequent
matrix product equality, so no property of the pivot selection is assumed. -/
private def candidateData {n : Nat} (M : Matrix (Fin n) (Fin n) ℚ) :
    Array (Array ℚ) := Id.run do
  let mut rows := Array.ofFn fun i : Fin n => Array.ofFn fun j : Fin (2*n) =>
    if h : j.val < n then M i ⟨j.val,h⟩ else if j.val == n+i.val then 1 else 0
  for k in [:n] do
    let some p := (List.range n).find? (fun i => i ≥ k && (rows[i]!)[k]! != 0)
      | return #[]
    rows := rows.swapIfInBounds k p
    let pivot := rows[k]!
    let unit := pivot.map (fun x => x / pivot[k]!)
    rows := rows.set! k unit
    for i in [:n] do
      if i != k then
        let row := rows[i]!
        let coeff := row[k]!
        rows := rows.set! i (row.zipWith (fun x y => x - coeff*y) unit)
  return rows

private def fromData {n : Nat} (rows : Array (Array ℚ)) : Matrix (Fin n) (Fin n) ℚ :=
  fun i j => (rows[i.val]?.getD #[])[n+j.val]?.getD 0

@[noinline] private def checkData {n : Nat} (M : Matrix (Fin n) (Fin n) ℚ)
    (rows : Array (Array ℚ)) : Bool := decide (M * fromData rows = 1)

private def checked {n : Nat} (M : Matrix (Fin n) (Fin n) ℚ) :=
  checkData M (candidateData M)

private theorem bound {n : Nat} (M : Matrix (Fin n) (Fin n) ℚ)
    (ok : checked M) : n ≤ M.rank := by
  have eq : M * fromData (candidateData M) = 1 := of_decide_eq_true ok
  have h := Matrix.rank_mul_le_left M (fromData (candidateData M))
  simpa [eq, Matrix.rank_one] using h

private def firstRow (i : Fin 15) : Fin 16 := i.castSucc
private def minorCol (i : Fin 15) : Fin 16 := if i.val = 14 then 15 else i.castSucc

private theorem regular : ∀ s : Bool, ∀ m : Fin 256, balanced m = true →
    (s = true ∨ m.val ≠ 77) → checked (cut s m) := by native_decide

private theorem exceptional : let M := (cut false 77).submatrix firstRow minorCol
                              checked M := by native_decide

theorem rankLower (s : Bool) (m : Fin 256) (hm : balanced m) :
    (if s then 16 else 15) ≤ (cut s m).rank := by
  by_cases h : s = true ∨ m.val ≠ 77
  · exact le_trans (by cases s <;> decide : (if s then 16 else 15) ≤ 16)
      (bound _ (regular s m hm h))
  · have hs : s = false := by cases s <;> simp_all
    have em : m = 77 := Fin.ext (by by_contra hn; exact h (Or.inr hn))
    subst s
    subst m
    exact (bound _ exceptional).trans (Matrix.rank_submatrix_le _ _ _)

/-- Every exact rational matrix factorization across this split must
allocate at least this many middle indices. -/
theorem bondLower (s : Bool) (m : Fin 256) (hm : balanced m) {d : Nat}
    (L : Matrix (Fin 16) (Fin d) ℚ) (R : Matrix (Fin d) (Fin 16) ℚ)
    (h : cut s m = L * R) : (if s then 16 else 15) ≤ d := by
  have lower := rankLower s m hm
  rw [h] at lower
  exact lower.trans ((Matrix.rank_mul_le_left L R).trans L.rank_le_width)

end M31TensorCuts
