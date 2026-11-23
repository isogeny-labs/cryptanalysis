import Init

namespace M31ReciprocalWitness

abbrev p : Nat := 2^31 - 1

def liftsAt (a b x y : Nat) : Prop :=
  y^2 % p = (x^3 + a*x + b) % p

/-- Both reciprocal coordinates have signed magnitude a power of two.
Each lifts on the original curve and on the auxiliary curve. -/
theorem smooth_reciprocal_pair :
    let x : Nat := 4
    let u : Nat := 536870912
    x ≠ u ∧ x*u % p = 1 ∧
    min x (p-x) = 2^2 ∧ min u (p-u) = 2^29 ∧
    liftsAt 2 14 x 560044975 ∧ liftsAt 2 14 u 759798956 ∧
    liftsAt 1 0 x 518571843 ∧ liftsAt 1 0 u 435063924 := by
  unfold liftsAt
  decide +kernel


/-- Each row contains (r, A, B) from the frozen depth-17 constructor,
followed by inverse witnesses for the two inputs. -/
private abbrev Row := Nat × Nat × Nat × Nat × Nat
private def depth17 : List Row := [
    (0, 0, 1, 2130725020, 1001859875),
    (2, 6, 8, 530372142, 530372142),
    (262150, 786438, 3145792, 919430440, 919430440),
    (135006214, 403445766, 562160130, 1535176261, 1535176261),
    (199756251, 1939860868, 1327400300, 2056626176, 2056626176),
    (362281882, 1502091204, 1682583214, 1926961415, 1926961415),
    (1725080288, 23574809, 969764128, 1680736539, 1680736539),
    (350589864, 1004619974, 6444359, 187100988, 187100988),
    (47285803, 280101108, 627117762, 578606214, 578606214),
    (727792114, 1623174126, 289087550, 1046489814, 1046489814),
    (1398452374, 949008870, 415138803, 935060255, 935060255),
    (1149625992, 1550860236, 1037305887, 1541158513, 1541158513),
    (191112109, 1766583149, 1967955754, 981810741, 981810741),
    (1177953325, 693677, 1422947164, 183591811, 183591811),
    (1288656778, 1717099333, 393057247, 162570844, 162570844),
    (1979195732, 355904883, 1618056509, 829294582, 829294582),
    (1810907817, 425946391, 763015431, 840849800, 840849800)]

/-- Reject a row unless both supplied inverses multiply back to one.
This also excludes poles at each evaluated coordinate. -/
private def evaluatePair : List Row → Nat → Nat → Option (Nat × Nat)
  | [], x, y => some (x, y)
  | (r, a, b, ix, iy) :: rows, x, y =>
    let u := (x + p - r) % p
    let v := (y + p - r) % p
    if u * ix % p = 1 ∧ v * iy % p = 1 then
      evaluatePair rows ((u + a + b*ix) % p) ((v + a + b*iy) % p)
    else none

theorem depth17_reciprocal_pair :
    let x := 1001859875
    let y := 2130725020
    x ≠ y ∧ x*y % p = 1 ∧
    min x (p-x) = 5^3 * 23^2 * 109 * 139 ∧
    min y (p-y) = 3 * 19 * 41 * 71 * 101 ∧
    liftsAt 2 14 x 710316576 ∧ liftsAt 2 14 y 941064458 ∧
    depth17.length = 17 ∧
    evaluatePair depth17 x y = some (539375225, 539375225) := by
  unfold liftsAt
  decide +kernel

end M31ReciprocalWitness
