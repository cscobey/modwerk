#!/usr/bin/env python3
# Copyright 2026 cscobey. MIT; see LICENSE.
"""Check a lossless SRC table layout proposal; does not change native DSP."""
import argparse
import hashlib
import json
from pathlib import Path

from generate_src import bank

ROOT = Path(__file__).resolve().parent


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


def decode(data, descriptors, phase, taps):
    word = descriptors[phase]
    start = word & ((1 << 17) - 1)
    step = -1 if word & (1 << 17) else 1
    count = taps - bool(word & (1 << 18))
    return [data[start + step * i] for i in range(count)] + [0] * (taps - count)


def report():
    banks = []
    for rate, output, taps in ((44100, 32000, 96), (32000, 44100, 48)):
        rows, data, descriptors = packed_bank(rate, taps)
        assert [decode(data, descriptors, p, taps) for p in range(33)] == rows
        period = output // 100
        # Check both endpoints of every phase interpolation in a complete
        # rational clock period, including endpoint 32 and all reverse rows.
        endpoint_checks = 0
        for n in range(period):
            phase, remainder = divmod(((n * rate) % output) * 32, output)
            assert 0 <= (remainder << 23) // output < 1 << 23
            for endpoint in (phase, phase + 1):
                assert decode(data, descriptors, endpoint, taps) == rows[endpoint]
                endpoint_checks += 1
        banks.append(dict(inputRate=rate, outputRate=output, taps=taps,
                          originalCoefficientWords=33 * taps,
                          packedCoefficientWords=len(data), descriptorWords=33,
                          exactRows=33, scheduleEndpointChecks=endpoint_checks))
    coefficients = sum(b['packedCoefficientWords'] for b in banks)
    descriptors = sum(b['descriptorWords'] for b in banks)
    schedule = 2 * (320 + 441)
    native = json.loads((ROOT / 'evidence/performance-controls/ramp-final-wet.json').read_text())
    total = native['programWords'] + native['tableWords'] + 128
    proposed = native['programWords'] + coefficients + descriptors + schedule + 128
    return dict(scope='Host layout proof only; native DSP still uses full tables',
                sourceHashes={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in ('generate_src.py', 'verify_src_layout.py')},
                banks=banks, unchangedScheduleWords=schedule,
                currentProgramAndTablesWords=total,
                proposedTablesWords=coefficients + descriptors + schedule,
                proposedTotalBeforeDecoderChanges=proposed,
                savedTableWords=4752 - coefficients - descriptors,
                documentedEmptyArenaWords=[4304, 4432],
                minimumDeficitBeforeDecoderChanges=[proposed - n for n in (4304, 4432)],
                nativeDecoderImplemented=False, installedFitProven=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = json.dumps(report(), indent=2) + '\n'
    target = ROOT / 'evidence/src-layout.json'
    if args.check:
        assert target.read_text() == text, 'Layout evidence is stale'
        print('All 66 coefficient rows and 1522 schedule endpoints match exactly.')
    else:
        target.write_text(text)
        print(text, end='')
