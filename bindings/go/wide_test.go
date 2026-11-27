package cryptanalysis

import (
	"errors"
	"math/big"
	"testing"
)

// Groups above 2^53 (where a float64 stops holding every integer) up to the
// library's 64-bit limit; the same instances as tests/test_wide.c. Answers
// are checked against math/big as well as against the planted secret.
const (
	wideP = 1<<64 - 3059
	wideQ = (wideP - 1) / 4
	wideX = 1<<62 - 904

	smoothP = 18412301237266326539 // 64-bit prime with 2^28-smooth p-1

	ec64P = 18446744056529682403
	ec64A = 5
	ec64B = 5
	ec64N = 18446744051100303869 // 7 * ec64Q
	ec64Q = 2635249150157186267
)

func bigPowMod(b, e, m uint64) uint64 {
	r := new(big.Int).Exp(new(big.Int).SetUint64(b), new(big.Int).SetUint64(e),
		new(big.Int).SetUint64(m))
	return r.Uint64()
}

func TestWideZpIntervals(t *testing.T) {
	z, err := NewZp(wideP, wideQ)
	if err != nil {
		t.Fatal(err)
	}
	defer z.Close()
	g, err := z.FindGenerator(3)
	if err != nil {
		t.Fatal(err)
	}
	if bigPowMod(g.Residue(), wideQ, wideP) != 1 {
		t.Fatalf("generator %d does not have order dividing q", g.Residue())
	}
	h, err := z.Mul(g, wideX)
	if err != nil {
		t.Fatal(err)
	}
	if want := bigPowMod(g.Residue(), wideX, wideP); h.Residue() != want {
		t.Fatalf("Mul = %d, math/big says %d", h.Residue(), want)
	}
	opts := &Options{Seed: 7}
	lo, hi := uint64(wideX-(1<<30)), uint64(wideQ-1)
	solvers := map[string]func(Elem, Elem, uint64, uint64, *Options) (uint64, Stats, error){
		"bsgs": z.BSGS, "kangaroo": z.Kangaroo, "grumpy": z.Grumpy,
	}
	for name, solve := range solvers {
		x, _, err := solve(g, h, lo, hi, opts)
		if err != nil || x != wideX {
			t.Fatalf("%s: x=%d err=%v, want %d", name, x, err, uint64(wideX))
		}
	}
	if _, _, err := z.BSGS(g, h, 1<<51, 1<<51+1<<20, opts); !errors.Is(err, ErrNotFound) {
		t.Fatalf("interval without the answer: err=%v, want ErrNotFound", err)
	}
}

func TestWideZpFullGroup(t *testing.T) {
	for _, f := range Factorize(smoothP - 1) {
		if f.P >= 1<<28 {
			t.Fatalf("p-1 has a factor %d above 2^28", f.P)
		}
	}
	z, err := NewZp(smoothP, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer z.Close()
	if z.Order() != smoothP-1 {
		t.Fatalf("order %d, want p-1", z.Order())
	}
	root := PrimitiveRoot(smoothP)
	for _, x := range []uint64{smoothP - 2, 1<<53 + 1, 1<<63 + 12345} {
		h, err := z.Mul(ZpElem(root), x)
		if err != nil {
			t.Fatal(err)
		}
		if want := bigPowMod(root, x, smoothP); h.Residue() != want {
			t.Fatalf("Mul = %d, math/big says %d", h.Residue(), want)
		}
		got, _, err := z.Dlog(ZpElem(root), h, nil)
		if err != nil || got != x {
			t.Fatalf("Dlog: got %d err=%v, want %d", got, err, x)
		}
	}
}

func TestWideEC64(t *testing.T) {
	n, err := ECCountPoints(ec64P, ec64A, ec64B)
	if err != nil || n != ec64N {
		t.Fatalf("ECCountPoints = %d, %v; want %d", n, err, uint64(ec64N))
	}
	e, err := NewEC(ec64P, ec64A, ec64B, ec64Q)
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	e.SetOrder(ec64Q, ec64N/ec64Q)
	g, err := e.FindGenerator(5)
	if err != nil {
		t.Fatal(err)
	}
	if ord, err := e.ElemOrder(g); err != nil || ord != ec64Q {
		t.Fatalf("generator order %d, %v", ord, err)
	}
	x := uint64(ec64Q - 123456789)
	h, err := e.Mul(g, x)
	if err != nil {
		t.Fatal(err)
	}
	// The curve equation, in math/big.
	px, py := h.XY()
	P := new(big.Int).SetUint64(ec64P)
	X, Y := new(big.Int).SetUint64(px), new(big.Int).SetUint64(py)
	lhs := new(big.Int).Mul(Y, Y)
	rhs := new(big.Int).Exp(X, big.NewInt(3), nil)
	rhs.Add(rhs, new(big.Int).Mul(big.NewInt(ec64A), X)).Add(rhs, big.NewInt(ec64B))
	if lhs.Sub(lhs, rhs).Mod(lhs, P).Sign() != 0 {
		t.Fatal("h is not on the curve")
	}
	lo, hi := x-(1<<30), uint64(ec64Q-1)
	for name, solve := range map[string]func(Elem, Elem, uint64, uint64, *Options) (uint64, Stats, error){
		"bsgs": e.BSGS, "kangaroo": e.Kangaroo, "grumpy": e.Grumpy,
	} {
		got, _, err := solve(g, h, lo, hi, &Options{Seed: 9})
		if err != nil || got != x {
			t.Fatalf("%s: got %d err=%v, want %d", name, got, err, x)
		}
	}
}

func TestWideIndexCalculus(t *testing.T) {
	const p = 4503599627370023 // 52-bit safe prime
	if !IsPrime(p) || !IsPrime((p-1)/2) {
		t.Fatal("p is not a safe prime")
	}
	g := PrimitiveRoot(p)
	h := bigPowMod(g, 1<<51+7, p)
	x, _, err := ICSolve(p, g, h, nil)
	if err != nil || bigPowMod(g, x, p) != h {
		t.Fatalf("ICSolve: x=%d err=%v", x, err)
	}
	if _, _, err := ICSolve(wideP, PrimitiveRoot(wideP), 99, nil); !errors.Is(err, ErrUnsupported) {
		t.Fatalf("p >= 2^63: err=%v, want ErrUnsupported", err)
	}
}
