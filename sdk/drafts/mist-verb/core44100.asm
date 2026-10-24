; Native 44.1 kHz experiment: SRC, reverb and mixer on DSP.
; Copyright 2014 Emilie Gillet; translation Copyright 2026 cscobey.
; MIT: see LICENSE and pinned upstream source.
; 32 kHz core experiment ONLY. Not a 44.1 kHz Octatrack effect.
; X r7+00..6f own scalar state. Y first 15238 words own buffer.
tank_start:
        move #>$ffffff,m5
        move r7,r5
        clr a
        do #112,>rv_core_zero
        move a1,x:(r5)+
rv_core_zero:
        nop
        move x:>$213,r4
        move x:(r4),a
        move a1,x:(r7+$20)
        move x:(r7+$20),a
        add #>$0,a
        move a1,x:(r7+$60)
        move x:(r7+$20),a
        add #>$71,a
        move a1,x:(r7+$61)
        move x:(r7+$20),a
        add #>$113,a
        move a1,x:(r7+$62)
        move x:(r7+$20),a
        add #>$204,a
        move a1,x:(r7+$63)
        move x:(r7+$20),a
        add #>$393,a
        move a1,x:(r7+$64)
        move x:(r7+$20),a
        add #>$a08,a
        move a1,x:(r7+$65)
        move x:(r7+$20),a
        add #>$11fe,a
        move a1,x:(r7+$66)
        move x:(r7+$20),a
        add #>$1ae0,a
        move a1,x:(r7+$67)
        move x:(r7+$20),a
        add #>$2259,a
        move a1,x:(r7+$68)
        move x:(r7+$20),a
        add #>$28d8,a
        move a1,x:(r7+$69)
        move #>$3b86,a
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
tank_run:
        move #>$ffffff,m4
        move #>$ffffff,m5
        move x:(r7+$22),a
        tst a
        beq rv_core_knobs
        move #>$96,x0
        cmp x0,a
        blt rv_core_short_clear
        move x0,a
rv_core_short_clear:
        move a1,n5
        move x:(r7+$22),b
        sub a,b
        move b1,x:(r7+$22)
        move b1,n4
        move x:(r7+$20),r4
        move (r4)+n4
        clr a
        do n5,>rv_core_wipe
        move a1,y:(r4)+
rv_core_wipe:
        nop
        rts
rv_core_knobs:
tank_frame:
        move #>$1,n0
        do n7,>rv_core_frame_end
        move x:(r0)+,a
        move a1,x:(r7+$39)
        asr #$3,a,a
        move a1,x:(r7+$28)
        move x:(r0)-,a
        move a1,x:(r7+$3a)
        asr #$3,a,a
        move a1,x:(r7+$29)
        move x:(r7+$50),a
        sub #>$1,a
        bpl rv_head_50_ready
        move #>$70,a
rv_head_50_ready:
        move a1,x:(r7+$50)
        move x:(r7+$51),a
        sub #>$1,a
        bpl rv_head_51_ready
        move #>$a1,a
rv_head_51_ready:
        move a1,x:(r7+$51)
        move x:(r7+$52),a
        sub #>$1,a
        bpl rv_head_52_ready
        move #>$f0,a
rv_head_52_ready:
        move a1,x:(r7+$52)
        move x:(r7+$53),a
        sub #>$1,a
        bpl rv_head_53_ready
        move #>$18e,a
rv_head_53_ready:
        move a1,x:(r7+$53)
        move x:(r7+$54),a
        sub #>$1,a
        bpl rv_head_54_ready
        move #>$674,a
rv_head_54_ready:
        move a1,x:(r7+$54)
        move x:(r7+$55),a
        sub #>$1,a
        bpl rv_head_55_ready
        move #>$7f5,a
rv_head_55_ready:
        move a1,x:(r7+$55)
        move x:(r7+$56),a
        sub #>$1,a
        bpl rv_head_56_ready
        move #>$d52,a
rv_head_56_ready:
        move a1,x:(r7+$56)
        move x:(r7+$57),a
        sub #>$1,a
        bpl rv_head_57_ready
        move #>$778,a
