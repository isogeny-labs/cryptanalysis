// Full ordered labels of P+jK on the two public M31 curves.
#include "m31-vector-field.hpp"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <random>
#include <vector>

namespace {
using W=uint32_t;
using namespace m31_vector;
W mul(W a,W b) { return uint64_t(a)*b%p; }
W add(W a,W b) { W s=a+b; return s>=p?s-p:s; }
W sub(W a,W b) { return a>=b?a-b:a+(p-b); }
W inv(W a) {
    if(!a) std::abort();
    W z=1;
    for(W n=p-2;n;n>>=1) { if(n&1) z=mul(z,a); a=mul(a,a); }
    return z;
}
struct Point { W x,y; };
constexpr Point K={1965083199,1854403464};
struct Shifts {
    Batch x{},y{};
    constexpr Shifts(Batch abscissas,Batch ordinates) : x(abscissas),y(ordinates) {}
    explicit Shifts(Point generator=K) {
        Point q=generator;
        for(unsigned j=1;j<32;++j) {
            x[j]=q.x; y[j]=q.y;
            if(j==31) break;
            W slope=j==1?mul(add(mul(3,mul(q.x,q.x)),1),inv(add(q.y,q.y))):
                         mul(sub(q.y,generator.y),inv(sub(q.x,generator.x)));
            W xn=sub(sub(mul(slope,slope),q.x),generator.x);
            q={xn,sub(mul(slope,sub(q.x,xn)),q.y)};
        }
        if(x[16]!=0 || y[16]!=0 || x[31]!=generator.x || add(y[31],generator.y)!=0) std::abort();
    }
};
// Coordinates of jK, with the identity lane handled separately.
constexpr Shifts fixed(
    {0,1965083199,177504693,1063718422,1825752205,1983108407,705231622,1948130974,
     1,139984982,1903942232,33359769,321862516,2085125131,1575660783,478064842,
     0,478064842,1575660783,2085125131,321862516,33359769,1903942232,139984982,
     1,1948130974,705231622,1983108407,1825752205,1063718422,177504693,1965083199},
    {0,1854403464,1560611074,804322263,828415538,1670523782,1784360027,1693218552,
     65536,761055499,1408832458,947317871,828153390,1252173442,982704225,181850505,
     0,1965633142,1164779422,895310205,1319330257,1200165776,738651189,1386428148,
     2147418111,454265095,363123620,476959865,1319068109,1343161384,586872573,293080183});
#include "orbit-shifts.hpp"
struct Row { Point point; Batch xs; Labels expected; };

Labels affine(const Point& q,const Shifts& s) {
    // One field inversion for the sixteen distinct chord denominators.
    W prefix[17]={1},dx[17];
    for(unsigned j=1;j<=16;++j) {
        dx[j]=sub(q.x,s.x[j]);
        prefix[j]=mul(prefix[j-1],dx[j]);
    }
    W reciprocal=inv(prefix[16]);
    Batch xs;
    xs[0]=q.x;
    for(unsigned j=16;j!=0;--j) {
        W scale=mul(prefix[j-1],reciprocal);
        reciprocal=mul(reciprocal,dx[j]);
        W sum=add(q.x,s.x[j]);
        W slope=mul(sub(q.y,s.y[j]),scale);
        xs[j]=sub(mul(slope,slope),sum);
        if(j!=16) {
            W other=mul(add(q.y,s.y[j]),scale);
            xs[32-j]=sub(mul(other,other),sum);
        }
    }
    return classify<3>(xs);
}

template<bool simplified,bool use_inverse=false> Labels homogeneous(const Point& q,const Shifts& s) {
    V inputs[8]; int32x4_t state[8];
    Batch inverse_dx{};
    if constexpr(use_inverse) {
        W prefix[17]={1};
        for(unsigned j=1;j<=16;++j) prefix[j]=mul(prefix[j-1],sub(q.x,s.x[j]));
        W scale=inv(prefix[16]);
        for(unsigned j=16;j!=0;--j) {
            inverse_dx[j]=inverse_dx[32-j]=mul(scale,prefix[j-1]);
            scale=mul(scale,sub(q.x,s.x[j]));
        }
    }
    V x=dup(q.x),y=dup(q.y);
    for(unsigned j=0;j<8;++j) {
        V a=vld1q_u32(&s.x[4*j]),b=vld1q_u32(&s.y[4*j]);
        V dx=minus(x,a),d=times(dx,dx),sum=plus(x,a);
        V n;
        if constexpr(use_inverse) {
            V slope=times(minus(y,b),vld1q_u32(&inverse_dx[4*j]));
            n=minus(times(slope,slope),sum);
            if(j==0) n=vsetq_lane_u32(q.x,n,0);
            inputs[j]=plus(times(n,plus(times(n,n),dup(2))),dup(14));
        } else {
            if constexpr(simplified) {
                V yb=times(y,b);
                n=minus(times(sum,plus(dup(1),times(x,a))),plus(yb,yb));
            } else {
                V dy=minus(y,b);
                n=minus(times(dy,dy),times(sum,d));
            }
            if(j==0) { n=vsetq_lane_u32(q.x,n,0); d=vsetq_lane_u32(1,d,0); }
            // f(n/d)*d^3; d is a nonzero square on the full affine fibers.
            V d2=times(d,d);
            inputs[j]=plus(times(n,plus(times(n,n),plus(d2,d2))),times(dup(14),times(d2,d)));
        }
        state[j]=vreinterpretq_s32_u32(inputs[j]);
    }
    for(unsigned k=0;k<30;++k) for(auto& lane:state) lane=complement_square(lane);
    Labels labels;
    for(unsigned j=0;j<8;++j) {
        auto lane=state[j];
        auto canon=vaddq_s32(lane,vandq_s32(vshrq_n_s32(lane,31),vdupq_n_s32(p)));
        W flags[4];
        vst1q_u32(flags,vshrq_n_u32(vceqq_u32(vreinterpretq_u32_s32(canon),inputs[j]),31));
        for(unsigned k=0;k<4;++k) labels[4*j+k]=flags[k];
    }
    return labels;
}
}

