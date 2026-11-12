// CT38 arithmetic cross-check. Separate Go implementation, public F101 fixtures.
package main
import("encoding/json";"fmt";"os")
const p=101
const n=109*113
const m1=1+p*n
const m0=1+4*p*n
const bad=1+p
type Point struct {X,Y int; Inf bool}
func imod(x int) int { x%=p; if x<0 {x+=p}; return x }
func pow(x,n int)int{r:=1; for n>0{if n&1==1{r=imod(r*x)};x=imod(x*x);n>>=1};return r}
func add(a Point,b Point,coeff int)Point{
 if a.Inf{return b};if b.Inf{return a};
 if a.X==b.X && imod(a.Y+b.Y)==0{return Point{Inf:true}}
 var slope int
 if a.X==b.X{slope=imod((3*a.X*a.X+coeff)*pow(2*a.Y,p-2))
 }else{slope=imod((b.Y-a.Y)*pow(b.X-a.X,p-2))}
 x:=imod(slope*slope-a.X-b.X)
 return Point{X:x,Y:imod(slope*(a.X-x)-a.Y)}
}
func scale(k int, v Point, c int)Point{
 acc:=Point{Inf:true};for k>0{if k&1==1{acc=add(acc,v,c)};v=add(v,v,c);k>>=1};return acc
}
func fatal(message string){fmt.Fprintln(os.Stderr,message);os.Exit(1)}
func ensure(ok bool,why string){if !ok{fatal(why)}}
func main(){
 ensure(m1%p==1 && m0%p==1 && m1%n==1 && m0%n==1 && m1%7==6 && m0%7==0,"residues")
 curves:=[]struct{Name string;A,B,Order int}{{"E109",1,46,109},{"E113",44,21,113}}
 checked:=0; changed:=0
 for _,c:=range curves{
  pts:=[]Point{{Inf:true}}
  for x:=0;x<p;x++{for y:=0;y<p;y++{if imod(y*y-x*x*x-c.A*x-c.B)==0{pts=append(pts,Point{X:x,Y:y})}}}
  ensure(len(pts)==c.Order,"point counts")
  for _,v:=range pts{
   ensure(scale(c.Order,v,c.A).Inf,"orders")
   ensure(scale(m1,v,c.A)==v && scale(m0,v,c.A)==v,"rational map")
   if scale(bad,v,c.A)!=v{changed++}
   checked++
  }
 }
 ensure(checked==222 && changed==220,"negative controls")
 data:=map[string]any{"field":p,"rational_points_checked":checked,"bad_changed":changed,"m1":m1,"m0":m0,"product_order":n,"product_pairs":109*113,"geometric_torsion_size":7*7*7*7,"standing":"pcc:unverified"}
 raw,_:=json.Marshal(data);fmt.Println(string(raw))
}
