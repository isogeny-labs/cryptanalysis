import Mathlib

namespace M31LiftBits

def positives : List Nat := [3,98625645,308768278,536276641,753804470,975624154,985108144,1171458932,1213058799,1393679185,1685732321,1760557235,1896314920,1900239952,1900319349,1908835095,2084456163]
def negatives : List Nat := [1950178058,1620095117,845665662,1533993268,1528659296,1851652048,987367763,1431655765,1857409341,80168778,1101836261,141165527,1491270739,2008905047,1560638367]

def liftBit (x : Nat) : Bool :=
  let v : ZMod 2147483647 := (x : ZMod 2147483647)^3 + 2*x + 14
  v == 0 || v^1073741823 == 1

def key (x : Nat) : Nat :=
  (x >>> 5) % 2 + 2*((x >>> 8)%2) + 4*((x >>> 15)%2) + 8*((x >>> 26)%2)

theorem fixture :
    positives.length = 17 ∧ negatives.length = 15 ∧
    (positives ++ negatives).Nodup ∧
    positives.all liftBit = true ∧ negatives.any liftBit = false ∧
    positives.all (fun x => Nat.testBit 10851 (key x)) = true ∧
    negatives.any (fun x => Nat.testBit 10851 (key x)) = false := by native_decide

-- Every unordered triple has an oppositely labeled pair agreeing on all three bits.
theorem tripleCollisions :
    (List.range 31).all (fun i => (List.range i).all (fun j =>
      (List.range j).all (fun k =>
        let mask := 2^i + 2^j + 2^k
        positives.any (fun x => negatives.any (fun y => (x &&& mask) == (y &&& mask)))))) = true := by
  native_decide
end M31LiftBits
