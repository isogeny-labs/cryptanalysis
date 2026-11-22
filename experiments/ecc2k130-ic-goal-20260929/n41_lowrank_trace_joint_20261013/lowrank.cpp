#define main inherited_bilinear_screen_main
#include "../n41_bilinear_rank_screen_20261013/native.cpp"
#undef main
#include <bit>
#include <iomanip>

// A trace projection is represented by its 41-bit dual pairing vector.
u64 dual(u64 value) {
  u64 out=0;
  for(int k=0;k<N;k++) if(tr(mul(1ULL<<k,value))) out|=1ULL<<k;
  return out;
}
int parity(u64 value) {return std::popcount(value)&1;}
int matrix_rank(std::vector<u64> rows,int columns) {
  int rank=0;
  for(int col=0;col<columns;col++) {
    int pivot=rank;
    while(pivot<int(rows.size()) && !(rows[pivot]&(1ULL<<col))) pivot++;
    if(pivot==int(rows.size())) continue;
    std::swap(rows[rank],rows[pivot]);
    for(int i=0;i<int(rows.size());i++) if(i!=rank && (rows[i]&(1ULL<<col))) rows[i]^=rows[rank];
    rank++;
  }
  return rank;
}
bool independent(u64 value,std::array<u64,N>& pivots) {
  u64 work=value;
  for(int bit=N-1;bit>=0;bit--) if(work&(1ULL<<bit)) {
    if(pivots[bit])work^=pivots[bit];
    else {pivots[bit]=work;return true;}
  }
  return false;
}
struct Projection {u64 lambda;int cross_rank;u64 left_mask,right_mask;std::vector<u64> cross_rows;int constant;};
struct ProjectionSource {std::vector<u64> left,right,cross;u64 constant;};
ProjectionSource make_source(const std::vector<u64>& left,const std::vector<u64>& right,u64 t) {
  int r=int(left.size()),s=int(right.size());
  ProjectionSource source{std::vector<u64>(r),std::vector<u64>(s),std::vector<u64>(r*s),dual(sq(t))};
  for(int i=0;i<r;i++)source.left[i]=dual(sq(left[i]));
  for(int j=0;j<s;j++)source.right[j]=dual(sq(right[j]));
  for(int i=0;i<r;i++)for(int j=0;j<s;j++) {
    u64 product=mul(left[i],right[j]);
    u64 coefficient=mul(sq(t),sq(product))^mul(t,product);
    source.cross[i*s+j]=dual(coefficient);
  }
  return source;
}
Projection project(u64 lambda,const ProjectionSource& source) {
  int r=int(source.left.size()),s=int(source.right.size());
  Projection out{lambda,0,0,0,std::vector<u64>(r),parity(lambda&source.constant)};
  for(int i=0;i<r;i++)if(parity(lambda&source.left[i]))out.left_mask|=1ULL<<i;
  for(int j=0;j<s;j++)if(parity(lambda&source.right[j]))out.right_mask|=1ULL<<j;
  for(int i=0;i<r;i++)for(int j=0;j<s;j++)
    if(parity(lambda&source.cross[i*s+j]))out.cross_rows[i]|=1ULL<<j;
  out.cross_rank=matrix_rank(out.cross_rows,s);
  return out;
}
int evaluate_cut(const Projection& p,u64 alpha,u64 beta) {
  int value=p.constant^parity(alpha&p.left_mask)^parity(beta&p.right_mask);
  for(int i=0;i<int(p.cross_rows.size());i++) if(alpha&(1ULL<<i))
    value^=parity(beta&p.cross_rows[i]);
  return value;
}
struct PanelRow {int left,right;u64 target;bool control;};
int main(int argc,char**argv) {
  if(argc!=2)return 2;
  const u64 constructed=1515824644274ULL,public_t=1000731834126ULL;
  std::mt19937_64 selection(202610131700ULL);
  std::vector<PanelRow> panel={{819,176,constructed,true},{819,176,public_t,false}};
  for(int i=0;i<30;i++) panel.push_back({int(selection()%2048),int(selection()%2048),public_t,false});
  std::ofstream output(argv[1]);assert(output.good());
  int low_reject=0,random_reject=0,positive_preserved=0;
  auto started=Clock::now();
  for(size_t case_id=0;case_id<panel.size();case_id++) {
    auto row=panel[case_id];auto left=family_basis(row.left),right=family_basis(row.right);
    int r=int(left.size()),s=int(right.size());
    auto source=make_source(left,right,row.target);
    std::mt19937_64 rng(202610131701ULL+case_id);
    std::vector<Projection> low,ordinary;
    std::array<u64,N> low_span{},ordinary_span{};
    int tries=0;
    while(low.size()<12 && tries<200000) {
      u64 lambda=rng()&MASK;tries++;if(!lambda)continue;
      auto p=project(lambda,source);
      if(ordinary.size()<12 && independent(lambda,ordinary_span))ordinary.push_back(p);
      if(p.cross_rank<=3 && independent(lambda,low_span))low.push_back(p);
    }
    assert(low.size()==12 && ordinary.size()==12);
    std::array<u64,13> low_survivors{},ordinary_survivors{};
    u64 exact=0;
    for(u64 alpha=0;alpha<(1ULL<<r);alpha++)for(u64 beta=0;beta<(1ULL<<s);beta++) {
      int low_prefix=0,ordinary_prefix=0;
      for(int k=0;k<12;k++) {
        if(low_prefix==k && evaluate_cut(low[k],alpha,beta)==0)low_prefix++;
        if(ordinary_prefix==k && evaluate_cut(ordinary[k],alpha,beta)==0)ordinary_prefix++;
      }
      for(int k=0;k<=low_prefix;k++)low_survivors[k]++;
      for(int k=0;k<=ordinary_prefix;k++)ordinary_survivors[k]++;
      u64 c=0,d=0;
      for(int i=0;i<r;i++)if(alpha&(1ULL<<i))c^=left[i];
      for(int j=0;j<s;j++)if(beta&(1ULL<<j))d^=right[j];
      if(c && d) {
        u64 z=mul(mul(c,d),row.target);
        if((sq(z)^z^sq(c)^sq(d)^sq(row.target))==0)exact++;
      }
    }
    if(row.control) {assert(exact>0 && low_survivors[12]>0 && ordinary_survivors[12]>0);positive_preserved++;}
    low_reject+=low_survivors[12]==0;random_reject+=ordinary_survivors[12]==0;
    output<<"{\"case\":"<<case_id<<",\"left_product\":"<<row.left
      <<",\"right_product\":"<<row.right<<",\"target\":"<<row.target
      <<",\"left_dimension\":"<<r<<",\"right_dimension\":"<<s
      <<",\"lambda_trials\":"<<tries<<",\"exact_hits\":"<<exact
      <<",\"control\":"<<(row.control?"true":"false")<<",\"low_rank_values\":[";
    for(int k=0;k<12;k++)output<<(k?",":"")<<low[k].cross_rank;
    output<<"],\"low_lambdas\":[";
    for(int k=0;k<12;k++)output<<(k?",":"")<<low[k].lambda;
    output<<"],\"ordinary_lambdas\":[";
    for(int k=0;k<12;k++)output<<(k?",":"")<<ordinary[k].lambda;
    output<<"],\"low_survivors\":[";
    for(int k=0;k<=12;k++)output<<(k?",":"")<<low_survivors[k];
    output<<"],\"ordinary_survivors\":[";
    for(int k=0;k<=12;k++)output<<(k?",":"")<<ordinary_survivors[k];
    output<<"]}\n";
  }
  auto seconds=std::chrono::duration<double>(Clock::now()-started).count();
  std::cout<<"{\"status\":\"COMPLETE_LOWRANK_TRACE_PANEL\",\"cases\":"<<panel.size()
    <<",\"low_rank_zero_survivor_cases\":"<<low_reject
    <<",\"ordinary_zero_survivor_cases\":"<<random_reject
    <<",\"positive_controls_preserved\":"<<positive_preserved
    <<",\"internal_seconds\":"<<std::setprecision(12)<<seconds<<"}\n";
}
