/*
 * QUARTET: A 4-bit Word-Oriented Block Cipher
 *
 * 16-bit block, 64-bit key, 16-round SPN (default).
 * PRESENT S-box (DP=4/16), FullMix linear layer (branch#4).
 *
 * This header is the umbrella C source of truth. It includes the
 * cipher core (quartet_core.h) and a self-test (below).
 *
 * The .c file that #includes it must first define the S-box tables and
 * the SBOX_READ / INV_SBOX_READ macros (see sbox.h for the values).
 *
 *   #include "sbox.h"
 *   #if defined(__AVR__)
 *   #include <avr/pgmspace.h>
 *   static const uint8_t sbox[16] __attribute__((progmem)) = QUARTET_SBOX_INIT;
 *   static const uint8_t inv_sbox[16] __attribute__((progmem)) = QUARTET_INV_SBOX_INIT;
 *   #define SBOX_READ(i)      pgm_read_byte(&sbox[(i)])
 *   #define INV_SBOX_READ(i)  pgm_read_byte(&inv_sbox[(i)])
 *   #else
 *   static const uint8_t sbox[16] = QUARTET_SBOX_INIT;
 *   static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
 *   #define SBOX_READ(i)      (sbox[(i)])
 *   #define INV_SBOX_READ(i)  (inv_sbox[(i)])
 *   #endif
 *   #include "quartet.h"
 *
 * Interface:
 *   uint16_t quartet_encrypt(uint16_t pt, uint64_t key);   // 16 rounds
 *   uint16_t quartet_decrypt(uint16_t ct, uint64_t key);   // 16 rounds
 *   int      quartet_self_test(void);                       // returns 1 on pass
 *
 *   #define QUARTET_ROUNDS n  before the include to change the round count.
 *
 * The cipher core (the 6 functions that operate on secret data) lives
 * in quartet_core.h. That file is the AST-checked constant-time
 * surface; see tests/test_constant_time.py.
 *
 * Mano H. | 2026
 */

#ifndef QUARTET_H
#define QUARTET_H

#include <stdint.h>

#include "quartet_core.h"

/* Test vectors from SPEC.md, Section 9.
 *
 * This is test code, not cipher code. The if() condition and the
 * for() loop here are data-dependent — the test exists to assert
 * specific outputs, and the test framework needs to branch on pass/
 * fail. This is why the constant-time check (tests/test_constant_time.py)
 * scans quartet_core.h and NOT this file.
 */
static inline int quartet_self_test(void)
{
    static const struct { uint64_t key; uint16_t pt; uint16_t ct; } tests[] = {
        { 0x0123456789ABCDEFULL, 0x0000, 0xDDDD },
        { 0x0123456789ABCDEFULL, 0x0001, 0xDDDF },
        { 0x0123456789ABCDEFULL, 0x1234, 0x6927 },
        { 0x0123456789ABCDEFULL, 0xDEAD, 0xBC0B },
        { 0x0123456789ABCDEFULL, 0xFFFF, 0x5555 },
        { 0xFFFFFFFFFFFFFFFFULL, 0x0000, 0x3333 },
        { 0xFFFFFFFFFFFFFFFFULL, 0x0001, 0x333A },
        { 0xFFFFFFFFFFFFFFFFULL, 0x1234, 0x19B4 },
        { 0x0000000000000000ULL, 0x0000, 0x4444 },
        { 0x0000000000000000ULL, 0x0001, 0x4440 },
        { 0x0000000000000000ULL, 0x1234, 0xCF7E },
        { 0xFEDCBA9876543210ULL, 0x0000, 0x9999 },
        { 0xFEDCBA9876543210ULL, 0x1234, 0x50CF },
    };
    for (unsigned int i = 0; i < sizeof(tests) / sizeof(tests[0]); i++) {
        uint16_t ct = quartet_encrypt(tests[i].pt, tests[i].key);
        if (ct != tests[i].ct) return 0;
        if (quartet_decrypt(ct, tests[i].key) != tests[i].pt) return 0;
    }
    return 1;
}

#endif /* QUARTET_H */
