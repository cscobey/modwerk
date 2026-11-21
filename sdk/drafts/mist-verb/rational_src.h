// Copyright 2026 cscobey. MIT; see LICENSE.
// Streaming, integer-arithmetic host reference. Not DSP56300 executable code.
#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <stdexcept>
#include <vector>
#include "src_coefficients.h"

namespace mist {
struct Stereo24 {
  int32_t l = 0, r = 0;
  bool operator==(const Stereo24& other) const { return l == other.l && r == other.r; }
};

class RationalSrc {
 public:
  explicit RationalSrc(bool down)
      : input_rate_(down ? 44100 : 32000), output_rate_(down ? 32000 : 44100),
        taps_(down ? 96 : 48), coefficients_(down ? kSrcDown : kSrcUp) {}

  void Reset() {
    history_.fill({}); cursor_ = 0; clock_ = 0; clipped_ = 0;
  }
  int input_rate() const { return input_rate_; }
  int output_rate() const { return output_rate_; }
  int taps() const { return taps_; }
  uint64_t clipped() const { return clipped_; }
  double delay_seconds() const { return (taps_ - 1) * .5 / input_rate_; }

  void Process(const Stereo24* input, std::size_t count, std::vector<Stereo24>& output) {
    for (std::size_t n = 0; n < count; ++n) {
      if (input[n].l < -8388608 || input[n].l > 8388607 ||
          input[n].r < -8388608 || input[n].r > 8388607)
        throw std::invalid_argument("SRC input exceeds signed 24-bit range");
      history_[cursor_] = input[n];
      // Bounded integer clock: exact 320:441 ratio, independent of chunk size.
      while (clock_ < output_rate_) {
        const int position = clock_ * kSrcPhases;
        const int phase = position / output_rate_;
        const int64_t weight = (int64_t(position % output_rate_) << 23) / output_rate_;
        int64_t left[2] = {}, right[2] = {};
        int index = cursor_;
        for (int k = 0; k < taps_; ++k) {
          const Stereo24 value = history_[index];
          for (int side = 0; side < 2; ++side) {
            const int32_t c = coefficients_[(phase + side) * taps_ + k];
            left[side] += int64_t(value.l) * c;
            right[side] += int64_t(value.r) * c;
          }
          if (--index < 0) index = taps_ - 1;
        }
        output.push_back({Interpolate(left, weight), Interpolate(right, weight)});
        clock_ += input_rate_;
      }
      clock_ -= output_rate_;
      if (++cursor_ == taps_) cursor_ = 0;
    }
  }

 private:
  static int64_t Rounded(int64_t value) {
    return value >= 0 ? (value + (1 << 22)) / (1 << 23)
                      : -((-value + (1 << 22)) / (1 << 23));
  }
  int32_t Interpolate(const int64_t sums[2], int64_t weight) {
    // Round the wide MAC outputs before the phase blend to keep its product
    // in int64. No float clock, samples, coefficients or runtime arithmetic.
    const int64_t a = Rounded(sums[0]), b = Rounded(sums[1]);
    const int64_t result = a + Rounded((b - a) * weight);
    if (result < -8388608 || result > 8388607) ++clipped_;
    return int32_t(std::clamp<int64_t>(result, -8388608, 8388607));
  }
  int input_rate_, output_rate_, taps_;
  const int32_t* coefficients_;
  std::array<Stereo24, 96> history_{};
  int cursor_ = 0, clock_ = 0;
  uint64_t clipped_ = 0;
};
}  // namespace mist
