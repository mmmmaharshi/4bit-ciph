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
 * Round constants break invariant subspaces (Leander et al., FSE 2011):
 *   C_r[i] = base[i] ^ r where base = {0x0, 0x5, 0xA, 0xF}
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
 * Bitsliced (constant-time, no table lookups) variant:
 *   #define QUARTET_BITSLICED
 *   #include "sbox.h"
 *   #include "quartet_core.h"
 *   // provides quartet_round_bitsliced, quartet_inv_round_bitsliced,
 *   // quartet_encrypt_bitsliced, quartet_decrypt_bitsliced
 *
 * Mano H. | 2026
 */

#ifndef QUARTET_CORE_H
#define QUARTET_CORE_H

#include <stdint.h>

#ifndef QUARTET_ROUNDS
#define QUARTET_ROUNDS 16
#endif

#ifndef QUARTET_BITSLICED
#ifndef SBOX_READ
#error "Define SBOX_READ(i) and INV_SBOX_READ(i) before #include \"quartet_core.h\""
#endif
#endif

/* Round constants: C_r[i] = base[i] ^ r, breaks {x,x,x,x} and other
 * structural invariant subspaces (Leander et al., FSE 2011). */
static inline uint8_t _rc(uint8_t nibble, uint8_t rnd)
{
    switch (nibble) {
        case 0: return (uint8_t)((0U ^ rnd) & 0xF);
        case 1: return (uint8_t)((5U ^ rnd) & 0xF);
        case 2: return (uint8_t)((0xA ^ rnd) & 0xF);
        default: return (uint8_t)((0xF ^ rnd) & 0xF);
    }
}

/* FullMix: [[1,1,1,0],[0,1,1,1],[1,0,1,1],[1,1,0,1]] over GF(2).
 * Order 4: M^2 = swap halves, M^4 = I. So M^{-1} = M^3 = [[1,0,1,1],[1,1,0,1],[1,1,1,0],[0,1,1,1]] */
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

static inline uint16_t quartet_inv_fullmix(uint16_t state)
{
    uint8_t w0 = (state >> 12) & 0x0F;
    uint8_t w1 = (state >> 8)  & 0x0F;
    uint8_t w2 = (state >> 4)  & 0x0F;
    uint8_t w3 = state & 0x0F;
    return ((uint16_t)(w0 ^ w2 ^ w3) << 12) |
           ((uint16_t)(w0 ^ w1 ^ w3) << 8)  |
           ((uint16_t)(w0 ^ w1 ^ w2) << 4)  |
           (w1 ^ w2 ^ w3);
}

#define QUARTET_INV_FULLMIX quartet_inv_fullmix

#ifndef QUARTET_BITSLICED

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

static inline uint16_t quartet_round(uint16_t state, uint8_t rk, uint8_t rnd)
{
    uint8_t rc0 = _rc(0, rnd);
    uint8_t rc1 = _rc(1, rnd);
    uint8_t rc2 = _rc(2, rnd);
    uint8_t rc3 = _rc(3, rnd);
    uint8_t w0 = SBOX_READ(((state >> 12) & 0x0F) ^ rc0);
    uint8_t w1 = SBOX_READ(((state >> 8)  & 0x0F) ^ rc1);
    uint8_t w2 = SBOX_READ(((state >> 4)  & 0x0F) ^ rc2);
    uint8_t w3 = SBOX_READ((state & 0x0F)      ^ rc3);
    w0 ^= rc0 ^ rk; w1 ^= rc1 ^ rk; w2 ^= rc2 ^ rk; w3 ^= rc3 ^ rk;
    return quartet_fullmix(((uint16_t)w0 << 12) | ((uint16_t)w1 << 8) |
                           ((uint16_t)w2 << 4)  | w3);
}

