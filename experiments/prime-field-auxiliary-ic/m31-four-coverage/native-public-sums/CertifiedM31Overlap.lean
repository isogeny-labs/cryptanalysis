import AuxiliaryWitnessGroups

namespace M31.CertifiedOverlap

set_option maxRecDepth 16000

open AuxiliaryWitnessGroups
open TwistRootCertificate (F p)
private instance : Fact (Nat.Prime p) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

private abbrev Raw := Option (F × F)
private def raw {W : WeierstrassCurve F} : W.toAffine.Point → Raw
  | .zero => none
  | .some (x := x) (y := y) _ => some (x,y)

private def plus (W : WeierstrassCurve F) : Raw → Raw → Raw
  | none, q => q
  | q, none => q
  | some (x,y), some (u,v) =>
    if x = u ∧ y = W.toAffine.negY u v then none else
      let s := W.toAffine.slope x u y v
      some (W.toAffine.addX x u s, W.toAffine.addY x u y s)

private theorem raw_add {W : WeierstrassCurve F} (P Q : W.toAffine.Point) :
    raw (P+Q) = plus W (raw P) (raw Q) := by
  cases P with
  | zero => cases Q <;> rfl
  | @some x y h =>
    cases Q with
    | zero => rfl
    | @some u v k =>
      by_cases e : x = u ∧ y = W.toAffine.negY u v
      · rw [WeierstrassCurve.Affine.Point.add_of_Y_eq e.1 e.2]
        simp only [raw, plus, if_pos e]
      · rw [WeierstrassCurve.Affine.Point.add_some e]
        simp only [raw, plus, if_neg e]

private abbrev Row := Bool × Raw
private def check (W : WeierstrassCurve F) (base goal : Raw) (acc : Raw) : List Row → Bool
  | [] => decide (acc = goal)
  | (bit,next) :: rest =>
    let dbl := plus W acc acc
    decide ((if bit then plus W dbl base else dbl) = next) && check W base goal next rest

private def weight (n : ℕ) : List Row → ℕ
  | [] => n
  | (bit,_) :: rest => weight (n+n+(if bit then 1 else 0)) rest

private theorem sound {W : WeierstrassCurve F} (P : W.toAffine.Point) (goal : Raw)
    (rows : List Row) (n : ℕ) (ok : check W (raw P) goal (raw (n • P)) rows = true) :
    raw (weight n rows • P) = goal := by
  induction rows generalizing n with
  | nil => simpa [check, weight] using ok
  | cons row rest ih =>
    rcases row with ⟨bit,next⟩
    simp only [check, Bool.and_eq_true, decide_eq_true_eq] at ok
    apply ih
    rw [← ok.1] at ok
    cases bit <;> simpa [add_nsmul, raw_add] using ok.2

private theorem zero_of_raw {W : WeierstrassCurve F} {P : W.toAffine.Point}
    (h : raw P = none) : P = 0 := by cases P <;> simp_all [raw, WeierstrassCurve.Affine.Point.zero_def]

private def chain₁_1 : List Row := [
  (true, some (3,1498289385)),
  (false, some (1189749104,743628849)),
  (false, some (358787717,125786941)),
  (false, some (2142218904,1204356041)),
  (false, some (1201279776,1847724616)),
  (false, some (2092112356,572101554)),
  (false, some (448002930,730393137)),
  (false, some (2031285945,16601366)),
  (false, some (2049571796,1621970708)),
  (false, some (831775174,894157827)),
  (false, some (452424297,685107865)),
  (false, some (207614446,1591904882)),
  (false, some (218811233,422835709)),
  (false, some (248057572,1929362897)),
  (false, some (267158040,1916768942)),
  (true, some (1894615113,1787465995)),
  (false, some (2120263311,1962139559)),
  (false, some (137297079,2018399967)),
  (false, some (127101553,1406632034)),
  (false, some (1253675495,1938750190)),
  (true, some (2096414505,1330555666)),
  (true, some (1106433781,1375073825)),
  (false, some (1279642787,2145094692)),
  (true, some (1650833734,1293892099)),
  (false, some (13393263,391976987)),
  (true, some (828944864,2038844429)),
  (false, some (1221807901,1125899791)),
  (false, some (1529049284,1118862865)),
  (true, some (1129456881,591724985)),
  (true, some (1839789142,1370437243)),
  (false, some (599174716,1695956467)),
  (true, none)]

