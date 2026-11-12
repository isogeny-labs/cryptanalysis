// CT33 independent Go arithmetic certificate for two cyclic-49 x-only supports.
// No imports from the Python evaluator or producer elliptic/Jacobian engines.
// The published fixed F101 kernels are inputs, not independently discovered.
// All checks are unsigned development evidence [pcc:unverified].
package main

import (
	"fmt"
	"reflect"
)

const prime = 101

type Pol []int

func mod(x int) int {
	x %= prime
	if x < 0 {
		x += prime
	}
	return x
}
func norm(a Pol) Pol {
	b := make(Pol, len(a))
	for i, v := range a {
		b[i] = mod(v)
	}
	for len(b) > 1 && b[len(b)-1] == 0 {
		b = b[:len(b)-1]
	}
	if len(b) == 0 {
		return Pol{0}
	}
	return b
}
func plus(a, b Pol) Pol {
	c := make(Pol, max(len(a), len(b)))
	for i := range c {
		if i < len(a) {
			c[i] += a[i]
		}
		if i < len(b) {
			c[i] += b[i]
		}
	}
	return norm(c)
}
func neg(a Pol) Pol {
	c := make(Pol, len(a))
	for i, v := range a {
		c[i] = -v
	}
	return norm(c)
}
func sub(a, b Pol) Pol { return plus(a, neg(b)) }
func times(a, b Pol) Pol {
	c := make(Pol, len(a)+len(b)-1)
	for i, x := range a {
		for j, y := range b {
			c[i+j] += x * y
		}
	}
	return norm(c)
}
func scale(a Pol, k int) Pol {
	c := make(Pol, len(a))
	for i, x := range a {
		c[i] = x * k
	}
	return norm(c)
}
func powint(v, e, m int) int {
	r := 1
	for e > 0 {
		if e&1 != 0 {
			r = r * v % m
		}
		v = v * v % m
		e >>= 1
	}
	return r
}
func derivative(a Pol) Pol {
	if len(a) <= 1 {
		return Pol{0}
	}
	c := make(Pol, len(a)-1)
	for i := 1; i < len(a); i++ {
		c[i-1] = a[i] * i
	}
	return norm(c)
}
func pow(a Pol, e int) Pol {
	v := Pol{1}
	for e > 0 {
		if e&1 != 0 {
			v = times(v, a)
		}
		a = times(a, a)
		e >>= 1
	}
	return v
}
func rem(a, b Pol) Pol {
	a = norm(a)
	b = norm(b)
	if len(b) == 1 && b[0] == 0 {
		panic("division by zero")
	}
	inv := powint(b[len(b)-1], prime-2, prime)
	for len(a) >= len(b) && !(len(a) == 1 && a[0] == 0) {
		d := len(a) - len(b)
		k := mod(a[len(a)-1] * inv)
		for i, x := range b {
			a[i+d] = mod(a[i+d] - k*x)
		}
		a = norm(a)
	}
	return a
}
func monic(a Pol) Pol { return scale(a, powint(a[len(a)-1], prime-2, prime)) }
func gcd(a, b Pol) Pol {
	for !(len(b) == 1 && b[0] == 0) {
		a, b = b, rem(a, b)
	}
	return monic(a)
}
func powmod(a Pol, e int, m Pol) Pol {
	v := Pol{1}
	for e > 0 {
		if e&1 != 0 {
			v = rem(times(v, a), m)
		}
		a = rem(times(a, a), m)
		e >>= 1
	}
	return v
}
func eq(a, b Pol) bool { return reflect.DeepEqual(norm(a), norm(b)) }
func ensure(x bool, msg string) {
	if !x {
		panic(msg)
	}
}

