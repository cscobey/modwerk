#!/usr/bin/env python3
"""Drive the stock name editor with panel input; no RAM or file injection."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
KEYS = {'YES': 0x31, 'NO': 0x32, 'MIDI': 0x35, 'SRC': 0x22, 'FX1': 0x25, 'FX2': 0x26,
        'PART': 0x1d, 'UP': 0x33, 'DOWN': 0x20, 'LEFT': 0x34, 'RIGHT': 0x21,
        'PUSH F': 0x3d, **{f'T{i+1}': 0x10+i for i in range(8)}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ['emulator', 'candidate', 'receipt', 'output']:
        p.add_argument('--'+field, type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if any((v/'.git').exists() for v in [out, *out.parents]):
        p.error('private output must be outside Git')
    receipt = json.loads(a.receipt.read_text())
    if hashlib.sha256(a.candidate.read_bytes()).hexdigest() != receipt['candidateSha256']:
        p.error('candidate differs from build receipt')
    if hashlib.sha256(Path(__file__).with_name('names.s').read_bytes()).hexdigest() != receipt['sourceSha256']:
        p.error('source differs from build receipt')
    out.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('names_lcd', ROOT/'sdk/octabam/tools/emu/lcd_view.py')
    lcd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lcd)
    lcd.ON, lcd.OFF = (240, 240, 240), (24, 24, 24)
    port = subprocess.Popen([str(a.emulator.resolve()), '--image', str(a.candidate.resolve()), '--mkii',
        '--boot-logo', '--ms', '4000', '--interactive', '--internal-clock', '--rtc', 'off',
        '--main-level', 'off', '--lcd', str(out/'lcd.private.bin')], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=(out/'stderr.private.log').open('wb'))
    selector = selectors.DefaultSelector()
    selector.register(port.stdout, selectors.EVENT_READ)
    pending = b''
    rows, steps, checks = [0]*8, [], []

    def response(prefix):
        nonlocal pending
        deadline = time.monotonic()+60
        while time.monotonic() < deadline:
            while b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                if line.startswith(prefix):
                    return line.decode()
            if port.poll() is not None:
                raise RuntimeError('emulator exited')
            if selector.select(1):
                pending += os.read(port.stdout.fileno(), 65536)
        raise TimeoutError('emulator reply timeout')

    def command(value):
        port.stdin.write((value+'\n').encode())
        port.stdin.flush()
        reply = response((b'ok', b'run ', b'err', b'peek '))
        steps.append([value, reply])
        if reply.startswith('err') or ('stop=' in reply and 'stop=time' not in reply):
            raise RuntimeError(reply)
        return reply

    def advance(ms=100):
        command(f'run {ms}')

    def key(name, down):
        code = KEYS[name]
        row, bit = code >> 3, 1 << (code & 7)
        rows[row] = rows[row] | bit if down else rows[row] & ~bit
        command(f'key {32|row} {rows[row]}')
        advance(50)

    def press(*names):
        for name in names:
            key(name, True)
        for name in reversed(names):
            key(name, False)

    def read(address, count):
        return bytes.fromhex(command(f'peek {hex(address)} {count}').split()[1])

    def expect(condition, description):
        if not condition:
            raise AssertionError(description)
        checks.append(description)

    def shot(name):
        lcd.png(lcd.screen(lcd.read_plane(out/'lcd.private.bin')), str(out/(name+'.png')), 6)

    def open_editor():
        press('SRC')
        advance(500)
        press('SRC'); press('SRC')
        advance(300)
        shot('setup')
        press('PUSH F')
        expect(any(read(0x460e7612, 4)), 'F opens stock name editor from MIDI SRC SETUP')

    def type_name(name):
        # Read only the stock editor's working buffer; every edit uses real keys.
        for _ in range(10):
            press('LEFT')
        for index, char in enumerate(name):
            for _ in range(61):
                if read(0x460e743c+index, 1) == char.encode('ascii'):
                    break
                press('UP')
            else:
                raise AssertionError('stock character selector failed to reach '+char)
            if index+1 < len(name):
                press('RIGHT')

    def stored(part, track):
        return read(receipt['symbols']['names_store']+16*(8*part+track), 16).split(b'\0', 1)[0]

    def pick_part(direction, expected):
        key('PART', True); press(direction); key('PART', False)
        advance(300)
        expect(read(0x100b14cf, 1) == bytes([expected]), f'native Part selector reaches Part {expected+1}')

    try:
        response(b'ready ')
        advance(1000); press('NO'); press('MIDI'); press('SRC'); advance(500)
        expect(read(receipt['symbols']['names_store'], 512) == bytes(512), 'all 32 volatile name slots start empty')
        shot('unnamed')
        before_src = read(0x40171442, 36)
        open_editor(); shot('editor')
        type_name('BASS'); shot('typed'); press('YES'); advance(300)
        expect(stored(0, 0) == b'BASS', 'YES commits the name entered with panel input')
        expect(read(0x40171442, 36) == before_src, 'naming leaves the selected MIDI track settings unchanged')
        shot('named')
        press('FX1'); advance(300); shot('control1')
        press('FX2'); advance(300); shot('control2')
        for track in range(1, 8):
            press(f'T{track+1}')
            expect(stored(0, track) == b'', f'T{track+1} starts unnamed')
            open_editor(); type_name(chr(ord('A')+track)); press('YES')
            expect(stored(0, track) == bytes([ord('A')+track]), f'T{track+1} keeps its own name')
        press('T1')
        expect(stored(0, 0) == b'BASS', 'editing seven other tracks preserves T1')
        shot('track1-return')
        open_editor(); press('UP'); press('NO'); advance(300)
        expect(stored(0, 0) == b'BASS', 'NO cancels without changing the committed name')
        shot('cancelled')
        for direction, part in [('RIGHT', 1), ('DOWN', 2), ('LEFT', 3)]:
            pick_part(direction, part)
            expect(stored(part, 0) == b'', f'Part {part+1} starts with a separate empty name')
            open_editor(); type_name('P'+str(part+1)); press('YES')
            expect(stored(part, 0) == ('P'+str(part+1)).encode(), f'Part {part+1} name commits independently')
        pick_part('UP', 0)
        expect(stored(0, 0) == b'BASS', 'returning to Part 1 preserves BASS')
        shot('part1-return')
        open_editor(); type_name('WWWWWWWWWW'); press('YES'); advance(300)
        expect(stored(0, 0) == b'WWWWWWWWWW', 'ten-character name is bounded and accepted')
        expect(stored(0, 1) == b'B', 'maximum-length edit leaves the next name intact')
        shot('max-length')
        press('MIDI'); press('SRC'); advance(300); shot('audio-src')
        press('SRC'); advance(500); press('SRC'); press('SRC'); press('PUSH F')
        expect(read(0x460e7612, 4) == bytes(4), 'audio SRC SETUP F does not open the MIDI editor')
        report = {'status': 'passed', 'checkCount': len(checks), 'checks': checks,
            'candidateSha256': receipt['candidateSha256'], 'sourceSha256': receipt['sourceSha256'],
            'emulatorSha256': hashlib.sha256(a.emulator.read_bytes()).hexdigest(),
            'verifierSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'notTested': ['hardware', 'USB package', 'composition with other modules', 'project/bank identity',
                          'save/load/reload', 'Part copy/clear', 'reboot persistence', 'compact/arranger views', 'MKI']}
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({'status': 'passed', 'checks': len(checks)}))
    finally:
        port.terminate(); port.wait(10)
        selector.close()
        (out/'commands.private.json').write_text(json.dumps(steps, indent=2)+'\n')


if __name__ == '__main__':
    main()
