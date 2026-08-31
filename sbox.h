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
 * The cipher (round, key schedule) lives in quartet.c and operates on
 * the SBOX_READ / INV_SBOX_READ macros — see quartet.h.
 */

#ifndef QUARTET_SBOX_H
#define QUARTET_SBOX_H

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

#endif /* QUARTET_SBOX_H */
