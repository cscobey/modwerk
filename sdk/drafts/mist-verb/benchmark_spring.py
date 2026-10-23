#!/usr/bin/env python3
# Copyright 2026 cscobey. MIT; see LICENSE.
"""Compare one Mist Verb and stock SPRING REV instance/core, privately.

This measures executed instructions under a finite workload, not chip cycles,
maximum supported instances, hardware headroom or release qualification.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sdk', 'stock', 'host', 'native-render', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--blocks', type=int, default=1024)
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('Use a private output directory')
    if args.blocks < 1024:
        parser.error('At least 1024 blocks are required')
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.sdk / 'tools'))
    import toolpath  # Exposes the SDK build/harness paths; no source writes.
    import send_probe
    from remix import stock
    stock._img = args.stock.read_bytes()
    parameters = stock._params(0x400d5726, 'SPRING REV', 'SPRING REV')
    type_index = next(i for i, p in enumerate(parameters) if p.name == b'TYPE')
    type_count = parameters[type_index].count
    if type_count != 3:
        raise RuntimeError('Unexpected SPRING REV descriptor')
    spec = importlib.util.spec_from_file_location('modmap', args.sdk / 'tools/build/dsp_modmap.py')
    modmap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modmap)
    for core in 'AB':
        modmap.dumpmem(stock._img, [core, str(out / (core + '.mem'))])
    spring_entries = [send_probe.entry_points(out / (core + '.mem'), 0x15) for core in 'AB']
    native = args.native_render
    native_report = json.loads((native / 'report.json').read_text())
    for name, sha in native_report['sourceHashes'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != sha:
            raise RuntimeError('Native render is stale: ' + name)
    symbols = {name: int(address, 16) for name, address in
               (line.split() for line in (native / 'src.sym').read_text().splitlines())}
    input_data = (native / 'input.raw').read_bytes()[:args.blocks * 16 * 8]
    if len(input_data) != args.blocks * 16 * 8:
        raise RuntimeError('Native render input is too short')
    (out / 'input.raw').write_bytes(input_data)

    def schedule(kind, type_value=0):
        rows = []
        for block in range(args.blocks):
            if kind == 'spring':
                values = [p.default or 0 for p in parameters]
                active = [i for i, p in enumerate(parameters) if p.active and i != type_index]
            else:
                values = [110, 64, 94, 0, 83, 127] + [0] * 6
                active = range(6)
            # Hold both extremes, then move each active knob every block.
            # Spring TYPE stays fixed so expensive modes are not diluted.
            for i in active:
                values[i] = (0 if block < 384 else 127 if block < 512
                             else ((block + 11 * i) * (2 * i + 1)) % 128)
            if kind == 'spring':
                values[type_index] = type_value
            rows.append(','.join(map(str, [block] + values)))
        path = out / f'{kind}-{type_value}.csv'
        path.write_text('\n'.join(rows) + '\n')
        return path

    schedules = {('spring', n): schedule('spring', n) for n in range(type_count)}
    schedules['mist', 0] = schedule('mist')

    def run(case):
        kind, type_value, split = case
        tag = f'{kind}-{type_value}-split{split:02}'
        folder = out / tag
        folder.mkdir(exist_ok=True)
        memories = [out / (c + '.mem') for c in 'AB'] if kind == 'spring' else [native / (c + '.mem') for c in 'AB']
        entries = spring_entries if kind == 'spring' else [(symbols['init'], symbols['proc'])] * 2
        automation = schedules[kind, type_value]
        cmd = [str(args.host), '-mem', str(memories[0]), '-memB', str(memories[1]),
               '-init', ','.join(format(e[0], 'x') for e in entries),
               '-proc', ','.join(format(e[1], 'x') for e in entries),
               '-inst', '2', '-core', '0,1', '-alloc', '1,1', '-r7', '2,2',
               '-audioidx', '0,0', '-allocproc', 'end', '-audio', '0',
               '-frames', '16', '-blocks', str(args.blocks), '-split', str(split),
               '-in', str(out / 'input.raw') + ',' + str(out / 'input.raw'), '-stereo',
               '-dirty', '1776', '-out', str(folder / 'audio.raw'),
               '-meter', str(folder / 'meter.txt'),
               '-params', '110,64,94,0,83,127,0,0,0,0,0,0',
               '-params', '110,64,94,0,83,127,0,0,0,0,0,0',
               '-paramfile', str(automation), '-paramfile', str(automation)]
        (folder / 'command.json').write_text(json.dumps(cmd, indent=2) + '\n')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        (folder / 'run.log').write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(tag + ': ' + (result.stdout + result.stderr)[-1500:])
        meters = [[int(v) for v in row.split()] for row in (folder / 'meter.txt').read_text().splitlines()]
        if len(meters) != args.blocks:
            raise RuntimeError(tag + ': incomplete meter')
        audio = (folder / 'audio.raw').read_bytes()
        if audio != (folder / 'audio.raw.i1').read_bytes():
            raise RuntimeError(tag + ': cores differ')
        return {'effect': kind, 'springType': type_value if kind == 'spring' else None,
                'split': split,
                'peakInstructionsPer16Frames': [max(row[k] for row in meters) for k in (1, 2)],
                'meanAfter256Blocks': [sum(row[k] for row in meters[256:]) / (args.blocks - 256) for k in (1, 2)],
                'coreOutputsIdentical': True}

    cases = [('spring', n, split) for n in range(type_count) for split in range(16)]
    cases += [('mist', 0, split) for split in range(16)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(run, cases))
    peaks = {effect: max(v for row in results if row['effect'] == effect
                         for v in row['peakInstructionsPer16Frames']) for effect in ('spring', 'mist')}
    report = {'scope': 'Finite matched standalone emulator workload, one instance/core; not hardware cycles or release qualification',
              'units': 'executed instructions/core/16 input frames', 'sampleRate': 44100,
              'blocks': args.blocks, 'instancesPerCore': 1, 'cores': [0, 1],
              'splits': list(range(16)), 'springTypes': list(range(type_count)),
              'movingControls': True, 'inputSha256': hashlib.sha256(input_data).hexdigest(),
              'stockSha256': hashlib.sha256(stock._img).hexdigest(), 'peak': peaks,
              'mistToSpringPeakRatio': peaks['mist'] / peaks['spring'],
              'sourceHashes': {'benchmark_spring.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               **native_report['sourceHashes']}, 'results': results}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('results', 'sourceHashes')}, indent=2))


if __name__ == '__main__':
    main()
