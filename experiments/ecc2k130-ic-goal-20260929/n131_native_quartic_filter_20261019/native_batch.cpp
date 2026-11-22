// Exact quartic/right-subspace resultant gate on frozen GF(2^131) controls.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <sys/resource.h>

#include "../n131_w20_fixedseed_threeleaf_full_20261016/field.hpp"
#include "../n131_w15_native_field_20261011/field_fast.hpp"

using Clock=std::chrono::steady_clock;
using Poly=std::array<Fe,4>;
static Field field(131);
static const Fe one{1,0,0};
static inline Fe fm(Fe a,Fe b){return mul131_fast(a,b);}
struct SquareBytes{
    std::array<std::array<Fe,256>,17> table{};
    SquareBytes(){
        for(int chunk=0;chunk<17;++chunk)for(int mask=1;mask<256;++mask){
            int low=__builtin_ctz(mask),index=8*chunk+low;
            table[chunk][mask]=xo(table[chunk][mask^(1<<low)],
                                  index<131?field.square_basis[index]:Fe{});
        }
    }
    Fe sq(Fe a)const{
        Fe result{};
        for(int i=0;i<8;++i)result=xo(result,table[i][(a.lo>>(8*i))&255]);
        for(int i=0;i<8;++i)result=xo(result,table[i+8][(a.mid>>(8*i))&255]);
        return xo(result,table[16][a.hi&7]);
    }
};
static SquareBytes squares;
static inline Fe fs(Fe a){return squares.sq(a);}
static inline void xor_into(Fe& a,Fe b){a=xo(a,b);}

static Fe inv(Fe a){
    if(zero(a))throw std::runtime_error("inverse zero");
    std::array<Fe,8> table{};table[0]=a;
    int length=1,level=0;
    while(length*2<=130){
        Fe raised=table[level];
        for(int i=0;i<length;++i)raised=fs(raised);
        table[level+1]=fm(raised,table[level]);
        ++level;length*=2;
    }
    Fe result=table[level];
    for(int j=level-1;j>=0;--j)if(130&(1<<j)){
        for(int i=0;i<(1<<j);++i)result=fs(result);
        result=fm(result,table[j]);
    }
    return fs(result);
}

