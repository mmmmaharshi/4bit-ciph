/**
 * QUARTET: A 4-bit Word-Oriented Block Cipher — Bitsliced Variant
 *
 * Constant-time implementation using bitsliced S-box (no table lookups).
 * Build:
 *   gcc -O3 -std=c11 -DQUARTET_BITSLICED -o quartet_c_bitsliced quartetchiffre_bitsliced.c
 *
 * Mano H. | 2026
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define QUARTET_BITSLICED
#include "sbox.h"
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
            uint16_t ct = quartet_encrypt_bitsliced(pts[p], keys[k]);
            if (quartet_decrypt_bitsliced(ct, keys[k]) != pts[p]) pass = 0;
        }
    }
    printf("%s: Roundtrip test\n", pass ? "PASS" : "FAIL");
    if (!pass) return 1;

    /* Benchmark. */
    const uint64_t key = 0x0123456789ABCDEFULL;
    const uint32_t count = 10000;
    clock_t start = clock();
    for (uint32_t i = 0; i < count; i++) {
        volatile uint16_t ct = quartet_encrypt_bitsliced((uint16_t)i, key);
        (void)ct;
    }
    double secs = (double)(clock() - start) / CLOCKS_PER_SEC;
    printf("Speed (bitsliced): %.0f enc/s (%.2f us/enc)\n",
           count / secs, 1e6 * secs / count);
    return 0;
}