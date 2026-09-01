/*
 * QUARTET — instrumented S-box table for structural Level 2 check.
 *
 * Same data as the real S-box (matches sbox.h), but with a global
 * read counter that increments on every S-box access. The C
 * runner (tests/fixtures/instrumented_runner.c) wraps
 * SBOX_READ with a counter read+reset before/after each
 * encryption.
 */

#ifndef QUARTET_INSTRUMENTED_SBOX_H
#define QUARTET_INSTRUMENTED_SBOX_H

#include <stdint.h>

static uint8_t sbox_inst[16] = {
    0x0C, 0x05, 0x06, 0x0B, 0x09, 0x00, 0x0A, 0x0D,
    0x03, 0x0E, 0x0F, 0x08, 0x04, 0x07, 0x01, 0x02
};
static uint8_t inv_sbox_inst[16] = {
    0x05, 0x0E, 0x0F, 0x08, 0x0C, 0x01, 0x02, 0x0D,
    0x0B, 0x04, 0x06, 0x03, 0x00, 0x07, 0x09, 0x0A
};

static volatile uint64_t g_sbox_read_count = 0;
static volatile uint64_t g_inv_sbox_read_count = 0;

static inline uint8_t SBOX_READ_INST(uint8_t i) {
    g_sbox_read_count++;
    return sbox_inst[i & 0x0F];
}
static inline uint8_t INV_SBOX_READ_INST(uint8_t i) {
    g_inv_sbox_read_count++;
    return inv_sbox_inst[i & 0x0F];
}

#define SBOX_READ(i)        SBOX_READ_INST((uint8_t)(i))
#define INV_SBOX_READ(i)    INV_SBOX_READ_INST((uint8_t)(i))

#endif