rv_head_57_ready:
        move a1,x:(r7+$57)
        move x:(r7+$58),a
        sub #>$1,a
        bpl rv_head_58_ready
        move #>$67e,a
rv_head_58_ready:
        move a1,x:(r7+$58)
        move x:(r7+$59),a
        sub #>$1,a
        bpl rv_head_59_ready
        move #>$12ad,a
rv_head_59_ready:
        move a1,x:(r7+$59)
        move x:(r7+$21),a
        sub #>$1,a
        and #>$003fff,a
        move a1,x:(r7+$21)
        and #>$00001f,a
        move a1,a
        tst a
        bne rv_core_lfo_hold
        move x:(r7+$40),x0
        move #>$43,y1
        mpy x0,y1,a
        move x0,b
        move x:(r7+$4a),b0
        asl #$1,b,b
        sub a,b
        move x:(r7+$41),a
        move x:(r7+$4b),a0
        sub a,b
        move x0,x:(r7+$41)
        move x:(r7+$4a),x1
        move x1,x:(r7+$4b)
        move b1,x:(r7+$40)
        move b0,x:(r7+$4a)
        move x0,a
        add #>$400000,a
        move a,x:(r7+$44)
        move x:(r7+$42),x0
        move #>$19,y1
        mpy x0,y1,a
        move x0,b
        move x:(r7+$4c),b0
        asl #$1,b,b
        sub a,b
        move x:(r7+$43),a
        move x:(r7+$4d),a0
        sub a,b
        move x0,x:(r7+$43)
        move x:(r7+$4c),x1
        move x1,x:(r7+$4d)
        move b1,x:(r7+$42)
        move b0,x:(r7+$4c)
        move x0,a
        add #>$400000,a
        move a,x:(r7+$45)
rv_core_lfo_hold:
        move x:(r7+$28),a
        move x:(r7+$29),x0
        add x0,a
        move a1,x0
        move x:(r7+$04),y1
        mpy x0,y1,a
        move a1,x:(r7+$3b)
        move x:(r7+$44),x0
        move #>$3c,y1
        mpy x0,y1,a
        clr b
        move a0,b1
        lsr b
        move b1,x:(r7+$46)
        move a1,a
        add #>$a,a
        move x:(r7+$50),x0
        add x0,a
        cmp #>$71,a
        blt rv_interpol_0000_first
        sub #>$71,a
rv_interpol_0000_first:
        move a1,x:(r7+$49)
        move a1,n5
        move x:(r7+$60),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$47)
        move x:(r7+$49),a
        add #>$1,a
        cmp #>$71,a
        blt rv_interpol_0000_second
        clr a
rv_interpol_0000_second:
        move a1,n5
        move x:(r7+$60),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move x:(r7+$47),x0
        sub x0,a
        move a1,x0
        move x:(r7+$46),y1
        mpy x0,y1,a
        move x:(r7+$47),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0283
        add #>$ff,a
rv_quant_0283:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$50),a
        add #>$64,a
        cmp #>$71,a
        blt rv_tap_0064_ready
        sub #>$71,a
rv_tap_0064_ready:
        move a1,n5
        move x:(r7+$60),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$3b),a
        move a1,x:(r7+$32)
        move x:(r7+$50),a
        sub #>$1,a
        bpl rv_tap_0070_ready
        move #>$70,a
rv_tap_0070_ready:
        move a1,n5
        move x:(r7+$60),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$33)
        move a1,x0
        move x:(r7+$02),y1
        mpy x0,y1,a
        move x:(r7+$32),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0324
        add #>$ff,a
rv_quant_0324:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$50),a
        move a1,n5
        move x:(r7+$60),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$32),x0
        move x:(r7+$02),y1
        mpy -x0,y1,a
        move x:(r7+$33),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$51),a
        sub #>$1,a
        bpl rv_tap_0113_ready
        move #>$a1,a
