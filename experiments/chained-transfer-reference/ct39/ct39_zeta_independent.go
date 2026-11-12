// CT39 independent square-table counter for F_101 and F_(101^2).
// Does not import the Python oracle or any isogeny/Jacobian engine.
package main

import "fmt"
const p = 101
const d = 2
type fe struct{ a, b int }
func mod(x int) int { x %= p; if x < 0 { x += p }; return x }
func mul(x, y fe) fe { return fe{mod(x.a*y.a+d*x.b*y.b), mod(x.a*y.b+x.b*y.a)} }
func sq(x fe) fe { return mul(x,x) }
func index(x fe) int { return x.a+p*x.b }
func eval(f []int, x fe) fe { y:=fe{}; for i:=len(f)-1;i>=0;i-- {y=mul(y,x);y.a=mod(y.a+f[i])};return y }
func failIf(b bool, s string){if b {panic(s)}}
func count(f []int, square1, square2 []bool) (int,int) {
    c1,c2:=2,2 // monic sextic has two points at infinity
    for a:=0;a<p;a++ {v:=eval(f,fe{a,0});c1++;if v.a==0 {continue};if square1[v.a] {c1++} else {c1--}}
    for a:=0;a<p;a++ {for b:=0;b<p;b++ {v:=eval(f,fe{a,b});c2++;if v== (fe{}) {continue};if square2[index(v)] {c2++} else {c2--}}}
    return c1,c2
}
func main(){
    s1:=make([]bool,p);s2:=make([]bool,p*p)
    for a:=0;a<p;a++ {s1[mod(a*a)]=true}
    for a:=0;a<p;a++ {for b:=0;b<p;b++ {s2[index(sq(fe{a,b}))]=true}}
    failIf(s1[d],"reducible quadratic extension")
    failIf(len(s2)!=p*p,"bad table")
    models:=[][]int{{31,75,74,54,71,55,1},{95,26,19,27,94,91,1},{95,93,43,39,92,17,1},{31,79,74,54,71,55,1}}
    names:=[]string{"T0","T1","T2","MUTANT"}
    for i,f:=range models {
        a,b:=count(f,s1,s2)
        A:=a-p-1; B:=(A*A-(p*p+1-b))/2
        j:=1+A+B+p*A+p*p
        if i<3 { failIf(a!=120||b!=10436||A!=18||B!=279||j!=12317,"target Weil mismatch") } else { failIf(a!=120||b!=10314||B!=218||j!=12256,"mutant mismatch") }
        fmt.Printf("%s: C(F101)=%d C(F101^2)=%d Weil=(1, %d, %d, %d, %d) Jac(F101)=%d\n",names[i],a,b,A,B,p*A,p*p,j)
    }
}
