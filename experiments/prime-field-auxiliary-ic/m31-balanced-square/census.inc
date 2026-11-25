// Compiled after the existing native NEON character evaluators.
enum class Fold { minimum, signedFold };

template<Fold fold> Vec nextSquare(Vec u) {
  auto x = vreinterpretq_s32_u32(u);
  Vec lo = vmulq_u32(u,u);
  Vec hi = vreinterpretq_u32_s32(vqdmulhq_s32(x,x));
  Vec p = vdupq_n_u32(prime);
  if constexpr (fold == Fold::signedFold)
    return vsubq_u32(hi,vbicq_u32(p,lo));
  Vec sum = vaddq_u32(hi,vandq_u32(p,lo));
  return vminq_u32(sum,vsubq_u32(sum,p));
}

template<bool projected,Fold fold>
void classify(const std::vector<Word>& x,std::vector<Word>& out,const Tables* table) {
  Vec p=vdupq_n_u32(prime);
  for (size_t i=0;i<x.size();i+=32) {
    Vec a[8],b[8];
    for (int j=0;j<8;++j) a[j]=b[j]=vld1q_u32(x.data()+i+4*j);
    for (int t=0;t<(projected?15:30);++t)
      for (auto& v:b) v=nextSquare<fold>(v);
    for (int j=0;j<8;++j) {
      auto v=b[j];
      if constexpr (fold==Fold::signedFold)
        v=vaddq_u32(v,vandq_u32(p,vcltzq_s32(vreinterpretq_s32_u32(v))));
      if constexpr (projected) {
        auto hi=vreinterpretq_u32_s32(vqdmulhq_s32(vreinterpretq_s32_u32(a[j]),vreinterpretq_s32_u32(v)));
        auto s=vaddq_u32(hi,vandq_u32(p,vmulq_u32(a[j],v)));
        Word lanes[4];
        vst1q_u32(lanes,vminq_u32(s,vsubq_u32(s,p)));
        for (int k=0;k<4;++k) out[i+4*j+k]=table->get(lanes[k]);
      } else vst1q_u32(out.data()+i+4*j,vshrq_n_u32(vceqq_u32(a[j],v),31));
    }
  }
}

std::vector<Word> census(int arm, const Tables& unusedDirectTable, unsigned& count) {
  std::vector<Word> rhs{1};
  for (Word q:{2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89}) {
    size_t stop=rhs.size();
    for (size_t i=0;i<stop;++i)
      for (uint64_t x=uint64_t(rhs[i])*q;x<prime;x*=q) rhs.push_back(Word(x));
  }
  for (auto& x:rhs) {
    uint64_t sq=uint64_t(x)*x%prime;
    x=(sq*x+2ULL*x+14)%prime;
  }
  size_t n=rhs.size();
  rhs.resize((n+31)/32*32,1);
  std::vector<Word> out(rhs.size());
  if (arm<3) {
    if (arm==0) eval<false>(rhs,out,unusedDirectTable);
    if (arm==1) classify<false,Fold::minimum>(rhs,out,nullptr);
    if (arm==2) classify<false,Fold::signedFold>(rhs,out,nullptr);
  } else {
    Tables table;
    if (arm==3) eval<true>(rhs,out,table);
    if (arm==4) classify<true,Fold::minimum>(rhs,out,&table);
    if (arm==5) classify<true,Fold::signedFold>(rhs,out,&table);
  }
  out.resize(n);
  count=std::accumulate(out.begin(),out.end(),0u);
  return out;
}

int main() {
  Tables unused;
  unsigned count=0;
  auto reference=census(0,unused,count);
  if (reference.size()!=3846525 || count!=1924024) return 1;
  std::puts("round,position,arm,ms,coordinates,lifts");
  const int order[]={0,1,5,2,4,3};
  for (int r=0;r<6;++r) for (int i=0;i<6;++i) {
    int arm=(order[i]+r)%6;
    auto start=std::chrono::steady_clock::now();
    auto result=census(arm,unused,count);
    double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    if (result!=reference || count!=1924024) return 2;
    std::printf("%d,%d,%d,%.6f,%zu,%u\n",r,i,arm,ms,result.size(),count);
  }
}
