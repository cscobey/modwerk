# Copyright 2026 cscobey. MIT; see LICENSE.
"""Lossless mirrored layout for the original 32-phase SRC banks."""
from generate_src import bank


def packed_bank(rate, taps):
    rows = bank(rate, taps)
    data, descriptors = [], []
    # The terminal phase has its own normalization: do not infer it from phase 0.
    canonical = {}
    for phase in [0, *range(1, 17), 32]:
        row = rows[phase]
        if phase:
            assert row[-1] == 0
            row = row[:-1]
        canonical[phase] = len(data)
        data.extend(row)
    for phase in range(33):
        mirror = 16 < phase < 32
        source = 32 - phase if mirror else phase
        count = taps if phase == 0 else taps - 1
        start = canonical[source] + (count - 1 if mirror else 0)
        step = -1 if mirror else 1
        # One 24-bit relative descriptor: pointer 0..16, reverse 17, short 18.
        assert start < 1 << 17
        word = start | (int(mirror) << 17) | (int(phase != 0) << 18)
        descriptors.append(word)
        recovered = [data[start + step * i] for i in range(count)]
        if count < taps:
            recovered.append(0)
        assert recovered == rows[phase], (rate, phase)
    return rows, data, descriptors

