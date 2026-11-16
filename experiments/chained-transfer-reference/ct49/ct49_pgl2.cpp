// CT49 exhaustive PGL2(F101) sextic equivalence audit.
// Tests polynomial equivalence up to any nonzero scale, a stronger exclusion
// than hyperelliptic F101 isomorphism (which needs a square scale).
// No curve-isomorphism tables, Magma, Sage or native producer used.
#include <array>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
using namespace std;
constexpr int p=101;
int m(int x){x%=p;return x<0?x+p:x;}
int pw(int b,int n){int r=1;for(;n;n/=2,b=m(b*b))if(n&1)r=m(r*b);return r;}
void check(bool b,const char* error){if(!b){fprintf(stderr,"FAIL: %s\n",error);exit(1);}}
using F=array<int,7>;
struct Model{string name; F f;};
const vector<Model> old={
 {"T0",{31,75,74,54,71,55,1}},
 {"T1",{95,26,19,27,94,91,1}},
 {"T2",{95,93,43,39,92,17,1}}
};
const vector<Model> target={
 {"Cpi1_R",{46,8,49,99,4,78,54}},
 {"Cpi2_R",{77,81,100,16,0,40,71}},
 {"C10_R",{49,17,85,87,33,9,10}},
 {"C20_R",{25,98,69,38,52,39,76}}
};
int hom(const F& f,int u,int v){
 int up[7],vp[7];up[0]=vp[0]=1;
 for(int i=1;i<7;i++){up[i]=m(up[i-1]*u);vp[i]=m(vp[i-1]*v);}
 int z=0;for(int i=0;i<7;i++)z=m(z+f[i]*up[i]*vp[6-i]);return z;
}
struct Result {long tested=0,eq=0,sq=0,nonsq=0;};
Result classify(const Model& src,const Model& dest){
 // Seven distinct points on P^1(F101) determine a homogeneous sextic.
 const int t[7]={0,1,-1,2,-2,3,-3};
 int map[101][101];
 for(int u=0;u<p;u++)for(int v=0;v<p;v++)map[u][v]=hom(src.f,u,v);
 int hv[7];for(int k=0;k<7;k++)hv[k]=hom(dest.f,m(t[k]),1);
 check(hv[0]!=0,"target has zero constant: normalization needs new point");
 int h0inv=pw(hv[0],p-2);
 Result out;
 auto attempt=[&](int a,int b,int c,int d){
  ++out.tested;
  int lambda=m(map[b][d]*h0inv);
  if(lambda==0)return;
  if(map[m(a+b)][m(c+d)]!=m(lambda*hv[1]))return;
  if(map[m(b-a)][m(d-c)]!=m(lambda*hv[2]))return;
  for(int k=3;k<7;k++)
   if(map[m(a*t[k]+b)][m(c*t[k]+d)]!=m(lambda*hv[k]))return;
  ++out.eq;
  if(pw(lambda,(p-1)/2)==1)++out.sq;else ++out.nonsq;
 };
 // Every PGL2 class has a unique matrix normalization with either
 // c=1, or c=0,d=1. Determinant != 0 is required.
 for(int a=0;a<p;a++)for(int b=0;b<p;b++)for(int d=0;d<p;d++)
  if(m(a*d-b)!=0)attempt(a,b,1,d);
 for(int a=1;a<p;a++)for(int b=0;b<p;b++)attempt(a,b,0,1);
 check(out.tested==long((p+1)*p*(p-1)),"PGL2 count wrong");
 check(out.eq==out.sq+out.nonsq,"scale count wrong");
 return out;
}
int main(){
 // Positive control: identical curve (identity matrix must be found).
 Result self=classify(old[0],old[0]);
 check(self.eq>0 && self.sq>0,"self isomorphism not detected");
 // Positive control: the -x partner of the first Richelot target.
 F neg=target[0].f;for(int i=1;i<7;i+=2)neg[i]=m(-neg[i]);
 Result mirror=classify(target[0],{"Cpi1_mirror",neg});
 check(mirror.eq>0 && mirror.sq>0,"x -> -x isomorphism not detected");
 // Negative control: deliberate change of source sextic constant term.
 F mutant=old[0].f;mutant[0]=37;
 Result deliberate=classify(old[0],{"T0_constant37",mutant});
 check(deliberate.eq==0,"deliberately perturbed sextic unexpectedly equivalent");
 printf("Controls: self %ld / mirrored %ld PGL2 matches, mutant %ld\n",self.eq,mirror.eq,deliberate.eq);
 long sum=0;
 for(const auto& src:old)for(const auto& dest:target){
  Result result=classify(src,dest);sum+=result.eq;
  printf("%s vs %s: %ld of %ld PGL2 equivalences (square %ld, nonsquare %ld)\n",src.name.c_str(),dest.name.c_str(),result.eq,result.tested,result.sq,result.nonsq);
 }
 check(sum==0,"unexpected old-T and new-target PGL2 equivalence");
 long mutual=0;
 for(size_t i=0;i<target.size();i++)for(size_t j=i+1;j<target.size();j++){
  Result result=classify(target[i],target[j]);mutual+=result.eq;
  printf("%s vs %s: %ld PGL2 equivalences\n",target[i].name.c_str(),target[j].name.c_str(),result.eq);
 }
 check(mutual==0,"unexpected Richelot target equivalence");
 printf("PASS C++: 12 old-versus-new and six pairwise-new pairs, exhaustive 1030200 PGL2 each; 3 controls\n");
}
