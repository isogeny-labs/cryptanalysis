CXX ?= c++
NVCC ?= nvcc
ARCH ?= sm_80
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra -Werror
.PHONY: all host cuda metal clean
all: host
host: certicom_emulator
certicom_emulator: emulator.cpp arithmetic.h wire.hpp
	$(CXX) $(CXXFLAGS) emulator.cpp -o $@
cuda: certicom_cuda
certicom_cuda: cuda.cu kernels.cu arithmetic.h wire.hpp
	$(NVCC) -O2 -std=c++17 -arch=$(ARCH) cuda.cu -o $@
metal: certicom_metal certicom.metallib
certicom.air: kernels.metal arithmetic.h
	xcrun -sdk macosx metal -std=metal3.0 -I. -c kernels.metal -o $@
certicom.metallib: certicom.air
	xcrun -sdk macosx metallib $< -o $@
certicom_metal: metal.mm arithmetic.h wire.hpp
	xcrun clang++ $(CXXFLAGS) -fobjc-arc -framework Foundation -framework Metal metal.mm -o $@
clean:
	rm -f certicom_emulator certicom_cuda certicom_metal certicom.air certicom.metallib
