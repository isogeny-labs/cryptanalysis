import Std.Tactic
set_option autoImplicit false
set_option maxRecDepth 100000
set_option maxHeartbeats 0
namespace OriginalKernelCensus
-- Entire finite input literals, projected without arithmetic from native88f828.
def masks : List (List Nat) := [[9511681577844867105, 5188291906266857505, 9232380353346274305, 2341872925073736705, 1155177839943778305, 1155175778390933505], [9511681577844867105, 5188291906266857505, 2341872925073736705, 9232380353346274305, 1155175778390933505, 1155177839943778305], [9511681577844867105, 5188291906266857505, 2341872925073736705, 9232380353346274305, 1155177839943778305, 1155175778390933505]]

def stored_eligibility : List (List Bool) := [[true, true, false, true, true, false], [false, true, true, false, false, false], [false, false, true, false, true, false]]

def D : List (List (List Nat)) := [[[100, 0, 0], [47, 0, 0], [10, 0, 0], [109, 0, 0], [116, 0, 0], [12, 0, 0]], [[24, 0, 0], [39, 0, 0], [116, 0, 0], [193, 0, 0], [173, 0, 0], [88, 0, 0]], [[193, 0, 0], [11, 0, 0], [38, 0, 0], [111, 0, 0], [36, 0, 0], [67, 0, 0]]]

def factors : List (List (List (List Nat))) := [[[[171, 167, 150], [171, 10, 52], [171, 46, 21], [84, 183, 145], [84, 39, 80], [84, 1, 221], [53, 0, 0]], [[171, 167, 150], [171, 10, 52], [171, 46, 21], [130, 108, 166], [130, 140, 7], [130, 198, 50], [121, 0, 0]], [[201, 120, 206], [201, 106, 6], [201, 220, 11], [14, 33, 55], [14, 18, 138], [14, 172, 30], [199, 0, 0]], [[201, 120, 206], [201, 106, 6], [201, 220, 11], [115, 64, 181], [115, 116, 146], [115, 43, 119], [110, 0, 0]], [[218, 91, 112], [218, 151, 131], [218, 204, 203], [164, 164, 118], [164, 130, 142], [164, 152, 186], [178, 0, 0]], [[218, 91, 112], [218, 151, 131], [218, 204, 203], [83, 83, 57], [83, 25, 216], [83, 115, 173], [126, 0, 0]]], [[[23, 99, 55], [23, 54, 138], [23, 70, 30], [98, 176, 177], [98, 96, 213], [98, 174, 56], [58, 0, 0]], [[23, 99, 55], [23, 54, 138], [23, 70, 30], [8, 160, 19], [8, 67, 72], [8, 219, 132], [188, 0, 0]], [[199, 121, 51], [199, 66, 205], [199, 36, 190], [131, 76, 74], [131, 82, 210], [131, 65, 162], [178, 0, 0]], [[199, 121, 51], [199, 66, 205], [199, 36, 190], [130, 135, 196], [130, 175, 62], [130, 136, 188], [7, 0, 0]], [[74, 222, 55], [74, 40, 138], [74, 184, 30], [179, 31, 73], [179, 98, 171], [179, 94, 202], [69, 0, 0]], [[74, 222, 55], [74, 40, 138], [74, 184, 30], [208, 117, 182], [208, 3, 185], [208, 103, 79], [86, 0, 0]]], [[[203, 148, 36], [203, 101, 66], [203, 197, 121], [65, 70, 197], [65, 99, 101], [65, 54, 148], [7, 0, 0]], [[203, 148, 36], [203, 101, 66], [203, 197, 121], [61, 100, 154], [61, 14, 208], [61, 109, 84], [78, 0, 0]], [[155, 59, 21], [155, 93, 150], [155, 71, 52], [35, 114, 153], [35, 123, 169], [35, 209, 124], [37, 0, 0]], [[155, 59, 21], [155, 93, 150], [155, 71, 52], [21, 113, 181], [21, 163, 146], [21, 170, 119], [49, 0, 0]], [[192, 161, 182], [192, 27, 185], [192, 35, 79], [197, 32, 21], [197, 58, 150], [197, 133, 52], [19, 0, 0]], [[192, 161, 182], [192, 27, 185], [192, 35, 79], [36, 213, 91], [36, 177, 204], [36, 56, 151], [109, 0, 0]]]]

