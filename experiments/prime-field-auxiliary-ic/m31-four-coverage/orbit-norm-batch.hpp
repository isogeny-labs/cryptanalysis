// All arms receive the first abscissa of each orbit from the same shuffled rows.
namespace orbit_batch {
using V=uint32x4_t;
inline V dup(Word x) { return vdupq_n_u32(x); }
inline V plus(V x,V y) {
    V s=vaddq_u32(x,y);
    return vminq_u32(s,vsubq_u32(s,dup(p)));
}
inline V minus(V x,V y) { return plus(x,vsubq_u32(dup(p),y)); }
inline V times(V x,V y) {
    V h=vreinterpretq_u32_s32(vqdmulhq_s32(vreinterpretq_s32_u32(x),vreinterpretq_s32_u32(y)));
    return plus(h,vandq_u32(vmulq_u32(x,y),dup(p)));
}
constexpr bool cancels(Step s) { return add(mul(s.t,s.t),s.B)==mul(s.A,s.t); }
static_assert(cancels(steps[1]) && cancels(steps[2]) && cancels(steps[3]) && cancels(steps[4]));

bool scalar_factored(Word x) {
    Word u=add(mul(x,x),1),v=x;
    for(unsigned i=1;i<steps.size();++i) {
        const auto s=steps[i];
        Word den=mul(v,sub(u,mul(s.t,v)));
        u=mul(u,add(u,mul(sub(s.A,add(s.t,s.t)),v)));
        v=den;
    }
    Word vv=mul(v,v);
    Word val=add(mul(add(mul(f[0],u),mul(f[1],v)),mul(u,u)),
                 mul(vv,add(mul(f[2],u),mul(f[3],v))));
    return square(mul(val,v));
}

template<bool factored> __attribute__((noinline))
void vector_batch(const Row* rows,uint8_t* out) {
    std::array<V,8> input;
    std::array<int32x4_t,8> state;
    for(unsigned j=0;j<8;++j) {
        const Row* r=rows+4*j;
        V x={r[0].xs[0],r[1].xs[0],r[2].xs[0],r[3].xs[0]};
        V u=plus(times(x,x),dup(1)),v=x;
        for(unsigned i=1;i<steps.size();++i) {
            auto s=steps[i];
            V w=minus(u,times(dup(s.t),v));
            V den=times(v,w);
            if constexpr(factored)
                u=times(u,plus(u,times(dup(sub(s.A,add(s.t,s.t))),v)));
            else
                u=plus(plus(times(w,w),times(dup(s.A),den)),times(dup(s.B),times(v,v)));
            v=den;
        }
        V vv=times(v,v);
        V val=plus(times(plus(times(dup(f[0]),u),times(dup(f[1]),v)),times(u,u)),
                   times(vv,plus(times(dup(f[2]),u),times(dup(f[3]),v))));
        input[j]=times(val,v);
        state[j]=vreinterpretq_s32_u32(input[j]);
    }
    for(unsigned k=0;k<30;++k) for(auto& s:state) s=complement_square(s);
    for(unsigned j=0;j<8;++j) {
        auto s=state[j];
        auto canonical=vaddq_s32(s,vandq_s32(vshrq_n_s32(s,31),vdupq_n_s32(p)));
        uint32_t flags[4];
        vst1q_u32(flags,vshrq_n_u32(vceqq_u32(vreinterpretq_u32_s32(canonical),input[j]),31));
        for(unsigned k=0;k<4;++k) out[4*j+k]=flags[k];
    }
}
}

int batch_bench(const std::vector<Row>& rows,unsigned seed,unsigned selected=4) {
    if(rows.size()%32) return 6;
    std::vector<uint8_t> out(rows.size());
    std::array<unsigned,4> order={0,1,2,3};
    for(unsigned k=0;k<seed%24;++k) std::next_permutation(order.begin(),order.end());
    unsigned passes=selected==4?64:1;
    for(auto method:order) {
        if(selected!=4 && method!=selected) continue;
        auto start=std::chrono::steady_clock::now();
        for(unsigned pass=0;pass<passes;++pass) {
            if(method<2) {
                auto fn=method==0?projective:orbit_batch::scalar_factored;
                for(size_t i=0;i<rows.size();++i) out[i]=fn(rows[i].xs[0]);
            } else {
                auto fn=method==2?orbit_batch::vector_batch<false>:orbit_batch::vector_batch<true>;
                for(size_t i=0;i<rows.size();i+=32) fn(rows.data()+i,out.data()+i);
            }
            asm volatile("" : : "r"(out.data()) : "memory");
        }
        auto elapsed=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start);
        for(size_t i=0;i<rows.size();++i) if(out[i]!=rows[i].expected) return 5;
        std::cout<<method<<','<<elapsed.count()/(passes*rows.size())<<'\n';
    }
    return 0;
}