private theorem check₁_1 : 2147552589 • P₁ = 0 := by
  have h := sound P₁ none chain₁_1 0 (by decide +kernel)
  change raw (2147552589 • P₁) = none at h
  exact zero_of_raw h

private def chain₁_3 : List Row := [
  (true, some (3,1498289385)),
  (false, some (1189749104,743628849)),
  (true, some (1284568837,1031614747)),
  (false, some (1965387750,388974731)),
  (true, some (1548028497,1804317301)),
  (false, some (754338994,2101332900)),
  (true, some (348438345,561941694)),
  (false, some (400260376,1704025134)),
  (true, some (1358643210,1011870667)),
  (false, some (1423383216,1053501711)),
  (true, some (1531876779,2038177538)),
  (false, some (1227171220,1204370057)),
  (true, some (939103601,215714471)),
  (true, some (338840446,1527657357)),
  (false, some (181540044,111462891)),
  (false, some (305182533,1971619084)),
  (false, some (1698685920,333460372)),
  (false, some (180504130,787964666)),
  (false, some (205700965,338623039)),
  (true, some (669115375,424121658)),
  (false, some (430039251,1906962118)),
  (false, some (1245384009,456910582)),
  (false, some (287525007,1440267420)),
  (true, some (1873842825,808475331)),
  (true, some (613149449,328406866)),
  (false, some (487561706,1797311460)),
  (true, some (1263291595,295197460)),
  (true, some (758167298,1747428017)),
  (true, some (2105366765,850825546)),
  (true, some (1528970894,1621963169))]

private theorem check₁_3 : 715850863 • P₁ ≠ 0 := by
  have h := sound P₁ (some (1528970894,1621963169)) chain₁_3 0 (by decide +kernel)
  change raw (715850863 • P₁) = (some (1528970894,1621963169)) at h
  intro hz; rw [hz] at h; contradiction

private def chain₁_7 : List Row := [
  (true, some (3,1498289385)),
  (false, some (1189749104,743628849)),
  (false, some (358787717,125786941)),
  (true, some (1782377694,2107027086)),
  (false, some (232969986,1108156474)),
  (false, some (2145948776,998398068)),
  (true, some (1580040789,993012921)),
  (false, some (103220768,158810618)),
  (false, some (1788536763,157742673)),
  (true, some (1880333931,482965104)),
  (false, some (688905448,1260295434)),
  (false, some (1789210106,934744046)),
  (true, some (310454507,26009196)),
  (false, some (1640263254,35260476)),
  (true, some (1424029590,1798373181)),
  (false, some (983349627,2081927838)),
  (false, some (1382991577,936208657)),
  (true, some (1152350389,931585846)),
  (false, some (1587234876,1631222330)),
  (true, some (1485926180,2016039241)),
  (true, some (1294311641,965552898)),
  (false, some (1262408707,1935120292)),
  (false, some (1211932626,1498661455)),
  (false, some (1234852409,1889398348)),
  (false, some (1647389240,661814199)),
  (true, some (1688898228,1314007320)),
  (false, some (1803362936,1457991135)),
  (true, some (98852793,82897410)),
  (true, some (328286980,1708147608))]

private theorem check₁_7 : 306793227 • P₁ ≠ 0 := by
  have h := sound P₁ (some (328286980,1708147608)) chain₁_7 0 (by decide +kernel)
  change raw (306793227 • P₁) = (some (328286980,1708147608)) at h
  intro hz; rw [hz] at h; contradiction

private def chain₁_13 : List Row := [
  (true, some (3,1498289385)),
  (false, some (1189749104,743628849)),
  (false, some (358787717,125786941)),
  (true, some (1782377694,2107027086)),
  (true, some (1032050176,1588306913)),
  (true, some (158430550,1894405119)),
  (false, some (625733190,2034790404)),
  (true, some (261207440,416291985)),
  (true, some (537423938,72956618)),
  (false, some (2127041704,1380673688)),
  (false, some (1088504298,564248541)),
  (false, some (1943833598,1740523795)),
  (true, some (1838370692,1194964448)),
  (false, some (672913753,1096396368)),
  (true, some (1871112642,1676245971)),
  (true, some (864387040,528609605)),
  (false, some (1450350835,2125381322)),
  (false, some (398684063,366109692)),
  (true, some (329235208,467899254)),
  (false, some (1454015847,1901080989)),
  (false, some (115531698,1819483215)),
  (true, some (2062784328,399176972)),
  (false, some (2099153672,1275362758)),
  (false, some (264008744,345882286)),
  (false, some (1387220748,1159613273)),
  (false, some (605624768,2058260267)),
  (false, some (748165171,1737791118)),
  (true, some (1230800076,964208902))]

