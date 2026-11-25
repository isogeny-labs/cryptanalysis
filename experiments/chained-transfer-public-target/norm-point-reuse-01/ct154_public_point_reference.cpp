// CT154: point-only cold source ECDLP runner; reuses the exact CT153 arithmetic.
// No scalar fixture is accepted by this executable. All results are [pcc:unverified].
#define main ct153_legacy_entry_not_called
#include "ct153_original_cold_reference.cpp"
#undef main
#include <array>
#include <cerrno>
#include <climits>

static int parse_coord(const char* s) {
 if(!s||!*s||*s=='-'||*s=='+')throw std::runtime_error("coordinate is not canonical decimal");
 char* end=nullptr; errno=0;
 unsigned long z=std::strtoul(s,&end,10);
 if(errno||*end||z>=static_cast<unsigned long>(p))throw std::runtime_error("coordinate outside canonical F223");
 return static_cast<int>(z);
}
static void canon(Walk& w,u64 n){
 if(w.p.inf)return;
 F minus_y=sub(zero,w.p.y);
 if(fkey(minus_y)<fkey(w.p.y)) {
  w.p.y=minus_y;
  w.a=(n-w.a)%n;w.b=(n-w.b)%n;
 }
}
static Walk seed_walk(Pt Q,u64 restart){
 u64 a=(restart*3191+12345)%ell,b=(restart*5701+17)%ell;
 Walk w{plus(scalar(G,a),scalar(Q,b)),a,b};canon(w,ell);
 return w;
}
struct Jump {Pt P;u64 a,b;};
static u64 mix64(u64 x){
 x+=0x9e3779b97f4a7c15ULL;
 x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;
 x=(x^(x>>27))*0x94d049bb133111ebULL;
 return x^(x>>31);
}
static std::array<Jump,16> jumps_for(Pt Q,u64 restart){
 std::array<Jump,16> js{};
 for(unsigned j=0;j<16;j++){
  // Explicit deterministic nonzero coefficients; model-specific seed, never fixture-dependent.
  u64 a=mix64(0x151701ULL+9973*restart+2*j)%ell;
  u64 b=mix64(0x151701ULL+9973*restart+2*j+1)%ell;
  if(a==0&&b==0)a=1;
  js[j]={plus(scalar(G,a),scalar(Q,b)),a,b};
 }
 return js;
}
static Walk rstep(Walk w,const std::array<Jump,16>& js){
 const unsigned branch=w.p.inf?0u:static_cast<unsigned>(fkey(w.p.x)&15u);
 if(branch==0u){ // deliberate mixed doubling to limit short fruitless cycles
  w.p=plus(w.p,w.p);w.a=2*w.a%ell;w.b=2*w.b%ell;
 }else{
  const Jump& z=js[branch];
  Walk try_add=w;
  try_add.p=plus(w.p,z.P);
  try_add.a=(w.a+z.a)%ell;try_add.b=(w.b+z.b)%ell;
  canon(try_add,ell);
  // A same-partition re-entry after negation often creates an exact 2-cycle.
  // Break that edge deterministically with doubling instead (Bos--Kleinjung--Lenstra).
  const unsigned next_branch=try_add.p.inf?0u:static_cast<unsigned>(fkey(try_add.p.x)&15u);
  if(next_branch==branch){
   w.p=plus(w.p,w.p);w.a=2*w.a%ell;w.b=2*w.b%ell;
  }else return try_add;
 }
 canon(w,ell);return w;
}
static Result solve_neg_rho(Pt Q){
 if(Q.inf||!point_bound(Q)||!on(Q)||!scalar(Q,ell).inf)
   throw std::runtime_error("public Q is invalid or outside source prime subgroup");
 u64 steps=0;
 for(u64 restart=0;restart<40;restart++){
  auto jumps=jumps_for(Q,restart);
  Walk slow=seed_walk(Q,restart),fast=slow;
  for(u64 i=0;i<20000;i++){
   slow=rstep(slow,jumps);fast=rstep(rstep(fast,jumps),jumps);steps++;
   if(slow.p==fast.p){
    u64 den=(fast.b+ell-slow.b)%ell;
    if(den){
     u64 num=(slow.a+ell-fast.a)%ell;
     u64 log=num*powmod(den,ell-2,ell)%ell;
     if(scalar(G,log)==Q)return {log,steps,restart,0};
    }
    break; // fruitless collision: fresh table and seed
   }
  }
 }
 throw std::runtime_error("negation rho exhausted bounded restarts without a verified logarithm");
}
static void check_relations(){
 for(u64 k: {1ULL,17ULL,12345ULL,159273ULL,2300011ULL,2773072ULL}){
  Pt Q=scalar(G,k);
  Walk w=seed_walk(Q,1);
  auto jumps=jumps_for(Q,1);
  for(int i=0;i<50;i++){
   require(w.p==plus(scalar(G,w.a),scalar(Q,w.b)),"r-adding invariant failed");
   w=rstep(w,jumps);
  }
  require(solve_bsgs(G,Q,ell).k==k,"BSGS public-point failure");
  require(solve_neg_rho(Q).k==k,"negation rho public-point failure");
 }
}
int main(int argc,char** argv){
 try{
  if(argc==2 && std::strcmp(argv[1],"--self-test")==0){check_relations();std::puts("{\"schema\":\"ct154-self-test/v1\",\"public_cases\":6,\"walk_invariant\":true,\"complete_solve\":true}");return 0;}
  if(argc!=9||std::strcmp(argv[1],"--arm")!=0)
    throw std::runtime_error("usage: ct154 --arm bsgs|rho|neg-rho x0 x1 x2 y0 y1 y2");
  std::string arm=argv[2];
  if(arm!="bsgs"&&arm!="rho"&&arm!="neg-rho")throw std::runtime_error("unknown solve arm");
  auto start=std::chrono::steady_clock::now();
  Pt Q{{parse_coord(argv[3]),parse_coord(argv[4]),parse_coord(argv[5])},
       {parse_coord(argv[6]),parse_coord(argv[7]),parse_coord(argv[8])},false};
  if(!on(G)||!scalar(G,ell).inf||!on(Q)||!scalar(Q,ell).inf)
    throw std::runtime_error("public source model, generator, point or subgroup invalid");
  fmult=finv=padd=pdouble=0;
  auto begin=std::chrono::steady_clock::now();
  Result answer=arm=="bsgs"?solve_bsgs(G,Q,ell):arm=="rho"?solve_rho(G,Q,ell):solve_neg_rho(Q);
  auto end=std::chrono::steady_clock::now();
  u64 solver_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count();
  u64 fm=fmult,fi=finv,pa=padd,pd=pdouble;
  require(answer.k<ell&&scalar(G,answer.k)==Q,"unverified output");
  long rss=read_vmhwm();
  u64 elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();
  std::printf("{\"schema\":\"ct154-q223-public-point/v1\",\"arm\":\"%s\",\"field\":223,\"degree\":3,\"subgroup_order\":2773073,\"source_public\":[[%d,%d,%d],[%d,%d,%d]],\"recovered\":%llu,\"verified\":true,\"solver_ns\":%llu,\"process_ns\":%llu,\"field_mul\":%llu,\"field_inv\":%llu,\"point_add\":%llu,\"point_double\":%llu,\"steps\":%llu,\"restarts\":%llu,\"table_entries\":%llu,\"peak_rss_kb\":%ld,\"standing\":\"pcc:unverified\"}\n",
    arm.c_str(),Q.x.a,Q.x.b,Q.x.d,Q.y.a,Q.y.b,Q.y.d,(unsigned long long)answer.k,
    (unsigned long long)solver_ns,(unsigned long long)elapsed,(unsigned long long)fm,(unsigned long long)fi,(unsigned long long)pa,(unsigned long long)pd,
    (unsigned long long)answer.steps,(unsigned long long)answer.restarts,(unsigned long long)answer.table,rss);
  return 0;
 }catch(const std::exception& e){std::fprintf(stderr,"ct154 REJECTED: %s\n",e.what());return 2;}
}
