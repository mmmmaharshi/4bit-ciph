/*
 * QUARTET — PRESENT S-box and its inverse.
 *
 * Single source of truth for the 4-bit S-box used by the QUARTET cipher.
 * Source: Bogdanov et al., "PRESENT: An Ultra-Lightweight Block Cipher," CHES 2007.
 *
 * Properties:
 *   - Bijection (all 16 output values distinct)
 *   - Differential uniformity 4, max DP = LP = 2^(-2)
 *   - Algebraic degree 3
 *   - No fixed points
 *   - Not involution
 *
 * Usage: define the table in your translation unit using these initializers,
 * then choose placement yourself (AVR flash, PC RAM, etc.):
 *
 *   #include "sbox.h"
 *   #if defined(__AVR__)
 *   static const uint8_t sbox[16] __attribute__((progmem)) = QUARTET_SBOX_INIT;
 *   static const uint8_t inv_sbox[16] __attribute__((progmem)) = QUARTET_INV_SBOX_INIT;
 *   #include <avr/pgmspace.h>
 *   #define SBOX_READ(i) pgm_read_byte(&sbox[(i)])
 *   #else
 *   static const uint8_t sbox[16] = QUARTET_SBOX_INIT;
 *   static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
 *   #define SBOX_READ(i) (sbox[(i)])
 *   #endif
 *
 * Bitsliced (constant-time, no table lookups) variant:
 *   #define QUARTET_BITSLICED
 *   #include "sbox.h"
 *   // provides quartet_sbox_bitsliced() and quartet_inv_sbox_bitsliced()
 *   // operates on 4 nibbles in parallel packed in a 16-bit word
 *
 * The cipher (round, key schedule) lives in quartet_core.h and operates on
 * the SBOX_READ / INV_SBOX_READ macros — see quartet.h.
 */

#ifndef QUARTET_SBOX_H
#define QUARTET_SBOX_H

#include <stdint.h>

/* PRESENT S-box */
#define QUARTET_SBOX_INIT { \
    0x0C, 0x05, 0x06, 0x0B, 0x09, 0x00, 0x0A, 0x0D, \
    0x03, 0x0E, 0x0F, 0x08, 0x04, 0x07, 0x01, 0x02  \
}

/* Inverse PRESENT S-box */
#define QUARTET_INV_SBOX_INIT { \
    0x05, 0x0E, 0x0F, 0x08, 0x0C, 0x01, 0x02, 0x0D, \
    0x0B, 0x04, 0x06, 0x03, 0x00, 0x07, 0x09, 0x0A  \
}

/* Bitsliced S-box: applies PRESENT S-box to 4 nibbles in parallel.
 * Input: 16-bit word with 4 nibbles (n0 | n1<<4 | n2<<8 | n3<<12)
 * Output: 16-bit word with 4 S-box outputs in same layout.
 * No table lookups, no data-dependent control flow. */
static inline uint16_t quartet_sbox_bitsliced(uint16_t state)
{
    /* Extract bit planes: each holds bit i of all 4 nibbles at positions 0,4,8,12 */
    uint16_t x0 =  state        & 0x1111;   /* bit 0 */
    uint16_t x1 = (state >> 1)  & 0x1111;   /* bit 1 */
    uint16_t x2 = (state >> 2)  & 0x1111;   /* bit 2 */
    uint16_t x3 = (state >> 3)  & 0x1111;   /* bit 3 */

    /* Shared subexpressions (ANF of PRESENT S-box) */
    uint16_t t1 = x0 & x1;          /* x0x1 */
    uint16_t t2 = x0 & x2;          /* x0x2 */
    uint16_t t3 = x0 & x3;          /* x0x3 */
    uint16_t t4 = x1 & x2;          /* x1x2 */
    uint16_t t5 = x1 & x3;          /* x1x3 */
    uint16_t t6 = x2 & x3;          /* x2x3 */
    uint16_t t7 = t1 & x2;          /* x0x1x2 */
    uint16_t t8 = t1 & x3;          /* x0x1x3 */
    uint16_t t9 = t2 & x3;          /* x0x2x3 */

    /* Output bits (ANF) */
    uint16_t y0 = x0 ^ x2 ^ t4 ^ x3;
    uint16_t y1 = x1 ^ x3 ^ t5 ^ t6 ^ t7 ^ t8 ^ t9;
    uint16_t y2 = 0x1111 ^ x2 ^ x3 ^ t1 ^ t3 ^ t5 ^ t8 ^ t9;  /* 1 at each nibble */
    uint16_t y3 = 0x1111 ^ x0 ^ x1 ^ x3 ^ t4 ^ t7 ^ t8 ^ t9;

    /* Reassemble: y0 at bit 0, y1 at bit 1, y2 at bit 2, y3 at bit 3 */
    return y0 | (y1 << 1) | (y2 << 2) | (y3 << 3);
}

/* Bitsliced inverse S-box: applies inverse PRESENT S-box to 4 nibbles in parallel. */
static inline uint16_t quartet_inv_sbox_bitsliced(uint16_t state)
{
    uint16_t x0 =  state        & 0x1111;
    uint16_t x1 = (state >> 1)  & 0x1111;
    uint16_t x2 = (state >> 2)  & 0x1111;
    uint16_t x3 = (state >> 3)  & 0x1111;

    /* Shared subexpressions (ANF of inverse PRESENT S-box) */
    uint16_t t1 = x0 & x1;          /* x0x1 */
    uint16_t t2 = x0 & x2;          /* x0x2 */
    uint16_t t3 = x1 & x2;          /* x1x2 */
    uint16_t t4 = t1 & x2;          /* x0x1x2 */
    uint16_t t5 = x1 & x3;          /* x1x3 */
    uint16_t t6 = x2 & x3;          /* x2x3 */
    uint16_t t7 = x0 & x3;          /* x0x3 */
    uint16_t t8 = t1 & x3;          /* x0x1x3 */
    uint16_t t9 = t2 & x3;          /* x0x2x3 */

    uint16_t y0 = 0x1111 ^ x0 ^ x2 ^ t5;
    uint16_t y1 = x0 ^ x1 ^ t2 ^ t4 ^ x3 ^ t5 ^ t8 ^ t6 ^ t9;
    uint16_t y2 = 0x1111 ^ t1 ^ t2 ^ t3 ^ t4 ^ x3 ^ t7 ^ t5 ^ t8 ^ t9;
    uint16_t y3 = x0 ^ x1 ^ t1 ^ x2 ^ t4 ^ x3 ^ t9;

    return y0 | (y1 << 1) | (y2 << 2) | (y3 << 3);
}

#endif /* QUARTET_SBOX_H */
