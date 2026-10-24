; Copyright 2026 cscobey. MIT; see LICENSE.
; DSP56300 storage proof, NOT the Mist Verb audio engine.
; Three raw 16-bit cells in two 24-bit Y words. No shared/global writable state.
; r7+20 buffer base, +21 index, +30 staged write value, +31 current read.
; init preserves r1/n1/m1. proc returns current/previous cells as L/R integers.
init:
        move    x:>$213,r4
        move    x:(r4),a
        move    a1,x:(r7+$20)
        clr     a
        move    a1,x:(r7+$21)
        rts
proc:
        move    #>$ffffff,m5
        move    #>$1,n0
        do      n7,>probe_end
        move    x:(r0),x0
        move    x0,x:(r7+$30)
        move    x:(r7+$21),a
        bsr     >cell_address
        bsr     >cell_store
        move    x:(r7+$21),a
        bsr     >cell_address
        bsr     >cell_fetch
        move    a1,x:(r7+$31)
        move    x:(r7+$21),a
        sub     #>$1,a
        and     #>$003fff,a
        move    a1,a
        bsr     >cell_address
        bsr     >cell_fetch
        move    a1,b
        move    x:(r7+$31),a
        move    a1,x:(r0)+
        move    b1,x:(r0)+
        move    x:(r7+$21),a
        add     #>$1,a
        and     #>$003fff,a
        move    a1,x:(r7+$21)
probe_end:
        nop
        rts

; Input A: logical cell index, 0..16383. Output r5 physical pair, x1 residue.
; ceil(2^23/3) divides this bounded integer domain exactly after truncation.
cell_address:
        move    a1,x0
        move    #>$2aaaab,y1
        mpy     x0,y1,a
        move    a1,a
        move    a1,y0
        asl     #$1,a,a
        move    a1,n5
        add     y0,a
        move    x0,b
        sub     a,b
        move    b1,x1
        move    x:(r7+$20),r5
        move    (r5)+n5
        rts

; Output A: unsigned 16-bit pattern. Stores from a1 avoid extension limiting.
cell_fetch:
        move    x1,a
        tst     a
        beq     fetch_first
        cmp     #>$1,a
        beq     fetch_middle
        move    (r5)+
        move    y:(r5),a
        and     #>$00ffff,a
        move    a1,a
        rts
fetch_first:
        move    y:(r5),a
        asr     #$8,a,a
        and     #>$00ffff,a
        move    a1,a
        rts
fetch_middle:
        move    y:(r5)+,a
        and     #>$0000ff,a
        move    a1,a
        asl     #$8,a,a
        move    a1,y0
        move    y:(r5),a
        asr     #$10,a,a
        and     #>$0000ff,a
        or      y0,a
        move    a1,a
        rts

; Input r5/x1 as above, staged unsigned 16-bit value at r7+30.
cell_store:
        move    x1,a
        tst     a
        beq     store_first
        cmp     #>$1,a
        beq     store_middle
        move    (r5)+
        move    y:(r5),a
        and     #>$ff0000,a
        move    x:(r7+$30),x0
        or      x0,a
        move    a1,y:(r5)
        rts
store_first:
        move    y:(r5),a
        and     #>$0000ff,a
        move    a1,y0
        move    x:(r7+$30),a
        asl     #$8,a,a
        or      y0,a
        move    a1,y:(r5)
        rts
store_middle:
        move    y:(r5),a
        and     #>$ffff00,a
        move    a1,y0
        move    x:(r7+$30),a
        asr     #$8,a,a
        or      y0,a
        move    a1,y:(r5)+
        move    y:(r5),a
        and     #>$00ffff,a
        move    a1,y0
        move    x:(r7+$30),a
        and     #>$0000ff,a
        move    a1,a
        asl     #$10,a,a
        or      y0,a
        move    a1,y:(r5)
        rts
