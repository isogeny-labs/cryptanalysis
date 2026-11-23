#include <ctime>
constexpr Word factors[]={2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89};
template<bool prune> std::vector<Word> generate() {
  std::vector<Word> all{1}, live;
  if constexpr (prune) live.push_back(1);
  for (auto q:factors) {
    if constexpr (prune) {
      const auto limit=(prime-1)/q;
      live.erase(std::remove_if(live.begin(),live.end(),[&](Word x){return x>limit;}),live.end());
      auto stop=live.size();
      for (size_t i=0;i<stop;++i) {
        for (uint64_t y=uint64_t(live[i])*q;y<prime;y*=q) {
          all.push_back(y);
          if (y<=limit) live.push_back(y);
        }
      }
    } else {
      const auto stop=all.size();
      for (size_t i=0;i<stop;++i)
        for (uint64_t y=uint64_t(all[i])*q;y<prime;y*=q) all.push_back(y);
    }
  }
  return all;
}

Vec reduceOnce(Vec x) {
  return vminq_u32(x,vsubq_u32(x,vdupq_n_u32(prime)));
}
Vec fieldProduct(Vec a,Vec b) {
  auto hi=vreinterpretq_u32_s32(vqdmulhq_s32(vreinterpretq_s32_u32(a),vreinterpretq_s32_u32(b)));
  return reduceOnce(vaddq_u32(hi,vandq_u32(vdupq_n_u32(prime),vmulq_u32(a,b))));
}
void inplaceLabels(std::vector<Word>& data) {
  size_t n=data.size();
  data.resize((n+31)/32*32,1);
  for (size_t i=0;i<data.size();i+=32) {
    Vec rhs[8],v[8];
    for (int j=0;j<8;++j) {
      Vec x=vld1q_u32(data.data()+i+4*j);
      Vec sqPlusTwo=reduceOnce(vaddq_u32(nextSquare<Fold::minimum>(x),vdupq_n_u32(2)));
      rhs[j]=v[j]=reduceOnce(vaddq_u32(fieldProduct(x,sqPlusTwo),vdupq_n_u32(14)));
    }
    for (int t=0;t<30;++t)
      for (auto& k:v) k=nextSquare<Fold::signedFold>(k);
    for (int j=0;j<8;++j) {
      auto canonical=vaddq_u32(v[j],vandq_u32(vdupq_n_u32(prime),vcltzq_s32(vreinterpretq_s32_u32(v[j]))));
      vst1q_u32(data.data()+i+4*j,vshrq_n_u32(vceqq_u32(rhs[j],canonical),31));
    }
  }
  data.resize(n);
}
void separateLabels(std::vector<Word>& data) {
  for (auto& x:data) {
    uint64_t sq=uint64_t(x)*x%prime;
    x=(sq*x+2ULL*x+14)%prime;
  }
  auto n=data.size();
  data.resize((n+31)/32*32,1);
  std::vector<Word> out(data.size());
  classify<false,Fold::signedFold>(data,out,nullptr);
  out.resize(n);
  data.swap(out);
}
int main(int argc,char** argv) {
  if (argc!=2) return 1;
  int run=std::atoi(argv[1]);
  if (generate<true>()!=generate<false>()) return 2;
  Tables unused;
  unsigned expected;
  auto ref=census(0,unused,expected);
  if (ref.size()!=3846525 || expected!=1924024) return 3;
  std::puts("run,round,position,arm,gen_cpu_ms,label_cpu_ms,count_cpu_ms,total_cpu_ms,wall_ms");
  const int seq[]={0,1,3,2};
  for (int r=0;r<12;++r) for (int j=0;j<4;++j) {
    int arm=(seq[j]+r+run)%4;
    auto start=std::chrono::steady_clock::now();
    auto cpu=std::clock();
    auto data=(arm&1) ? generate<true>() : generate<false>();
    auto gen=std::clock();
    if (arm&2) inplaceLabels(data); else separateLabels(data);
    auto label=std::clock();
    auto count=std::accumulate(data.begin(),data.end(),0u);
    auto end=std::clock();
    auto ms=[](auto t){return 1000.0*t/CLOCKS_PER_SEC;};
    double wall=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    if (data!=ref || count!=expected) return 4;
    std::printf("%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f\n",run,r,j,arm,ms(gen-cpu),
                ms(label-gen),ms(end-label),ms(end-cpu),wall);
  }
}
