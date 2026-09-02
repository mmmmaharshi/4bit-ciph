#pragma once
// QUARTET-32 — thin C adapter over quartet.h, no S-box duplication.
// Block 32 bits = hi16 || lo16, key 128 bits = hi64 || lo64.
// Include order (same as quartet.h): define SBOX_READ/INV_SBOX_READ, include sbox.h, include quartet.h, then include this file.
#include <stdint.h>
/* forward decls — real defs come from quartet.h when consumer defines SBOX_READ first */
uint16_t quartet_encrypt(uint16_t pt, uint64_t key);
uint16_t quartet_decrypt(uint16_t ct, uint64_t key);

static inline uint32_t quartet32_encrypt(uint32_t pt, uint64_t k_hi, uint64_t k_lo) {
    uint16_t hi = (uint16_t)(pt >> 16);
    uint16_t lo = (uint16_t)(pt & 0xFFFF);
    uint16_t ch = quartet_encrypt(hi, k_hi);
    uint16_t cl = quartet_encrypt(lo, k_lo);
    return ((uint32_t)ch << 16) | cl;
}
static inline uint32_t quartet32_decrypt(uint32_t ct, uint64_t k_hi, uint64_t k_lo) {
    uint16_t hi = (uint16_t)(ct >> 16);
    uint16_t lo = (uint16_t)(ct & 0xFFFF);
    uint16_t ph = quartet_decrypt(hi, k_hi);
    uint16_t pl = quartet_decrypt(lo, k_lo);
    return ((uint32_t)ph << 16) | pl;
}
