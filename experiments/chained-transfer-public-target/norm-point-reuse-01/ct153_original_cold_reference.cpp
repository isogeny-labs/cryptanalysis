// CT153 source-only, public-Q complete DLP baseline for the independent CT152 original q223 source.
// No input scalar reaches solve_bsgs or solve_rho. [pcc:unverified]
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
using u64 = uint64_t;
static constexpr int p=223, c=3; 
static constexpr u64 ell=2773073, fq=(u64)p*p*p;
struct F { int a,b,d; bool operator==(F z)const{return a==z.a&&b==z.b&&d==z.d;} bool operator!=(F z)const{return !(*this==z);} };
static constexpr F zero{0,0,0},one{1,0,0};
static u64 fmult=0,finv=0,padd=0,pdouble=0;
static F add(F x,F y){return {(x.a+y.a)%p,(x.b+y.b)%p,(x.d+y.d)%p};}
static F sub(F x,F y){return {(x.a+p-y.a)%p,(x.b+p-y.b)%p,(x.d+p-y.d)%p};}
static F mul(F x,F y){
 ++fmult;
 // Explicit polynomial reduction of (a+bz+dz^2)*(e+fz+gz^2), z^3=3.
 return {(x.a*y.a+c*(x.b*y.d+x.d*y.b))%p,
 (x.a*y.b+x.b*y.a+c*x.d*y.d)%p,
 (x.a*y.d+x.b*y.b+x.d*y.a)%p};
}
static F fpow(F a,u64 n){ F out=one;while(n){if(n&1)out=mul(out,a);n>>=1;if(n)a=mul(a,a);}return out;}
static F inverse(F a){if(a==zero)throw std::runtime_error("zero field divisor");++finv;return fpow(a,fq-2);}
static constexpr F a2{127,56,199},a4{152,35,36},a6{212,109,150};
struct Pt{F x,y;bool inf;bool operator==(const Pt& z)const{return inf==z.inf&&(inf||(x==z.x&&y==z.y));}};
static const Pt O{zero,zero,true};
static const Pt G{{162,197,140},{45,11,207},false};
static F curve_rhs(F x){F x2=mul(x,x);return add(add(mul(x2,x),mul(a2,x2)),add(mul(a4,x),a6));}
static bool on(Pt P){return P.inf||mul(P.y,P.y)==curve_rhs(P.x);}
static Pt neg(Pt P){if(!P.inf)P.y=sub(zero,P.y);return P;}
static Pt plus(Pt A,Pt B){
 if(A.inf)return B;
 if(B.inf)return A;
 if(A.x==B.x&&add(A.y,B.y)==zero)return O;
 F slope;
 if(A.x==B.x){++pdouble;
  F x2=mul(A.x,A.x);F num=add(add(add(x2,x2),x2),add(mul(add(a2,a2),A.x),a4));
  slope=mul(num,inverse(add(A.y,A.y)));
 }else{++padd;slope=mul(sub(B.y,A.y),inverse(sub(B.x,A.x)));}
 F X=sub(sub(sub(mul(slope,slope),a2),A.x),B.x);
 F Y=sub(mul(slope,sub(A.x,X)),A.y);
 return {X,Y,false};
}
static Pt scalar(Pt P,u64 n){Pt r=O;while(n){if(n&1)r=plus(r,P);n>>=1;if(n)P=plus(P,P);}return r;}
static u64 fkey(F z){return z.a+(u64)p*(z.b+(u64)p*z.d);}
static u64 key(Pt P){return P.inf?std::numeric_limits<u64>::max():fkey(P.x)*fq+fkey(P.y);}
static bool point_bound(Pt P){return P.inf || (P.x.a>=0 && P.x.a<p && P.x.b>=0 && P.x.b<p && P.x.d>=0 && P.x.d<p && P.y.a>=0 && P.y.a<p && P.y.b>=0 && P.y.b<p && P.y.d>=0 && P.y.d<p);}
struct Result {u64 k, steps, restarts, table;};
static Result solve_bsgs(Pt generator,Pt public_point,u64 order){
 if(order!=ell || generator.inf || public_point.inf||!on(generator)||!on(public_point)
    || !scalar(generator,order).inf || !scalar(public_point,order).inf)
   throw std::runtime_error("invalid source prime-subgroup DLP instance");
 u64 m=1;while(m*m<order)++m;
 std::unordered_map<u64,u64> babies;babies.reserve(m*2);
 Pt cur=O;for(u64 j=0;j<m;j++){babies.emplace(key(cur),j);cur=plus(cur,generator);}
 Pt minus_stride=neg(scalar(generator,m));cur=public_point;
 for(u64 i=0;i<=m;i++){
  auto it=babies.find(key(cur));
  if(it!=babies.end()){
   u64 k=i*m+it->second;
   if(k<order && scalar(generator,k)==public_point)return {k,i+1,0,babies.size()};
  }
  cur=plus(cur,minus_stride);
 }
 throw std::runtime_error("BSGS has no verified source solution");
}
struct Walk {Pt p;u64 a,b;};
static Walk step(Walk w,Pt generator,Pt public_point,u64 n){
 int branch=(w.p.inf?0:(int)(fkey(w.p.x)%3));
 if(branch==0){w.p=plus(w.p,generator);w.a=(w.a+1)%n;}
 else if(branch==1){w.p=plus(w.p,public_point);w.b=(w.b+1)%n;}
 else{w.p=plus(w.p,w.p);w.a=2*w.a%n;w.b=2*w.b%n;}
 return w;
}
static u64 powmod(u64 a,u64 n,u64 modulus){u64 out=1;while(n){if(n&1)out=out*a%modulus;n>>=1;if(n)a=a*a%modulus;}return out;}
static Result solve_rho(Pt generator,Pt public_point,u64 order){
 if(order!=ell||generator.inf||public_point.inf||!on(generator)||!on(public_point)
    || !scalar(generator,order).inf || !scalar(public_point,order).inf)
   throw std::runtime_error("invalid source prime-subgroup DLP instance");
 u64 total=0;
 for(u64 restart=0;restart<12;restart++){
  u64 a=(restart*17+1)%order,b=(restart*127+7)%order;
  Walk init{plus(scalar(generator,a),scalar(public_point,b)),a,b};
  Walk tort=init,hare=init;
  for(u64 i=0;i<50000;i++){
   tort=step(tort,generator,public_point,order);
   hare=step(step(hare,generator,public_point,order),generator,public_point,order);
   total++;
   if(tort.p==hare.p){
    u64 numerator=(tort.a+order-hare.a)%order;
    u64 denominator=(hare.b+order-tort.b)%order;
    if(denominator){
     u64 k=numerator*powmod(denominator,order-2,order)%order;
     if(scalar(generator,k)==public_point)return {k,total,restart,0};
    }
    break;
   }
  }
 }
 throw std::runtime_error("rho exhausted 12 bounded restarts without valid source answer");
}
static void require(bool ok,const char* s){if(!ok)throw std::runtime_error(s);}
static long read_vmhwm(){
 std::ifstream stream("/proc/self/status");
 std::string line;
 while(std::getline(stream,line)){
  if(line.rfind("VmHWM:",0)==0){
   std::istringstream input(line.substr(6));
   long kb=-1;input>>kb;
   if(kb>0)return kb;
  }
 }
 throw std::runtime_error("Linux current-process VmHWM is required");
}
static bool wrong_source_coefficient_rejected(){
 // A6 -> A6+1 changes the RHS of every affine point; hardcoded fixture G is not on altered source.
 return mul(G.y,G.y)!=add(curve_rhs(G.x),one);
}
static bool wrong_point_rejected(){
 Pt bad=G;bad.y=add(bad.y,one);
 return !on(bad);
}
static bool wrong_order_rejected(){return !scalar(G,ell+1).inf;}
static Pt find_outside_subgroup(){
 // Quadratic Euler root (q^3 == 3 mod 4) on a few deterministic x-values.
 for(int j=0;j<512;j++){
  F x={j%p,(j/p)%p,0};F rhs=curve_rhs(x);
  F y=fpow(rhs,(fq+1)/4);
  if(mul(y,y)!=rhs)continue;
  Pt R{x,y,false};
  if(on(R)&&!scalar(R,ell).inf)return R;
 }
 throw std::runtime_error("negative-control nonsubgroup point not found within 512 x-values");
}
static int negative_test(){
 require(wrong_source_coefficient_rejected(),"source a6-mutation not caught");
 require(wrong_point_rejected(),"changed generator/public ordinate accepted");
 require(wrong_order_rejected(),"invalid subgroup order accepted");
 Pt R=find_outside_subgroup();
 bool rejected=false;
 try{(void)solve_bsgs(G,R,ell);}catch(const std::exception&){rejected=true;}
 require(rejected,"out-of-subgroup public not rejected");
 require(on(G)&&scalar(G,ell).inf,"real generator was altered");
 std::puts("{\"schema\":\"ct153-negative-controls/v1\",\"a6_mutation\":true,\"off_curve_generator\":true,\"wrong_order\":true,\"out_of_subgroup_public\":true}");
 return 0;
}
static u64 parse_scalar(const char* s){
 if(!s||!*s)throw std::runtime_error("missing scalar fixture");
 char* end=nullptr;auto n=std::strtoull(s,&end,10);
 if(*end||n==0||n>=ell)throw std::runtime_error("invalid fixture scalar");
 return n;
}
int main(int argc,char**argv){
 try{
  if(argc==2 && std::strcmp(argv[1],"--self-test-negative")==0)return negative_test();
  if(argc!=4||std::strcmp(argv[1],"--arm")!=0)throw std::runtime_error("usage: ct153 --arm bsgs|rho SCALAR_FIXTURE");
  std::string arm=argv[2];require(arm=="bsgs"||arm=="rho","unknown arm");
  u64 fixture=parse_scalar(argv[3]);
  auto process_start=std::chrono::steady_clock::now();
  require(fq==11089567&&on(G)&&scalar(G,ell).inf,"wrong frozen source generator, curve or subgroup order");
  Pt Q=scalar(G,fixture);
  require(!Q.inf&&on(Q)&&scalar(Q,ell).inf&&point_bound(Q),"invalid input public Q");
  fmult=finv=padd=pdouble=0;
  auto begin=std::chrono::steady_clock::now();
  Result answer=arm=="bsgs"?solve_bsgs(G,Q,ell):solve_rho(G,Q,ell);
  auto end=std::chrono::steady_clock::now();
  u64 solver_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count();
  u64 operations_field_mul=fmult, operations_field_inv=finv, operations_point_add=padd, operations_point_double=pdouble;
  require(answer.k==fixture && answer.k<ell && scalar(G,answer.k)==Q,"source answer mismatch");
  long vmhwm=read_vmhwm();
  u64 process_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-process_start).count();
  std::printf("{\"schema\":\"ct153-q223-source-cold/v1\",\"arm\":\"%s\",\"field\":223,\"degree\":3,\"subgroup_order\":%llu,\"source_full_order\":11092292,\"fixture\":%llu,\"source_public\":[[%d,%d,%d],[%d,%d,%d]],\"recovered\":%llu,\"verified\":true,\"solver_ns\":%llu,\"process_ns\":%llu,\"field_mul\":%llu,\"field_inv\":%llu,\"point_add\":%llu,\"point_double\":%llu,\"steps\":%llu,\"restarts\":%llu,\"table_entries\":%llu,\"peak_rss_kb\":%ld,\"standing\":\"pcc:unverified\"}\n",
   arm.c_str(),(unsigned long long)ell,(unsigned long long)fixture,Q.x.a,Q.x.b,Q.x.d,Q.y.a,Q.y.b,Q.y.d,(unsigned long long)answer.k,(unsigned long long)solver_ns,(unsigned long long)process_ns,(unsigned long long)operations_field_mul,(unsigned long long)operations_field_inv,(unsigned long long)operations_point_add,(unsigned long long)operations_point_double,(unsigned long long)answer.steps,(unsigned long long)answer.restarts,(unsigned long long)answer.table,vmhwm);
  return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"ct153 REJECTED: %s\n",e.what());return 2;}
}
