| SPDX-License-Identifier: MIT
| Emulator-only name editor spike. Volatile Part/track names, no file writes.
.text
.global names_header,names_open,names_store,names_setup_draw
names_slot:
 clrl %d0
 moveb 0x100b14cf,%d0
 andil #3,%d0
 lsll #3,%d0
 clrl %d1
 moveb 0x100b14cc,%d1
 andil #7,%d1
 addl %d1,%d0
 lsll #4,%d0
 lea names_store,%a0
 addal %d0,%a0
 rts
names_header:
 lea %sp@(-24),%sp
 moveml %d0-%d1/%a0-%a3,%sp@
 tstl 0x80000012
 beq.s names_header_done
 bsr names_slot
 tstb %a0@
 beq.s names_header_done
 movel %a0,%sp@-
 pea %fp@(-120)
 jsr 0x40013f40
 addql #8,%sp
names_header_done:
 moveml %sp@,%d0-%d1/%a0-%a3
 lea %sp@(24),%sp
 .incbin "header.private.bin"
 jmp 0x4004c414
names_open:
 movel 0x400bcd14,%d0
 cmpil #0x400bc6b8,%d0
 bne.s names_open_stock
 tstl %sp@(8)
 bne.s names_open_return
 tstl 0x80000012
 beq.s names_open_return
 lea %sp@(-4),%sp
 movel %a2,%sp@
 bsr names_slot
 moveal %a0,%a2
 jsr 0x40056808
 pea names_finished
 pea 1
 movel %a2,%sp@-
 pea names_title
 pea 10
 jsr 0x4007e664
 lea %sp@(20),%sp
 movel %sp@+,%a2
names_open_return:
 rts
names_open_stock:
 jmp 0x4004ae08
names_finished:
 pea -1
 jsr 0x4004d948
 addql #4,%sp
 rts
names_setup_draw:
 jsr 0x40036548
 movel 0x400bc6c0,%d0
 beq.s names_setup_return
 .macro names_text text,y
 pea \text
 pea 0x400b37cf
 pea 0x400b451d
 clrl %sp@-
 pea 1
 pea \y
 pea 102
 moveal 0x400bc6c0,%a0
 pea %a0@(36)
 pea 0x400ba876
 jsr 0x40013904
 lea %sp@(36),%sp
 .endm
 names_text names_caption,21
 names_text names_push,7
names_setup_return:
 rts
names_caption: .asciz "NAME"
names_push: .asciz "PUSH"
names_title: .asciz "MIDI TRACK NAME"
.align 4
names_store: .space 512
