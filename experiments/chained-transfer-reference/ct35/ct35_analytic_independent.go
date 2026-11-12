// CT35 independent structural accounting for a normalized separable odd-degree
// isogeny x=N/K^2, y'=y d(N/K^2)/dx. No numeric field implementation.
// Value+derivative Horner costs two field mults and two field adds per degree;
// inverse/power bookkeeping adds 8 multiplications, 1 addition, 1 inversion.
// Scientific standing [pcc:unverified].
package main
import "fmt"
type Cost struct {Adds int; Multiplies int; Inversions int}
func evalDegree(d int) Cost {
 if d<3 || d%2!=1 {panic("odd degree >=3 required")}
 r:=(d-1)/2
 return Cost{2*(d+r)+1,2*(d+r)+8,1}
}
func plus(a,b Cost) Cost{return Cost{a.Adds+b.Adds,a.Multiplies+b.Multiplies,a.Inversions+b.Inversions}}
func main(){
 seven:=evalDegree(7); double:=plus(seven,seven);direct:=evalDegree(49)
 if seven!=(Cost{21,28,1})||double!=(Cost{42,56,2})||direct!=(Cost{147,154,1}){panic("wrong accounting")}
 if direct.Multiplies<=double.Multiplies || direct.Adds<=double.Adds || direct.Inversions>=double.Inversions {panic("wrong tradeoff")}
 fmt.Printf("degree7 %+v\ndegree7plus7 %+v\ndegree49 %+v\n",seven,double,direct)
 fmt.Printf("break_even_inversion_mul_units >= %d + %d * addition_mul_units\n",direct.Multiplies-double.Multiplies,direct.Adds-double.Adds)
 fmt.Println("CT35 GO PASS [pcc:unverified]")
}
