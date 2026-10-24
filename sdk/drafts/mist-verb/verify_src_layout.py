#!/usr/bin/env python3
# Copyright 2026 cscobey. MIT; see LICENSE.
"""Verify the lossless SRC layout used by the native DSP experiment."""
import argparse
import hashlib
import json
from pathlib import Path

from src_layout import packed_bank

ROOT = Path(__file__).resolve().parent



def decode(data, descriptors, phase, taps):
    word = descriptors[phase]
    start = word & ((1 << 17) - 1)
    step = -1 if word & (1 << 17) else 1
    count = taps - bool(word & (1 << 18))
    return [data[start + step * i] for i in range(count)] + [0] * (taps - count)


def report():
    banks = []
    actual = json.loads((ROOT / 'native_src_tables.json').read_text())
    words, base = actual['words'], actual['base']
    coefficient_cursor, descriptor_cursor = 0, 2558
    schedule_cursor = 2624
    for rate, output, taps in ((44100, 32000, 96), (32000, 44100, 48)):
        rows, data, descriptors = packed_bank(rate, taps)
        assert [decode(data, descriptors, p, taps) for p in range(33)] == rows
        assert words[coefficient_cursor:coefficient_cursor+len(data)] == [v & 0xffffff for v in data]
        assert words[descriptor_cursor:descriptor_cursor+33] == descriptors
        period = output // 100
        # Check both endpoints of every phase interpolation in a complete
        # rational clock period, including endpoint 32 and all reverse rows.
        endpoint_checks = 0
        for n in range(period):
            phase, remainder = divmod(((n * rate) % output) * 32, output)
            weight = (remainder << 23) // output
            assert 0 <= weight < 1 << 23
            assert words[schedule_cursor+2*n:schedule_cursor+2*n+2] == [base+descriptor_cursor+phase, weight]
            for endpoint in (phase, phase + 1):
                assert decode(data, descriptors, endpoint, taps) == rows[endpoint]
                endpoint_checks += 1
        coefficient_cursor += len(data)
        descriptor_cursor += 33
        schedule_cursor += period * 2
        banks.append(dict(inputRate=rate, outputRate=output, taps=taps,
                          originalCoefficientWords=33 * taps,
                          packedCoefficientWords=len(data), descriptorWords=33,
                          exactRows=33, scheduleEndpointChecks=endpoint_checks))
    coefficients = sum(b['packedCoefficientWords'] for b in banks)
    descriptors = sum(b['descriptorWords'] for b in banks)
    schedule = 2 * (320 + 441)
    assert coefficient_cursor == 2558 and descriptor_cursor == 2624
    assert schedule_cursor == len(words) == 4146
    native = json.loads((ROOT / 'evidence/optimization/wet.json').read_text())
    for name, sha in native['sourceHashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
    assert native['tableWords'] == len(words)
    assert native['coreOutputsIdentical'] and native['exactHostParity']
    total = native['programWords'] + native['tableWords'] + 128
    return dict(scope='Host reconstruction and schedule check of actual native tables; native parity report source hashes verified',
                sourceHashes={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in ('generate_src.py', 'src_layout.py', 'verify_src_layout.py', 'native_src_tables.json')},
                banks=banks, unchangedScheduleWords=schedule,
                currentProgramAndTablesWords=total,
                nativeTableWords=coefficients + descriptors + schedule,
                nativeParityReport="evidence/optimization/wet.json",
                savedTableWords=4752 - coefficients - descriptors,
                documentedEmptyArenaWords=[4304, 4432],
                minimumDeficitWords=[total - n for n in (4304, 4432)],
                nativeDecoderImplemented=True, installedFitProven=False)


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
