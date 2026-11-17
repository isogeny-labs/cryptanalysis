// CT168: standalone exhaustive F_(223^3) point count for E: y^2=x^3+9
// and E_d: y^2=x^3+9(2+z), with z^3=-3. Producer-only independent arithmetic.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <stdexcept>
#include <string>
#include <cassert>

constexpr int P=223, PP=P*P, Q=P*P*P;
inline int mod(int64_t a){int v=int(a%P);return v<0?v+P:v;}
struct F {int a,b,c;};
inline F mul(F x,F y){
 return {mod((int64_t)x.a*y.a-3LL*((int64_t)x.b*y.c+(int64_t)x.c*y.b)),
         mod((int64_t)x.a*y.b+(int64_t)x.b*y.a-3LL*(int64_t)x.c*y.c),
         mod((int64_t)x.a*y.c+(int64_t)x.b*y.b+(int64_t)x.c*y.a)};
}
inline F sqr(F x){return {mod((int64_t)x.a*x.a-6LL*x.b*x.c),
                           mod(2LL*x.a*x.b-3LL*x.c*x.c),
                           mod((int64_t)x.b*x.b+2LL*x.a*x.c)};}
inline F cube(F x){return mul(sqr(x),x);}
inline int encode(F x){return x.a+P*x.b+PP*x.c;}
inline F decode(int n){return {n%P,(n/P)%P,n/PP};}
inline bool iszero(F x){return x.a==0&&x.b==0&&x.c==0;}
inline F add(F x,F y){return {mod(x.a+y.a),mod(x.b+y.b),mod(x.c+y.c)};}
inline F powf(F a,uint64_t n){F r={1,0,0};while(n){if(n&1)r=mul(r,a);a=sqr(a);n>>=1;}return r;}

struct Count {uint64_t points,square,zero,nonsquare;};
Count count(F B,const std::vector<uint8_t>& squares){
 uint64_t points=1, square=0,zero=0,nonsquare=0;
 for(int k=0;k<Q;k++){
   F rhs=add(cube(decode(k)),B);
   if(iszero(rhs)){points++;zero++;}
   else if(squares[encode(rhs)>>3]&(1u<<(encode(rhs)&7))){points+=2;square++;}
   else nonsquare++;
 }
 if(zero+square+nonsquare!=(uint64_t)Q)throw std::runtime_error("partition");
 return {points,square,zero,nonsquare};
}
void print(const char* key,Count c){printf("\"%s\":{\"points\":%llu,\"nonzero_square_x\":%llu,\"zero_rhs_x\":%llu,\"nonsquare_x\":%llu}", key,(unsigned long long)c.points,(unsigned long long)c.square,(unsigned long long)c.zero,(unsigned long long)c.nonsquare);}
int main(){
 if(P%6!=1)throw std::runtime_error("p");
 std::vector<uint8_t> squares((Q+7)/8,0);
 for(int y=0;y<Q;y++){int i=encode(sqr(decode(y)));squares[i>>3]|=uint8_t(1u<<(i&7));}
 F d={2,1,0};F character=powf(d,(Q-1)/6);
 if(character.a!=40||character.b!=0||character.c!=0)throw std::runtime_error("sixth character mismatch");
 F one={1,0,0};
 if(encode(powf(character,6))!=encode(one)||encode(powf(character,3))==encode(one)||encode(powf(character,2))==encode(one))throw std::runtime_error("character order");
 F Bsrc={9,0,0},Btwist={18,9,0};
 Count src=count(Bsrc,squares),dst=count(Btwist,squares);
 if(src.points!=11092788ULL||dst.points!=11086129ULL)throw std::runtime_error("point counts mismatch");
 Count mutation=count({18,9,1},squares);
 if(mutation.points==dst.points)throw std::runtime_error("mutant was not distinguished");
 F y={72,131,189},x={1,0,0};
 if(encode(sqr(y))!=encode(add(cube(x),Btwist)))throw std::runtime_error("published point off curve");
 int basePoints=1;bool bs[P]={};for(int i=0;i<P;i++)bs[(i*i)%P]=true;
 for(int xx=0;xx<P;xx++){int v=(xx*xx*xx+9)%P;basePoints+=(v==0)?1:(bs[v]?2:0);}
 if(basePoints!=219)throw std::runtime_error("prime-field point count mismatch");
 printf("{\"schema\":\"ct168-complete-census-v1\",\"p\":223,\"field_size\":%d,\"x_enumerations_each\":%d,\"y_square_enumerations\":%d,\"source_prime_order\":%d,\"d_sixth_character\":%d,",Q,Q,Q,basePoints,character.a);
 print("source_cubic",src);printf(",");
 print("twist_cubic",dst);printf(",");
 print("mutated_twist",mutation);printf(",\"producer_standing\":\"pcc:unverified\"}\n");
}