rv_tap_0113_ready:
        move a1,n5
        move x:(r7+$61),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$33)
        move a1,x0
        move x:(r7+$02),y1
        mpy x0,y1,a
        move x:(r7+$32),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0364
        add #>$ff,a
rv_quant_0364:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$51),a
        move a1,n5
        move x:(r7+$61),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$32),x0
        move x:(r7+$02),y1
        mpy -x0,y1,a
        move x:(r7+$33),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$52),a
        sub #>$1,a
        bpl rv_tap_0205_ready
        move #>$f0,a
rv_tap_0205_ready:
        move a1,n5
        move x:(r7+$62),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$33)
        move a1,x0
        move x:(r7+$02),y1
        mpy x0,y1,a
        move x:(r7+$32),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0404
        add #>$ff,a
rv_quant_0404:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$52),a
        move a1,n5
        move x:(r7+$62),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$32),x0
        move x:(r7+$02),y1
        mpy -x0,y1,a
        move x:(r7+$33),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$53),a
        sub #>$1,a
        bpl rv_tap_0395_ready
        move #>$18e,a
rv_tap_0395_ready:
        move a1,n5
        move x:(r7+$63),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$33)
        move a1,x0
        move x:(r7+$02),y1
        mpy x0,y1,a
        move x:(r7+$32),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0444
        add #>$ff,a
rv_quant_0444:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$53),a
        move a1,n5
        move x:(r7+$63),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$32),x0
        move x:(r7+$02),y1
        mpy -x0,y1,a
        move x:(r7+$33),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a1,x:(r7+$34)
        move x:(r7+$45),x0
        move #>$64,y1
        mpy x0,y1,a
        clr b
        move a0,b1
        lsr b
        move b1,x:(r7+$46)
        move a1,a
        add #>$1248,a
        move x:(r7+$59),x0
        add x0,a
        cmp #>$12ae,a
        blt rv_interpol_2d52_first
        sub #>$12ae,a
rv_interpol_2d52_first:
        move a1,x:(r7+$49)
        move a1,n5
        move x:(r7+$69),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$47)
        move x:(r7+$49),a
        add #>$1,a
        cmp #>$12ae,a
        blt rv_interpol_2d52_second
        clr a
rv_interpol_2d52_second:
        move a1,n5
        move x:(r7+$69),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move x:(r7+$47),x0
        sub x0,a
        move a1,x0
        move x:(r7+$46),y1
        mpy x0,y1,a
        move x:(r7+$47),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),x0
        move x:(r7+$00),y1
        mpy x0,y1,a
        move x:(r7+$34),x0
        add x0,a
        move x:(r7+$35),x0
        sub x0,a
        move a1,x0
        move x:(r7+$01),y1
        mpy x0,y1,a
        move x:(r7+$35),x0
        add x0,a
        move a1,x:(r7+$35)
        move a1,x:(r7+$32)
        move x:(r7+$54),a
        sub #>$1,a
        bpl rv_tap_0a0b_ready
        move #>$674,a
rv_tap_0a0b_ready:
        move a1,n5
        move x:(r7+$64),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$33)
        move a1,x0
        move x:(r7+$02),y1
        mpy -x0,y1,a
        move x:(r7+$32),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0543
        add #>$ff,a
rv_quant_0543:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$54),a
        move a1,n5
        move x:(r7+$64),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$32),x0
        move x:(r7+$02),y1
        mpy x0,y1,a
        move x:(r7+$33),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$55),a
        sub #>$1,a
        bpl rv_tap_1202_ready
        move #>$7f5,a
rv_tap_1202_ready:
        move a1,n5
        move x:(r7+$65),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$33)
        move a1,x0
        move x:(r7+$02),y1
        mpy x0,y1,a
        move x:(r7+$32),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0583
        add #>$ff,a
rv_quant_0583:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$55),a
        move a1,n5
        move x:(r7+$65),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$32),x0
        move x:(r7+$02),y1
        mpy -x0,y1,a
        move x:(r7+$33),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0605
        add #>$ff,a
