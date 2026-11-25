import OrbitParityRank

namespace M31OrbitSideCode
abbrev F := ZMod 2147483647
abbrev Step := M31OrbitNorm.Step F
abbrev J := Fin 32
abbrev B := ZMod 2
private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def tag (a b : F) := decide (a.val ≤ b.val)

theorem ordered_root {a b c d : F} (sum : a+b=c+d) (prod : a*b=c*d)
    (same : tag a b = tag c d) : a=c := by
  have h : (a-c)*(a-d)=0 := by linear_combination a*sum-prod
  rcases mul_eq_zero.mp h with h|h
  · exact sub_eq_zero.mp h
  · have ad := sub_eq_zero.mp h
    have bc : b=c := by linear_combination sum-ad
    subst d
    subst c
    have eq : a.val=b.val := by
      have iff : a.val ≤ b.val ↔ b.val ≤ a.val := by simpa [tag] using same
      omega
    exact ZMod.val_injective _ eq

def next (s : Step) (x : F) := x-s.t+s.A+s.B/(x-s.t)
def branch (s : Step) (x : F) := tag (x-s.t) (s.B/(x-s.t))

theorem step_injective (s : Step) {x y : F} (hx : x ≠ s.t) (hy : y ≠ s.t)
    (image : next s x = next s y) (same : branch s x = branch s y) : x=y := by
  have h := ordered_root (a:=x-s.t) (b:=s.B/(x-s.t)) (c:=y-s.t) (d:=s.B/(y-s.t))
  have sum : x-s.t+s.B/(x-s.t) = y-s.t+s.B/(y-s.t) := by
    unfold next at image
    linear_combination image
  have prod : (x-s.t)*(s.B/(x-s.t)) = (y-s.t)*(s.B/(y-s.t)) := by
    field_simp [sub_ne_zero.mpr hx, sub_ne_zero.mpr hy]
  exact sub_left_inj.mp (h sum prod same)

def code : List Step → F → Option (F × List Bool)
  | [], x => some (x,[])
  | s::ss,x => if x=s.t then none else
      (code ss (next s x)).map fun (z,bs) => (z,branch s x :: bs)

theorem code_unique (ss : List Step) {x y z : F} {bs : List Bool}
    (hx : code ss x=some (z,bs)) (hy : code ss y=some (z,bs)) : x=y := by
  induction ss generalizing x y bs with
  | nil => simp [code] at hx hy; exact hx.1.trans hy.1.symm
  | cons s ss ih =>
    by_cases h1 : x=s.t
    · simp [code,h1] at hx
    by_cases h2 : y=s.t
    · simp [code,h2] at hy
    cases ex : code ss (next s x) with
    | none => simp [code,h1,ex] at hx
    | some px =>
      obtain ⟨zx,bx⟩ := px
      cases ey : code ss (next s y) with
      | none => simp [code,h2,ey] at hy
      | some py =>
        obtain ⟨zy,by'⟩ := py
        simp [code,h1,ex] at hx
        simp [code,h2,ey] at hy
        obtain ⟨rfl,rfl⟩ := hx
        obtain ⟨rfl,hbits⟩ := hy
        obtain ⟨hb,ht⟩ := List.cons.inj hbits
        subst by'
        exact step_injective s h1 h2 (ih ex ey) hb.symm

theorem code_length (ss : List Step) (x z : F) (bs : List Bool)
    (h : code ss x=some (z,bs)) : bs.length=ss.length := by
  induction ss generalizing x bs with
  | nil => simp [code] at h; simp [← h.2]
  | cons s ss ih =>
    by_cases pole : x=s.t
    · simp [code,pole] at h
    cases e : code ss (next s x) with
    | none => simp [code,pole,e] at h
    | some pair =>
      obtain ⟨v,b⟩ := pair
      simp [code,pole,e] at h
      obtain ⟨rfl,rfl⟩ := h
      simpa using ih _ _ e

def imageStep (x : F) (s : Step) : Option F :=
  if x=s.t then none else some (next s x)

