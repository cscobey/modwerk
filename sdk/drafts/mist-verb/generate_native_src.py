#!/usr/bin/env python3
"""Generate the native streaming SRC experiment and its original P tables.

The assembly is tested separately before integration with the reverb.
"""
from pathlib import Path
import re
import argparse
from generate_src import bank
ROOT=Path(__file__).resolve().parent
# P addresses are standalone experiment placements, not installed allocations.
TABLE=0x18000
DOWN=TABLE
UP=DOWN+33*96
SCHEDULE=UP+33*48
code=[]
def emit(s): code.extend(x.strip() for x in s.strip().splitlines())
def generate():
    # These bounds justify quarter-scale storage of wide rounded endpoints,
    # and a signed-24 delta between adjacent phase outputs, at full input scale.
    for rate,taps in ((44100,96),(32000,48)):
        rows=bank(rate,taps)
        assert max(sum(map(abs,row)) for row in rows) < 3*(1<<23)
        assert max(sum(abs(a-b) for a,b in zip(x,y)) for x,y in zip(rows,rows[1:]))+2 < (1<<23)
    tables=[v & 0xffffff for rate,taps in ((44100,96),(32000,48)) for row in bank(rate,taps) for v in row]
    starts=[]
    for rate,out,taps,base in ((44100,32000,96,DOWN),(32000,44100,48,UP)):
        start=TABLE+len(tables);starts.append(start)
        period=320 if rate==44100 else 441
        for n in range(period):
            clock=(n*rate)%out
            phase,rem=divmod(clock*32,out)
            tables.extend((base+phase*taps,(rem<<23)//out))
    # Buffer bases deliberately match the planned reverb tail layout.
    # Down 96-cell rings aligned to 128, up 48-cell rings aligned to 64.
    emit('''; Copyright 2026 cscobey. MIT; see LICENSE.
; Native SRC round-trip experiment. No reverb, stock effect or firmware.
; X scalar offsets 70..af; Y histories at 15488,15616,15744,15808.
init:
        move #>$ffffff,m4
        move #>$ffffff,m5
        move r7,r4
        move #>$70,n4
        move (r4)+n4
        clr a
        do #$40,>src_zero_scalar
        move a1,x:(r4)+
src_zero_scalar:
        nop
        move x:>$213,r4
        move x:(r4),a
        move a1,x:(r7+$70)''')
    for i,(offset,length) in enumerate(((15488,96),(15616,96),(15744,48),(15808,48))):
        emit(f'''move x:(r7+$70),a
        add #>${offset:x},a
        move a1,x:(r7+${0x71+i:x})
        move a1,r4
        clr a
        do #{length},>src_zero_hist_{i}
        move a1,y:(r4)+
src_zero_hist_{i}:
        nop''')
    for slot,value in ((0x77,starts[0]),(0x78,starts[1]),(0x79,2)):
        emit(f'move #>${value:x},a\nmove a1,x:(r7+${slot:x})')
    emit('''rts
proc:
        move #>$ffffff,m4
        move #>$ffffff,m5
        move #>$1,n0
        do n7,>src_frame_done
        move x:(r0)+,a
        move a1,x:(r7+$80)
        move x:(r0)-,a
        move a1,x:(r7+$81)
        bsr >src_down_push
        move x:(r7+$75),a
        cmp #>32000,a
        bge src_down_skipped
        bsr >src_down_filter
        bsr >src_up_push
src_up_again:
        move x:(r7+$76),a
        cmp #>44100,a
        bge src_up_finished
        bsr >src_up_filter
        ; FIFO has eight stereo frames. Startup supplies two zero frames.
        move x:(r7+$7b),a
        asl #$1,a,a
        add #>$a0,a
        move a1,n4
        move r7,r4
        move (r4)+n4
        move x:(r7+$80),a
        move a1,x:(r4)+
        move x:(r7+$81),a
        move a1,x:(r4)
        move x:(r7+$7b),a
        add #>$1,a
        and #>$7,a
        move a1,x:(r7+$7b)
        move x:(r7+$79),a
        add #>$1,a
        move a1,x:(r7+$79)
        move x:(r7+$76),a
        add #>32000,a
        move a1,x:(r7+$76)
        move #>src_up_again,r4
        jmp (r4)
src_up_finished:
        move x:(r7+$76),a
        sub #>44100,a
        move a1,x:(r7+$76)
        move x:(r7+$75),a
        add #>44100,a
        move a1,x:(r7+$75)
src_down_skipped:
        move x:(r7+$75),a
        sub #>32000,a
        move a1,x:(r7+$75)
        move x:(r7+$79),a
        sub #>$1,a
        move a1,x:(r7+$79)
        move x:(r7+$7a),a
        asl #$1,a,a
        add #>$a0,a
        move a1,n4
        move r7,r4
        move (r4)+n4
        move x:(r4)+,a
        move a1,x:(r0)+
        move x:(r4),a
        move a1,x:(r0)+
        move x:(r7+$7a),a
        add #>$1,a
        and #>$7,a
        move a1,x:(r7+$7a)
src_frame_done:
        nop
        move #>$ffffff,m5
        rts''')
    # FIFO write index starts at two (the first two entries are silent).
    idx=code.index('rts');code[idx:idx]=['move #>$2,a','move a1,x:(r7+$7b)']
    for direction,taps,slots,schedule,period in [('down',96,(0x71,0x72),starts[0],320),('up',48,(0x73,0x74),starts[1],441)]:
        emit(f'src_{direction}_push:')
        for c,slot in enumerate(slots):
            emit(f'''move #>{taps-1},m5
            move x:(r7+${slot:x}),r5
            move x:(r7+${0x80+c:x}),a
            move a1,y:(r5)+
            move r5,x:(r7+${slot:x})''')
        emit('move #>$ffffff,m5\nrts')
        slot=0x77 if direction=='down' else 0x78
        emit(f'''src_{direction}_filter:
            move x:(r7+${slot:x}),r4
            move p:(r4)+,a
            move a1,x:(r7+$82)
            move p:(r4)+,a
            move a1,x:(r7+$83)
            move r4,a
            cmp #>${schedule+period*2:x},a
            blt src_{direction}_schedule
            move #>${schedule:x},a
src_{direction}_schedule:
            move a1,x:(r7+${slot:x})''')
        for c,head in enumerate(slots):
            emit(f'''move #>{taps-1},m5
            move x:(r7+${head:x}),r5
            move (r5)-
            move x:(r7+$82),r4
            clr a
            do #{taps},>src_{direction}_mac_{c}_first
            move y:(r5)-,x0
            move p:(r4)+,y1
            mac x0,y1,a
src_{direction}_mac_{c}_first:
            nop
            bsr >src_round_q23
            asr #$2,a,a
            move a1,x:(r7+$84)
            move a0,x:(r7+$86)
            clr a
            do #{taps},>src_{direction}_mac_{c}_second
            move y:(r5)-,x0
            move p:(r4)+,y1
            mac x0,y1,a
src_{direction}_mac_{c}_second:
            nop
            bsr >src_round_q23
            move x:(r7+$84),b
            move x:(r7+$86),b0
            asl #$2,b,b
            sub b,a
            move a1,x0
            move x:(r7+$83),y1
            mpy x0,y1,a
            bsr >src_round_q23
            move x:(r7+$84),b
            move x:(r7+$86),b0
            asl #$2,b,b
            add b,a
            move a,x:(r7+${0x80+c:x})''')
        emit('move #>$ffffff,m5\nrts')
    emit('''; Explicit half-away-from-zero rounding (not DSP convergent RND).
; Preserve wide rounded endpoints; saturation happens only after blending.
src_round_q23:
        tst a
        bpl src_round_positive
        clr b
        move #>$7fffff,b0
        bra src_round_addend
src_round_positive:
        clr b
        move #>$800000,b0
src_round_addend:
        add b,a
        ; Record endpoint overflow rather than silently claiming parity.
        move a,x0
        move a1,y0
        move x0,b
        cmp y0,b
        beq src_round_inrange
        move x:(r7+$85),b
        add #>$1,b
        move b1,x:(r7+$85)
src_round_inrange:
        move #>$0,a0
        rts''')
    return '\n'.join(('' if s.endswith(':') or s.startswith(';') else '        ')+s for s in code)+'\n',tables
def combined(assembly):
    core=(ROOT/'core32.asm').read_text()
    labels=re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):',core,re.M)
    for label in sorted(labels,key=len,reverse=True):
        core=re.sub(r'\b'+re.escape(label)+r'\b','rv_'+label,core)
    # The conversion wrapper owns dry/wet mixing; the tank returns wet audio.
    core=core.replace('rv_init','tank_start').replace('rv_proc','tank_run')
    core=core.replace('move x:(r6+$5),a','move #>$7f0000,a')
    assembly=assembly.replace('init:\n','init:\n        move #>tank_start,r4\n        jsr (r4)\n',1)
    assembly=assembly.replace('proc:\n',"""proc:
        move x:(r7+$22),a
        tst a
        beq src_audio_active
        move #>tank_run,r4
        jsr (r4)
        rts
src_audio_active:
""",1)
    assembly=assembly.replace('bsr >src_up_push',"""move r0,x:(r7+$b2)
        move n7,x:(r7+$b3)
        move x:(r7+$80),a
        move a1,x:(r7+$b0)
        move x:(r7+$81),a
        move a1,x:(r7+$b1)
        move r7,r0
        move #>$b0,n0
        move (r0)+n0
        move #>$1,n7
        move #>tank_run,r4
        jsr (r4)
        move x:(r7+$b2),r0
        move x:(r7+$b3),n7
        move x:(r7+$b0),a
        move a1,x:(r7+$80)
        move x:(r7+$b1),a
        move a1,x:(r7+$81)
        bsr >src_up_push""",1)
    assembly=assembly.replace('move a1,x:(r7+$80)\n        move x:(r0)-,a','move a1,x:(r7+$80)\n        move a1,x:(r7+$b4)\n        move x:(r0)-,a',1)
    assembly=assembly.replace('move a1,x:(r7+$81)\n        bsr >src_down_push','move a1,x:(r7+$81)\n        move a1,x:(r7+$b5)\n        bsr >src_down_push',1)
    assembly=assembly.replace('move x:(r4)+,a\n        move a1,x:(r0)+','move x:(r4)+,a\n        move x:(r7+$b4),y0\n        bsr >src_mix_output\n        move a,x:(r0)+',1)
    assembly=assembly.replace('move x:(r4),a\n        move a1,x:(r0)+','move x:(r4),a\n        move x:(r7+$b5),y0\n        bsr >src_mix_output\n        move a,x:(r0)+',1)
    assembly+="""
src_mix_output:
        move x:(r6+$5),b
        and #>$7f0000,b
        move b1,b
        tst b
        bne src_mix_nonzero
        move y0,a
        rts
src_mix_nonzero:
        cmp #>$7f0000,b
        beq src_mix_done
        move b1,y1
        move a1,x0
        mpy x0,y1,a
        move y0,x0
        mac -x0,y1,a
        add x0,a
src_mix_done:
        rts
"""
    return '; Native 44.1 kHz experiment: SRC, reverb and mixer on DSP.\n'+core+'\n'+assembly.replace('; Native SRC round-trip experiment. No reverb, stock effect or firmware.','; Streaming wrapper; no installed effect or hardware qualification.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    asm,table=generate()
    import json
    for name,text in [('native_src.asm',asm),('core44100.asm',combined(asm)),('native_src_tables.json',json.dumps({'base':TABLE,'words':table},separators=(',',':'))+'\n')]:
        path=ROOT/name
        if args.check:
            if path.read_text()!=text:raise SystemExit(name+' is stale')
        else:path.write_text(text)