rv_quant_0605:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$56),a
        bsr >cell_address
        move #>$11fe,n5
        move (r5)+n5
        bsr >rv_cell_store
        move x:(r7+$32),a
        move a1,x:(r7+$37)
        move x:(r7+$56),a
        sub #>$1,a
        bpl rv_tap_1f56_ready
        move #>$d52,a
rv_tap_1f56_ready:
        bsr >cell_address
        move #>$11fe,n5
        move (r5)+n5
        bsr >rv_cell_fetch
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$32)
        move x:(r7+$32),x0
        move x:(r7+$00),y1
        mpy x0,y1,a
        move x:(r7+$34),x0
        add x0,a
        move x:(r7+$36),x0
        sub x0,a
        move a1,x0
        move x:(r7+$01),y1
        mpy x0,y1,a
        move x:(r7+$36),x0
        add x0,a
        move a1,x:(r7+$36)
        move a1,x:(r7+$32)
        move x:(r7+$57),a
        sub #>$1,a
        bpl rv_tap_26d0_ready
        move #>$778,a
rv_tap_26d0_ready:
        move a1,n5
        move x:(r7+$67),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$33)
        move a1,x0
        move x:(r7+$02),y1
        mpy x0,y1,a
        move x:(r7+$32),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0666
        add #>$ff,a
rv_quant_0666:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$57),a
        move a1,n5
        move x:(r7+$67),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$32),x0
        move x:(r7+$02),y1
        mpy -x0,y1,a
        move x:(r7+$33),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$58),a
        sub #>$1,a
        bpl rv_tap_2d50_ready
        move #>$67e,a
rv_tap_2d50_ready:
        move a1,n5
        move x:(r7+$68),r5
        move (r5)+n5
        move y:(r5),a
        asl #$8,a,a
        move a1,a
        move a1,x:(r7+$33)
        move a1,x0
        move x:(r7+$02),y1
        mpy -x0,y1,a
        move x:(r7+$32),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0706
        add #>$ff,a
rv_quant_0706:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$58),a
        move a1,n5
        move x:(r7+$68),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$32),x0
        move x:(r7+$02),y1
        mpy x0,y1,a
        move x:(r7+$33),x0
        add x0,a
        move a1,x:(r7+$32)
        move x:(r7+$32),a
        move a,x0
        move x0,a
        tst a
        bpl rv_quant_0728
        add #>$ff,a
rv_quant_0728:
        asr #$8,a,a
        and #>$00ffff,a
        move a1,x:(r7+$30)
        move x:(r7+$59),a
        move a1,n5
        move x:(r7+$69),r5
        move (r5)+n5
        move x:(r7+$30),a
        move a1,y:(r5)
        move x:(r7+$32),a
        move a1,x:(r7+$38)
        move x:(r7+$39),x0
        move x:(r7+$05),y1
        mpy -x0,y1,a
        add x0,a
        move a1,x:(r7+$3c)
        move x:(r7+$37),x0
        mpy x0,y1,a
        asl #$4,a,a
        move x:(r7+$3c),x0
        add x0,a
        move a,x:(r0)+
        move x:(r7+$3a),x0
        move x:(r7+$05),y1
        mpy -x0,y1,a
        add x0,a
        move a1,x:(r7+$3c)
        move x:(r7+$38),x0
        mpy x0,y1,a
        asl #$4,a,a
        move x:(r7+$3c),x0
        add x0,a
        move a,x:(r0)+
rv_core_frame_end:
        nop
        rts
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
rv_cell_fetch:
        move    x1,a
        tst     a
        beq     rv_fetch_first
        cmp     #>$1,a
        beq     rv_fetch_middle
        move    (r5)+
        move    y:(r5),a
        and     #>$00ffff,a
        move    a1,a
        rts
rv_fetch_first:
        move    y:(r5),a
        asr     #$8,a,a
        and     #>$00ffff,a
        move    a1,a
        rts
