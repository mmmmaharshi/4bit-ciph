/*
 * QUARTET — instrumented runner for structural Level 2 check.
 *
 * Wraps SBOX_READ / INV_SBOX_READ with read counters (via
 * quartet_instrumented.h). Protocol (driven from Python):
 *
 *   count  - print the cumulative S-box read counter, then reset
 *
 *   <key> <pt>  - run one encryption, return the per-encryption
 *                  S-box read count via a side channel:
 *                  stdout is the CT, stderr is the count.
 *
 *   exit   - exit
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
            /* Print cumulative count, then reset. */
            printf("COUNT %" PRIu64 " %" PRIu64 "\n",
                   (uint64_t)g_sbox_read_count,
                   (uint64_t)g_inv_sbox_read_count);
            g_sbox_read_count = 0;
            g_inv_sbox_read_count = 0;
            fflush(stdout);
        } else if (strcmp(line, "exit") == 0) {
            break;
        } else {
            /* Parse "key pt" — read key and pt as separate tokens */
            if (sscanf(line, "%" SCNx64, &key) != 1) continue;
            if (scanf("%" SCNx32, &pt) != 1) continue;
            /* Reset counters, run, report. */
            g_sbox_read_count = 0;
            g_inv_sbox_read_count = 0;
            uint16_t ct = quartet_encrypt((uint16_t)pt, key);
            printf("%04X %" PRIu64 " %" PRIu64 "\n", ct,
                   (uint64_t)g_sbox_read_count,
                   (uint64_t)g_inv_sbox_read_count);
            fflush(stdout);
        }
    }
    return 0;
}