def transport_images : List (List Nat) := [[0, 3, 2, 1, 12, 15, 14, 13, 8, 11, 10, 9, 4, 7, 6, 5, 48, 51, 50, 49, 60, 63, 62, 61, 56, 59, 58, 57, 52, 55, 54, 53, 32, 35, 34, 33, 44, 47, 46, 45, 40, 43, 42, 41, 36, 39, 38, 37, 16, 19, 18, 17, 28, 31, 30, 29, 24, 27, 26, 25, 20, 23, 22, 21], [0, 3, 2, 1, 12, 15, 14, 13, 8, 11, 10, 9, 4, 7, 6, 5, 48, 51, 50, 49, 60, 63, 62, 61, 56, 59, 58, 57, 52, 55, 54, 53, 32, 35, 34, 33, 44, 47, 46, 45, 40, 43, 42, 41, 36, 39, 38, 37, 16, 19, 18, 17, 28, 31, 30, 29, 24, 27, 26, 25, 20, 23, 22, 21]]

def mask (d i : Nat) : Nat := (masks[d]!)[i]!
def image (e v : Nat) : Nat := (transport_images[e]!)[v]!
def computedEligible (d i : Nat) : Bool :=
  ((factors[d]!)[i]!).all (fun factor => factor.any (fun x => x != 0)) &&
  (List.range 223).any (fun root => root * root % 223 == ((D[d]!)[i]!)[0]!)
def compatible (e i j : Nat) : Bool :=
  (List.range 64).all (fun v =>
    (mask e i).testBit v == (mask (e+1) j).testBit (image e v))
def supportedPair (e i j : Nat) : Bool :=
  computedEligible e i && computedEligible (e+1) j && compatible e i j
def accepted (i j k : Nat) : Bool := supportedPair 0 i j && supportedPair 1 j k

def pairs (e : Nat) : List (Nat × Nat) :=
  ((List.range 6).flatMap (fun i => (List.range 6).map (fun j => (i,j)))).filter
    (fun ij => supportedPair e ij.1 ij.2)
def triples : List (Nat × Nat × Nat) :=
  (List.range 6).flatMap (fun i =>
    (List.range 6).flatMap (fun j => (List.range 6).map (fun k => (i,j,k))))
def acceptedTriples : List (Nat × Nat × Nat) :=
  triples.filter (fun ijk => accepted ijk.1 ijk.2.1 ijk.2.2)

/-- All literals have the required finite shapes; every D is in F223. -/
theorem actual_data_shapes :
    masks.length = 3 ∧ (masks.all (fun row => row.length == 6)) = true ∧
    stored_eligibility.length = 3 ∧
    (stored_eligibility.all (fun row => row.length == 6)) = true ∧
    D.length = 3 ∧ (D.all (fun row => row.length == 6 && row.all
      (fun d => d.length == 3 && d[0]! < 223 && d[1]! == 0 && d[2]! == 0))) = true ∧
    factors.length = 3 ∧ (factors.all (fun row => row.length == 6 && row.all
      (fun fs => fs.length == 7 && fs.all (fun f => f.length == 3)))) = true ∧
    transport_images.length = 2 ∧
    (transport_images.all (fun row => row.length == 64 && row.all (fun v => v < 64))) = true := by
  decide

/-- Each actual table is a permutation of all64 vectors; no image-set assumption. -/
theorem actual_transport_bijections :
    ((transport_images[0]!).eraseDups).length = 64 ∧
    ((transport_images[1]!).eraseDups).length = 64 := by
  decide

/-- Smoothness nonzero vectors and an exhaustive F223 square test independently
reproduce every stored supplied-source eligibility flag. Geometry is separate. -/
theorem all18_eligibility_checks :
    ∀ d : Fin 3, ∀ i : Fin 6,
      computedEligible d.val i.val = (stored_eligibility[d.val]!)[i.val]! := by
  decide

/-- The explicit Cartesian enumeration covers every finite candidate triple. -/
theorem complete_triple_coverage :
    triples.length = 216 ∧ ∀ i j k : Fin 6, (i.val,j.val,k.val) ∈ triples := by
  decide

/-- Both edges and the entire216-triple verdict are derived from all18 masks,
all64 membership tests per pair and independently recomputed eligibility. -/
theorem actual_supported_verdict :
    pairs 0 = [(4,1)] ∧ pairs 1 = [(1,4)] ∧
    acceptedTriples = [(4,1,4)] := by
  decide

/-- No other finite-family triple satisfies both complete supported edges. -/
theorem actual_path_unique :
    ∀ i j k : Fin 6,
      accepted i.val j.val k.val = true ↔ i.val = 4 ∧ j.val = 1 ∧ k.val = 4 := by
  decide
end OriginalKernelCensus
