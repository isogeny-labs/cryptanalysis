// Independent native all-pairs audit of the bounded W20 norm subset.
#include "../n131_w20_paired_raw_quotient_20261016/field.hpp"
#include <array>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

constexpr unsigned SEED = 898618;
struct Source {unsigned code; Fe p,q; std::array<Fe,5> pp,qq;};

unsigned code_of(unsigned mask) {
    constexpr unsigned pivot=19;
    return (mask&((1u<<pivot)-1))|((mask>>(pivot+1))<<pivot);
}

int main(int argc,char**argv) {
  try {
    if(argc!=4)throw std::runtime_error("usage: direct_audit support.tsv coeff.tsv subset_size");
    Field f(131);
    std::map<unsigned,unsigned> columns;
    std::ifstream in(argv[1]);
    unsigned mask,col,shift;
    while(in>>mask>>col>>shift) {
      if(!columns.emplace(mask,col).second)throw std::runtime_error("duplicate mask");
    }
    if(columns.size()!=524493)throw std::runtime_error("source rows");
    std::map<unsigned,unsigned> valid;
    for(auto [a,c]:columns) {
      unsigned b=a^SEED;
      auto it=columns.find(b);
      if(a<b&&it!=columns.end()&&c!=it->second)valid[code_of(a)]=a;
    }
    if(valid.size()!=132045)throw std::runtime_error("valid count");
    unsigned n=std::stoul(argv[3]);
    if(n<2||n>=valid.size())throw std::runtime_error("subset size");
    std::vector<Source> source;
    for(auto [c,a]:valid) {
      if(source.size()==n-1)break;
      Fe p=f.mul(decimal(std::to_string(a<<1)),decimal(std::to_string((a^SEED)<<1)));
      Fe q=p;
      for(int j=0;j<18;++j)q=f.sq(q);
      Source item{c,p,q,{},{}};
      item.pp[0]=item.qq[0]=Fe{1,0,0};
      for(int j=1;j<5;++j) {
        item.pp[j]=f.mul(item.pp[j-1],p);
        item.qq[j]=f.mul(item.qq[j-1],q);
      }
      source.push_back(item);
    }
    if(source.front().code!=3 || source.back().code>=16722)
      throw std::runtime_error("subset fixture");
    unsigned a=valid.at(16722);
    Fe p=f.mul(decimal(std::to_string(a<<1)),decimal(std::to_string((a^SEED)<<1)));
    Fe q=p;
    for(int j=0;j<18;++j)q=f.sq(q);
    Source extra{16722,p,q,{},{}};
    extra.pp[0]=extra.qq[0]=Fe{1,0,0};
    for(int j=1;j<5;++j){extra.pp[j]=f.mul(extra.pp[j-1],p);extra.qq[j]=f.mul(extra.qq[j-1],q);}
    source.push_back(extra);
    std::ifstream coeffs(argv[2]);
    for(unsigned row=0;row<2;++row) {
      std::string tag;
      unsigned index;
      coeffs>>tag>>index;
      if(tag!="T"||index!=row)throw std::runtime_error("target row");
      Fe c[5][5]{};
      for(unsigned term=0;term<13;++term) {
        unsigned i,j;
        std::string value;
        coeffs>>tag>>index>>i>>j>>value;
        if(tag!="C"||index!=row||i>4||j>4||!zero(c[i][j]))
          throw std::runtime_error("coefficient row");
        c[i][j]=decimal(value);
      }
      std::vector<std::pair<unsigned,unsigned>> hits;
      for(const auto& left:source) {
        Fe weighted[5]{};
        for(int j=0;j<5;++j)for(int i=0;i<5;++i)
          if(!zero(c[i][j]))weighted[j]=xo(weighted[j],f.mul(c[i][j],left.pp[i]));
        for(const auto& right:source) {
          Fe value{};
          for(int j=0;j<5;++j)if(!zero(weighted[j]))
            value=xo(value,f.mul(weighted[j],right.qq[j]));
          if(zero(value))hits.emplace_back(left.code,right.code);
        }
      }
      std::cout << "ROW " << row << " " << hits.size();
      for(auto [x,y]:hits)std::cout << " " << x << "," << y;
      std::cout << "\n";
    }
    std::string trailing;
    if(coeffs>>trailing)throw std::runtime_error("trailing coefficient data");
    return 0;
  } catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
