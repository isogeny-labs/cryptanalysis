
#include <cstdint>
#include <cstddef>
#include <algorithm>
template<unsigned P> static inline void strip(uint32_t *v, const uint32_t *odd){
 unsigned mask=0;
 for(unsigned j=0;j<32;++j)
   mask |= unsigned(odd[j]%P==0)<<j;
 while(mask){
   unsigned j=__builtin_ctz(mask);
   do {v[j]/=P;} while(v[j]%P==0);
   mask &= mask-1;
 }
}
extern "C" size_t m31_smooth211(uint32_t* xs,size_t n) {
 size_t kept=0;
 for(size_t i=0;i<n;i+=32){
   uint32_t v[32], odd[32];
   size_t count=std::min(size_t(32),n-i);
   for(unsigned j=0;j<32;++j){
     uint32_t x=j<count?xs[i+j]:0;
     uint32_t t=std::min(x,2147483647u-x);
     odd[j]=v[j]=t?t>>__builtin_ctz(t):1;
   }
   strip<3>(v,odd);
strip<5>(v,odd);
strip<7>(v,odd);
strip<11>(v,odd);
strip<13>(v,odd);
strip<17>(v,odd);
strip<19>(v,odd);
strip<23>(v,odd);
strip<29>(v,odd);
strip<31>(v,odd);
strip<37>(v,odd);
strip<41>(v,odd);
strip<43>(v,odd);
strip<47>(v,odd);
strip<53>(v,odd);
strip<59>(v,odd);
strip<61>(v,odd);
strip<67>(v,odd);
strip<71>(v,odd);
strip<73>(v,odd);
strip<79>(v,odd);
strip<83>(v,odd);
strip<89>(v,odd);
strip<97>(v,odd);
strip<101>(v,odd);
strip<103>(v,odd);
strip<107>(v,odd);
strip<109>(v,odd);
strip<113>(v,odd);
strip<127>(v,odd);
strip<131>(v,odd);
strip<137>(v,odd);
strip<139>(v,odd);
strip<149>(v,odd);
strip<151>(v,odd);
strip<157>(v,odd);
strip<163>(v,odd);
strip<167>(v,odd);
strip<173>(v,odd);
strip<179>(v,odd);
strip<181>(v,odd);
strip<191>(v,odd);
strip<193>(v,odd);
strip<197>(v,odd);
strip<199>(v,odd);
strip<211>(v,odd);
   for(unsigned j=0;j<count;++j)
     if(v[j]==1 && xs[i+j] && xs[i+j]!=2147483647u)xs[kept++]=xs[i+j];
 }
 return kept;
}
