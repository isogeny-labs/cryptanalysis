#include <cuda_runtime.h>
#include "wire.hpp"
#include "kernels.cu"
inline void cc_cuda_check(cudaError_t rc) {
    if (rc!=cudaSuccess) throw std::runtime_error(cudaGetErrorString(rc));
}
struct CcCudaBuffer {
    void *p=nullptr;
    explicit CcCudaBuffer(std::size_t n,const void *data=nullptr) {
        cc_cuda_check(cudaMalloc(&p,n));
        if (data) {
            cudaError_t rc=cudaMemcpy(p,data,n,cudaMemcpyHostToDevice);
            if (rc!=cudaSuccess) {cudaFree(p);p=nullptr;cc_cuda_check(rc);}
        }
    }
    ~CcCudaBuffer() {if (p) cudaFree(p);}
    CcCudaBuffer(const CcCudaBuffer &)=delete;
    CcCudaBuffer &operator=(const CcCudaBuffer &)=delete;
};
class CcCuda {
    std::string label;
public:
    CcCuda(int ordinal,const char *) {
        cc_cuda_check(cudaSetDevice(ordinal));
        cudaDeviceProp props{};cc_cuda_check(cudaGetDeviceProperties(&props,ordinal));
        label=props.name;
    }
    const char *kind() const {return "cuda";}
    const std::string &name() const {return label;}
    void execute(CcRequest &r) {
        unsigned threads=64,blocks=(r.n+threads-1)/threads;
        if (r.op==3) {
            std::size_t n=r.n*sizeof(CcRho);
            CcCudaBuffer in(n,r.states.data()),out(n);
            certicom_rho<<<blocks,threads>>>(r.curve,static_cast<CcRho *>(in.p),
                                           static_cast<CcRho *>(out.p),r.n,r.steps);
            cc_cuda_check(cudaGetLastError());cc_cuda_check(cudaDeviceSynchronize());
            cc_cuda_check(cudaMemcpy(r.rho.data(),out.p,n,cudaMemcpyDeviceToHost));
        } else {
            std::size_t n=r.n*sizeof(CcPoint);
            CcCudaBuffer left(n,r.left.data()),out(n);
            if (r.op==1) {
                CcCudaBuffer right(n,r.right.data());
                certicom_add<<<blocks,threads>>>(r.curve,static_cast<CcPoint *>(left.p),
                    static_cast<CcPoint *>(right.p),static_cast<CcPoint *>(out.p),r.n);
                cc_cuda_check(cudaGetLastError());cc_cuda_check(cudaDeviceSynchronize());
            } else {
                CcCudaBuffer scalars(r.n*sizeof(CcInteger),r.scalars.data());
                certicom_mul<<<blocks,threads>>>(r.curve,static_cast<CcPoint *>(left.p),
                    static_cast<CcInteger *>(scalars.p),static_cast<CcPoint *>(out.p),r.n);
                cc_cuda_check(cudaGetLastError());cc_cuda_check(cudaDeviceSynchronize());
            }
            cc_cuda_check(cudaMemcpy(r.points.data(),out.p,n,cudaMemcpyDeviceToHost));
        }
    }
};
int main(int argc,char **argv) {return cc_worker_main<CcCuda>(argc,argv);}
