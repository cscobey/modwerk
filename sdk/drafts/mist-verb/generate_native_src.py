#!/usr/bin/env python3
"""Generate the native streaming SRC experiment and its original P tables.

The assembly is tested separately before integration with the reverb.
"""
from pathlib import Path
import re
import argparse
from generate_src import bank
from src_layout import packed_bank
ROOT=Path(__file__).resolve().parent
# P addresses are standalone experiment placements, not installed allocations.
TABLE=0x18000
DOWN=TABLE
UP=DOWN+1711
DOWN_DESCRIPTORS=UP+847
UP_DESCRIPTORS=DOWN_DESCRIPTORS+33
SCHEDULE=UP_DESCRIPTORS+33
code=[]
def emit(s): code.extend(x.strip() for x in s.strip().splitlines())
def generate():
    # These bounds justify quarter-scale storage of wide rounded endpoints,
    # and a signed-24 delta between adjacent phase outputs, at full input scale.
    for rate,taps in ((44100,96),(32000,48)):
        rows=bank(rate,taps)
        assert max(sum(map(abs,row)) for row in rows) < 3*(1<<23)
        assert max(sum(abs(a-b) for a,b in zip(x,y)) for x,y in zip(rows,rows[1:]))+2 < (1<<23)
    packed=[packed_bank(rate,taps) for rate,taps in ((44100,96),(32000,48))]
    assert [len(p[1]) for p in packed]==[1711,847]
    tables=[v & 0xffffff for p in packed for v in p[1]]
    tables += [v for p in packed for v in p[2]]
    assert TABLE+len(tables)==SCHEDULE
    starts=[]
    for rate,out,base in ((44100,32000,DOWN_DESCRIPTORS),(32000,44100,UP_DESCRIPTORS)):
        start=TABLE+len(tables);starts.append(start)
        period=320 if rate==44100 else 441
        for n in range(period):
            clock=(n*rate)%out
            phase,rem=divmod(clock*32,out)
            tables.extend((base+phase,(rem<<23)//out))
    # Buffer bases deliberately match the planned reverb tail layout.
    # Down 96-cell rings aligned to 128, up 48-cell rings aligned to 64.
    emit('''; Copyright 2026 cscobey. MIT; see LICENSE.
; Native SRC round-trip experiment. No reverb, stock effect or firmware.
; X scalar offsets 70..af; Y histories at 15360,15488,15616,15680.
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
    for i,(offset,length) in enumerate(((15360,96),(15488,96),(15616,48),(15680,48))):
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
        move r3,x:(r7+$8e)
        move m3,x:(r7+$8f)
        move n2,x:(r7+$91)
        move n3,x:(r7+$92)
        move #>$ffffff,m3
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
        move x:(r7+$8e),r3
        move x:(r7+$8f),m3
        move x:(r7+$91),n2
        move x:(r7+$92),n3
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
        # Reuse each coefficient for both channels. Parallel Y reads load
        # the next sample while the current sample is accumulated.
        emit(f"""move #>{taps-1},m4
            move #>{taps-1},m5
            move x:(r7+$82),r3""")
        coefficient_base=DOWN if direction=='down' else UP
        for phase in ('first','second'):
            if phase=='second':emit('move x:(r7+$90),r3')
            emit(f"""move p:(r3)+,a
            move r3,x:(r7+$90)
            move a1,x1
            and #>$1ffff,a
            add #>${coefficient_base:x},a
            move a1,r3
            move #>$1,n3
            move #>{taps-2},n2
            move x1,a
            and #>$40000,a
            tst a
            bne src_{direction}_{phase}_short
            move #>{taps-1},n2
src_{direction}_{phase}_short:
            move x1,a
            and #>$20000,a
            tst a
            beq src_{direction}_{phase}_forward
            move #>$ffffff,n3
src_{direction}_{phase}_forward:
            ; A short phase omits its zero tail: restart both history reads.
            move x:(r7+${slots[0]:x}),r5
            move x:(r7+${slots[1]:x}),r4
            move (r5)-
            move (r4)-
            clr a
            clr b
            move y:(r5)-,y0
            move y:(r4)-,y1
            do n2,>src_{direction}_stereo_{phase}
            move p:(r3)+n3,x0
            mac y0,x0,a  y:(r5)-,y0
            mac x0,y1,b  y:(r4)-,y1
src_{direction}_stereo_{phase}:
            nop
            move p:(r3)+n3,x0
            mac y0,x0,a
            mac x0,y1,b
            ; Save the right accumulator without losing its extension bits.
            move b1,x:(r7+$8b)
            move b0,x:(r7+$8c)
            move b2,x:(r7+$8d)""")
            for channel,high,low in ((0,0x84,0x86),(1,0x88,0x89)):
                if channel:
                    emit("""move x:(r7+$8b),a
                        move x:(r7+$8c),a0
                        move x:(r7+$8d),a2""")
                emit('bsr >src_round_q23')
                if phase=='first':
                    emit(f"""asr #$2,a,a
                        move a1,x:(r7+${high:x})
                        move a0,x:(r7+${low:x})""")
                else:
                    emit(f"""move x:(r7+${high:x}),b
                        move x:(r7+${low:x}),b0
                        asl #$2,b,b
                        sub b,a
                        move a1,x0
                        move x:(r7+$83),y1
                        mpy x0,y1,a
                        bsr >src_round_q23
                        move x:(r7+${high:x}),b
                        move x:(r7+${low:x}),b0
                        asl #$2,b,b
                        add b,a
                        move a,x:(r7+${0x80+channel:x})""")
        emit('move #>$ffffff,m4\nmove #>$ffffff,m5\nrts')
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
        ; Keep the wide endpoint; host parity checks cover final saturation.
        move #>$0,a0
        rts''')
    return '\n'.join(('' if s.endswith(':') or s.startswith(';') else '        ')+s for s in code)+'\n',tables
def replace_one(source,before,after,count=1):
    if count!=1 or source.count(before)!=1:
        raise RuntimeError(f'Expected one wrapper splice: {before!r}')
    return source.replace(before,after,1)

def control_smoothing():
    """Generate five retargetable 256-sample ramps with 24 fractional bits."""
    lines=[]
    def add(text):lines.extend(line.strip() for line in text.strip().splitlines())
    current=(0,1,2,3,4,0xbf)
    add("""src_control_targets:
        move #>$7fffff,a
        move a1,x:(r7+$05)
        move x:(r6+$5),a
        and #>$7f0000,a
        cmp #>$7f0000,a
        bne src_mix_goal_ready
        move #>$7fffff,a
src_mix_goal_ready:
        move a1,x:(r7+$c5)
        move x:(r7+$b6),a
        tst a
        bne src_controls_live""")
    for i in (0,1,2,4,5):
        slot=current[i]
        add(f"""move x:(r7+${0xc0+i:x}),a
            move a1,x:(r7+${slot:x})
            move a1,x:(r7+${0xe8+i:x})
            clr a
            move a1,x:(r7+${0xc8+i:x})
            move a1,x:(r7+${0xe0+i:x})""")
    add("""move #>$1,a
        move a1,x:(r7+$b6)
        rts
src_controls_live:""")
    for i in (0,1,2,4,5):
        slot=current[i]
        add(f"""move x:(r7+${0xc0+i:x}),a
            move x:(r7+${0xe8+i:x}),x0
            cmp x0,a
            beq src_target_{i}_done
            move a1,x:(r7+${0xe8+i:x})
            move x:(r7+${slot:x}),b
            move x:(r7+${0xc8+i:x}),b0
            sub b,a
            bpl src_target_{i}_divide
            ; Truncate a negative slope toward zero at Q47 precision.
            clr b
            move #>$ff,b0
            add b,a
src_target_{i}_divide:
            asr #$8,a,a
            move a1,x:(r7+${0xd0+i:x})
            move a0,x:(r7+${0xd8+i:x})
            move #>$100,a
            move a1,x:(r7+${0xe0+i:x})
src_target_{i}_done:""")
    add('rts')
    for name,indices in (('src_tank_slew',(0,1,2,4)),('src_mix_slew',(5,))):
        add(name+':')
        for i in indices:
            add(f"""move x:(r7+${0xe0+i:x}),a
                tst a
                beq src_slew_{i}_done
                sub #>$1,a
                move a1,x:(r7+${0xe0+i:x})
                beq src_slew_{i}_snap
                move x:(r7+${current[i]:x}),a
                move x:(r7+${0xc8+i:x}),a0
                move x:(r7+${0xd0+i:x}),b
                move x:(r7+${0xd8+i:x}),b0
                add b,a
                move a1,x:(r7+${current[i]:x})
                move a0,x:(r7+${0xc8+i:x})
                bra src_slew_{i}_done
src_slew_{i}_snap:
                move x:(r7+${0xe8+i:x}),a
                move a1,x:(r7+${current[i]:x})
                clr a
                move a1,x:(r7+${0xc8+i:x})
src_slew_{i}_done:""")
        add('rts')
    return '\n'.join(lines)+'\n'

def combined(assembly):
    core=(ROOT/'core32.asm').read_text()
    labels=re.findall(r'^([A-Za-z_][A-Za-z_0-9]*):',core,re.M)
    for label in sorted(labels,key=len,reverse=True):
        core=re.sub(r'\b'+re.escape(label)+r'\b','rv_'+label,core)
    # The conversion wrapper owns dry/wet mixing; the tank returns wet audio.
    core=core.replace('rv_init','tank_start').replace('rv_proc','tank_run')
    core=core.replace('move x:(r6+$5),a','move #>$7f0000,a')
    # Calculate targets once per external call; render only one tank frame
    # per downsampled sample without recalculating knob mappings.
    start=core.index('rv_core_knobs:\n')+len('rv_core_knobs:\n')
    end=core.index('        move #>$1,n0',start)
    targets=core[start:end]
    targets=re.sub(r'x:\(r7\+\$0?([0-5])\)',
                   lambda m:f'x:(r7+${0xc0+int(m[1]):x})',targets)
    core=core[:start]+'tank_frame:\n'+core[end:]
    targets='tank_control_targets:\n'+targets+'        rts\n'
    assembly=replace_one(assembly,'do #$40,>src_zero_scalar','do #$80,>src_zero_scalar',1)
    assembly=replace_one(assembly,'move #>$1,n0','bsr >tank_control_targets\n        bsr >src_control_targets\n        move #>$1,n0',1)
    assembly=replace_one(assembly,'bsr >src_down_push','bsr >src_mix_slew\n        bsr >src_down_push',1)
    assembly=replace_one(assembly,'init:\n','init:\n        move #>tank_start,r4\n        jsr (r4)\n',1)
    assembly=replace_one(assembly,'proc:\n',"""proc:
        move x:(r7+$22),a
        tst a
        beq src_audio_active
        move #>tank_run,r4
        jsr (r4)
        rts
src_audio_active:
""",1)
    assembly=replace_one(assembly,'bsr >src_up_push',"""bsr >src_tank_slew
        move r0,x:(r7+$b2)
        move n7,x:(r7+$b3)
        move x:(r7+$80),a
        move a1,x:(r7+$b0)
        move x:(r7+$81),a
        move a1,x:(r7+$b1)
        move r7,r0
        move #>$b0,n0
        move (r0)+n0
        move #>$1,n7
        move #>tank_frame,r4
        jsr (r4)
        move x:(r7+$b2),r0
        move x:(r7+$b3),n7
        move x:(r7+$b0),a
        move a1,x:(r7+$80)
        move x:(r7+$b1),a
        move a1,x:(r7+$81)
        bsr >src_up_push""",1)
    assembly=replace_one(assembly,'move a1,x:(r7+$80)\n        move x:(r0)-,a','move a1,x:(r7+$80)\n        move a1,x:(r7+$b4)\n        move x:(r0)-,a',1)
    assembly=replace_one(assembly,'move a1,x:(r7+$81)\n        bsr >src_mix_slew','move a1,x:(r7+$81)\n        move a1,x:(r7+$b5)\n        bsr >src_mix_slew',1)
    assembly=replace_one(assembly,'move x:(r4)+,a\n        move a1,x:(r0)+','move x:(r4)+,a\n        move x:(r7+$b4),y0\n        bsr >src_mix_output\n        move a,x:(r0)+',1)
    assembly=replace_one(assembly,'move x:(r4),a\n        move a1,x:(r0)+','move x:(r4),a\n        move x:(r7+$b5),y0\n        bsr >src_mix_output\n        move a,x:(r0)+',1)
    assembly+="""
src_mix_output:
        move x:(r7+$bf),b
        tst b
        bne src_mix_nonzero
        move y0,a
        rts
src_mix_nonzero:
        cmp #>$7fffff,b
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
    return '; Native 44.1 kHz experiment: SRC, reverb and mixer on DSP.\n'+core+'\n'+assembly.replace('; Native SRC round-trip experiment. No reverb, stock effect or firmware.','; Streaming wrapper; no installed effect or hardware qualification.')+targets+control_smoothing()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    asm,table=generate()
    import json
    for name,text in [('native_src.asm',asm),('core44100.asm',combined(asm)),('native_src_tables.json',json.dumps({'base':TABLE,'words':table},separators=(',',':'))+'\n')]:
        path=ROOT/name
        if args.check:
            if path.read_text()!=text:raise SystemExit(name+' is stale')
        else:path.write_text(text)
