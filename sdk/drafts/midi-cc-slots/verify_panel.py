#!/usr/bin/env python3
"""Execute real MKII panel edits and inspect UART0 via the private monitor.

This stopped-panel gate does not claim sequencer or persistence coverage.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--emulator', type=Path, required=True)
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--sequencer', action='store_true', help='also attempt the unqualified lock fixture')
a = p.parse_args()
out = a.output.resolve()
if any((v/'.git').exists() for v in [out, *out.parents]):
    p.error('private output must be outside Git')
out.mkdir(parents=True, exist_ok=False)
port = subprocess.Popen([str(a.emulator.resolve()), '--image', str(a.candidate.resolve()),
    '--mkii', '--boot-logo', '--ms', '4000', '--interactive', '--internal-clock', '--rtc', 'off',
    '--main-level', 'off', '--lcd', str(out/'lcd.private.bin')],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=(out/'stderr.private.log').open('wb'))
selector = selectors.DefaultSelector()
selector.register(port.stdout, selectors.EVENT_READ)
pending = b''
steps = []
checks = []
rows = [0]*8
keys = {'YES': 0x31, 'NO': 0x32, 'MIDI': 0x35, 'FUNC': 0x2d,
        'SRC': 0x22, 'FX1': 0x25, 'FX2': 0x26, 'REC': 0x29,
        'PLAY': 0x28, 'STOP': 0x27, 'TRIG1': 0,
        **{f'T{i+1}': 0x10+i for i in range(8)},
        **{f'PUSH {c}': 0x38+i for i, c in enumerate('ABCDEF')}}

def response(prefix):
    global pending
    deadline = time.monotonic()+180
    while time.monotonic() < deadline:
        while b'\n' in pending:
            line, pending = pending.split(b'\n', 1)
            if line.startswith(prefix):
                return line.decode()
        if port.poll() is not None:
            raise RuntimeError('emulator exited before reply')
        if selector.select(1):
            pending += os.read(port.stdout.fileno(), 65536)
    raise TimeoutError('emulator reply timeout')

def command(value):
    port.stdin.write((value+'\n').encode())
    port.stdin.flush()
    reply = response((b'ok', b'run ', b'err', b'midi-tx ', b'peek ', b'hits '))
    steps.append([value, reply])
    if reply.startswith('err') or ('stop=' in reply and 'stop=time' not in reply):
        raise RuntimeError(reply)
    return reply

def advance(ms=100):
    command(f'run {ms}')

def key(name, down):
    code = keys[name]
    row, bit = code >> 3, 1 << (code & 7)
    rows[row] = rows[row] | bit if down else rows[row] & ~bit
    command(f'key {32|row} {rows[row]}')
    advance(50)

def press(*names):
    for name in names:
        key(name, True)
    for name in reversed(names):
        key(name, False)

def encoder(name, delta):
    command(f'knob {48+"ABCDEF".index(name)} {delta}')
    advance(200)

def wire():
    return bytes.fromhex(command('midi-tx').split(' ', 1)[1])

def messages():
    result, data, status = [], [], None
    for byte in wire():
        if byte >= 0xf8:
            continue
        if byte & 0x80:
            assert byte < 0xf0, 'unexpected system message in this stopped-panel fixture'
            status, data = byte, []
            continue
        assert status is not None, 'data without running status'
        data.append(byte)
        if len(data) == (1 if status & 0xf0 in [0xc0, 0xd0] else 2):
            result.append(bytes([status, *data]))
            data = []
    assert not data, 'incomplete MIDI message after settling'
    return result

def contains(channel, cc, value, before, label):
    new = messages()[before:]
    expected = bytes([0xb0+channel, cc, value])
    assert expected in new, f'{label}: wanted {expected.hex()}, observed {[v.hex() for v in new]}'
    assert all(v[0] & 0xf0 not in [0xd0, 0xe0] for v in new), f'{label}: native PB/AT leaked'
    checks.append(label)

try:
    response(b'ready ')
    advance()
    press('YES')
    press('NO')
    press('MIDI')
    for track in range(8):
        press(f'T{track+1}')
        press('FUNC', 'SRC')
        # Stock channel selector uses four encoder counts per increment.
        encoder('A', 4*(track+1))
        press('YES')
        # Stock applies encoder acceleration. Confirm the actual channel byte,
        # then use individual detents to reach the requested distinct channel.
        for attempt in range(64):
            channel = int(command(f'peek {hex(0x40171442+36*track)} 1').split()[1], 16)
            if channel == track+1:
                break
            encoder('A', 4 if channel < track+1 else -4)
            press('YES')
        else:
            raise AssertionError('could not select the required stock channel')
        press('SRC')
        press('FUNC', 'FX1')
        encoder('A', 1)       # encoded CC0
        encoder('B', 127)
        encoder('B', 1)       # encoded CC127
        press('YES')
        press('FX1')
        press('FUNC', 'PUSH A')
        press('FUNC', 'PUSH B')
        for slot, cc, initial in [('A', 0, 64), ('B', 127, 0)]:
            current = initial
            for value in [1, 63, 64, 126, 127, 0]:
                before = len(messages())
                encoder(slot, value-current)
                contains(track, cc, value, before, f'track {track+1} {slot} CC{cc} value {value}')
                current = value
        print(f'track {track+1}: endpoint panel checks passed', flush=True)
    press('T1')
    current_a = current_b = 0
    for cc in range(1, 128):
        press('FUNC', 'FX1')
        encoder('A', 1)
        encoder('B', -1)
        press('YES')
        press('FX1')
        for slot, controller, value, previous in [
            ('A', cc, cc, current_a), ('B', 127-cc, 128-cc, current_b)]:
            before = len(messages())
            encoder(slot, value-previous)
            contains(0, controller, value, before, f'all assignments {slot} CC{controller}')
        current_a, current_b = cc, 128-cc
        if cc % 32 == 0:
            print(f'assignment sweep: {cc}/127 passed', flush=True)
    for page, slots in [('FX1', [('C', 7), ('D', 1), ('E', 2), ('F', 10)]),
                        ('FX2', list(zip('ABCDEF', range(71, 77))))]:
        press(page)
        for slot, cc in slots:
            press('FUNC', f'PUSH {slot}')
            encoder(slot, -127)
            encoder(slot, -127)
            before = len(messages())
            encoder(slot, 37)
            contains(0, cc, 37, before, f'stock {page} {slot} CC{cc}')
    press('FX1')
    press('FUNC', 'FX1')
    encoder('A', -127)
    encoder('A', -1)
    encoder('B', -1)
    press('YES')
    press('FX1')
    for slot, delta, expected in [('A', -1, bytes([0xe0, 0, 126])),
                                   ('B', 1, bytes([0xd0, 2]))]:
        before = len(messages())
        encoder(slot, delta)
        new = messages()[before:]
        assert expected in new, f'STK restore {slot}: {[v.hex() for v in new]}'
        checks.append(f'STK restore {slot}')
    press('T2')
    for slot, cc in [('A', 0), ('B', 127)]:
        before = len(messages())
        encoder(slot, 5)
        contains(1, cc, 5, before, f'track 2 assignment survives track 1 STK restore {slot}')
    if a.sequencer:
        press('REC')
        press('TRIG1')
        key('TRIG1', True)
        encoder('A', 37)
        encoder('B', 38)
        key('TRIG1', False)
        advance()
        base = bytes.fromhex(command(f'peek {hex(0x46c76dc0+68+18)} 2').split()[1])
        assert base == bytes([5, 5]), f'lock fixture changed live base: {base.hex()}'
        press('REC')
        command('frame on')
        command('watch 0x40010bc8,0x4009eec8,0x400d6b20')
        before = len(messages())
        press('PLAY')
        advance(1200)
        press('STOP')
        command('frame off')
        command('hits')
        command(f'peek {hex(0x46c76dc0+68+50)} 2')
        new = messages()[before:]
        assert not any(v[0] in [0xd1, 0xe1] for v in new), 'native PB/AT leaked during mapped locks'
        for cc, value in [(0, 42), (127, 43)]:
            assert bytes([0xb1, cc, value]) in new, f'locked CC{cc} missing from playback'
            checks.append(f'sequenced track 2 CC{cc} lock {value}')
    report = {'status': 'passed', 'checks': checks, 'checkCount': len(checks),
        'candidateSha256': hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
        'emulatorSha256': hashlib.sha256(a.emulator.read_bytes()).hexdigest(),
        'adaptersSha256': hashlib.sha256(Path(__file__).with_name('slots.s').read_bytes()).hexdigest(),
        'verifierSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'coverage': 'MKII panel; eight distinct channels; all CC assignments; stock controls; STK restore'
                    + ('; two actual sequencer locks with live base unchanged' if a.sequencer else ''),
        'notTested': ([] if a.sequencer else ['sequencer locks']) + ['persistence', 'same-channel arbitration',
                      'LFOs', 'USB lifecycle', 'hardware']}
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
finally:
    if port.poll() is None:
        port.terminate()
        port.wait(10)
    (out/'commands.private.json').write_text(json.dumps(steps, indent=2)+'\n')
    selector.close()
