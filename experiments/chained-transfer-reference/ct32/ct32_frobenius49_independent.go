// Independent CT32 cross-check. No libraries beyond the Go standard library.
// Execution is producer-local unsigned arithmetic, not PCC certification.
package main

import "fmt"

func mod(x, m int) int { x %= m; if x < 0 { x += m }; return x }
func order(v, m int) int {
    p := 1
    for d := 1; d <= 200; d++ { p = (p*v)%m; if p == 1 { return d } }
    panic("unit order > 200")
}
func roots(t, p, modn int) []int {
    var v []int
    for a:=0; a<modn; a++ { if mod(a*a-t*a+p,modn)==0 {v=append(v,a)} }
    return v
}
func count(a,b,p int) int {
    n:=1
    for x:=0;x<p;x++ {f:=mod(x*x*x+a*x+b,p); for y:=0;y<p;y++ {if mod(y*y-f,p)==0{n++}}}
    return n
}
func require(ok bool) {if !ok {panic("CT32 negative/mathematical control failed")}}
func main() {
    type item struct{name string; a,b,n,mod7,forward,dual,pdeg,xdeg int}
    cases:=[]item{{"E109",1,46,109,5,33,9,42,21},{"E113",44,21,113,6,27,11,14,7}}
    for _,c:=range cases {
       n:=count(c.a,c.b,101); require(n==c.n)
       t:=102-n; r7:=roots(t,101,7); r49:=roots(t,101,49)
       require(len(r7)==2 && len(r49)==2)
       require(mod(c.forward*c.forward-t*c.forward+101,49)==0)
       require(mod(c.dual*c.dual-t*c.dual+101,49)==0)
       require(mod(c.forward,7)==c.mod7 && mod(c.forward+c.dual,49)==mod(t,49))
       require(order(c.forward,49)==c.pdeg)
       power:=1;xd:=0
       for d:=1;d<=50;d++ {power=mod(power*c.forward,49);if power==1||power==48{xd=d;break}}
       require(xd==c.xdeg && power==48)
       power=1;for d:=0;d<6;d++ {power=mod(power*c.forward,49)}
       fixed:=0;for u:=0;u<49;u++ {if mod((power-1)*u,49)==0 {fixed++}}
       require(fixed==7)
       fmt.Printf("%s: independent Go count=%d, mod7 roots=%v, mod49 roots=%v, point degree=%d, x degree=%d; F101^6 fixed=%d/49\n",c.name,n,r7,r49,c.pdeg,xd,fixed)
    }
}
