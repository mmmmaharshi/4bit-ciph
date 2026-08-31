/*
 * Minimal stdint.h for pycparser — only the types we actually use.
 * Real builds use the system <stdint.h>; this exists so that
 * pycparser can parse quartet.h without the full libc.
 */
typedef signed char      int8_t;
typedef short            int16_t;
typedef int              int32_t;
typedef long long        int64_t;
typedef unsigned char    uint8_t;
typedef unsigned short   uint16_t;
typedef unsigned int     uint32_t;
typedef unsigned long long uint64_t;
