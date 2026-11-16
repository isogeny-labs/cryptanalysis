// CT155: original q223 source only. Bounded projective/batch-inversion BSGS.
// Complete public-Q log recovery, never a transferred Jacobian solve. [pcc:unverified]
#define main ct153_legacy_entry_not_called
#include "ct153_original_cold_reference.cpp"
#undef main
#include <vector>
#include <cerrno>
#include <climits>
#include <array>

// Translate y^2=x^3+a2*x^2+a4*x+a6 to x'=x+a2/3.
// Use ordinary short Weierstrass Jacobian X/Z^2,Y/Z^3.
static F shift_x(){return mul(a2,{149,0,0});} // 3*149=1 mod 223
static F curve_A(){F sh=shift_x();return sub(a4,mul(a2,sh));}
struct JP{F X,Y,Z;bool inf;};
static JP jp0(){return {zero,one,zero,true};}
static JP to_j(Pt P){if(P.inf)return jp0();return {add(P.x,shift_x()),P.y,one,false};}
static F dbl(F x){return add(x,x);}
static F triple(F x){return add(dbl(x),x);}
static JP jdouble(JP P){
 if(P.inf||P.Y==zero)return jp0();
 ++pdouble;
 F A=mul(P.X,P.X), B=mul(P.Y,P.Y), C=mul(B,B);
 F D=dbl(sub(sub(mul(add(P.X,B),add(P.X,B)),A),C));
 F Z2=mul(P.Z,P.Z);F Z4=mul(Z2,Z2);
 F E=add(triple(A),mul(curve_A(),Z4));F F2=mul(E,E);
 F X3=sub(F2,dbl(D));
 F Y3=sub(mul(E,sub(D,X3)),dbl(dbl(dbl(C))));
 F Z3=dbl(mul(P.Y,P.Z));
 return {X3,Y3,Z3,false};
}
static JP jmix(JP P,Pt Q){
 if(Q.inf)return P;
 if(P.inf)return {Q.x,Q.y,one,false};
 // Q is in SHORT coordinates here, no further x-shift.
 F Z2=mul(P.Z,P.Z),U2=mul(Q.x,Z2),S2=mul(Q.y,mul(P.Z,Z2));
 F H=sub(U2,P.X),R=sub(S2,P.Y);
 if(H==zero){if(R==zero)return jdouble(P);return jp0();}
 ++padd;
 F HH=mul(H,H),HHH=mul(HH,H),V=mul(P.X,HH);
 F X3=sub(sub(mul(R,R),HHH),dbl(V));
 F Y3=sub(mul(R,sub(V,X3)),mul(P.Y,HHH));
 F Z3=mul(P.Z,H);
 return {X3,Y3,Z3,false};
}
static Pt short_affine(Pt P){if(!P.inf)P.x=add(P.x,shift_x());return P;}
// One inverse for arbitrarily many non-infinity Z's, with explicit prefix/back sweep.
static std::vector<Pt> normalize_batch(const std::vector<JP>& a){
 std::vector<F> pref(a.size());F product=one;
 for(size_t i=0;i<a.size();i++){
  pref[i]=product;
  if(!a[i].inf){if(a[i].Z==zero)throw std::runtime_error("nonidentity zero Z");product=mul(product,a[i].Z);}
 }
 F invproduct=inverse(product);
 std::vector<Pt> out(a.size(),O);
 for(size_t j=a.size();j>0;j--){size_t i=j-1;
  if(a[i].inf)continue;
  F zi=mul(invproduct,pref[i]);invproduct=mul(invproduct,a[i].Z);
  F zi2=mul(zi,zi),zi3=mul(zi2,zi);
  out[i]={sub(mul(a[i].X,zi2),shift_x()),mul(a[i].Y,zi3),false};
 }
 if(invproduct!=one)throw std::runtime_error("batch normalization product failed");
 return out;
}
static Result solve_projective_bsgs(Pt Q){
 if(Q.inf||!on(Q)||!point_bound(Q)||!scalar(Q,ell).inf||!on(G)||!scalar(G,ell).inf)
  throw std::runtime_error("invalid source DLP input");
 u64 m=1;while(m*m<ell)++m;
 Pt gs=short_affine(G);
 std::vector<JP> bj;bj.reserve(m);JP cur=jp0();
 for(u64 j=0;j<m;j++){bj.push_back(cur);cur=jmix(cur,gs);}
 std::vector<Pt> ba=normalize_batch(bj);
 std::unordered_map<u64,u64> babies;babies.reserve(m*2);
 for(u64 j=0;j<m;j++){
   if(!on(ba[j]))throw std::runtime_error("normalized baby off curve");
   if(!babies.emplace(key(ba[j]),j).second)throw std::runtime_error("baby collision before subgroup order");
 }
 Pt stride=short_affine(neg(scalar(G,m)));
 cur=to_j(Q);u64 processed=0;
 constexpr u64 BATCH=64;
 for(u64 i=0;i<=m;){
  std::vector<JP> batch;batch.reserve(BATCH);
  u64 len=std::min(BATCH,m+1-i);
  for(u64 z=0;z<len;z++){batch.push_back(cur);cur=jmix(cur,stride);}
  std::vector<Pt> ga=normalize_batch(batch);
  for(u64 z=0;z<len;z++){
   ++processed;
   auto match=babies.find(key(ga[z]));
   if(match!=babies.end()){
    u64 k=(i+z)*m+match->second;
    if(k<ell&&scalar(G,k)==Q)return {k,processed,0,babies.size()};
   }
  }
  i+=len;
 }
 throw std::runtime_error("projective BSGS no verified solution");
}
static int coord(const char* s){
 if(!s||!*s||*s=='-'||*s=='+')throw std::runtime_error("noncanonical coordinate");
 char* end=nullptr;errno=0;unsigned long v=std::strtoul(s,&end,10);
 if(errno||*end||v>=p)throw std::runtime_error("coordinate out of F223 range");
 return (int)v;
}
static void selftest(){
 require(on(G)&&scalar(G,ell).inf,"base source invalid");
 for(u64 n:{0ULL,1ULL,2ULL,3ULL,5ULL,13ULL,64ULL,255ULL,1666ULL,2773072ULL}){
  JP j=jp0();Pt gshort=short_affine(G);
  for(u64 a=0;a<n;a++)j=jmix(j,gshort);
  auto check=normalize_batch({j})[0];
  if(!(check==scalar(G,n)))throw std::runtime_error("projective coordinate mismatch");
 }
 Pt gshort=short_affine(G);
 if(!normalize_batch({jmix(to_j(G),gshort)})[0].operator==(scalar(G,2)))
   throw std::runtime_error("H=0 doubling branch failed");
 if(!jmix(to_j(G),short_affine(neg(G))).inf)throw std::runtime_error("H=0 inverse branch failed");
 for(u64 n:{1ULL,17ULL,12345ULL,159273ULL,2300011ULL,2773072ULL}){
  Pt Q=scalar(G,n);
  if(solve_projective_bsgs(Q).k!=n)throw std::runtime_error("public target DLP failed");
 }
 std::puts("{\"schema\":\"ct155-test/v1\",\"jacobian_cases\":10,\"public_dlp_cases\":6,\"result\":\"pass\",\"standing\":\"pcc:unverified\"}");
}
int main(int argc,char**argv){
 try{
  if(argc==2&&std::strcmp(argv[1],"--self-test")==0){selftest();return 0;}
  if(argc!=7)throw std::runtime_error("usage: ct155 x0 x1 x2 y0 y1 y2 (public point only)");
  auto beginproc=std::chrono::steady_clock::now();
  Pt Q{{coord(argv[1]),coord(argv[2]),coord(argv[3])},{coord(argv[4]),coord(argv[5]),coord(argv[6])},false};
  require(on(Q)&&scalar(Q,ell).inf&&!Q.inf,"invalid public target");
  fmult=finv=padd=pdouble=0;
  auto begin=std::chrono::steady_clock::now();Result r=solve_projective_bsgs(Q);
  auto end=std::chrono::steady_clock::now();
  u64 ns=std::chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count();
  u64 fm=fmult,fi=finv,pa=padd,pd=pdouble;
  require(r.k<ell&&scalar(G,r.k)==Q,"invalid recovered log");
  auto wall=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-beginproc).count();
  std::printf("{\"schema\":\"ct155-q223-public-point/v1\",\"arm\":\"projective-bsgs\",\"source_public\":[[%d,%d,%d],[%d,%d,%d]],\"recovered\":%llu,\"solver_ns\":%llu,\"process_ns\":%llu,\"field_mul\":%llu,\"field_inv\":%llu,\"point_add\":%llu,\"point_double\":%llu,\"steps\":%llu,\"table_entries\":%llu,\"peak_rss_kb\":%ld,\"standing\":\"pcc:unverified\"}\n",Q.x.a,Q.x.b,Q.x.d,Q.y.a,Q.y.b,Q.y.d,(unsigned long long)r.k,(unsigned long long)ns,(unsigned long long)wall,(unsigned long long)fm,(unsigned long long)fi,(unsigned long long)pa,(unsigned long long)pd,(unsigned long long)r.steps,(unsigned long long)r.table,read_vmhwm());
  return 0;
 }catch(const std::exception &e){std::fprintf(stderr,"ct155 REJECTED: %s\n",e.what());return 2;}
}
