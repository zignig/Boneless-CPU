; \Build a forth in Assembly
; Simon Kirkby
; obetgiantrobot@gmail.com
; 20190319

.alloc stack, 4
.alloc rstack, 4
; redifine the registers

.def W, R0 ; working register
.def IP, R1 ; interpreter pointer
.def PSP, R2 ; parameter stack pointer 
.def TOS, R7 ; top of parameter stack
.def RSP, R4 ; return stack pointer 
.def JUMP, R5 ; jump saver , no direct access to PC
.def SP, R6 ; spare register 2
.def RTN, R3 ; cpu jump store

reset:
    MOVL PSP,4 
    MOVL RSP,8
    J init

abort:
    J init

.macro _call, name
    JAL RTN, $name
.endm
; stack structures
.macro RET
    JR RTN, 0
.endm

.macro pop
    _call POP
.endm

.macro push
    _call PUSH
.endm

.macro rpop
    _call RPOP
.endm

.macro rpush
    _call RPUSH
.endm

; unprotected stack functions

.label PUSH
    ST TOS, PSP, 0
    ADDI PSP, 1
    MOV TOS, W
    RET

.label POP
    MOV W, TOS
    SUBI PSP, 1
    LD TOS,PSP, 0
    RET

.label RPUSH
    ST W , RSP, 0
    ADDI RSP, 1
    RET

.label RPOP
    LD W , RSP, 0
    SUBI RSP, 1
    RET

; start of low level forth words

.macro NEXT
    LD W,IP,0
    J W
.endm

.equ latest, r_R0 

.macro HEADER, name
    .label $name
    .pos latest ; add current pos to code
    .set latest, $name ; copy this ref for next header
    .ulstring $name ; unlabeled string length then characters
.endm

.macro _fcall, addr ; call forth word from assembly.
    MOVA W,$addr
    LD SP,W,0
    ADD W,W,SP
    JR W,0
.endm

; do colon 
HEADER DOCOL 
NEXT

; from address find the first code word
HEADER >CFA
    LD W,PSP,1 ; load the value after the current pointer
    ADD W,PSP,W ; add the offset
    MOV PSP,W    
NEXT

HEADER DUP
    MOV W,TOS
    push 
NEXT

HEADER [
NEXT

HEADER ]
NEXT

; MAIN LOOP
init:
    _fcall DUP
J init

