#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <sys/resource.h>

using Clock=std::chrono::steady_clock;
using Row=std::vector<uint64_t>;
static bool graded=false;
static bool monomial_less(uint64_t a,uint64_t b){
  if(graded){int da=__builtin_popcountll(a),db=__builtin_popcountll(b);
    if(da!=db)return da<db;}
  return a<b;
}

static double seconds(Clock::time_point t){
  return std::chrono::duration<double>(Clock::now()-t).count();
}
static uint64_t peak_rss(){
  rusage r{};getrusage(RUSAGE_SELF,&r);
  return static_cast<uint64_t>(r.ru_maxrss); // Darwin reports bytes.
}
static Row make_row(const Row& source,uint64_t factor){
  Row words;words.reserve(source.size());
  for(uint64_t monomial:source)words.push_back(monomial|factor);
  std::sort(words.begin(),words.end(),monomial_less);
  Row out;out.reserve(words.size());
  for(size_t i=0;i<words.size();){
    size_t j=i+1;while(j<words.size()&&words[j]==words[i])++j;
    if((j-i)&1)out.push_back(words[i]);
    i=j;
  }
  return out;
}
static Row xor_rows(const Row&a,const Row&b){
  Row out;out.reserve(a.size()+b.size());
  size_t i=0,j=0;
  while(i<a.size()||j<b.size()){
    if(j==b.size()||(i<a.size()&&monomial_less(a[i],b[j])))out.push_back(a[i++]);
    else if(i==a.size()||monomial_less(b[j],a[i]))out.push_back(b[j++]);
    else{++i;++j;}
  }
  return out;
}

int main(int argc,char**argv){
 try{
  if(argc<2||argc>5)throw std::runtime_error("usage: sparse_degree6 equations.txt [max_rows] [numeric|graded] [limit_s]");
  uint64_t max_rows=argc==3?std::stoull(argv[2]):78076;
  if(argc>=3)max_rows=std::stoull(argv[2]);
  if(max_rows==0||max_rows>78076)throw std::runtime_error("invalid max_rows");
  if(argc>=4){std::string mode=argv[3];
    if(mode!="graded"&&mode!="numeric")throw std::runtime_error("mode");
    graded=mode=="graded";}
  double limit_s=argc>=5?std::stod(argv[4]):180.0;
  if(limit_s<=0||limit_s>180)throw std::runtime_error("limit_s");
  auto started=Clock::now();
  std::ifstream input(argv[1]);if(!input)throw std::runtime_error("input missing");
  std::string magic;int vars,eqs,anf,target;
  input>>magic>>vars>>eqs>>anf>>target;
  if(magic!="W33"||vars!=34||eqs!=131||anf!=1619||(target!=0&&target!=1))
    throw std::runtime_error("header mismatch");
  std::vector<Row> equations(eqs);
  uint64_t raw_support=0;
  for(int bit=0;bit<eqs;++bit){
   size_t count;input>>count;
   if(count<1||count>1619)throw std::runtime_error("equation support count");
   auto &row=equations[bit];row.resize(count);
   for(auto &m:row){input>>m;if(m>=(1ULL<<vars)||__builtin_popcountll(m)>4)
     throw std::runtime_error("bad monomial");}
   if(!input)throw std::runtime_error("short input");
   std::sort(row.begin(),row.end(),monomial_less);
   if(std::adjacent_find(row.begin(),row.end())!=row.end())
     throw std::runtime_error("duplicate source monomial");
   raw_support+=count;
  }
  uint64_t extra;if(input>>extra)throw std::runtime_error("trailing input");
  std::vector<uint64_t> factors;factors.reserve(596);
  factors.push_back(0);
  for(int i=0;i<vars;++i)factors.push_back(1ULL<<i);
  for(int i=0;i<vars;++i)for(int j=i+1;j<vars;++j)
    factors.push_back((1ULL<<i)|(1ULL<<j));
  if(factors.size()!=596||raw_support<100000||raw_support>110000)
    throw std::runtime_error("frozen source dimensions");
  double setup_s=seconds(started);
  auto loop_start=Clock::now();
  std::unordered_map<uint64_t,Row> pivots;
  pivots.reserve(max_rows);
  uint64_t processed=0,zero_rows=0,xor_count=0,stored_words=0,max_words=0;
  std::string status="COMPLETE";
  for(int bit=0;bit<eqs&&status=="COMPLETE";++bit){
   for(uint64_t factor:factors){
    if(processed>=max_rows)break;
    Row row=make_row(equations[bit],factor);
    while(!row.empty()){
     auto p=pivots.find(row.back());
     if(p==pivots.end())break;
     row=xor_rows(row,p->second);++xor_count;
    }
    max_words=std::max(max_words,static_cast<uint64_t>(row.size()));
    if(row.empty())++zero_rows;
    else{
     stored_words+=row.size();
     pivots.emplace(row.back(),std::move(row));
    }
    ++processed;
    if((processed&15)==0){
     if(seconds(loop_start)>limit_s){status="BOUNDED_TIME";break;}
     if(peak_rss()>4000000000ULL||stored_words>450000000ULL){
       status="BOUNDED_MEMORY";break;}
    }
   }
   if(processed>=max_rows)break;
  }
  if(status=="COMPLETE"&&processed<78076)status="PARTIAL_ROWS";
  bool constant_in_span=false;
  Row value{0};
  while(!value.empty()){
   auto p=pivots.find(value.back());if(p==pivots.end())break;
   value=xor_rows(value,p->second);
  }
  constant_in_span=value.empty();
  if(target==0&&constant_in_span)
    throw std::runtime_error("constructed positive control rejected");
  std::cout<<"{\"status\":\""<<status<<"\",\"mode\":\""<<(graded?"graded":"numeric")
           <<"\",\"target_index\":"<<target
           <<",\"rows_processed\":"<<processed<<",\"total_rows\":78076"
           <<",\"rank\":"<<pivots.size()<<",\"zero_rows\":"<<zero_rows
           <<",\"constant_in_span\":"<<(constant_in_span?"true":"false")
           <<",\"xor_count\":"<<xor_count<<",\"stored_words\":"<<stored_words
           <<",\"max_row_words\":"<<max_words<<",\"raw_equation_support\":"<<raw_support
           <<",\"setup_s\":"<<setup_s<<",\"loop_s\":"<<seconds(loop_start)
           <<",\"wall_s\":"<<seconds(started)<<",\"maxrss_raw\":"<<peak_rss()<<"}\n";
  return 0;
 }catch(std::exception const&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
