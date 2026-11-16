// CT156: source-only x-quotient/negation BSGS for fixed cubic q223 subgroup.
// Public-Q only; no Jacobian transfer or prime-field attack. [pcc:unverified]
#define main ct153_original_entry_not_called
#include "ct153_original_cold_reference.cpp"
#undef main
#include <vector>
#include <cerrno>
#include <climits>
#include <array>
// Jacobian arithmetic below is reused from the CT155 source comparator.
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
static int coord(const char* s){
 if(!s||!*s||*s=='-'||*s=='+')throw std::runtime_error("noncanonical coordinate");
 char* end=nullptr;errno=0;unsigned long v=std::strtoul(s,&end,10);
 if(errno||*end||v>=p)throw std::runtime_error("coordinate out of F223 range");
 return (int)v;
}
// Normalize only X/Z^2: the x-coordinate identifies {P,-P}.
// The full source point is independently recomputed for every proposed log.
static std::vector<u64> batch_xkeys(const std::vector<JP>& points){
 std::vector<F> pref(points.size());F product=one;
 for(size_t i=0;i<points.size();++i){
  pref[i]=product;
  if(!points[i].inf){
   if(points[i].Z==zero)throw std::runtime_error("nonidentity zero Z");
   product=mul(product,points[i].Z);
  }
 }
 F running=inverse(product);
 std::vector<u64> out(points.size(),std::numeric_limits<u64>::max());
 for(size_t j=points.size();j>0;--j){size_t i=j-1;
  if(points[i].inf)continue;
  F zi=mul(running,pref[i]);running=mul(running,points[i].Z);
  F x=sub(mul(points[i].X,mul(zi,zi)),shift_x());
  out[i]=fkey(x);
 }
 if(running!=one)throw std::runtime_error("invalid field inverse batch");
 return out;
}
static Result solve_negation_bsgs(Pt Q){
 if(Q.inf||!on(Q)||!point_bound(Q)||!scalar(Q,ell).inf||!on(G)||!scalar(G,ell).inf)
  throw std::runtime_error("invalid source DLP input");
 // If the baby table holds jG for 0<=j<=m, each giant offset 2m*i
 // covers BOTH positive and negative deviations from that offset.
 u64 m=1;while(2*m*m<ell)++m;
 std::vector<JP> baby_points;baby_points.reserve(m+1);
 JP cur=jp0();Pt gs=short_affine(G);
 for(u64 j=0;j<=m;++j){baby_points.push_back(cur);cur=jmix(cur,gs);}
 std::vector<u64> baby_keys=batch_xkeys(baby_points);
 std::unordered_map<u64,u64> babies;babies.reserve(2*(m+1));
 for(u64 j=0;j<=m;++j){
  if(!babies.emplace(baby_keys[j],j).second)throw std::runtime_error("baby x collision");
 }
 Pt minus_stride=short_affine(neg(scalar(G,2*m)));
 cur=to_j(Q);
 constexpr u64 BATCH=64;
 u64 bound=(ell+m)/(2*m)+1,seen=0;
 for(u64 i=0;i<=bound;){
  u64 len=std::min(BATCH,bound+1-i);
  std::vector<JP> batch;batch.reserve(len);
  for(u64 j=0;j<len;++j){batch.push_back(cur);cur=jmix(cur,minus_stride);}
  std::vector<u64> keys=batch_xkeys(batch);
  for(u64 j=0;j<len;++j){
   ++seen;auto it=babies.find(keys[j]);if(it==babies.end())continue;
   u64 offset=((i+j)*2*m)%ell,k=it->second;
   // The x match alone does NOT choose the sign. Verify actual source Q.
   u64 plus_candidate=(offset+k)%ell;
   if(scalar(G,plus_candidate)==Q)return {plus_candidate,seen,0,babies.size()};
   if(k){u64 minus_candidate=(offset+ell-k)%ell;
    if(scalar(G,minus_candidate)==Q)return {minus_candidate,seen,0,babies.size()};}
  }
  i+=len;
 }
 throw std::runtime_error("negation BSGS no verified solution");
}
static int ct156_selftest(){
 require(on(G)&&scalar(G,ell).inf,"source generator mismatch");
 for(u64 k:{1ULL,2ULL,3ULL,5ULL,13ULL,64ULL,255ULL,1177ULL,1178ULL,1179ULL,
             2355ULL,2356ULL,2357ULL,2773072ULL,2773071ULL,2773070ULL}){
  Pt Q=scalar(G,k);
  if(solve_negation_bsgs(Q).k!=k)throw std::runtime_error("signed giant-step recovery failed");
 }
 // Verify the x quotient equality on positive/negative and reject a changed y.
 if(fkey(G.x)!=fkey(neg(G).x)||neg(G).y==G.y)throw std::runtime_error("bad sign quotient");
 if(!wrong_source_coefficient_rejected()||!wrong_point_rejected()||!wrong_order_rejected())
  throw std::runtime_error("source-mutation controls invalid");
 std::printf("{\"schema\":\"ct156-self-test/v1\",\"public_dlps\":16,\"quotient_sign_control\":true,\"source_mutations\":3,\"result\":\"pass\",\"standing\":\"pcc:unverified\"}\n");
 return 0;
}
int main(int argc,char**argv){
 try{
  if(argc==2&&std::strcmp(argv[1],"--self-test")==0)return ct156_selftest();
  if(argc!=7)throw std::runtime_error("usage: ct156 x0 x1 x2 y0 y1 y2 (public Q)");
  auto process_start=std::chrono::steady_clock::now();
  Pt Q{{coord(argv[1]),coord(argv[2]),coord(argv[3])},{coord(argv[4]),coord(argv[5]),coord(argv[6])},false};
  require(on(Q)&&scalar(Q,ell).inf&&!Q.inf,"invalid public target");
  fmult=finv=padd=pdouble=0;
  auto solve_start=std::chrono::steady_clock::now();Result r=solve_negation_bsgs(Q);
  auto solver_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-solve_start).count();
  u64 fm=fmult,fi=finv,pa=padd,pd=pdouble;
  require(r.k<ell&&scalar(G,r.k)==Q,"recovered scalar mismatch");
  auto process_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-process_start).count();
  std::printf("{\"schema\":\"ct156-q223-public-point/v1\",\"arm\":\"negation-x-bsgs\",\"source_public\":[[%d,%d,%d],[%d,%d,%d]],\"recovered\":%llu,\"solver_ns\":%llu,\"process_ns\":%llu,\"field_mul\":%llu,\"field_inv\":%llu,\"point_add\":%llu,\"point_double\":%llu,\"steps\":%llu,\"table_entries\":%llu,\"peak_rss_kb\":%ld,\"standing\":\"pcc:unverified\"}\n",Q.x.a,Q.x.b,Q.x.d,Q.y.a,Q.y.b,Q.y.d,(unsigned long long)r.k,(unsigned long long)solver_ns,(unsigned long long)process_ns,(unsigned long long)fm,(unsigned long long)fi,(unsigned long long)pa,(unsigned long long)pd,(unsigned long long)r.steps,(unsigned long long)r.table,read_vmhwm());
  return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"ct156 REJECTED: %s\n",e.what());return 2;}
}