private theorem check₁_13 : 165196353 • P₁ ≠ 0 := by
  have h := sound P₁ (some (1230800076,964208902)) chain₁_13 0 (by decide +kernel)
  change raw (165196353 • P₁) = (some (1230800076,964208902)) at h
  intro hz; rw [hz] at h; contradiction

private def chain₁_7866493 : List Row := [
  (true, some (3,1498289385)),
  (false, some (1189749104,743628849)),
  (false, some (358787717,125786941)),
  (false, some (2142218904,1204356041)),
  (true, some (738309965,22661287)),
  (false, some (1650519842,1237069822)),
  (false, some (458673501,436815521)),
  (false, some (69401205,633476805)),
  (true, some (1752285603,849585296))]

private theorem check₁_7866493 : 273 • P₁ ≠ 0 := by
  have h := sound P₁ (some (1752285603,849585296)) chain₁_7866493 0 (by decide +kernel)
  change raw (273 • P₁) = (some (1752285603,849585296)) at h
  intro hz; rw [hz] at h; contradiction

private theorem order₁ : addOrderOf P₁ = 2147552589 := by
  apply addOrderOf_eq_of_nsmul_and_div_prime_nsmul (by decide) check₁_1
  intro q hq hd
  change q ∣ 3 * 7 * 13 * 7866493 at hd
  simp only [hq.dvd_mul] at hd
  rcases hd with (((h | h) | h) | h)
  all_goals first
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 3)).mp h
      subst q; exact check₁_3
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 7)).mp h
      subst q; exact check₁_7
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 13)).mp h
      subst q; exact check₁_13
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 7866493)).mp h
      subst q; exact check₁_7866493

private def chain₂_1 : List Row := [
  (true, some (2,221281234)),
  (false, some (1197032039,1334417193)),
  (false, some (1651931379,699747676)),
  (false, some (394808542,1474308905)),
  (false, some (800317322,2063276274)),
  (false, some (1788450939,1457390524)),
  (false, some (480721930,1105874432)),
  (false, some (1249499259,1639646508)),
  (false, some (132854603,1973699428)),
  (false, some (1049734385,1707649059)),
  (false, some (630046215,60351210)),
  (false, some (1259996501,1895296914)),
  (false, some (1308423045,749512014)),
  (false, some (932999937,405315989)),
  (false, some (1110363569,663999459)),
  (false, some (25311607,469799951)),
  (true, some (471248344,844696491)),
  (false, some (1800673069,1041097146)),
  (false, some (190679052,1914135347)),
  (true, some (1982924316,531808330)),
  (false, some (1663208236,92614078)),
  (false, some (137581182,75064656)),
  (false, some (1492816067,1376534043)),
  (false, some (387403901,2066980165)),
  (true, some (976716239,2107554474)),
  (false, some (959550390,628237406)),
  (false, some (878329087,1035899719)),
  (false, some (1309028380,1651528652)),
  (true, some (1524430358,1059960804)),
  (false, some (300839685,924713949)),
  (false, some (1231793772,785235869)),
  (true, none)]

private theorem check₂_1 : 2147520649 • P₂ = 0 := by
  have h := sound P₂ none chain₂_1 0 (by decide +kernel)
  change raw (2147520649 • P₂) = none at h
  exact zero_of_raw h

