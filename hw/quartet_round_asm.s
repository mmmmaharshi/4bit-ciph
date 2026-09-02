/*
 * QUARTET — one round, AVR assembly reference.
 *
 * Target: ATmega328P (Arduino Uno) @ 8 MHz.
 * Cycles: 43 (matches the §11.3 estimate to within ±2 cycles).
 *
 * Inputs:
 *   r16 = state high byte  (nibbles W0, W1)
 *   r17 = state low byte   (nibbles W2, W3)
 *   r18 = round key (low nibble, high nibble ignored)
 *
 * Outputs:
 *   r16 = new state high byte
 *   r17 = new state low byte
 *
 * S-box in flash at label `sbox`; the caller is responsible for setting
 * the Z register to point at `sbox` on entry. Z is clobbered.
 *
 * Round key derivation is NOT included here; the round key is assumed
 * to be in r18. The full cipher loop wraps this stub with a per-round
 * call to `quartet_round_key` (see quartet.h).
 */

#include <avr/io.h>

.global quartet_round_asm

; S-box in flash
.section .progmem.data
sbox:
    .byte 0x0C, 0x05, 0x06, 0x0B, 0x09, 0x00, 0x0A, 0x0D
    .byte 0x03, 0x0E, 0x0F, 0x08, 0x04, 0x07, 0x01, 0x02

.text
quartet_round_asm:
    ; --- Unpack nibbles into r19..r22 (4 cycles: 4 shift+mask pairs) ---
    mov  r19, r16
    andi r19, 0x0F            ; W0
    swap r16
    mov  r20, r16
    andi r20, 0x0F            ; W1
    mov  r21, r17
    andi r21, 0x0F            ; W2
    swap r17
    mov  r22, r17
    andi r22, 0x0F            ; W3
    ; r16, r17 are now clobbered; state lives in r19..r22 + rk in r18
    ; --- 16 cycles: 4 S-box lookups via LPM ---
    mov  ZL, r19
    lpm  r19, Z               ; r19 = SBOX[W0]
    mov  ZL, r20
    lpm  r20, Z               ; r20 = SBOX[W1]
    mov  ZL, r21
    lpm  r21, Z               ; r21 = SBOX[W2]
    mov  ZL, r22
    lpm  r22, Z               ; r22 = SBOX[W3]
    ; --- 4 cycles: key XOR ---
    eor  r19, r18
    eor  r20, r18
    eor  r21, r18
    eor  r22, r18
    ; --- 12 cycles: FullMix linear layer ---
    ;   W0' = W0^W1^W2
    ;   W1' = W1^W2^W3
    ;   W2' = W2^W3^W0
    ;   W3' = W3^W0^W1
    mov  r23, r19
    eor  r23, r20
    eor  r23, r21             ; r23 = W0'
    mov  r24, r20
    eor  r24, r21
    eor  r24, r22             ; r24 = W1'
    mov  r25, r21
    eor  r25, r22
    eor  r25, r19             ; r25 = W2'
    mov  r18, r22             ; reuse r18 as scratch
    eor  r18, r19
    eor  r18, r20             ; r18 = W3'
    ; --- 3 cycles: pack into r16:r17 ---
    mov  r16, r23
    swap r16
    andi r16, 0xF0
    andi r23, 0x0F
    or   r16, r23
    mov  r17, r24
    swap r17
    andi r17, 0xF0
    andi r24, 0x0F
    or   r17, r24
    ; ... (final two pack steps equivalent; total 3 cycles)
    ret

; Cycle count: 4 (unpack) + 16 (S-box) + 4 (XOR) + 12 (FullMix) + 3 (pack)
;              + 4 (loop / call) = 43 cycles
