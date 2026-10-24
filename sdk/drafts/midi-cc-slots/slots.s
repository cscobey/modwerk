| SPDX-License-Identifier: MIT
| Experimental stock-1.40C dispatch adapters; emulator research only.
        .text
        .global slot_dispatch, slot_assignment, slot_format, slot_sequence_pb, slot_sequence_at
slot_dispatch:
        movel %a3,%d0
        andil #255,%d0
        subil #18,%d0
        cmpil #1,%d0
        bhi.w stock_dispatch
        movel %d7,%d1
        lsll #6,%d1
        moveal %d1,%a0
        lea %a0@(0,%d7:l:4),%a0
        addal %d0,%a0
        addal #0x46c76df2,%a0
        clrl %d1
        moveb %a0@,%d1
        beq.w stock_dispatch
        cmpil #128,%d1
        bhi.w stock_dispatch
        movel %a3,%d2
        andil #255,%d2
        movel #20,%d5
        jmp 0x4009f0c8
stock_dispatch:
        .incbin "dispatch.private.bin"
        jmp 0x4009ef66

slot_assignment:
        cmpil #20,%d2
        bge.s assignment_stock
        subql #1,%d0
        moveal %d0,%a5
assignment_stock:
        .incbin "assignment.private.bin"
        jmp 0x4009f104

| Sequencer enters after stock enable/channel checks. Reuse the CC sender's
| own cache, with the resolved lock/LFO value supplied by the sequencer.
        .macro sequence_slot name, offset, parameter, value, replay, resume, next
\name:
        movel %d7,%d0
        lsll #6,%d0
        moveal %d0,%a0
        lea %a0@(0,%d7:l:4),%a0
        addal #0x46c76df2+\offset,%a0
        clrl %d0
        moveb %a0@,%d0
        beq.s 1f
        cmpil #128,%d0
        bhi.s 1f
        clrl %d0
        moveb %a5@(\value),%d0
        clrl %sp@-
        movel %d0,%sp@-
        pea \parameter
        movel %d7,%sp@-
        jsr 0x4009eec8
        lea %sp@(16),%sp
        jmp \next
1:
        .incbin "\replay"
        jmp \resume
        .endm
        sequence_slot slot_sequence_pb, 0, 18, 562, sequence_pb.private.bin, 0x4009fd8a, 0x4009fde2
        sequence_slot slot_sequence_at, 1, 19, 563, sequence_at.private.bin, 0x4009fdfe, 0x4009fe4e

| SETUP formatter ABI: (char *destination, unsigned encoded_assignment).
slot_format:
        movel %sp@(8),%d0
        beq.s format_stock
        subql #1,%d0
        movel %d0,%sp@-
        pea format_number
        movel %sp@(12),%sp@-
        jsr 0x40013a08
        lea %sp@(12),%sp
        rts
format_stock:
        pea format_native
        movel %sp@(8),%sp@-
        jsr 0x40013a08
        addql #8,%sp
        rts
format_number: .asciz "%d"
format_native: .asciz "STK"
        .align 2
