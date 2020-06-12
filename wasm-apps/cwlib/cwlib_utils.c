 /** @file cwlib_utils.c
 *  @brief Utility functions (time,..) for cwlib
 * 
 */
#include "cwlib_utils.h"
#include "limits.h"

static inline int timespec_to_timestamp_clamp (
    const struct timespec *timespec, __wasi_timestamp_t *timestamp) {
  // Invalid nanoseconds field.
  if (timespec->tv_nsec < 0 || timespec->tv_nsec >= NSEC_PER_SEC)
    return 0;

  if (timespec->tv_sec < 0) {
    // Timestamps before the Epoch are not supported.
    *timestamp = 0;
  } else if (mul_overflow(timespec->tv_sec, NSEC_PER_SEC, timestamp) ||
             add_overflow(*timestamp, timespec->tv_nsec, timestamp)) {
    // Make sure our timestamp does not overflow.
    *timestamp = NUMERIC_MAX(__wasi_timestamp_t);
  }
  return 1;
}
