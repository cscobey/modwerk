#!/usr/bin/env python3
# Copyright 2026 cscobey. MIT; see LICENSE.
"""Verify assembled DSP SRC against the integer host reference, privately."""
import argparse, array, hashlib, importlib.util, json, math, struct, subprocess, sys
from pathlib import Path
from verify_src import compile_source
from control_reference import TRACE, events, verify_trace
ROOT = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('sdk', 'stock', 'assembler', 'host', 'disassembler', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--frames', type=int, default=7056)
    p.add_argument('--controls', default='110,64,94,83')
    p.add_argument('--signal', choices=('noise', 'silence', 'dc', 'impulse'), default='noise')
    p.add_argument('--mix', type=int, default=127, choices=range(128))
    p.add_argument('--reverb', action='store_true')
    p.add_argument('--control-events', action='store_true')
    p.add_argument('--full-scale', action='store_true')
    p.add_argument('--split', type=int, default=0, choices=range(16))
    args = p.parse_args()
    out = args.output.resolve()
    controls = [int(v) for v in args.controls.split(',')]
    if len(controls) != 4 or any((not 0 <= v <= 127 for v in controls)):
        p.error('Controls need four values 0..127')
    params = ','.join(map(str, controls[:3] + [0, controls[3], args.mix] + [0] * 6))
    if out == ROOT or ROOT in out.parents:
        p.error('Use a private output directory')
    if args.frames <= 0 or args.frames % 7056:
        p.error('Frames must be a multiple of 7056')
    if args.control_events and (not args.reverb or args.frames < 7056):
        p.error('Control events require the joined reverb path and at least 7056 frames')
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-B', str(ROOT / 'generate_native_src.py'), '--check'], check=True)
    sys.path.insert(0, str(args.sdk / 'tools/build'))
    from nolabelprefix import refuse_label_prefix
    assembly = ROOT / ('core44100.asm' if args.reverb else 'native_src.asm')
    refuse_label_prefix(assembly.read_text())
    subprocess.run([str(args.assembler), '-in', str(assembly), '-org', '15000', '-out', str(out / 'src.bin'), '-sym', str(out / 'src.sym')], check=True)
    listing = subprocess.check_output([str(args.disassembler), '-in', str(out / 'src.bin'), '-pc', '15000', '-le'], text=True)
    if any((x in listing.lower() for x in ('mpysu', 'invalid', '\trep '))):
        raise RuntimeError('Unexpected instruction')
    (out / 'disassembly.txt').write_text(listing)
    sym = {s: int(v, 16) for (s, v) in (line.split() for line in (out / 'src.sym').read_text().splitlines())}
    blob = (out / 'src.bin').read_bytes()
    words = [int.from_bytes(blob[i:i + 3], 'little') for i in range(0, len(blob), 3)]
    table = json.loads((ROOT / 'native_src_tables.json').read_text())
    regions = [(86016, words), (table['base'], table['words'])]
    if args.reverb:
        if words.count(16429536) != 1:
            raise RuntimeError('Gain marker drift')
        words[words.index(16429536)] = 81920
        regions.append((81920, [min(8388607, round(10 ** ((-40 + 40 * n / 127) / 20) * 8388608)) for n in range(128)]))
    spec = importlib.util.spec_from_file_location('modmap', args.sdk / 'tools/build/dsp_modmap.py')
    modmap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modmap)
    for core in 'AB':
        path = out / (core + '.mem')
        modmap.dumpmem(args.stock.read_bytes(), [core, str(path)])
        data = path.read_bytes()
        offset = 0
        while offset + 9 <= len(data):
            (space, start, count) = struct.unpack_from('<BII', data, offset)
            if space == 255:
                break
            if space == 0:
                for (address, values) in regions:
                    if start < address + len(values) and start + count > address:
                        raise RuntimeError('Placement overlap')
            offset += 9 + count * 4
        data = data[:offset]
        for (address, values) in regions:
            data += struct.pack('<BII', 0, address, len(values)) + struct.pack('<' + 'I' * len(values), *values)
        path.write_bytes(data + struct.pack('<BII', 255, 0, 0))

    def write(path, values):
        path.write_bytes(struct.pack('<' + 'i' * len(values), *values))

    def read(path):
        a = array.array('i')
        a.frombytes(path.read_bytes())
        if sys.byteorder != 'little':
            a.byteswap()
        return list(a)
    seed = 42
    values = []
    for n in range(args.frames):
        seed = 1664525 * seed + 1013904223 & 4294967295
        values.extend((0 if n < 128 else (seed >> 8) - 8388608 if args.full_scale else (seed >> 11) - 1048576, 0 if n < 128 else round(0.15 * 8388608 * math.sin(2 * math.pi * 13000 * n / 44100))))
    prefix = (102 if args.split == 0 else 51) * 16 if args.reverb else 0
    if args.signal == 'silence':
        values = [0] * len(values)
    elif args.signal == 'dc':
        values = [v for _ in range(args.frames) for v in (1048576, -524288)]
    elif args.signal == 'impulse':
        values = [0] * 256 + [2097152, -1048576] + [0] * (len(values) - 258)
    elif not args.full_scale:
        values[args.frames:] = [0] * args.frames
    write(out / 'conversion-input.raw', values)
    write(out / 'input.raw', [0] * (prefix * 2) + values)
    if not args.control_events:
        compile_source('src_convert.cpp', out / 'convert')
        subprocess.run([str(out / 'convert'), 'down', str(out / 'conversion-input.raw'), str(out / 'down.raw')], check=True)
        up_input = out / 'down.raw'
        if args.reverb:
            write(out / 'tank-input.raw', [0] * 3264 + read(out / 'down.raw'))
            command = [sys.executable, '-B', str(ROOT / 'render_core32.py')]
            for name in ('sdk', 'stock', 'assembler', 'host', 'disassembler'):
                command += ['--' + name, str(getattr(args, name))]
            command += ['--controls', args.controls, '--input-stereo', str(out / 'tank-input.raw'), '--output', str(out / 'tank')]
            subprocess.run(command, check=True)
            up_input = out / 'tank-wet.raw'
            write(up_input, read(out / 'tank/wet.raw')[3264:])
        subprocess.run([str(out / 'convert'), 'up', str(up_input), str(out / 'reference.raw')], check=True)
    cmd = [str(args.host), '-mem', str(out / 'A.mem'), '-memB', str(out / 'B.mem'), '-init', format(sym['init'], 'x'), '-proc', format(sym['proc'], 'x'), '-inst', '2', '-core', '0,1', '-alloc', '1,1', '-r7', '2,2', '-audioidx', '0,0', '-frames', '16', '-blocks', str((args.frames + prefix) // 16), '-in', str(out / 'input.raw') + ',' + str(out / 'input.raw'), '-stereo', '-split', str(args.split), '-allocproc', 'end', '-audio', '0', '-guard', '13808', '-guard-shared', '-dirty', '1776', '-out', str(out / 'native.raw'), '-meter', str(out / 'native.meter'), '-trackout', str(out / 'track.txt'), '-track', '79,85', '-params', params, '-params', params]
    timeline = None
    if args.control_events:
        timeline = events(controls[:3] + [0, controls[3], args.mix] + [0] * 6, prefix // 16)
        automation = out / 'parameters.csv'
        automation.write_text(''.join(','.join(map(str, [block] + values)) + '\n'
                                      for block, values in sorted(timeline.items())))
        cmd += ['-paramfile', str(automation), '-paramfile', str(automation)]
        cmd[cmd.index('-track') + 1] += ',' + ','.join(format(v, 'x') for v in TRACE)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    (out / 'native.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr)[-3000:])
    actual = read(out / 'native.raw')
    other = read(out / 'native.raw.i1')
    if actual != other:
        raise RuntimeError('Cores differ')
    if args.control_events:
        reference = None
        if args.signal == 'silence' and any(actual):
            raise RuntimeError('Control changes produce nonzero output from silence')
    else:
        reference = [0] * (prefix * 2 + 4) + read(out / 'reference.raw')[:-4]
        if args.reverb and args.mix != 127:
            dry = [0] * (prefix * 2) + values
            reference = dry if args.mix == 0 else [max(-8388608, min(8388607, d + (w - d) * (args.mix << 16) // (1 << 23))) for (d, w) in zip(dry, reference)]
        if len(actual) != len(reference):
            raise RuntimeError('Frame count mismatch')
        errors = [a - b for (a, b) in zip(actual, reference)]
    meters = [[int(v) for v in row.split()] for row in (out / 'native.meter').read_text().splitlines()]
    track = [[int(v) for v in row.split()] for row in (out / 'track.txt').read_text().splitlines()]
    if any((not 0 <= row[1] <= 4 for row in track)):
        raise RuntimeError('FIFO occupancy out of range')
    trace_result = verify_trace(track, prefix, timeline) if args.control_events else None
    errors = [] if args.control_events else errors
    report = {'controlTrace': trace_result, 'peakInstructionsPer16Frames': [max((row[k] for row in meters)) for k in (1, 2)], 'fifoOccupancyRange': [min((row[1] for row in track)), max((row[1] for row in track))], 'yExtentWords': 13808, 'scope': 'Native 44.1 kHz experiment; no installed effect or hardware qualification' if args.reverb else 'Standalone native SRC round trip; no reverb or hardware qualification', 'controls': controls, 'signal': args.signal, 'mix': args.mix, 'fullScaleInput': args.full_scale, 'reverb': args.reverb, 'frames': args.frames + prefix, 'split': args.split, 'programWords': len(words), 'tableWords': len(table['words']), 'startupFifoFrames': 2, 'coreOutputsIdentical': True, 'exactHostParity': None if args.control_events else not any(errors), 'maxErrorLsb': max(map(abs, errors), default=0), 'firstMismatch': None if args.control_events else next(((i, a, b) for (i, (a, b)) in enumerate(zip(actual, reference)) if a != b), None), 'sourceHashes': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ('generate_native_src.py', 'native_src.asm', 'native_src_tables.json', 'rational_src.h', 'core44100.asm', 'core32.asm', 'control_reference.py')}}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if any(errors):
        raise RuntimeError('Native SRC differs from reference')
if __name__ == '__main__':
    main()