rv_fetch_middle:
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
rv_cell_store:
        move    x1,a
        tst     a
        beq     rv_store_first
        cmp     #>$1,a
        beq     rv_store_middle
        move    (r5)+
        move    y:(r5),a
        and     #>$ff0000,a
        move    x:(r7+$30),x0
        or      x0,a
        move    a1,y:(r5)
        rts
rv_store_first:
        move    y:(r5),a
        and     #>$0000ff,a
        move    a1,y0
        move    x:(r7+$30),a
        asl     #$8,a,a
        or      y0,a
        move    a1,y:(r5)
        rts
rv_store_middle:
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


; Copyright 2026 cscobey. MIT; see LICENSE.
; Streaming wrapper; no installed effect or hardware qualification.
; X scalar offsets 70..af; Y histories at 15360,15488,15616,15680.
init:
        move #>tank_start,r4
        jsr (r4)
        move #>$ffffff,m4
        move #>$ffffff,m5
        move r7,r4
        move #>$70,n4
        move (r4)+n4
        clr a
        do #$80,>src_zero_scalar
        move a1,x:(r4)+
src_zero_scalar:
        nop
        move x:>$213,r4
        move x:(r4),a
        move a1,x:(r7+$70)
        move x:(r7+$70),a
        add #>$3c00,a
        move a1,x:(r7+$71)
        move a1,r4
        clr a
        do #96,>src_zero_hist_0
        move a1,y:(r4)+
src_zero_hist_0:
        nop
        move x:(r7+$70),a
        add #>$3c80,a
        move a1,x:(r7+$72)
        move a1,r4
        clr a
        do #96,>src_zero_hist_1
        move a1,y:(r4)+
src_zero_hist_1:
        nop
        move x:(r7+$70),a
        add #>$3d00,a
        move a1,x:(r7+$73)
        move a1,r4
        clr a
        do #48,>src_zero_hist_2
        move a1,y:(r4)+
src_zero_hist_2:
        nop
        move x:(r7+$70),a
        add #>$3d40,a
        move a1,x:(r7+$74)
        move a1,r4
        clr a
        do #48,>src_zero_hist_3
        move a1,y:(r4)+
src_zero_hist_3:
        nop
        move #>$18a40,a
        move a1,x:(r7+$77)
        move #>$18cc0,a
        move a1,x:(r7+$78)
        move #>$2,a
        move a1,x:(r7+$79)
        move #>$2,a
        move a1,x:(r7+$7b)
        rts
proc:
        move x:(r7+$22),a
        tst a
        beq src_audio_active
        move #>tank_run,r4
        jsr (r4)
        rts
src_audio_active:
        move r3,x:(r7+$8e)
        move m3,x:(r7+$8f)
        move n2,x:(r7+$91)
        move n3,x:(r7+$92)
        move #>$ffffff,m3
        move #>$ffffff,m4
        move #>$ffffff,m5
        bsr >tank_control_targets
        bsr >src_control_targets
        move #>$1,n0
        do n7,>src_frame_done
        move x:(r0)+,a
        move a1,x:(r7+$80)
        move a1,x:(r7+$b4)
        move x:(r0)-,a
        move a1,x:(r7+$81)
        move a1,x:(r7+$b5)
        bsr >src_mix_slew
        bsr >src_down_push
        move x:(r7+$75),a
        cmp #>32000,a
        bge src_down_skipped
        bsr >src_down_filter
        bsr >src_tank_slew
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
        move x:(r7+$b4),y0
        bsr >src_mix_output
        move a,x:(r0)+
        move x:(r4),a
        move x:(r7+$b5),y0
        bsr >src_mix_output
        move a,x:(r0)+
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
        cmp #>$18cc0,a
        blt src_down_schedule
        move #>$18a40,a
src_down_schedule:
        move a1,x:(r7+$77)
        move #>95,m4
        move #>95,m5
        move x:(r7+$82),r3
        move p:(r3)+,a
        move r3,x:(r7+$90)
        move a1,x1
        and #>$1ffff,a
        add #>$18000,a
        move a1,r3
        move #>$1,n3
        move #>94,n2
        move x1,a
        and #>$40000,a
        tst a
        bne src_down_first_short
        move #>95,n2
