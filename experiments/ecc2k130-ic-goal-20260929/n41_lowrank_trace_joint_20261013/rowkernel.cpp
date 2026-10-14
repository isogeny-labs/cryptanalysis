#include "lowrank_core.hpp"

std::vector<u64> binary_kernel(std::vector<u64> equations) {
  int rank=0;std::array<int,N> pivot{};pivot.fill(-1);
  for(int bit=N-1;bit>=0;bit--) {
    int found=rank;
    while(found<int(equations.size()) && !(equations[found]&(1ULL<<bit)))found++;
    if(found==int(equations.size()))continue;
    std::swap(equations[rank],equations[found]);
    for(int i=0;i<int(equations.size());i++)if(i!=rank && (equations[i]&(1ULL<<bit)))
      equations[i]^=equations[rank];
    pivot[bit]=rank++;
  }
  std::vector<u64> basis;
  for(int free=0;free<N;free++)if(pivot[free]<0) {
    u64 vector=1ULL<<free;
    for(int bit=0;bit<N;bit++)if(pivot[bit]>=0 && (equations[pivot[bit]]&(1ULL<<free)))
      vector|=1ULL<<bit;
    for(u64 row:equations)assert(parity(row&vector)==0);
    basis.push_back(vector);
  }
  assert(int(basis.size())==N-rank);
  return basis;
}

int main(int argc,char**argv) {
  if(argc!=2)return 2;
  const u64 constructed=1515824644274ULL,public_t=1000731834126ULL;
  std::mt19937_64 selection(202610131700ULL);
  std::vector<PanelRow> panel={{819,176,constructed,true},{819,176,public_t,false}};
  for(int i=0;i<30;i++)panel.push_back({int(selection()%2048),int(selection()%2048),public_t,false});
  std::ofstream output(argv[1]);assert(output.good());
  int row_reject=0,ordinary_reject=0,positive_preserved=0;
  auto started=Clock::now();
  for(size_t case_id=0;case_id<panel.size();case_id++) {
    auto input=panel[case_id];
    auto left=family_basis(input.left),right=family_basis(input.right);
    auto source=make_source(left,right,input.target);
    int r=int(left.size()),s=int(right.size());
    std::vector<Projection> cuts;
    std::array<u64,N> span{};
    int forced_rows=0;
    for(int keep=0;keep<r && cuts.size()<12;keep++) {
      std::vector<u64> equations;
      for(int i=0;i<r;i++)if(i!=keep)
        for(int j=0;j<s;j++)equations.push_back(source.cross[i*s+j]);
      auto kernel=binary_kernel(equations);
      forced_rows=std::max(forced_rows,r-1);
      for(u64 lambda:kernel)if(independent(lambda,span)) {
        auto cut=project(lambda,source);
        assert(cut.cross_rank<=1);
        cuts.push_back(cut);
        if(cuts.size()==12)break;
      }
    }
    assert(cuts.size()==12);
    std::vector<Projection> ordinary;
    std::array<u64,N> ordinary_span{};
    std::mt19937_64 rng(202610131701ULL+case_id);
    while(ordinary.size()<12) {
      u64 lambda=rng()&MASK;if(!lambda)continue;
      auto cut=project(lambda,source);
      if(independent(lambda,ordinary_span))ordinary.push_back(cut);
    }
    std::array<u64,13> row_survivors{},ordinary_survivors{};
    u64 exact=0;
    for(u64 alpha=0;alpha<(1ULL<<r);alpha++)for(u64 beta=0;beta<(1ULL<<s);beta++) {
      int row_prefix=0,ordinary_prefix=0;
      for(int k=0;k<12;k++) {
        if(row_prefix==k && evaluate_cut(cuts[k],alpha,beta)==0)row_prefix++;
        if(ordinary_prefix==k && evaluate_cut(ordinary[k],alpha,beta)==0)ordinary_prefix++;
      }
      for(int k=0;k<=row_prefix;k++)row_survivors[k]++;
      for(int k=0;k<=ordinary_prefix;k++)ordinary_survivors[k]++;
      u64 c=0,d=0;
      for(int i=0;i<r;i++)if(alpha&(1ULL<<i))c^=left[i];
      for(int j=0;j<s;j++)if(beta&(1ULL<<j))d^=right[j];
      if(c && d) {
        u64 z=mul(mul(c,d),input.target);
        if((sq(z)^z^sq(c)^sq(d)^sq(input.target))==0)exact++;
      }
      if(((alpha*(1ULL<<s)+beta)%257)==0) {
        u64 z=mul(mul(c,d),input.target);
        u64 direct=sq(z)^z^sq(c)^sq(d)^sq(input.target);
        for(auto& cut:cuts)assert(evaluate_cut(cut,alpha,beta)==tr(mul(cut.lambda,direct)));
      }
    }
    if(input.control){assert(exact>0 && row_survivors[12]>0);positive_preserved++;}
    row_reject+=row_survivors[12]==0;
    ordinary_reject+=ordinary_survivors[12]==0;
    output<<"{\"case\":"<<case_id<<",\"left_product\":"<<input.left
      <<",\"right_product\":"<<input.right<<",\"target\":"<<input.target
      <<",\"left_dimension\":"<<r<<",\"right_dimension\":"<<s
      <<",\"forced_cross_rows\":"<<forced_rows<<",\"exact_hits\":"<<exact
      <<",\"control\":"<<(input.control?"true":"false")<<",\"row_ranks\":[";
    for(int k=0;k<12;k++)output<<(k?",":"")<<cuts[k].cross_rank;
    output<<"],\"row_lambdas\":[";
    for(int k=0;k<12;k++)output<<(k?",":"")<<cuts[k].lambda;
    output<<"],\"ordinary_lambdas\":[";
    for(int k=0;k<12;k++)output<<(k?",":"")<<ordinary[k].lambda;
    output<<"],\"row_survivors\":[";
    for(int k=0;k<=12;k++)output<<(k?",":"")<<row_survivors[k];
    output<<"],\"ordinary_survivors\":[";
    for(int k=0;k<=12;k++)output<<(k?",":"")<<ordinary_survivors[k];
    output<<"]}\n";
  }
  auto seconds=std::chrono::duration<double>(Clock::now()-started).count();
  std::cout<<"{\"status\":\"COMPLETE_ROW_KERNEL_TRACE_PANEL\",\"cases\":"<<panel.size()
    <<",\"row_zero_survivor_cases\":"<<row_reject
    <<",\"ordinary_zero_survivor_cases\":"<<ordinary_reject
    <<",\"positive_controls_preserved\":"<<positive_preserved
    <<",\"internal_seconds\":"<<std::setprecision(12)<<seconds<<"}\n";
}
