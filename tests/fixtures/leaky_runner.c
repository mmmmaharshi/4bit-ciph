/*
 * QUARTET — C leaky reference for TVLA negative control.
 *
 * Reads "<64-bit key hex> <16-bit pt hex>" on stdin, writes the
 * 16-bit ct on stdout. Same I/O contract as quartet_runner.c, but
 * the encryption is the deliberately-leaky variant: when the top
 * bit of the key is 1, the runner sleeps for 1 microsecond before
 * encrypting. The real cipher (and the real quartet_runner.c)
 * does not have this branch.
 *
 * The wall-clock counter differs by ~1us between the two groups
 * in the TVLA; the Welch t-test should report a large |t| on
 * the wall-clock counter, demonstrating that the test methodology
 * catches the known leakage.
 */

#include <stdint.h>
#include <stdio.h>
#include <time.h>

#include "sbox.h"

static const uint8_t sbox[16]     = QUARTET_SBOX_INIT;
static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
#define SBOX_READ(i)     (sbox[(i)])
#define INV_SBOX_READ(i) (inv_sbox[(i)])

#include "quartet.h"

static void leak_sleep_us(unsigned us)
{
    struct timespec ts = { 0, (long)us * 1000L };
    nanosleep(&ts, NULL);
}

int main(void)
{
    /* Fully unbuffered stdout: see quartet_runner.c. */
    setbuf(stdout, NULL);

    uint64_t key;
    uint16_t pt;
    while (scanf("%llX %hX", (unsigned long long *)&key, &pt) == 2) {
        if ((key >> 63) & 1u) {
            leak_sleep_us(1000);  /* 1 ms — large enough to dominate */
                                   /* the bursty Windows pipe IPC. */
        }
        printf("%04X\n", quartet_encrypt(pt, key));
    }
    return 0;
}
