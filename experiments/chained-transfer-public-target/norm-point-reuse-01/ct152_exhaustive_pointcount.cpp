// CT152 independently enumerates #E(F223^3); no Rust/producer engine imports.
// Original q223 source reconstructed from Inst::search(223,1,200000).
// [pcc:unverified]. Protocol: CT152_SOURCE_POINTCOUNT_PROTOCOL.md.
#include <cstdint>
#include <cstdio>
#include <vector>
#include <chrono>
#include <cstdlib>
#include <algorithm>
#include <cstring>
#include <stdexcept>
// Independent cubic polynomial arithmetic F_223[t]/(t^3-3) via convolution.
struct F {int a[3];};
constexpr int Q=223, C=3;
constexpr int64_t SIZE=(int64_t)Q*Q*Q;
static inline F fmul(F x,F y) {
 int t[5]={0,0,0,0,0};
 for(int i=0;i<3;i++)for(int j=0;j<3;j++) t[i+j]+=x.a[i]*y.a[j];
 for(int i=4;i>=3;i--)t[i-3]+=C*t[i];
 return {{t[0]%Q,t[1]%Q,t[2]%Q}};
}
static inline F fadd(F x,F y){F z;for(int i=0;i<3;i++)z.a[i]=(x.a[i]+y.a[i])%Q;return z;}
static inline int enc(F x){return x.a[0]+Q*(x.a[1]+Q*x.a[2]);}
static inline bool zero(F x){return x.a[0]==0&&x.a[1]==0&&x.a[2]==0;}
int main(int argc,char** argv){
 if(argc>2 || (argc==2 && std::strcmp(argv[1], "--mutated-a6") != 0)) return 2;
 const bool mutation = argc==2;
 const F a2={{127,56,199}},a4={{152,35,36}},a6={{mutation?213:212,109,150}};
 auto start=std::chrono::steady_clock::now();
 std::vector<uint8_t> residues(SIZE,0);
 for(int z=0;z<SIZE;z++){
   F y={{z%Q,(z/Q)%Q,z/(Q*Q)}};
   residues[enc(fmul(y,y))]=1;
 }
 int64_t count=1,nzero=0,nsquare=0,nnonsquare=0;
 for(int z=0;z<SIZE;z++){
   F x={{z%Q,(z/Q)%Q,z/(Q*Q)}};
   F x2=fmul(x,x);
   F rhs=fadd(fadd(fmul(x,x2),fmul(a2,x2)),fadd(fmul(a4,x),a6));
   if(zero(rhs)) {count++;nzero++;}
   else if(residues[enc(rhs)]) {count+=2;nsquare++;}
   else nnonsquare++;
 }
 const auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
 const auto roster=std::count(residues.begin(),residues.end(),(uint8_t)1);
 const bool checks = nzero+nsquare+nnonsquare==SIZE && roster==(SIZE+1)/2 &&
                      count==1+nzero+2*nsquare;
 // Byte-stable integer record; time is diagnostic and stays on stderr.
 std::printf("{\"schema\":\"ct152-exhaustive-pointcount/v1\",\"field_size\":%lld,\"square_residue_roster\":%lld,\"zero_rhs\":%lld,\"nonzero_square_rhs\":%lld,\"nonsquare_rhs\":%lld,\"group_order\":%lld,\"mutation\":%s,\"invariants_valid\":%s}\n",
       (long long)SIZE,(long long)roster,(long long)nzero,(long long)nsquare,
       (long long)nnonsquare,(long long)count,mutation?"true":"false",checks?"true":"false");
 std::fprintf(stderr,"ct152 local elapsed_seconds=%.6f\n",elapsed);
 if(!checks) return 1;
 if(mutation) return count==11092292 ? 1 : 0; // negative control passes only if changed
 if(count!=11092292 || nzero!=3 || nsquare!=5546144 || nnonsquare!=5543420) return 1;
 return 0;
}