src_down_first_short:
        move x1,a
        and #>$20000,a
        tst a
        beq src_down_first_forward
        move #>$ffffff,n3
src_down_first_forward:
; A short phase omits its zero tail: restart both history reads.
        move x:(r7+$71),r5
        move x:(r7+$72),r4
        move (r5)-
        move (r4)-
        clr a
        clr b
        move y:(r5)-,y0
        move y:(r4)-,y1
        do n2,>src_down_stereo_first
        move p:(r3)+n3,x0
        mac y0,x0,a  y:(r5)-,y0
        mac x0,y1,b  y:(r4)-,y1
src_down_stereo_first:
        nop
        move p:(r3)+n3,x0
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
        move x:(r7+$90),r3
        move p:(r3)+,a
        move r3,x:(r7+$90)
        move a1,x1
        and #>$1ffff,a
        add #>$18000,a
        move a1,r3
        move #>$1,n3
        move #>94,n2
        move x1,a
        and #>$40000,a
        tst a
        bne src_down_second_short
        move #>95,n2
src_down_second_short:
        move x1,a
        and #>$20000,a
        tst a
        beq src_down_second_forward
        move #>$ffffff,n3
src_down_second_forward:
; A short phase omits its zero tail: restart both history reads.
        move x:(r7+$71),r5
        move x:(r7+$72),r4
        move (r5)-
        move (r4)-
        clr a
        clr b
        move y:(r5)-,y0
        move y:(r4)-,y1
        do n2,>src_down_stereo_second
        move p:(r3)+n3,x0
        mac y0,x0,a  y:(r5)-,y0
        mac x0,y1,b  y:(r4)-,y1
src_down_stereo_second:
        nop
        move p:(r3)+n3,x0
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
        cmp #>$19032,a
        blt src_up_schedule
        move #>$18cc0,a
src_up_schedule:
        move a1,x:(r7+$78)
        move #>47,m4
        move #>47,m5
        move x:(r7+$82),r3
        move p:(r3)+,a
        move r3,x:(r7+$90)
        move a1,x1
        and #>$1ffff,a
        add #>$186af,a
        move a1,r3
        move #>$1,n3
        move #>46,n2
        move x1,a
        and #>$40000,a
        tst a
        bne src_up_first_short
        move #>47,n2
src_up_first_short:
        move x1,a
        and #>$20000,a
        tst a
        beq src_up_first_forward
        move #>$ffffff,n3
src_up_first_forward:
; A short phase omits its zero tail: restart both history reads.
        move x:(r7+$73),r5
        move x:(r7+$74),r4
        move (r5)-
        move (r4)-
        clr a
        clr b
        move y:(r5)-,y0
        move y:(r4)-,y1
        do n2,>src_up_stereo_first
        move p:(r3)+n3,x0
        mac y0,x0,a  y:(r5)-,y0
        mac x0,y1,b  y:(r4)-,y1
src_up_stereo_first:
        nop
        move p:(r3)+n3,x0
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
        move x:(r7+$90),r3
        move p:(r3)+,a
        move r3,x:(r7+$90)
        move a1,x1
        and #>$1ffff,a
        add #>$186af,a
        move a1,r3
        move #>$1,n3
        move #>46,n2
        move x1,a
        and #>$40000,a
        tst a
        bne src_up_second_short
        move #>47,n2
src_up_second_short:
        move x1,a
        and #>$20000,a
        tst a
        beq src_up_second_forward
        move #>$ffffff,n3
src_up_second_forward:
; A short phase omits its zero tail: restart both history reads.
        move x:(r7+$73),r5
        move x:(r7+$74),r4
        move (r5)-
        move (r4)-
        clr a
        clr b
        move y:(r5)-,y0
        move y:(r4)-,y1
        do n2,>src_up_stereo_second
        move p:(r3)+n3,x0
        mac y0,x0,a  y:(r5)-,y0
        mac x0,y1,b  y:(r4)-,y1