int main(int argc,char** argv) {
    bool stream=argc==4 && std::string(argv[3])=="shift-stream";
    bool shifts_test=argc==5 && std::string(argv[3])=="shifts";
    bool single=argc==5 && std::string(argv[3])=="single";
    if(argc!=4 && !single && !shifts_test) return 1;
    unsigned seed=std::stoul(argv[1]);
    bool check=std::string(argv[3])=="check";
    unsigned passes=(check||single||shifts_test||stream)?0:std::stoul(argv[3]);
    if(!check && !single && !shifts_test && !stream && passes==0) return 1;
    std::ifstream in(argv[2]); std::vector<Row> rows(1024);
    for(auto& r:rows) {
        for(unsigned j=0;j<32;++j) {
            W b;
            if(!(in>>r.xs[j]>>b) || r.xs[j]>=p || b>1) return 2;
            r.expected[j]=b;
        }
        W x=r.xs[0],a=K.x,dx=sub(x,a);
        W chord=mul(mul(dx,dx),add(add(x,a),r.xs[1]));
        W y=mul(sub(add(mul(x,add(mul(x,x),1)),mul(K.y,K.y)),chord),inv(add(K.y,K.y)));
        r.point={x,y};
        if(mul(y,y)!=mul(x,add(mul(x,x),1))) return 3;
    }
    if(check) {
        Shifts shifts;
        if(fixed.x!=shifts.x || fixed.y!=shifts.y) return 7;
        std::vector<RawShifts> generators;
        for(unsigned k=1;k<32;k+=2) generators.emplace_back(Point{fixed.x[k],fixed.y[k]});
        for(auto& row:rows) for(unsigned j=0;j<32;++j) {
            W x=row.xs[j],dx=sub(x,K.x),xn=row.xs[(j+1)%32];
            W y=mul(sub(add(mul(x,add(mul(x,x),1)),mul(K.y,K.y)),
                        mul(mul(dx,dx),add(add(x,K.x),xn))),inv(add(K.y,K.y)));
            for(unsigned i=1;i<=16;++i) if(x==shifts.x[i]) return 5;
            for(bool reverse:{false,true}) {
                Point pt={x,reverse?sub(0,y):y};
                Labels expected;
                for(unsigned k=0;k<32;++k) expected[k]=row.expected[(j+(reverse?32-k:k))%32];
                unsigned g=j%16,stride=2*g+1;
                auto rotated=raw_labels(pt,generators[g]);
                for(unsigned k=0;k<32;++k) if(rotated[k]!=expected[k*stride%32]) return 9;
                for(auto fn:std::array{affine,homogeneous<false>,homogeneous<true>,homogeneous<false,true>})
                    if(fn(pt,shifts)!=expected) return 6;
            }
        }
        std::cout<<rows.size()*64<<" oriented starts matched\n";
        return 0;
    }
    std::mt19937 gen(seed); std::shuffle(rows.begin(),rows.end(),gen);
    if(stream) {
        std::vector<Point> generators;
        std::vector<Labels> output(rows.size());
        for(size_t i=0;i<rows.size();++i) {
            unsigned k=2*((seed+i)%16)+1;
            generators.push_back({fixed.x[k],fixed.y[k]});
        }
        for(unsigned pos=0;pos<2;++pos) {
            auto method=3+(seed+pos)%2;
            auto start=std::chrono::steady_clock::now();
            for(size_t i=0;i<rows.size();++i) {
                if(method==3) output[i]=raw_labels(rows[i].point,RawShifts(generators[i]));
                else output[i]=homogeneous<false>(rows[i].point,reindex(generators[i]));
            }
            auto ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start);
            for(size_t i=0;i<rows.size();++i) for(unsigned j=0;j<32;++j) {
                unsigned k=2*((seed+i)%16)+1;
                if(output[i][j]!=rows[i].expected[j*k%32]) return 8;
            }
            std::cout<<method<<','<<ns.count()/rows.size()<<'\n';
        }
        return 0;
    }
    if(shifts_test) {
        unsigned method=std::stoul(argv[4]);
        if(method>=5) return 1;
        unsigned stride=2*(seed%16)+1;
        Point generator={fixed.x[stride],fixed.y[stride]};
        asm volatile("" : "+r"(generator.x), "+r"(generator.y));
        const Point pt=rows[0].point;
        auto begin=std::chrono::steady_clock::now();
        if(method==3) {
            RawShifts shifts(generator);
            Labels result=raw_labels(pt,shifts);
            asm volatile("" : : "r"(result.data()) : "memory");
            auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-begin);
            for(unsigned j=0;j<32;++j) {
                unsigned idx=(j*stride)%32;
                W z=shifts.z[j],zz=mul(z,z);
                if(!z || shifts.x[j]!=mul(fixed.x[idx],zz) ||
                   shifts.y[j]!=mul(fixed.y[idx],mul(z,zz)) || result[j]!=rows[0].expected[idx]) return 8;
            }
            std::cout<<method<<','<<elapsed.count()<<'\n';
            return 0;
        }
        Shifts shifts=method==0?Shifts(generator):method==1?layered(generator):
                      method==2?projective_shifts(generator):reindex(generator);
        Labels result=homogeneous<false>(pt,shifts);
        asm volatile("" : : "r"(result.data()) : "memory");
        auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-begin);
        for(unsigned j=0;j<32;++j) {
            unsigned index=(stride*j)%32;
            if(result[j]!=rows[0].expected[index] || shifts.x[j]!=fixed.x[index] ||
               shifts.y[j]!=fixed.y[index]) return 8;
        }
        std::cout<<method<<','<<elapsed.count()<<'\n';
        return 0;
    }
    if(single) {
        unsigned method=std::stoul(argv[4]);
        if(method>=4) return 1;
        auto fn=(method%2==0)?homogeneous<false,true>:homogeneous<false>;
        const Point pt=rows[0].point;
        auto start=std::chrono::steady_clock::now();
        Labels result;
        if(method<2) {
            const Shifts shifts;
            result=fn(pt,shifts);
        } else result=fn(pt,fixed);
        asm volatile("" : : "r"(result.data()) : "memory");
        auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start);
        if(result!=rows[0].expected) return 4;
        std::cout<<method<<','<<ns.count()<<'\n';
        return 0;
    }
    std::array<unsigned,4> order={0,1,2,3};
    for(unsigned k=0;k<seed%24;++k) std::next_permutation(order.begin(),order.end());
    std::vector<Labels> out(rows.size());
    for(unsigned method:order) {
        auto fn=std::array{affine,homogeneous<false>,homogeneous<true>,homogeneous<false,true>}[method];
        auto start=std::chrono::steady_clock::now();
        const Shifts shifts;
        for(unsigned k=0;k<passes;++k) {
            for(size_t i=0;i<rows.size();++i) out[i]=fn(rows[i].point,shifts);
            asm volatile("" : : "r"(out.data()) : "memory");
        }
        auto ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start);
        for(size_t i=0;i<rows.size();++i) if(out[i]!=rows[i].expected) return 4;
        std::cout<<method<<','<<ns.count()/(passes*rows.size())<<'\n';
    }
}
