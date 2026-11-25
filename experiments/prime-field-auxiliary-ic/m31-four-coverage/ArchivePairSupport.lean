import ArchiveData

namespace M31ArchivePairSupport

abbrev Point := Nat × Nat
def p := 2147483647
def neg (x : Nat) := (p - x) % p
def sub (x y : Nat) := (x + neg y) % p
def signed := M31ArchiveData.archived.flatMap fun (x,y) => [(x,y), (x,neg y)]

def onCurve (q : Point) : Bool :=
  q.1 < p && q.2 < p && q.2^2 % p == (q.1^3 + 2*q.1 + 14) % p

-- A reciprocal candidate via 31 squarings. Every use checks the reciprocal.
def powBits : Nat → Nat → Nat → Nat
  | 0, _, _ => 1
  | fuel+1, b, e =>
    ((if e % 2 = 1 then b else 1) * powBits fuel (b*b % p) (e/2)) % p

-- Encode infinity as zero, finite points as one plus their radix-p encoding.
-- Alongside each result check the exceptional case or the affine formula inputs.
def chord (a b : Point) : Bool × Nat :=
  if a.1 = b.1 && (a.2 + b.2) % p = 0 then (true,0) else
  let tangent := a.1 == b.1
  let num := if tangent then (3*a.1^2 + 2) % p else sub b.2 a.2
  let den := if tangent then (2*a.2) % p else sub b.1 a.1
  let inv := powBits 31 den (p-2)
  let slope := num * inv % p
  let x := sub (sub (slope^2 % p) a.1) b.1
  let y := sub (slope * sub a.1 x % p) a.2
  ((den*inv % p == 1) && (!tangent || a.2 == b.2) && onCurve (x,y), 1 + p*x + y)

def entries := signed.flatMap fun a => signed.map (chord a)
def endpoints := entries.map Prod.snd
set_option maxRecDepth 65536 in
set_option maxHeartbeats 0 in
theorem census : signed.length = 34 ∧ signed.all onCurve = true ∧
    entries.length = 1156 ∧ entries.all Prod.fst = true ∧
    endpoints.eraseDups.length = 579 ∧ endpoints.count 0 = 34 := by decide +kernel

end M31ArchivePairSupport
