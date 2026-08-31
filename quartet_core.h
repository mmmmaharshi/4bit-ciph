/*
 * QUARTET — cipher core: FullMix, round, key schedule, encrypt, decrypt.
 *
 * This is the constant-time-checked cipher core. It contains ONLY the
 * 6 functions that operate on secret data:
 *
 *   - quartet_fullmix
 *   - quartet_round_key
 *   - quartet_round
 *   - quartet_inv_round
 *   - quartet_encrypt
 *   - quartet_decrypt
 *
 * The `quartet_self_test` function (in quartet.h) is NOT here; it is
 * test code with data-dependent control flow and is not part of the
 * cipher core.
 *
 * The .c file that #includes this must first define SBOX_READ and
 * INV_SBOX_READ (see sbox.h for the values).
 *
 *   #include "sbox.h"
 *   static const uint8_t sbox[16]     = QUARTET_SBOX_INIT;
 *   static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
 *   #define SBOX_READ(i)     (sbox[(i)])
 *   #define INV_SBOX_READ(i) (inv_sbox[(i)])
 *   #include "quartet_core.h"
 *
 * Mano H. | 2026
 */

#ifndef QUARTET_CORE_H
#define QUARTET_CORE_H

#include <stdint.h>

#ifndef QUARTET_ROUNDS
#define QUARTET_ROUNDS 16
#endif

#ifndef SBOX_READ
#error "Define SBOX_READ(i) and INV_SBOX_READ(i) before #include \"quartet_core.h\""
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

#endif /* QUARTET_CORE_H */
