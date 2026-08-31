/*
 * QUARTET — runner adapter.
 *
 * Reads "<64-bit key hex> <16-bit pt hex>" pairs on stdin, writes the
 * 16-bit ct on stdout. Powers the cross-validation harness.
 *
 * The cipher itself lives in quartet.h; this file is the I/O adapter.
 */

#include <stdint.h>
#include <stdio.h>

#include "sbox.h"

static const uint8_t sbox[16]     = QUARTET_SBOX_INIT;
static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
#define SBOX_READ(i)     (sbox[(i)])
#define INV_SBOX_READ(i) (inv_sbox[(i)])

#include "quartet.h"

int main(void)
{
    /* Fully unbuffered stdout: each printf immediately writes
     * to the pipe, which the parent reads line-by-line. This is
     * required for the persistent-runner mode in tests/tvla.py
     * (the runner is launched as a long-running subprocess and
     * driven via stdin/stdout, so default full-buffered stdout
     * would deadlock). */
    setbuf(stdout, NULL);

    uint64_t key;
    uint16_t pt;
    while (scanf("%llX %hX", (unsigned long long *)&key, &pt) == 2) {
        printf("%04X\n", quartet_encrypt(pt, key));
    }
    return 0;
}