// Independent construction via the sums at the kernel roots rather than
// Python's simplified logarithmic-derivative expression:
// X = x + 2 sum f'(t)/(x-t) + 4 sum f(t)/(x-t)^2.
func xmap(a, b int, h Pol) (Pol, Pol) {
	h = norm(h)
	f := Pol{b, a, 0, 1}
	hp := derivative(h)
	hpp := derivative(hp)
	// Sum t = -h[2].
	s1 := mod(-h[2])
	d := times(h, h)
	// A/h = sum f'(t)/(x-t); A=f'(x)h' - (9x+3s1)h.
	A := sub(times(Pol{a, 0, 3}, hp), times(Pol{3 * s1, 9}, h))
	// B/h^2 = sum f(t)/(x-t)^2:
	// B = f(x)(h'^2-h h'') - (f'(x)h'-(6x+s1)h)h.
	B := sub(times(f, sub(times(hp, hp), times(h, hpp))),
		times(sub(times(derivative(f), hp), times(Pol{s1, 6}, h)), h))
	n := plus(times(Pol{0, 1}, d), plus(scale(times(A, h), 2), scale(B, 4)))
	return n, d
}
func codomain(a, b int, h Pol) (int, int) {
	s1 := mod(-h[2])
	s2 := mod(s1*s1 - 2*h[1])
	s3 := mod(s1*s1*s1 - 3*s1*h[1] - 3*h[0])
	v := mod(2 * (3*s2 + 3*a))
	w := mod(2 * (5*s3 + 3*a*s1 + 6*b))
	return mod(a - 5*v), mod(b - 7*w)
}
func homogeneous(h, n, d Pol) Pol {
	degree := len(h) - 1
	np := make([]Pol, degree+1)
	dp := make([]Pol, degree+1)
	np[0], dp[0] = Pol{1}, Pol{1}
	for i := 1; i <= degree; i++ {
		np[i] = times(np[i-1], n)
		dp[i] = times(dp[i-1], d)
	}
	out := Pol{0}
	for i, c := range h {
		out = plus(out, scale(times(np[i], dp[degree-i]), c))
	}
	return out
}
func lifted(h, n, d Pol) Pol {
	return plus(plus(pow(n, 3), scale(times(times(n, n), d), h[2])), plus(scale(times(n, times(d, d)), h[1]), scale(pow(d, 3), h[0])))
}
func frobFixed(f Pol, degree int) int {
	x := Pol{0, 1}
	z := x
	for i := 0; i < degree; i++ {
		z = powmod(z, prime, f)
	}
	return len(gcd(f, sub(z, x))) - 1
}
func globalEquation(a, b, aa, bb int, n, d Pol) bool {
	w := sub(times(derivative(n), d), times(n, derivative(d)))
	lhs := times(Pol{b, a, 0, 1}, times(w, w))
	rhs := times(d, plus(plus(pow(n, 3), scale(times(n, times(d, d)), aa)), scale(pow(d, 3), bb)))
	return eq(lhs, rhs)
}
func run(name string, a, b int, h0 Pol, e1a, e1b int, h1, dual, expected Pol, degree int) {
	n, d := xmap(a, b, h0)
	ca, cb := codomain(a, b, h0)
	ensure(ca == e1a && cb == e1b, name+" codomain0")
	ensure(globalEquation(a, b, ca, cb, n, d), name+" elliptic identity0")
	n2, d2 := xmap(ca, cb, h1)
	c2a, c2b := codomain(ca, cb, h1)
	ensure(globalEquation(ca, cb, c2a, c2b, n2, d2), name+" elliptic identity1")
	H := lifted(h1, n, d)
	ensure(eq(H, expected), name+" fixed primitive 49 polynomial mismatch")
	ensure(len(H) == 22 && H[21] == 1 && eq(gcd(H, h0), Pol{1}), name+" degree/overlap")
	K := times(h0, H)
	ensure(len(K) == 25 && K[24] == 1, name+" composite degree")
	Ncomp := homogeneous(n2, n, d)
	Dcomp := times(d, times(H, H))
	ensure(len(Ncomp) == 50 && Ncomp[49] == 1, name+" normalized composite numerator")
	ensure(eq(gcd(Ncomp, Dcomp), Pol{1}), name+" reduced composite map")
	ensure(globalEquation(a, b, c2a, c2b, Ncomp, Dcomp), name+" global composed degree49 identity")
	ensure(!globalEquation(a, b, c2a, mod(c2b+1), Ncomp, Dcomp), name+" wrong degree49 target")
	ensure(eq(times(d, times(H, H)), times(K, K)), name+" expected composite denominator")
	ensure(eq(gcd(H, derivative(H)), Pol{1}), name+" squarefree")
	ensure(frobFixed(H, degree) == 21, name+" Frobenius minimal field")
	for i := 1; i < degree; i++ {
		ensure(frobFixed(H, i) == 0, name+" premature subfield")
	}
	wrong := lifted(dual, n, d)
	ensure(!eq(H, wrong), name+" backtracking accepted")
	ensure(!globalEquation(a, b, ca, mod(cb+1), n, d), name+" incorrect first target")
	ensure(!globalEquation(ca, cb, c2a, mod(c2b+1), n2, d2), name+" incorrect second target")
	fmt.Printf("%s independent Go: composite degree=%d, primitive degree=%d, Frobenius x degree=%d, second target=(%d,%d); wrong/backtracking controls rejected [pcc:unverified]\n", name, len(K)-1, len(H)-1, degree, c2a, c2b)
}
func main() {
	run("E109", 1, 46, Pol{72, 100, 35, 1}, 26, 58, Pol{99, 94, 75, 1}, Pol{58, 26, 58, 1},
		Pol{9, 78, 22, 78, 88, 78, 90, 64, 94, 74, 63, 12, 66, 63, 87, 78, 67, 69, 81, 60, 83, 1}, 21)
	run("E113", 44, 21, Pol{59, 46, 8, 1}, 69, 50, Pol{53, 19, 40, 1}, Pol{29, 88, 45, 1},
		Pol{69, 65, 23, 53, 73, 2, 51, 98, 84, 33, 33, 30, 95, 34, 26, 89, 25, 69, 19, 29, 88, 1}, 7)
}