#ifndef _CWLIB_UTILS_
#define _CWLIB_UTILS_

// overflow util (https://github.com/WebAssembly/wasi-libc/blob/320054e84f8f2440def3b1c8700cedb8fd697bf8/libc-bottom-half/cloudlibc/src/common/overflow.h)
#define add_overflow(x, y, out) __builtin_add_overflow(x, y, out)
#define sub_overflow(x, y, out) __builtin_sub_overflow(x, y, out)
#define mul_overflow(x, y, out) __builtin_mul_overflow(x, y, out)

// time util (https://github.com/WebAssembly/wasi-libc/blob/446cb3f1aa21f9b1a1eab372f82d65d19003e924/libc-bottom-half/cloudlibc/src/common/time.h)
#define NSEC_PER_SEC 1000000000
#define NSEC_PER_MS 1000000

static inline int timespec_to_timestamp_clamp (
    const struct timespec *timespec, __wasi_timestamp_t *timestamp);

#endif