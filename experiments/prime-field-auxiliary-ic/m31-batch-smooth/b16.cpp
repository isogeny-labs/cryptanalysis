
#include <cstdint>
#include <cstddef>
#include <algorithm>
template<unsigned P> static inline void strip(uint32_t *v){
 unsigned mask=0;
 for(unsigned j=0;j<16;++j)
   mask |= unsigned(v[j]%P==0)<<j;
 while(mask){
   unsigned j=__builtin_ctz(mask);
   do {v[j]/=P;} while(v[j]%P==0);
   mask &= mask-1;
 }
}
extern "C" size_t m31_smooth211(uint32_t* xs,size_t n) {
 size_t kept=0;
 for(size_t i=0;i<n;i+=16){
   uint32_t v[16];
   size_t count=std::min(size_t(16),n-i);
   for(unsigned j=0;j<16;++j){
     uint32_t x=j<count?xs[i+j]:0;
     uint32_t t=std::min(x,2147483647u-x);
     v[j]=t?t>>__builtin_ctz(t):1;
   }
   strip<3>(v);
strip<5>(v);
strip<7>(v);
strip<11>(v);
strip<13>(v);
strip<17>(v);
strip<19>(v);
strip<23>(v);
strip<29>(v);
strip<31>(v);
strip<37>(v);
strip<41>(v);
strip<43>(v);
strip<47>(v);
strip<53>(v);
strip<59>(v);
strip<61>(v);
strip<67>(v);
strip<71>(v);
strip<73>(v);
strip<79>(v);
strip<83>(v);
strip<89>(v);
strip<97>(v);
strip<101>(v);
strip<103>(v);
strip<107>(v);
strip<109>(v);
strip<113>(v);
strip<127>(v);
strip<131>(v);
strip<137>(v);
strip<139>(v);
strip<149>(v);
strip<151>(v);
strip<157>(v);
strip<163>(v);
strip<167>(v);
strip<173>(v);
strip<179>(v);
strip<181>(v);
strip<191>(v);
strip<193>(v);
strip<197>(v);
strip<199>(v);
strip<211>(v);
   for(unsigned j=0;j<count;++j)
     if(v[j]==1 && xs[i+j] && xs[i+j]!=2147483647u)xs[kept++]=xs[i+j];
 }
 return kept;
}