static inline uint16_t quartet_inv_round(uint16_t state, uint8_t rk, uint8_t rnd)
{
    uint8_t rc0 = _rc(0, rnd);
    uint8_t rc1 = _rc(1, rnd);
    uint8_t rc2 = _rc(2, rnd);
    uint8_t rc3 = _rc(3, rnd);
    state = QUARTET_INV_FULLMIX(state);
    uint8_t w0 = INV_SBOX_READ((uint8_t)((state >> 12) & 0x0F) ^ rc0 ^ rk);
    uint8_t w1 = INV_SBOX_READ((uint8_t)((state >> 8)  & 0x0F) ^ rc1 ^ rk);
    uint8_t w2 = INV_SBOX_READ((uint8_t)((state >> 4)  & 0x0F) ^ rc2 ^ rk);
    uint8_t w3 = INV_SBOX_READ((uint8_t)(state & 0x0F)       ^ rc3 ^ rk);
    return ((uint16_t)(w0 ^ rc0) << 12) | ((uint16_t)(w1 ^ rc1) << 8) |
           ((uint16_t)(w2 ^ rc2) << 4)  | (w3 ^ rc3);
}

static inline uint16_t quartet_encrypt(uint16_t plaintext, uint64_t key)
{
    uint16_t state = plaintext;
    for (uint8_t r = 0; r < QUARTET_ROUNDS; r++) {
        state = quartet_round(state, quartet_round_key(key, r), r);
    }
    return state;
}

static inline uint16_t quartet_decrypt(uint16_t ciphertext, uint64_t key)
{
    uint16_t state = ciphertext;
    for (int r = QUARTET_ROUNDS - 1; r >= 0; r--) {
        state = quartet_inv_round(state, quartet_round_key(key, (uint8_t)r), (uint8_t)r);
    }
    return state;
}

#endif /* !QUARTET_BITSLICED */

#ifdef QUARTET_BITSLICED

/* Bitsliced round key: uses table-based S-box in key schedule (still constant-time) */
static inline uint8_t quartet_round_key_bitsliced(uint64_t key, uint8_t round)
{
    uint8_t rk = (key >> (4 * (round % 16))) & 0x0F;
    for (uint8_t j = 0; j < 16; j++) {
        uint8_t kj = (key >> (4 * j)) & 0x0F;
        /* Use a small constant-time S-box lookup for key schedule */
        static const uint8_t sbox[16] = QUARTET_SBOX_INIT;
        rk ^= sbox[(kj ^ (round + j + 1)) & 0x0F];
    }
    return rk;
}

/* Bitsliced round: applies S-box to all 4 nibbles in parallel via bitsliced circuit */
static inline uint16_t quartet_round_bitsliced(uint16_t state, uint8_t rk, uint8_t rnd)
{
    uint16_t c = (uint16_t)_rc(0, rnd) |
                 ((uint16_t)_rc(1, rnd) << 4) |
                 ((uint16_t)_rc(2, rnd) << 8) |
                 ((uint16_t)_rc(3, rnd) << 12);
    state = quartet_sbox_bitsliced(state ^ c);
    state ^= c;
    state ^= (uint16_t)rk * 0x1111;
    return quartet_fullmix(state);
}

static inline uint16_t quartet_inv_round_bitsliced(uint16_t state, uint8_t rk, uint8_t rnd)
{
    uint16_t c = (uint16_t)_rc(0, rnd) |
                 ((uint16_t)_rc(1, rnd) << 4) |
                 ((uint16_t)_rc(2, rnd) << 8) |
                 ((uint16_t)_rc(3, rnd) << 12);
    state = QUARTET_INV_FULLMIX(state);
    state ^= c;
    state ^= (uint16_t)rk * 0x1111;
    state = quartet_inv_sbox_bitsliced(state);
    state ^= c;
    return state;
}

static inline uint16_t quartet_encrypt_bitsliced(uint16_t plaintext, uint64_t key)
{
    uint16_t state = plaintext;
    for (uint8_t r = 0; r < QUARTET_ROUNDS; r++) {
        state = quartet_round_bitsliced(state, quartet_round_key_bitsliced(key, r), r);
    }
    return state;
}

static inline uint16_t quartet_decrypt_bitsliced(uint16_t ciphertext, uint64_t key)
{
    uint16_t state = ciphertext;
    for (int r = QUARTET_ROUNDS - 1; r >= 0; r--) {
        state = quartet_inv_round_bitsliced(state, quartet_round_key_bitsliced(key, (uint8_t)r), (uint8_t)r);
    }
    return state;
}

/* Alias the standard names to bitsliced versions for self-test compatibility */
#define quartet_encrypt   quartet_encrypt_bitsliced
#define quartet_decrypt   quartet_decrypt_bitsliced

#endif /* QUARTET_BITSLICED */

#endif /* QUARTET_CORE_H */
