/* Pre-include for AST analysis: defines SBOX_READ / INV_SBOX_READ
 * as macros that the AST visitor will recognise as S-box table
 * lookups. The real macro definitions live in the .c files that
 * include quartet.h; for AST analysis we need stub definitions.
 */
#ifndef QUARTET_SBOX_FOR_AST_H
#define QUARTET_SBOX_FOR_AST_H

/* Stub S-box table. The AST visitor treats sbox[] and inv_sbox[]
 * lookups with runtime index as constant-time by construction. */
static const unsigned char sbox[16] = {
    0x0C, 0x05, 0x06, 0x0B, 0x09, 0x00, 0x0A, 0x0D,
    0x03, 0x0E, 0x0F, 0x08, 0x04, 0x07, 0x01, 0x02
};
static const unsigned char inv_sbox[16] = {
    0x05, 0x0E, 0x0F, 0x08, 0x0C, 0x01, 0x02, 0x0D,
    0x0B, 0x04, 0x06, 0x03, 0x00, 0x07, 0x09, 0x0A
};
#define SBOX_READ(i)     (sbox[(i)])
#define INV_SBOX_READ(i) (inv_sbox[(i)])

#endif
