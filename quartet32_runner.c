/*
 * QUARTET-32 — runner adapter. Reuses sbox.h/quartet.h/quartet32.h.
 * Reads "<128-bit key hex (32 hex)> <32-bit pt hex>" stdin, writes 32-bit ct.
 */
#include <stdint.h>
#include <stdio.h>
#include <inttypes.h>
#include "sbox.h"
static const uint8_t sbox[16] = QUARTET_SBOX_INIT;
static const uint8_t inv_sbox[16] = QUARTET_INV_SBOX_INIT;
#define SBOX_READ(i) (sbox[(i)])
#define INV_SBOX_READ(i) (inv_sbox[(i)])
#include "quartet.h"
#include "quartet32.h"
int main(void){
    setbuf(stdout,NULL);
    unsigned long long khi, klo;
    uint32_t pt;
    // key as 32 hex chars -> two 64-bit halves; pt as 8 hex
    while (scanf("%16llX%16llX %X", &khi, &klo, &pt)==3){
        uint64_t kh=(uint64_t)khi, kl=(uint64_t)klo;
        uint32_t ct=quartet32_encrypt(pt, kh, kl);
        printf("%08X\n", ct);
    }
    return 0;
}
