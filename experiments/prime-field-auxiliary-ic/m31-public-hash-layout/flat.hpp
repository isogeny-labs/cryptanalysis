// M31 signed keys and x coordinates fit below UINT32_MAX.
class FlatIndex {
  using Entry = std::pair<uint32_t, uint32_t>;
  std::vector<Entry> slots_;
  size_t used_ = 0;
  size_t slot(U key) const {
    const size_t mask = slots_.size() - 1;
    size_t i = Hasher{}(key) & mask;
    while (slots_[i].first != UINT32_MAX && slots_[i].first != key)
      i = (i + 1) & mask;
    return i;
  }
public:
  void reserve(size_t bound) {
    size_t capacity = 1;
    while (capacity < 2 * bound)
      capacity *= 2;
    slots_.assign(capacity, {UINT32_MAX, 0});
  }
  void emplace(U key, uint32_t value) {
    auto &entry = slots_[slot(key)];
    if (entry.first == UINT32_MAX) {
      entry = {static_cast<uint32_t>(key), value};
      ++used_;
    }
  }
  const Entry *find(U key) const {
    auto &entry = slots_[slot(key)];
    return entry.first == UINT32_MAX ? nullptr : &entry;
  }
  const Entry *end() const { return nullptr; }
  size_t size() const { return used_; }
};
