; Copyright 2026 cscobey. MIT; see LICENSE.
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
        move a1,x:(r7+$70)
        move x:(r7+$70),a
        add #>$3c80,a
        move a1,x:(r7+$71)
        move a1,r4
        clr a
        do #96,>src_zero_hist_0
        move a1,y:(r4)+
src_zero_hist_0:
        nop
        move x:(r7+$70),a
        add #>$3d00,a
        move a1,x:(r7+$72)
        move a1,r4
        clr a
        do #96,>src_zero_hist_1
        move a1,y:(r4)+
src_zero_hist_1:
        nop
        move x:(r7+$70),a
        add #>$3d80,a
        move a1,x:(r7+$73)
        move a1,r4
        clr a
        do #48,>src_zero_hist_2
        move a1,y:(r4)+
src_zero_hist_2:
        nop
        move x:(r7+$70),a
        add #>$3dc0,a
        move a1,x:(r7+$74)
        move a1,r4
        clr a
        do #48,>src_zero_hist_3
        move a1,y:(r4)+
src_zero_hist_3:
        nop
        move #>$19290,a
        move a1,x:(r7+$77)
        move #>$19510,a
        move a1,x:(r7+$78)
        move #>$2,a
        move a1,x:(r7+$79)
        move #>$2,a
        move a1,x:(r7+$7b)
        rts
proc:
        move r3,x:(r7+$8e)
        move m3,x:(r7+$8f)
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
        move #>$ffffff,m5
        rts
src_down_push:
        move #>95,m5
        move x:(r7+$71),r5
        move x:(r7+$80),a
        move a1,y:(r5)+
        move r5,x:(r7+$71)
        move #>95,m5
        move x:(r7+$72),r5
        move x:(r7+$81),a
        move a1,y:(r5)+
        move r5,x:(r7+$72)
        move #>$ffffff,m5
        rts
src_down_filter:
        move x:(r7+$77),r4
        move p:(r4)+,a
        move a1,x:(r7+$82)
        move p:(r4)+,a
        move a1,x:(r7+$83)
        move r4,a
        cmp #>$19510,a
        blt src_down_schedule
        move #>$19290,a
src_down_schedule:
        move a1,x:(r7+$77)
        move #>95,m4
        move #>95,m5
        move x:(r7+$71),r5
        move x:(r7+$72),r4
        move (r5)-
        move (r4)-
        move x:(r7+$82),r3
        clr a
        clr b
        move y:(r5)-,y0
        move y:(r4)-,y1
        do #95,>src_down_stereo_first
        move p:(r3)+,x0
        mac y0,x0,a  y:(r5)-,y0
        mac x0,y1,b  y:(r4)-,y1
src_down_stereo_first:
        nop
        move p:(r3)+,x0
        mac y0,x0,a
        mac x0,y1,b
; Save the right accumulator without losing its extension bits.
        move b1,x:(r7+$8b)
        move b0,x:(r7+$8c)
        move b2,x:(r7+$8d)
        bsr >src_round_q23
        asr #$2,a,a
        move a1,x:(r7+$84)
        move a0,x:(r7+$86)
        move x:(r7+$8b),a
        move x:(r7+$8c),a0
        move x:(r7+$8d),a2
        bsr >src_round_q23
        asr #$2,a,a
        move a1,x:(r7+$88)
        move a0,x:(r7+$89)
        clr a
        clr b
        move y:(r5)-,y0
        move y:(r4)-,y1
        do #95,>src_down_stereo_second
        move p:(r3)+,x0
        mac y0,x0,a  y:(r5)-,y0
        mac x0,y1,b  y:(r4)-,y1
src_down_stereo_second:
        nop
        move p:(r3)+,x0
        mac y0,x0,a
        mac x0,y1,b
; Save the right accumulator without losing its extension bits.
        move b1,x:(r7+$8b)
        move b0,x:(r7+$8c)
        move b2,x:(r7+$8d)
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
        move a,x:(r7+$80)
        move x:(r7+$8b),a
        move x:(r7+$8c),a0
        move x:(r7+$8d),a2
        bsr >src_round_q23
        move x:(r7+$88),b
        move x:(r7+$89),b0
        asl #$2,b,b
        sub b,a
        move a1,x0
        move x:(r7+$83),y1
        mpy x0,y1,a
        bsr >src_round_q23
        move x:(r7+$88),b
        move x:(r7+$89),b0
        asl #$2,b,b
        add b,a
        move a,x:(r7+$81)
        move #>$ffffff,m4
        move #>$ffffff,m5
        rts
src_up_push:
        move #>47,m5
        move x:(r7+$73),r5
        move x:(r7+$80),a
        move a1,y:(r5)+
        move r5,x:(r7+$73)
        move #>47,m5
        move x:(r7+$74),r5
        move x:(r7+$81),a
        move a1,y:(r5)+
        move r5,x:(r7+$74)
        move #>$ffffff,m5
        rts
src_up_filter:
        move x:(r7+$78),r4
        move p:(r4)+,a
        move a1,x:(r7+$82)
        move p:(r4)+,a
        move a1,x:(r7+$83)
        move r4,a
        cmp #>$19882,a
        blt src_up_schedule
        move #>$19510,a
src_up_schedule:
        move a1,x:(r7+$78)
        move #>47,m4
        move #>47,m5
        move x:(r7+$73),r5
        move x:(r7+$74),r4
        move (r5)-
        move (r4)-
        move x:(r7+$82),r3
        clr a
        clr b
        move y:(r5)-,y0
        move y:(r4)-,y1
        do #47,>src_up_stereo_first
        move p:(r3)+,x0
        mac y0,x0,a  y:(r5)-,y0
        mac x0,y1,b  y:(r4)-,y1
src_up_stereo_first:
        nop
        move p:(r3)+,x0
        mac y0,x0,a
        mac x0,y1,b
; Save the right accumulator without losing its extension bits.
        move b1,x:(r7+$8b)
        move b0,x:(r7+$8c)
        move b2,x:(r7+$8d)
        bsr >src_round_q23
        asr #$2,a,a
        move a1,x:(r7+$84)
        move a0,x:(r7+$86)
        move x:(r7+$8b),a
        move x:(r7+$8c),a0
        move x:(r7+$8d),a2
        bsr >src_round_q23
        asr #$2,a,a
        move a1,x:(r7+$88)
        move a0,x:(r7+$89)
        clr a
        clr b
        move y:(r5)-,y0
        move y:(r4)-,y1
        do #47,>src_up_stereo_second
        move p:(r3)+,x0
        mac y0,x0,a  y:(r5)-,y0
        mac x0,y1,b  y:(r4)-,y1
src_up_stereo_second:
        nop
        move p:(r3)+,x0
        mac y0,x0,a
        mac x0,y1,b
; Save the right accumulator without losing its extension bits.
        move b1,x:(r7+$8b)
        move b0,x:(r7+$8c)
        move b2,x:(r7+$8d)
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
        move a,x:(r7+$80)
        move x:(r7+$8b),a
        move x:(r7+$8c),a0
        move x:(r7+$8d),a2
        bsr >src_round_q23
        move x:(r7+$88),b
        move x:(r7+$89),b0
        asl #$2,b,b
        sub b,a
        move a1,x0
        move x:(r7+$83),y1
        mpy x0,y1,a
        bsr >src_round_q23
        move x:(r7+$88),b
        move x:(r7+$89),b0
        asl #$2,b,b
        add b,a
        move a,x:(r7+$81)
        move #>$ffffff,m4
        move #>$ffffff,m5
        rts
; Explicit half-away-from-zero rounding (not DSP convergent RND).
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
        rts
