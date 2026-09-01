/*
 * QUARTET — leaky instrumented runner (negative control for the
 * structural Level 2 check).
 *
 * Same as instrumented_runner.c but with an algorithm-level leak:
 * when the top bit of the key is 1, an extra S-box read is performed
 * before encryption. This is the negative control: the real cipher
 * does 320 S-box reads per encryption regardless of key; this leaky
 * variant does 321 in the leak group, which the t-test catches with
 * |t| = inf.
 */

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <inttypes.h>

#include "tests/fixtures/quartet_instrumented.h"
#include "quartet.h"

int main(void)
{
    setbuf(stdout, NULL);
    setvbuf(stdin, NULL, _IONBF, 0);
    setbuf(stderr, NULL);

    char line[64];
    uint64_t key;
    uint32_t pt;
    while (scanf("%63s", line) == 1) {
        if (strcmp(line, "count") == 0) {
            printf("COUNT %" PRIu64 " %" PRIu64 "\n",
                   (uint64_t)g_sbox_read_count,
                   (uint64_t)g_inv_sbox_read_count);
            g_sbox_read_count = 0;
            g_inv_sbox_read_count = 0;
            fflush(stdout);
        } else if (strcmp(line, "exit") == 0) {
            break;
        } else {
            if (sscanf(line, "%" SCNx64, &key) != 1) continue;
            if (scanf("%" SCNx32, &pt) != 1) continue;
            g_sbox_read_count = 0;
            g_inv_sbox_read_count = 0;
            /* Algorithm-level leak: extra S-box read on the leak key. */
            if ((key >> 63) & 1u) {
                (void)SBOX_READ((uint8_t)(pt & 0x0F));
            }
            uint16_t ct = quartet_encrypt((uint16_t)pt, key);
            printf("%04X %" PRIu64 " %" PRIu64 "\n", ct,
                   (uint64_t)g_sbox_read_count,
                   (uint64_t)g_inv_sbox_read_count);
            fflush(stdout);
        }
    }
    return 0;
}
