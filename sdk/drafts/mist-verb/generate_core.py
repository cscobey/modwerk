#!/usr/bin/env python3
"""Generate a 32 kHz DSP56300 tank experiment, NOT a 44.1 kHz OT effect.

Translated from the pinned MIT Clouds topology. Fixed taps cache their packed
addresses; moving taps retain the verified generic address routine.
Control smoothing and rate conversion are not implemented here.
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parent
code = []
INPUT_APS = ((0, 113), (114, 162), (277, 241), (519, 399))
TANK_APS = ((919, 1653), (2573, 2038), (8024, 1913), (9938, 1663))
# Each fixed tap is visited exactly once per processed sample. Two X words
# cache its physical pair pointer and 0/1/2 position inside that pair.
FIXED_TAPS = sorted({100, 4612, 8022, 11602} |
                    {offset for base, length in INPUT_APS + TANK_APS
                     for offset in (base, base + length - 1)})
CACHE = {offset: 0x50 + 2 * i for i, offset in enumerate(FIXED_TAPS)}
STATE_WORDS = 0x50 + 2 * len(FIXED_TAPS)


def emit(text):
    code.extend(line.strip() for line in text.strip().splitlines())


def q(value):
    return f'$%06x' % (max(-8388608, min(8388607, round(value * 8388608))) & 0xffffff)


def address(offset):
    slot = CACHE[offset]
    emit(f'''move x:(r7+${slot + 1:x}),a
        sub #>$1,a
        bpl tap_{offset:04x}_ready
        move x:(r7+${slot:x}),b
        sub #>$2,b
        move x:(r7+$20),x0
        cmp x0,b
        bge tap_{offset:04x}_pair
        move x0,b
        add #>$2aaa,b
        clr a
        bra tap_{offset:04x}_saved
tap_{offset:04x}_pair:
        move #>$2,a
tap_{offset:04x}_saved:
        move b1,x:(r7+${slot:x})
tap_{offset:04x}_ready:
        move a1,x:(r7+${slot + 1:x})
        move a1,x1
        move x:(r7+${slot:x}),r5''')


def read(offset):
    address(offset)
    emit('''bsr >cell_fetch
        asl #$8,a,a
        move a1,a''')


def write(offset):
    # x32 keeps the unquantized accumulator, as in FxEngine::Write().
    emit('''move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl core_quant_pos
        add #>$ff,a
core_quant_pos:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)'''.replace('core_quant_pos', f'quant_{len(code):04d}'))
    address(offset)
    emit('bsr >cell_store')


def ap(base, length, read_sign=1):
    read(base + length - 1)
    emit(f'''move a1,x:(r7+$33)
        move a1,x0
        move x:(r7+$02),y1
        mpy {'-' if read_sign < 0 else ''}x0,y1,a
        move x:(r7+$32),x0
        add x0,a
        move a1,x:(r7+$32)''')
    write(base)
    emit(f'''move x:(r7+$32),x0
        move x:(r7+$02),y1
        mpy {'-' if read_sign > 0 else ''}x0,y1,a
        move x:(r7+$33),x0
        add x0,a
        move a1,x:(r7+$32)''')


def interp(base, center, depth, lfo_slot):
    emit(f'''move x:(r7+${lfo_slot:x}),x0
        move #>${depth:x},y1
        mpy x0,y1,a
        clr b
        move a0,b1
        lsr b
        move b1,x:(r7+$46)
        move a1,a
        add #>${base + center:x},a
        move x:(r7+$21),x0
        add x0,a
        and #>$003fff,a
        move a1,x:(r7+$49)
        move a1,a
        bsr >cell_address
        bsr >cell_fetch
        asl #$8,a,a
        move a1,x:(r7+$47)
        move x:(r7+$49),a
        add #>$1,a
        and #>$003fff,a
        move a1,a
        bsr >cell_address
        bsr >cell_fetch
        asl #$8,a,a
        move a1,a
        move x:(r7+$47),x0
        sub x0,a
        move a1,x0
        move x:(r7+$46),y1
        mpy x0,y1,a
        move x:(r7+$47),x0
        add x0,a
        move a1,x:(r7+$32)''')


def diffuser(base, length):
    for offset, output in [(base + length - 1, False), (base, True)]:
        emit(f'''move x:(r7+$21),a
            add #>${offset:x},a
            and #>$0007ff,a
            add #>$002aac,a
            move a1,n5
            move x:(r7+$20),r5
            move (r5)+n5''')
        if not output:
            emit(f'''move y:(r5),x0
                move x0,x:(r7+$33)
                move #>{q(.625)},y1
                mpy x0,y1,a
                move x:(r7+$32),x0
                add x0,a
                move a1,x:(r7+$32)''')
        else:
            emit(f'''move x:(r7+$32),a
                move a1,y:(r5)
                move a1,x0
                move #>{q(.625)},y1
                mpy -x0,y1,a
                move x:(r7+$33),x0
                add x0,a
                move a1,x:(r7+$32)''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    emit(f'''; Copyright 2014 Emilie Gillet; translation Copyright 2026 cscobey.
        ; MIT: see LICENSE and pinned upstream source.
        ; 32 kHz core experiment ONLY. Not a 44.1 kHz Octatrack effect.
        ; X r7+00..{STATE_WORDS - 1:02x} own scalar state. Y first 12972 words own buffer.
init:
        move #>$ffffff,m5
        move r7,r5
        clr a
        do #{STATE_WORDS},>core_zero
        move a1,x:(r5)+
core_zero:
        nop
        move x:>$213,r4
        move x:(r4),a
        move a1,x:(r7+$20)
''')
    for offset, slot in CACHE.items():
        emit(f'''move x:(r7+$20),a
            add #>${2 * (offset // 3):x},a
            move a1,x:(r7+${slot:x})
            move #>${offset % 3:x},a
            move a1,x:(r7+${slot + 1:x})''')
    emit('''
        move #>$0032ac,a
        move a1,x:(r7+$22)
        move #>$400000,a
        move a1,x:(r7+$40)
        move a1,x:(r7+$42)
        move #>$3fffef,a
        move a1,x:(r7+$41)
        move #>$400000,a
        move a1,x:(r7+$4b)
        move #>$3ffff9,a
        move a1,x:(r7+$43)
        move #>$c00000,a
        move a1,x:(r7+$4d)
        move #>$7fffef,a
        move a1,x:(r7+$44)
        move #>$7ffffa,a
        move a1,x:(r7+$45)
        rts
proc:
        move #>$ffffff,m4
        move #>$ffffff,m5
        move x:(r7+$22),a
        tst a
        beq core_knobs
        move #>$80,x0
        cmp x0,a
        blt core_short_clear
        move x0,a
core_short_clear:
        move a1,n5
        move x:(r7+$22),b
        sub a,b
        move b1,x:(r7+$22)
        move b1,n4
        move x:(r7+$20),r4
        move (r4)+n4
        clr a
        do n5,>core_wipe
        move a1,y:(r4)+
core_wipe:
        nop
        rts
core_knobs:''')
    for i, factor in [(0, .98*128/127), (2, .95*128/127)]:
        emit(f'''move x:(r6+${i:x}),x0
            move #>{q(factor)},y1
            mpy x0,y1,a
            move a1,x:(r7+${i:x})''')
    emit(f'''move x:(r6+$1),x0
        move #>{q(.85*128/127)},y1
        mpy x0,y1,b
        move #>{q(.9)},a
        sub b,a
        move a1,x:(r7+$01)''')
    for i in (3, 5):
        emit(f'''move x:(r6+${i:x}),a
            move #>$7f0000,x0
            cmp x0,a
            bne knob_{i}_hold
            move #>$7fffff,a
knob_{i}_hold:
            move a1,x:(r7+${i:x})''')
    emit('''move x:(r6+$4),a
        and #>$7f0000,a
        move a1,a
        asr #$10,a,a
        move a1,n5
        move #>$fab1e0,r5
        move (r5)+n5
        move p:(r5),a
        move a1,x:(r7+$04)
        move #>$1,n0
        do n7,>core_frame_end
        move x:(r0)+,a
        move a1,x:(r7+$39)
        asr #$3,a,a
        move a1,x:(r7+$28)
        move x:(r0)-,a
        move a1,x:(r7+$3a)
        asr #$3,a,a
        move a1,x:(r7+$29)
        move x:(r7+$21),a
        sub #>$1,a
        and #>$003fff,a
        move a1,x:(r7+$21)
        and #>$00001f,a
        move a1,a
        tst a
        bne core_lfo_hold''')
    for first, second, value, epsilon, low_first, low_second in [
            (0x40, 0x41, 0x44, 67, 0x4a, 0x4b), (0x42, 0x43, 0x45, 25, 0x4c, 0x4d)]:
        emit(f'''move x:(r7+${first:x}),x0
            move #>${epsilon:x},y1
            mpy x0,y1,a
            move x0,b
            move x:(r7+${low_first:x}),b0
            asl #$1,b,b
            sub a,b
            move x:(r7+${second:x}),a
            move x:(r7+${low_second:x}),a0
            sub a,b
            move x0,x:(r7+${second:x})
            move x:(r7+${low_first:x}),x1
            move x1,x:(r7+${low_second:x})
            move b1,x:(r7+${first:x})
            move b0,x:(r7+${low_first:x})
            move x0,a
            add #>$400000,a
            move a,x:(r7+${value:x})''')
    emit('core_lfo_hold:')
    offset = 0
    for slot, lengths in [(0x28, (126, 180, 269, 444)), (0x29, (151, 205, 245, 405))]:
        emit(f'move x:(r7+${slot:x}),a\nmove a1,x:(r7+$32)')
        for length in lengths:
            diffuser(offset, length)
            offset += length + 1
        emit(f'''move x:(r7+$32),a
            move x:(r7+${slot:x}),x0
            sub x0,a
            move a1,x0
            move x:(r7+$03),y1
            mpy x0,y1,a
            move x:(r7+${slot:x}),x0
            add x0,a
            move a1,x:(r7+${slot:x})''')
    emit('''move x:(r7+$28),a
        move x:(r7+$29),x0
        add x0,a
        move a1,x0
        move x:(r7+$04),y1
        mpy x0,y1,a
        move a1,x:(r7+$3b)''')
    interp(0, 10, 60, 0x44)
    write(100)
    emit('move x:(r7+$3b),a\nmove a1,x:(r7+$32)')
    for base, length in INPUT_APS:
        ap(base, length)
    emit('move x:(r7+$32),a\nmove a1,x:(r7+$34)')
    for channel in range(2):
        if channel == 0:
            interp(11602, 4680, 100, 0x45)
        else:
            read(4612 + 3411 - 1)
            emit('move a1,x:(r7+$32)')
        emit(f'''move x:(r7+$32),x0
            move x:(r7+$00),y1
            mpy x0,y1,a
            move x:(r7+$34),x0
            add x0,a
            move x:(r7+${0x35+channel:x}),x0
            sub x0,a
            move a1,x0
            move x:(r7+$01),y1
            mpy x0,y1,a
            move x:(r7+${0x35+channel:x}),x0
            add x0,a
            move a1,x:(r7+${0x35+channel:x})
            move a1,x:(r7+$32)''')
        if channel == 0:
            ap(919,1653,-1); ap(2573,2038,1); write(4612)
        else:
            ap(8024,1913,1); ap(9938,1663,-1); write(11602)
        emit(f'move x:(r7+$32),a\nmove a1,x:(r7+${0x37+channel:x})')
    for channel in range(2):
        emit(f'''move x:(r7+${0x39+channel:x}),x0
            move x:(r7+$05),y1
            mpy -x0,y1,a
            add x0,a
            move a1,x:(r7+$3c)
            move x:(r7+${0x37+channel:x}),x0
            mpy x0,y1,a
            asl #$4,a,a
            move x:(r7+$3c),x0
            add x0,a
            move a,x:(r0)+''')
    emit('''core_frame_end:
        nop
        rts''')
    helper = (ROOT / 'packed_probe.asm').read_text().split('cell_address:', 1)[1]
    code.append('cell_address:' + helper)
    source = '\n'.join('        '+line if not line.endswith(':') and not line.startswith(';') else line
                       for line in code)+'\n'
    if args.check:
        if (ROOT / 'core32.asm').read_text() != source:
            raise SystemExit('core32.asm is stale; run generate_core.py')
    else:
        (ROOT / 'core32.asm').write_text(source)


if __name__ == '__main__':
    main()
