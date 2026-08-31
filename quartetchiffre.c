/**
 * QUARTET: A 4-bit Word-Oriented Block Cipher
 *
 * Canonical C reference. Self-contained — defines the S-box tables (from
 * sbox.h) and the SBOX_READ / INV_SBOX_READ macros, then includes
 * quartet.h for the cipher itself.
 *
 * The same quartet.h powers the runner and any other embedder.
 *
 * Build:
 *   gcc -O3 -std=c11 -o quartet_c quartetchiffre.c
 *
 * For 8-bit AVR targets, compile with -mmcu=atmega328p (or similar); the
 * __AVR__ branch below places the S-box tables in flash via progmem.
 *
 * Mano H. | 2026
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "sbox.h"

#if defined(__AVR__)
#include <avr/pgmspace.h>
static const uint8_t sbox[16] __attribute__((progmem))      = QUARTET_SBOX_INIT;
static const uint8_t inv_sbox[16] __attribute__((progmem))  = QUARTET_INV_SBOX_INIT;
#define SBOX_READ(i)     pgm_read_byte(&sbox[(i)])
#define INV_SBOX_READ(i) pgm_read_byte(&inv_sbox[(i)])
#else
static const uint8_t sbox[16]     = QUARTET_SBOX_INIT;
static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
#define SBOX_READ(i)     (sbox[(i)])
#define INV_SBOX_READ(i) (inv_sbox[(i)])
#endif

#include "quartet.h"

int main(void)
{
    if (!quartet_self_test()) {
        printf("FAIL: Self-test\n");
        return 1;
    }
    printf("PASS: Self-test\n");

    /* Roundtrip on the four spec keys, four plaintexts. */
    static const uint64_t keys[] = {
        0x0123456789ABCDEFULL, 0xFFFFFFFFFFFFFFFFULL,
        0x0000000000000000ULL, 0xFEDCBA9876543210ULL,
    };
    static const uint16_t pts[] = {0x0000, 0x1234, 0xDEAD, 0xFFFF};

    int pass = 1;
    for (size_t k = 0; k < sizeof(keys) / sizeof(keys[0]); k++) {
        for (size_t p = 0; p < sizeof(pts) / sizeof(pts[0]); p++) {
            uint16_t ct = quartet_encrypt(pts[p], keys[k]);
            if (quartet_decrypt(ct, keys[k]) != pts[p]) pass = 0;
        }
    }
    printf("%s: Roundtrip test\n", pass ? "PASS" : "FAIL");
    if (!pass) return 1;

    /* Benchmark. */
    const uint64_t key = 0x0123456789ABCDEFULL;
    const uint32_t count = 10000;
    clock_t start = clock();
    for (uint32_t i = 0; i < count; i++) {
        volatile uint16_t ct = quartet_encrypt((uint16_t)i, key);
        (void)ct;
    }
    double secs = (double)(clock() - start) / CLOCKS_PER_SEC;
    printf("Speed: %.0f enc/s (%.2f us/enc)\n",
           count / secs, 1e6 * secs / count);
    return 0;
}