theorem code_terminal (ss : List Step) (x : F) :
    (code ss x).map Prod.fst = ss.foldlM imageStep x := by
  induction ss generalizing x with
  | nil => rfl
  | cons s ss ih =>
    by_cases pole : x=s.t
    · simp [code,List.foldlM_cons,imageStep,pole]
    · simpa [code,List.foldlM_cons,imageStep,pole,Option.map_map,Function.comp_def] using
        ih (next s x)

theorem five_branches {x z : F} {bs : List Bool}
    (h : code M31OrbitNorm.steps x=some (z,bs)) : bs.length=5 :=
  code_length _ _ _ _ h

theorem point_unique {x y x' y' z : F} {bs : List Bool}
    (h : code M31OrbitNorm.steps x=some (z,bs))
    (h' : code M31OrbitNorm.steps x'=some (z,bs))
    (curve : y^2=x^3+x) (curve' : y'^2=x'^3+x')
    (sign : tag y (-y)=tag y' (-y')) : (x,y)=(x',y') := by
  obtain rfl := code_unique _ h h'
  have yy : y=y' := ordered_root (by simp) (by linear_combination -curve+curve') sign
  rw [yy]

def represents (z : F) (bs : List Bool) (sign : Bool) (pt : F × F) : Prop :=
  code M31OrbitNorm.steps pt.1 = some (z,bs) ∧
    pt.2^2 = pt.1^3+pt.1 ∧ tag pt.2 (-pt.2) = sign

/-- Existence of a decoder for every represented point, hence every deterministic
ordered label function of that point. The replay uses explicit square roots. -/
theorem sufficient {L : Type*} [Inhabited L] (read : F × F → L) :
    ∃ decode : F → List Bool → Bool → L, ∀ z bs sign pt,
      represents z bs sign pt → bs.length = 5 ∧ decode z bs sign = read pt := by
  classical
  refine ⟨fun z bs sign => if h : ∃ pt, represents z bs sign pt
    then read h.choose else default, ?_⟩
  intro z bs sign pt hp
  have h : ∃ q, represents z bs sign q := ⟨pt,hp⟩
  simp only [dite_eq_left h]
  refine ⟨five_branches hp.1, congrArg read ?_⟩
  have hq := h.choose_spec
  exact point_unique hq.1 hp.1 hq.2.1 hp.2.1 (hq.2.2.trans hp.2.2.symm)

def label (s : Bool × J) (j : J) : B :=
  M31OrbitParityRank.bit 1 0 (if s.1 then s.2-j else s.2+j)

def orientedIndex (s : Bool × J) (j : J) := if s.1 then s.2-j else s.2+j

def orientedX (s : Bool × J) (j : J) := M31OrbitParityRank.x 1 0 (orientedIndex s j)

def orientedY (s : Bool × J) (j : J) :=
  let y := M31OrbitParityRank.y 1 0 (orientedIndex s j)
  if s.1 then -y else y

theorem oriented_chords : ∀ (s : Bool × J) (j : J),
    let x := orientedX s j
    let y := orientedY s j
    let xn := orientedX s (j+1)
    let yn := orientedY s (j+1)
    let dx := x-1965083199
    let dy := y-1854403464
    y^2=x^3+x ∧ dx≠0 ∧ dy^2=(xn+x+1965083199)*dx^2 ∧
      (yn+y)*dx=dy*(x-xn) := by native_decide

theorem distinct : Function.Injective label := by
  have sep : ∀ a b : Bool × J, a ≠ b → ∃ j : J, label a j ≠ label b j := by native_decide
  intro a b eq
  by_contra h
  obtain ⟨j,ne⟩ := sep a b h
  exact ne (congrFun eq j)

theorem required {S : Type*} [Fintype S] (state : Bool × J → S)
    (decode : F → S → J → B)
    (correct : ∀ s, decode ((M31OrbitParityRank.terminal
      (M31OrbitParityRank.x 1 0 s.2)).getD 0) (state s) = label s) : 64 ≤ Fintype.card S := by
  have inj : Function.Injective state := by
    intro a b same
    apply distinct
    rw [← correct a, ← correct b, M31OrbitParityRank.common_terminal,
      M31OrbitParityRank.common_terminal, same]
  simpa using Fintype.card_le_of_injective state inj

end M31OrbitSideCode