private def chain₂_23 : List Row := [
  (true, some (2,221281234)),
  (false, some (1197032039,1334417193)),
  (true, some (1840278771,2015251951)),
  (true, some (84471046,1227786146)),
  (false, some (487100911,684933926)),
  (false, some (400261843,1334512312)),
  (true, some (615944915,1394332543)),
  (false, some (1211795910,1848134637)),
  (false, some (1523368995,1541923378)),
  (false, some (1929259592,82203314)),
  (false, some (74239933,1884615566)),
  (true, some (2109394210,2124092201)),
  (false, some (949277083,1931708836)),
  (true, some (250663126,1863138482)),
  (true, some (2089192697,60427319)),
  (true, some (1744314938,2142978892)),
  (false, some (349116409,1770861323)),
  (false, some (1451339828,317461342)),
  (false, some (27705556,1133872233)),
  (false, some (614732795,1438007369)),
  (true, some (403921521,1778216011)),
  (false, some (304651610,1820558832)),
  (true, some (1590376762,279490476)),
  (true, some (717502197,237954782)),
  (true, some (1203681961,1352169412)),
  (true, some (1186803800,1831587883)),
  (true, some (1681872467,1946491687))]

private theorem check₂_23 : 93370463 • P₂ ≠ 0 := by
  have h := sound P₂ (some (1681872467,1946491687)) chain₂_23 0 (by decide +kernel)
  change raw (93370463 • P₂) = (some (1681872467,1946491687)) at h
  intro hz; rw [hz] at h; contradiction

private def chain₂_67 : List Row := [
  (true, some (2,221281234)),
  (true, some (716796314,1979629817)),
  (true, some (48393497,509720831)),
  (true, some (983579884,505570337)),
  (false, some (634014956,1586672737)),
  (true, some (879425670,611677949)),
  (false, some (1628882139,432581763)),
  (false, some (1400661876,1089684355)),
  (true, some (285807181,608686187)),
  (false, some (1808436394,603173175)),
  (false, some (637114036,1247531546)),
  (false, some (188497042,1755198420)),
  (true, some (1345266263,381291063)),
  (false, some (1875190162,1502815739)),
  (true, some (698803897,390359835)),
  (false, some (1143707946,67944645)),
  (true, some (2061409003,833948768)),
  (false, some (2040914416,1527125132)),
  (true, some (939047960,1647649165)),
  (false, some (756792879,1595067865)),
  (false, some (214768154,1347349272)),
  (false, some (84138467,1715794574)),
  (false, some (839286942,1617448609)),
  (true, some (453112376,859696129)),
  (true, some (1918878045,268236321))]

private theorem check₂_67 : 32052547 • P₂ ≠ 0 := by
  have h := sound P₂ (some (1918878045,268236321)) chain₂_67 0 (by decide +kernel)
  change raw (32052547 • P₂) = (some (1918878045,268236321)) at h
  intro hz; rw [hz] at h; contradiction

private def chain₂_1393589 : List Row := [
  (true, some (2,221281234)),
  (true, some (716796314,1979629817)),
  (false, some (1521396725,395751123)),
  (false, some (694782614,1579347599)),
  (false, some (1623000543,405879265)),
  (false, some (355417161,47065319)),
  (false, some (344380232,1219839914)),
  (false, some (1777842328,1691216737)),
  (true, some (1526065244,891903403)),
  (false, some (1344671136,780702504)),
  (true, some (1521178302,1908414239))]

private theorem check₂_1393589 : 1541 • P₂ ≠ 0 := by
  have h := sound P₂ (some (1521178302,1908414239)) chain₂_1393589 0 (by decide +kernel)
  change raw (1541 • P₂) = (some (1521178302,1908414239)) at h
  intro hz; rw [hz] at h; contradiction

private theorem order₂ : addOrderOf P₂ = 2147520649 := by
  apply addOrderOf_eq_of_nsmul_and_div_prime_nsmul (by decide) check₂_1
  intro q hq hd
  change q ∣ 23 * 67 * 1393589 at hd
  simp only [hq.dvd_mul] at hd
  rcases hd with ((h | h) | h)
  all_goals first
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 23)).mp h
      subst q; exact check₂_23
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 67)).mp h
      subst q; exact check₂_67
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 1393589)).mp h
      subst q; exact check₂_1393589

/-- The exact common-lift cardinality with both auxiliary orders certified. -/
theorem census : Nat.card {x : F // IsSquare (x^3+2*x+14) ∧ IsSquare (x^3+2*x-14)} =
    536844426 := census_of_witness_orders order₁ order₂

end M31.CertifiedOverlap
