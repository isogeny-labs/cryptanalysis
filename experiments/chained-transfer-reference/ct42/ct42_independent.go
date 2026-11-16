package main
// CT42 independent Go polynomial Euclidean/Frobenius audit; [pcc:unverified].
import "fmt"
const p=101
var models=map[string][]int{
 "T0":{31,75,74,54,71,55,1},
 "T1":{95,26,19,27,94,91,1},
 "T2":{95,93,43,39,92,17,1},
 "mutant33":{37,75,74,54,71,55,1},
 "mutant24":{31,79,74,54,71,55,1},
}
func mod(a int)int{a%=p;if a<0 {a+=p};return a}
func norm(a []int)[]int{for len(a)>0&&mod(a[len(a)-1])==0{a=a[:len(a)-1]}; for i:=range a {a[i]=mod(a[i])};return a}
func times(a,b []int)[]int{if len(a)==0||len(b)==0{return nil}; c:=make([]int,len(a)+len(b)-1);for i,v:=range a {for j,w:=range b {c[i+j]=mod(c[i+j]+v*w)}};return norm(c)}
func power(a,n int)int{r:=1;for n>0 {if n&1==1{r=mod(r*a)};a=mod(a*a);n>>=1};return r}
func remainder(a,b []int)[]int{a=norm(append([]int(nil),a...));b=norm(append([]int(nil),b...));if len(b)==0{panic("zero divisor")};inv:=power(b[len(b)-1],p-2);for len(a)>=len(b){h:=mod(a[len(a)-1]*inv);off:=len(a)-len(b);for j,v:=range b{a[off+j]=mod(a[off+j]-h*v)};a=norm(a)};return a}
func gcd(a,b []int)[]int{a=norm(a);b=norm(b);for len(b)>0 {a,b=b,remainder(a,b)};if len(a)>0{u:=power(a[len(a)-1],p-2);for i:=range a{a[i]=mod(a[i]*u)}};return a}
func diff(a,b []int)[]int{n:=len(a);if len(b)>n{n=len(b)};c:=make([]int,n);for i:=0;i<n;i++{if i<len(a){c[i]+=a[i]};if i<len(b){c[i]-=b[i]};c[i]=mod(c[i])};return norm(c)}
func powMod(a []int,n int,f []int)[]int{r:=[]int{1};for n>0{if n&1==1{r=remainder(times(r,a),f)};a=remainder(times(a,a),f);n>>=1};return r}
func sig(f []int)[]int{der:=make([]int,6);for i:=1;i<=6;i++{der[i-1]=mod(f[i]*i)};if len(gcd(f,der))!=1{panic("singular")};a:=[]int{0,1};out:=[]int{};for k:=1;k<=6;k++{a=powMod(a,p,f);out=append(out,len(gcd(f,diff(a,[]int{0,1})))-1)};return out}
func eq(a,b []int)bool{if len(a)!=len(b){return false};for i:=range a{if a[i]!=b[i]{return false}};return true}
func main(){for _,name:=range []string{"T0","T1","T2","mutant33","mutant24"}{s:=sig(models[name]);fmt.Printf("%s: %v\n",name,s);want:=[]int{0,0,0,0,0,6};if name=="mutant33"{want=[]int{0,0,6,0,0,6}};if name=="mutant24"{want=[]int{0,2,0,6,0,2}};if !eq(s,want){panic("factor-degree mismatch")}};fmt.Println("PASS [pcc:unverified]: independent Go GF(101) Frobenius signature")}
