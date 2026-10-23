// Copyright 2026 cscobey. MIT; see LICENSE.
// Host model for a lossless three-16-bit-cells / two-24-bit-words layout.
// This proves storage semantics; it is not executable DSP56300 code.
#pragma once
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>

namespace mist {
template<std::size_t N>
class Packed16 {
 public:
  static constexpr std::size_t kWords = ((N + 2) / 3) * 2;
  void Clear() { words_.fill(0); }
  uint16_t Read(std::size_t i) const {
    assert(i < N);
    auto p = (i / 3) * 2;
    switch (i % 3) {
      case 0: return uint16_t(words_[p] >> 8);
      case 1: return uint16_t((words_[p] << 8) | (words_[p + 1] >> 16));
      default: return uint16_t(words_[p + 1]);
    }
  }
  void Write(std::size_t i, uint16_t v) {
    assert(i < N);
    auto p = (i / 3) * 2;
    switch (i % 3) {
      case 0:
        words_[p] = (uint32_t(v) << 8) | (words_[p] & 0xff);
        break;
      case 1:
        words_[p] = (words_[p] & 0xffff00) | (v >> 8);
        words_[p + 1] = (words_[p + 1] & 0xffff) | (uint32_t(v & 0xff) << 16);
        break;
      default:
        words_[p + 1] = (words_[p + 1] & 0xff0000) | v;
    }
  }
  struct Cell {
    Packed16& owner;
    std::size_t i;
    operator uint16_t() const { return owner.Read(i); }
    Cell& operator=(uint16_t value) { owner.Write(i, value); return *this; }
  };
  Cell operator[](std::size_t i) { return {*this, i}; }
  uint16_t operator[](std::size_t i) const { return Read(i); }
  bool ValidWords() const {
    for (auto word : words_) if (word > 0xffffff) return false;
    return true;
  }
 private:
  std::array<uint32_t, kWords> words_{};
};
}  // namespace mist