static Fe frob(Fe x,int power){for(int i=0;i<power;++i)x=fs(x);return x;}
static Fe source_product(unsigned code,const std::vector<int>& bits,Fe seed,int rotation){
    Fe a{};
    for(unsigned j=0;j<bits.size();++j)if(code&(1u<<j))a=xo(a,Fe{1ULL<<(bits[j]+1),0,0});
    return frob(xo(fs(a),fm(seed,a)),rotation);
}
static Fe linearized(const std::vector<Fe>& coefficients,Fe x){
    Fe result{};
    for(Fe c:coefficients){result=xo(result,fm(c,x));x=fs(x);}
    return result;
}
static std::vector<Fe> annihilator(const std::vector<Fe>& basis){
    std::vector<Fe> coefficients{one};
    for(Fe v:basis){
        Fe w=linearized(coefficients,v);
        if(zero(w))throw std::runtime_error("dependent right basis");
        std::vector<Fe> next(coefficients.size()+1);
        next[0]=fm(w,coefficients[0]);
        for(size_t j=1;j<coefficients.size();++j)
            next[j]=xo(fs(coefficients[j-1]),fm(w,coefficients[j]));
        next.back()=fs(coefficients.back());
        coefficients.swap(next);
    }
    return coefficients;
}
static Poly xmulmod(Poly v,const Poly& h,int d){
    Poly out{};
    for(int j=0;j<d-1;++j)out[j+1]=v[j];
    Fe top=v[d-1];
    if(!zero(top))for(int j=0;j<d;++j)xor_into(out[j],fm(top,h[j]));
    return out;
}
static Poly sqmod(const Poly& v,const std::vector<Poly>& powers,int d){
    Poly out{};
    for(int i=0;i<d;++i){
        Fe value=fs(v[i]);
        if(zero(value))continue;
        for(int j=0;j<d;++j)if(!zero(powers[2*i][j]))
            xor_into(out[j],fm(value,powers[2*i][j]));
    }
    return out;
}
static Fe determinant(const std::array<std::array<Fe,4>,4>& m,int d){
    if(d==4){
        Fe result{};
        for(int i=0;i<4;++i)for(int j=i+1;j<4;++j){
            int k=-1,l=-1;
            for(int q=0;q<4;++q)if(q!=i&&q!=j){if(k<0)k=q;else l=q;}
            Fe first=xo(fm(m[i][0],m[j][1]),fm(m[j][0],m[i][1]));
            Fe second=xo(fm(m[k][2],m[l][3]),fm(m[l][2],m[k][3]));
            xor_into(result,fm(first,second));
        }
        return result;
    }
    std::array<int,4> permutation{0,1,2,3};
    Fe result{};
    do{
        Fe term=one;
        for(int i=0;i<d;++i)term=fm(term,m[i][permutation[i]]);
        result=xo(result,term);
    }while(std::next_permutation(permutation.begin(),permutation.begin()+d));
    return result;
}
struct Term{int i,j;Fe c;};
static std::array<Fe,5> specialize(const std::vector<Term>& terms,Fe p){
    std::array<Fe,5> a{};
    std::array<Fe,5> powers{one,p,fm(p,p),{}, {}};
    powers[3]=fm(powers[2],p);powers[4]=fm(powers[3],p);
    for(const Term& term:terms)xor_into(a[term.j],fm(term.c,powers[term.i]));
    return a;
}
static Fe eval_quartic(const std::array<Fe,5>& a,Fe q){
    Fe out=a[4];
    for(int j=3;j>=0;--j)out=xo(fm(out,q),a[j]);
    return out;
}
static bool reject(const std::array<Fe,5>& coefficients,const std::vector<Fe>& annihilator_coeffs,
                   unsigned& exceptional,const Fe* supplied_inverse=nullptr){
    int d=4;
    while(d>=0&&zero(coefficients[d]))--d;
    if(d<0)return false;
    if(d==0)return true;
    if(d!=4)++exceptional;
    Fe leading_inv=supplied_inverse&&d==4?*supplied_inverse:inv(coefficients[d]);
    if(!eq(fm(leading_inv,coefficients[d]),one))throw std::runtime_error("inverse replay failed");
    Poly h{};
    for(int j=0;j<d;++j)h[j]=fm(coefficients[j],leading_inv);
    std::vector<Poly> powers(2*d-1);
    powers[0][0]=one;
    for(int k=1;k<2*d-1;++k)powers[k]=xmulmod(powers[k-1],h,d);
    Poly x=d==1?Poly{h[0],Fe{},Fe{},Fe{}}:powers[1],remainder{};
    for(size_t i=0;i<annihilator_coeffs.size();++i){
        for(int j=0;j<d;++j)xor_into(remainder[j],fm(annihilator_coeffs[i],x[j]));
        if(i+1<annihilator_coeffs.size())x=sqmod(x,powers,d);
    }
    std::array<std::array<Fe,4>,4> matrix{};
    for(int column=0;column<d;++column){
        for(int row=0;row<d;++row)matrix[row][column]=remainder[row];
        if(column+1<d)remainder=xmulmod(remainder,h,d);
    }
    return !zero(determinant(matrix,d));
}
int main(int argc,char** argv){
    if(argc!=4)throw std::runtime_error("usage: native INPUT SAMPLE_COUNT WALL_CAP_SECONDS");
    std::ifstream input(argv[1]);
    if(!input)throw std::runtime_error("input open failed");
    std::string header;std::getline(input,header);
    std::istringstream header_stream(header);
    std::string header_tag;int targets,term_count,control_count;
    header_stream>>header_tag>>targets>>term_count>>control_count;
    if(header_tag!="N131_NATIVE_QUARTIC"||targets!=2||term_count!=13||control_count<12)
        throw std::runtime_error("wrong input header");
    std::string tag;unsigned positive_p,positive_q;input>>tag>>positive_p>>positive_q;
    if(tag!="POS"||positive_p!=3||positive_q!=16722)throw std::runtime_error("wrong positive");
    std::array<std::vector<Term>,2> terms;
    for(int k=0;k<26;++k){int ti,i,j;std::string c;input>>tag>>ti>>i>>j>>c;
        if(tag!="C"||ti<0||ti>1||i<0||i>4||j<0||j>4)throw std::runtime_error("bad coefficient");
        terms[ti].push_back({i,j,decimal(c)});
    }
    struct Control{int ti;unsigned pcode;bool expected;};
    std::vector<Control> controls;
    for(int k=0;k<control_count;++k){int ti;unsigned code;int expected;input>>tag>>ti>>code>>expected;
        if(tag!="T"||ti<0||ti>1||expected<0||expected>1)throw std::runtime_error("bad control");
        controls.push_back({ti,code,expected!=0});
    }
    int sample_count=std::stoi(argv[2]);double wall_cap=std::stod(argv[3]);
    if(sample_count<0||sample_count>(1<<28)||wall_cap<=0)throw std::runtime_error("bad envelope");
    const auto start=Clock::now();
    auto seconds=[&](){return std::chrono::duration<double>(Clock::now()-start).count();};
    Fe seed{898618ULL<<1,0,0};
    std::vector<int> bits;
    for(int i=0;i<29;++i)if(i!=19)bits.push_back(i);
    if(bits.size()!=28)throw std::runtime_error("bad source bits");
    std::vector<Fe> pbasis,qbasis;
    for(int j=0;j<28;++j){pbasis.push_back(source_product(1u<<j,bits,seed,0));
                           qbasis.push_back(source_product(1u<<j,bits,seed,18));}
    auto av=annihilator(qbasis);
    if(av.size()!=29)throw std::runtime_error("bad annihilator");
    for(Fe b:qbasis)if(!zero(linearized(av,b)))throw std::runtime_error("annihilator basis check");
    Fe pp=source_product(positive_p,bits,seed,0),qq=source_product(positive_q,bits,seed,18);
    if(!zero(eval_quartic(specialize(terms[0],pp),qq)))throw std::runtime_error("positive eliminant check");
    if(!zero(linearized(av,qq)))throw std::runtime_error("positive membership check");
    const double prep=seconds();
    unsigned exceptional=0;
    for(const Control& control:controls){
        Fe p=source_product(control.pcode,bits,seed,0);
        bool actual=reject(specialize(terms[control.ti],p),av,exceptional);
        if(actual!=control.expected)throw std::runtime_error("frozen control mismatch");
    }
    const double controls_seconds=seconds()-prep;
    unsigned checked=0,hits=0;std::string status="COMPLETE_SAMPLE";
    const double sample_started=seconds();
    double batch_inverse_seconds=0;
    std::array<Fe,28> prefix{};
    prefix[0]=pbasis[0];
    for(int j=1;j<28;++j)prefix[j]=xo(prefix[j-1],pbasis[j]);
    Fe p{};
    for(unsigned base=0;base<(unsigned)sample_count;base+=1024){
        if(seconds()>=wall_cap){status="WALL_CAP_PARTIAL_SAMPLE";break;}
        struct rusage current{};getrusage(RUSAGE_SELF,&current);
        if(static_cast<uint64_t>(current.ru_maxrss)>4294967296ULL){status="RSS_CAP_PARTIAL_SAMPLE";break;}
        const unsigned count=std::min(1024u,(unsigned)sample_count-base);
        std::array<std::array<Fe,5>,1024> h{};
        std::array<Fe,1024> inverses{};
        std::array<Fe,1025> products{};
        for(unsigned i=0;i<count;++i){
            unsigned code=base+i;
            if(code)p=xo(p,prefix[__builtin_ctz(code)]);
            h[i]=specialize(terms[1],p);
        }
        const double inverse_started=seconds();
        products[0]=one;
        for(unsigned i=0;i<count;++i)
            products[i+1]=zero(h[i][4])?products[i]:fm(products[i],h[i][4]);
        Fe suffix=inv(products[count]);
        for(unsigned i=count;i-->0;){
            if(zero(h[i][4]))continue;
            inverses[i]=fm(products[i],suffix);
            suffix=fm(suffix,h[i][4]);
        }
        if(!eq(suffix,one))throw std::runtime_error("batch inverse product replay failed");
        batch_inverse_seconds+=seconds()-inverse_started;
        for(unsigned i=0;i<count;++i){
            const Fe* supplied=zero(h[i][4])?nullptr:&inverses[i];
            if(!reject(h[i],av,exceptional,supplied))++hits;
            ++checked;
        }
    }
    const double sample_seconds=seconds()-sample_started;
    struct rusage ru{};getrusage(RUSAGE_SELF,&ru);
    std::cout<<std::fixed<<std::setprecision(9)
             <<"{\"status\":\""<<status<<"\",\"controls_checked\":"<<controls.size()<<","
             <<"\"positive_pair_checked\":true,\"sample_target_index\":1,"
             <<"\"sample_requested\":"<<sample_count<<",\"sample_checked\":"<<checked
             <<",\"sample_unresolved\":"<<hits<<",\"exceptional_degree_count\":"<<exceptional
             <<",\"precompute_seconds\":"<<prep<<",\"controls_seconds\":"<<controls_seconds
             <<",\"batch_inverse_seconds\":"<<batch_inverse_seconds
             <<",\"sample_seconds\":"<<sample_seconds<<",\"wall_seconds\":"<<seconds()
             <<",\"peak_rss_raw\":"<<ru.ru_maxrss<<"}"<<std::endl;
}
