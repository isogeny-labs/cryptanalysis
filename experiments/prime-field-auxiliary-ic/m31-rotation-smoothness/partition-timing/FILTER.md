# Opposite-orientation bucket filter

Compare the frozen complete sort-and-match census with a 1 MiB byte table indexed by the low 20 bits of the smaller reciprocal key. Set a presence bit for each observed orientation. Compact the integer vector to entries in buckets with both bits set before the same exact sort and pair extraction. Inputs and outputs stay identical. Allocation and clearing are inside every call.

Run --hash-filter at bounds 67, 83 and 89 with clang++ -O3 -std=c++17 -mcpu=native. Use the prior control, two copies of each arm, twelve rounds at each bound and a four-order balanced crossover. Check the entire output after every call. Report the median paired ratio of the two-arm mean times per round and the A/A ratio. Diagnostic survivor counts come from the untimed initial call. No performance threshold is used to discard rows.
