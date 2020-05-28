 /** @file cwlib.c
 *  @brief CONIX WASM WASI Library
 * 
 *  WASI wrapper to expose a simple pubsub enabled event-based interface for WASM modules
 *  Callback waits are implemented with __wasi_poll_oneoff()
 *
 * Copyright (C) Wiselab CMU. 
 * @date April, 2020
 */
#include <unistd.h>

#include "cwlib.h"
#include "cwlib_utils.h"

//TMP some globals to hold the subscription for a timer (should be an array)
__wasi_subscription_t g_sub = {
  .type = __WASI_EVENTTYPE_CLOCK,
  .u.clock.clock_id = __WASI_CLOCK_REALTIME,
  .u.clock.flags = 0,
};
int g_nevents=0;
cwlib_event_handler_t g_timer_callback;
void *g_ctx;

/**
 * Setup a timer callback 
 * 
 * @param delay_ms interval in milliseconds
 * @param callback the time callback
 * @param ctx user provided context to pass to the timer
 */
cwlib_set_timer(int delay_ms, cwlib_timer_handler_t timer_callback, void *ctx) {
  // TODO: fix to properly count timeout
  g_sub.u.clock.timeout = delay_ms * NSEC_PER_MS;

  g_timer_callback = timer_callback;

  g_nevents=1;
}

/**
 * Polls timers and files and performs callbacks appropriately
 *
 * @param sleep_s amount of time, in milliseconds, to sleep if we have no events to wait
 * 
 */
void cwlib_poll(int sleep_ms) {
  size_t nevents;
  __wasi_event_t ev;

  // if no timer to wait for, sleep
  if (g_nevents == 0) {
    sleep(sleep_ms/1000); // TODO: setup a sub and poll for a timer instead
    return;
  }

  // call __wasi_poll_oneoff
  __wasi_errno_t error = __wasi_poll_oneoff(&g_sub, &ev, g_nevents, &nevents);
  
  // TODO: check ev and perform respective callback  
  // for now, only calls timer
  if (nevents > 0) {
    g_events=0;
    g_timer_callback(__WASI_EVENTTYPE_CLOCK, NULL, g_ctx); // timer does not provide any data
  }
}




/*
    //sleep(1);
    int seconds=5;
  struct timespec ts = {.tv_sec = seconds, .tv_nsec = 0};

     // Prepare polling subscription (https://github.com/wasmerio/wasmer/blob/master/lib/wasi/src/syscalls/types.rs)
     __wasi_subscription_t sub = {
      .type = __WASI_EVENTTYPE_CLOCK,
      .u.clock.clock_id = __WASI_CLOCK_REALTIME,
      .u.clock.flags = 0,
    };

  if (!timespec_to_timestamp_clamp(&ts, &sub.u.clock.timeout))
    return 1;

    size_t nevents;
    __wasi_event_t ev;
    __wasi_errno_t error = __wasi_poll_oneoff(&sub, &ev, 1, &nevents);
    printf("Done!\n");

*/