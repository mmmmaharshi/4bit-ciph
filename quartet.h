/*
 * QUARTET: A 4-bit Word-Oriented Block Cipher
 *
 * 16-bit block, 64-bit key, 16-round SPN (default).
 * PRESENT S-box (DP=4/16), FullMix linear layer (branch#4).
 *
 * This header is the single C source of truth for the cipher.
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
 * Mano H. | 2026
 */

#ifndef QUARTET_H
#define QUARTET_H

#include <stdint.h>

#ifndef QUARTET_ROUNDS
#define QUARTET_ROUNDS 16
#endif

#ifndef SBOX_READ
#error "Define SBOX_READ(i) and INV_SBOX_READ(i) before #include \"quartet.h\""
#endif

/* FullMix: [[1,1,1,0],[0,1,1,1],[1,0,1,1],[1,1,0,1]] over GF(2).
 * Self-inverse: FullMix(FullMix(s)) == s for all s. */
static inline uint16_t quartet_fullmix(uint16_t state)
{
    uint8_t w0 = (state >> 12) & 0x0F;
    uint8_t w1 = (state >> 8)  & 0x0F;
    uint8_t w2 = (state >> 4)  & 0x0F;
    uint8_t w3 = state & 0x0F;
    return ((uint16_t)(w0 ^ w1 ^ w2) << 12) |
           ((uint16_t)(w1 ^ w2 ^ w3) << 8)  |
           ((uint16_t)(w2 ^ w3 ^ w0) << 4)  |
           (w3 ^ w0 ^ w1);
}

#define QUARTET_INV_FULLMIX quartet_fullmix

/* Round key for round i: rk = K[i%16] XOR_{j=0..15} S[K[j] XOR (i+j+1)] */
static inline uint8_t quartet_round_key(uint64_t key, uint8_t round)
{
    uint8_t rk = (key >> (4 * (round % 16))) & 0x0F;
    for (uint8_t j = 0; j < 16; j++) {
        uint8_t kj = (key >> (4 * j)) & 0x0F;
        rk ^= SBOX_READ((kj ^ (round + j + 1)) & 0x0F);
    }
    return rk;
}

static inline uint16_t quartet_round(uint16_t state, uint8_t rk)
{
    uint8_t w0 = SBOX_READ((state >> 12) & 0x0F);
    uint8_t w1 = SBOX_READ((state >> 8)  & 0x0F);
    uint8_t w2 = SBOX_READ((state >> 4)  & 0x0F);
    uint8_t w3 = SBOX_READ(state & 0x0F);
    w0 ^= rk; w1 ^= rk; w2 ^= rk; w3 ^= rk;
    return quartet_fullmix(((uint16_t)w0 << 12) | ((uint16_t)w1 << 8) |
                           ((uint16_t)w2 << 4)  | w3);
}

static inline uint16_t quartet_inv_round(uint16_t state, uint8_t rk)
{
    state = QUARTET_INV_FULLMIX(state);
    uint8_t w0 = (uint8_t)((state >> 12) & 0x0F) ^ rk;
    uint8_t w1 = (uint8_t)((state >> 8)  & 0x0F) ^ rk;
    uint8_t w2 = (uint8_t)((state >> 4)  & 0x0F) ^ rk;
    uint8_t w3 = (uint8_t)(state & 0x0F)        ^ rk;
    w0 = INV_SBOX_READ(w0);
    w1 = INV_SBOX_READ(w1);
    w2 = INV_SBOX_READ(w2);
    w3 = INV_SBOX_READ(w3);
    return ((uint16_t)w0 << 12) | ((uint16_t)w1 << 8) |
           ((uint16_t)w2 << 4)  | w3;
}

static inline uint16_t quartet_encrypt(uint16_t plaintext, uint64_t key)
{
    uint16_t state = plaintext;
    for (uint8_t r = 0; r < QUARTET_ROUNDS; r++) {
        state = quartet_round(state, quartet_round_key(key, r));
    }
    return state;
}

static inline uint16_t quartet_decrypt(uint16_t ciphertext, uint64_t key)
{
    uint16_t state = ciphertext;
    for (int r = QUARTET_ROUNDS - 1; r >= 0; r--) {
        state = quartet_inv_round(state, quartet_round_key(key, (uint8_t)r));
    }
    return state;
}

/* Test vectors from SPEC.md, Section 9. */
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
    for (size_t i = 0; i < sizeof(tests) / sizeof(tests[0]); i++) {
        uint16_t ct = quartet_encrypt(tests[i].pt, tests[i].key);
        if (ct != tests[i].ct) return 0;
        if (quartet_decrypt(ct, tests[i].key) != tests[i].pt) return 0;
    }
    return 1;
}

#endif /* QUARTET_H */
