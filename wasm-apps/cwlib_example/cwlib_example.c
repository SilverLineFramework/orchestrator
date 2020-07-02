/** @file cwlib_example.c
  *  @brief Example showing how an ARENA WASM module looks like
  * 
  *  Uses CONIX WASM (cwlib), an event library to perform file-based IO (for pubsub and signals)
  * 
  *  The event loop implemented by cwlib allows modules to migrate without need to move machine state.
  *  This requires main() must have a predefined structure:
  *    1. First call performed by main should be to cwlib_init(); !NOTE: our makefile will do this for you if it does not find a call to cwlib_init()
  *    2. main sets up channels (or setup loop callback and timeout handlers, when available in cwlib)
  *    3. main calls cwlib_loop() to run the event loop
  *
  * Copyright (C) Wiselab CMU. 
  * @date April, 2020
  */
#include <stdio.h>
#include <unistd.h>

#include "cwlib.h"

// declaration of callbacks
void loop(void *ctx);                                           //  event loop callback (called every loop_sleep_ms)
void on_channel_light_data(void *buf, size_t count, void *ctx); // channel callback when new data is available

/** 
  *  main() must have a predefined structure:
  *    1. call cwlib_init(); !NOTE: our makefile will insert a call to cwlib_init() if it does not find it
  *    2. call cwlib_open_channel to set up channels (or setup loop callback and timers, when available in cwlib)
  *    3. call cwlib_loop() to run the event loop
  */
int main(int argc, char **argv)
{
  // call cwlib_init() to startup cwlib; *no* state initialization before this call
  // Makefile will add this call if it does not find it

  // open channel
  cwlib_open_channel("/ch/light/data", O_RDWR, 0660, on_channel_light_data, NULL);

  // setup loop callback
  int cnt = 0; // declare variable to pass as context
  cwlib_loop_callback(loop, &cnt);

  /** 
  * main can do more work here...
  * open more channels, setup timeout handlers, anything else
  *
  * 
  */

  // enter event loop
  cwlib_loop(2000);

  return 0;
}

/**
  * Event loop callback (called every time interval passed to cwlib_loop(time_interval_ms))
  * 
  * @param ctx user provided context to pass the handler
  * 
  * @see cwlib_loop_callback() (called by main)
  * @see cwlib_loop call in main
  */
void loop(void *ctx)
{
  int *c = (int *)ctx;

  printf("#%d\n", *c);
  (*c)++;
}

/**
  * Channel callback when new data is available
  * 
  * @param buf event-specific data read from the channel
  * @param count size of data read
  * @param ctx user provided context to pass the handler
  * 
  * @ see cwlib_open_channel() (called by main)
  */
void on_channel_light_data(void *buf, size_t count, void *ctx)
{
  char *str = (char *)buf;
  str[count] = '\0';

  printf("%s", str);
}