src_up_stereo_second:
        nop
        move p:(r3)+n3,x0
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
; Keep the wide endpoint; host parity checks cover final saturation.
        move #>$0,a0
        rts

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
tank_control_targets:
        move x:(r6+$0),x0
        move #>$7e6d7f,y1
        mpy x0,y1,a
        move a1,x:(r7+$c0)
        move x:(r6+$2),x0
        move #>$7a8eb7,y1
        mpy x0,y1,a
        move a1,x:(r7+$c2)
        move x:(r6+$1),x0
        move #>$6da81d,y1
        mpy x0,y1,b
        move #>$733333,a
        sub b,a
        move a1,x:(r7+$c1)
        move #>$7f0000,a
        move #>$7f0000,x0
        cmp x0,a
        bne rv_knob_5_hold
        move #>$7fffff,a
rv_knob_5_hold:
        move a1,x:(r7+$c5)
        move x:(r6+$4),a
        and #>$7f0000,a
        move a1,a
        asr #$10,a,a
        move a1,n5
        move #>$fab1e0,r5
        move (r5)+n5
        move p:(r5),a
        move a1,x:(r7+$c4)
        rts
src_control_targets:
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
bne src_controls_live
move x:(r7+$c0),a
move a1,x:(r7+$0)
move a1,x:(r7+$e8)
clr a
move a1,x:(r7+$c8)
move a1,x:(r7+$e0)
move x:(r7+$c1),a
move a1,x:(r7+$1)
move a1,x:(r7+$e9)
clr a
move a1,x:(r7+$c9)
move a1,x:(r7+$e1)
move x:(r7+$c2),a
move a1,x:(r7+$2)
move a1,x:(r7+$ea)
clr a
move a1,x:(r7+$ca)
move a1,x:(r7+$e2)
move x:(r7+$c4),a
move a1,x:(r7+$4)
move a1,x:(r7+$ec)
clr a
move a1,x:(r7+$cc)
move a1,x:(r7+$e4)
move x:(r7+$c5),a
move a1,x:(r7+$bf)
move a1,x:(r7+$ed)
clr a
move a1,x:(r7+$cd)
move a1,x:(r7+$e5)
move #>$1,a
move a1,x:(r7+$b6)
rts
src_controls_live:
move x:(r7+$c0),a
move x:(r7+$e8),x0
cmp x0,a
beq src_target_0_done
move a1,x:(r7+$e8)
move x:(r7+$0),b
move x:(r7+$c8),b0
sub b,a
bpl src_target_0_divide
; Truncate a negative slope toward zero at Q47 precision.
clr b
move #>$ff,b0
add b,a
src_target_0_divide:
asr #$8,a,a
move a1,x:(r7+$d0)
move a0,x:(r7+$d8)
move #>$100,a
move a1,x:(r7+$e0)
src_target_0_done:
move x:(r7+$c1),a
move x:(r7+$e9),x0
cmp x0,a
beq src_target_1_done
move a1,x:(r7+$e9)
move x:(r7+$1),b
move x:(r7+$c9),b0
sub b,a
bpl src_target_1_divide
; Truncate a negative slope toward zero at Q47 precision.
clr b
move #>$ff,b0
add b,a
src_target_1_divide:
asr #$8,a,a
move a1,x:(r7+$d1)
move a0,x:(r7+$d9)
move #>$100,a
move a1,x:(r7+$e1)
src_target_1_done:
move x:(r7+$c2),a
move x:(r7+$ea),x0
cmp x0,a
beq src_target_2_done
move a1,x:(r7+$ea)
move x:(r7+$2),b
move x:(r7+$ca),b0
sub b,a
bpl src_target_2_divide
; Truncate a negative slope toward zero at Q47 precision.
clr b
move #>$ff,b0
add b,a
src_target_2_divide:
asr #$8,a,a
move a1,x:(r7+$d2)
move a0,x:(r7+$da)
move #>$100,a
move a1,x:(r7+$e2)
src_target_2_done:
move x:(r7+$c4),a
move x:(r7+$ec),x0
cmp x0,a
beq src_target_4_done
move a1,x:(r7+$ec)
move x:(r7+$4),b
move x:(r7+$cc),b0
sub b,a
bpl src_target_4_divide
; Truncate a negative slope toward zero at Q47 precision.
clr b
move #>$ff,b0
add b,a
src_target_4_divide:
asr #$8,a,a
move a1,x:(r7+$d4)
move a0,x:(r7+$dc)
move #>$100,a
move a1,x:(r7+$e4)
src_target_4_done:
move x:(r7+$c5),a
move x:(r7+$ed),x0
cmp x0,a
beq src_target_5_done
move a1,x:(r7+$ed)
move x:(r7+$bf),b
move x:(r7+$cd),b0
sub b,a
bpl src_target_5_divide
; Truncate a negative slope toward zero at Q47 precision.
clr b
move #>$ff,b0
add b,a
src_target_5_divide:
asr #$8,a,a
move a1,x:(r7+$d5)
move a0,x:(r7+$dd)
move #>$100,a
move a1,x:(r7+$e5)
src_target_5_done:
rts
src_tank_slew:
move x:(r7+$e0),a
tst a
beq src_slew_0_done
sub #>$1,a
move a1,x:(r7+$e0)
beq src_slew_0_snap
move x:(r7+$0),a
move x:(r7+$c8),a0
move x:(r7+$d0),b
move x:(r7+$d8),b0
add b,a
move a1,x:(r7+$0)
move a0,x:(r7+$c8)
bra src_slew_0_done
src_slew_0_snap:
move x:(r7+$e8),a
move a1,x:(r7+$0)
clr a
move a1,x:(r7+$c8)
src_slew_0_done:
move x:(r7+$e1),a
tst a
beq src_slew_1_done
sub #>$1,a
move a1,x:(r7+$e1)
beq src_slew_1_snap
move x:(r7+$1),a
move x:(r7+$c9),a0
move x:(r7+$d1),b
move x:(r7+$d9),b0
add b,a
move a1,x:(r7+$1)
move a0,x:(r7+$c9)
bra src_slew_1_done
src_slew_1_snap:
move x:(r7+$e9),a
move a1,x:(r7+$1)
clr a
move a1,x:(r7+$c9)
src_slew_1_done:
move x:(r7+$e2),a
tst a
beq src_slew_2_done
sub #>$1,a
move a1,x:(r7+$e2)
beq src_slew_2_snap
move x:(r7+$2),a
move x:(r7+$ca),a0
move x:(r7+$d2),b
move x:(r7+$da),b0
add b,a
move a1,x:(r7+$2)
move a0,x:(r7+$ca)
bra src_slew_2_done
src_slew_2_snap:
move x:(r7+$ea),a
move a1,x:(r7+$2)
clr a
move a1,x:(r7+$ca)
src_slew_2_done:
move x:(r7+$e4),a
tst a
beq src_slew_4_done
sub #>$1,a
move a1,x:(r7+$e4)
beq src_slew_4_snap
move x:(r7+$4),a
move x:(r7+$cc),a0
move x:(r7+$d4),b
move x:(r7+$dc),b0
add b,a
move a1,x:(r7+$4)
move a0,x:(r7+$cc)
bra src_slew_4_done
src_slew_4_snap:
move x:(r7+$ec),a
move a1,x:(r7+$4)
clr a
move a1,x:(r7+$cc)
src_slew_4_done:
rts
src_mix_slew:
move x:(r7+$e5),a
tst a
beq src_slew_5_done
sub #>$1,a
move a1,x:(r7+$e5)
beq src_slew_5_snap
move x:(r7+$bf),a
move x:(r7+$cd),a0
move x:(r7+$d5),b
move x:(r7+$dd),b0
add b,a
move a1,x:(r7+$bf)
move a0,x:(r7+$cd)
bra src_slew_5_done
src_slew_5_snap:
move x:(r7+$ed),a
move a1,x:(r7+$bf)
clr a
move a1,x:(r7+$cd)
src_slew_5_done:
rts
