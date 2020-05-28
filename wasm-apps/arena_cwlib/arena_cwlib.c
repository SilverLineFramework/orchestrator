 /** @file cwlib_example.c
  *  @brief Example showing how an ARENA WASM module looks like
  * 
  *  Uses CONIX WASI (cwlib), a WASI wrapper that exposes a simple pubsub enabled event-based 
  *  interface for WASM modules
  *
  * Copyright (C) Wiselab CMU. 
  * @date April, 2020
  */
 #include <stdio.h>

 #include <unistd.h>

 #include "cwlib.h"

 /**
  * Timer event handler function 
  * 
  * @param ctx user provided context to pass the handler
  */
 void timer_callback(void * ctx) {
   // setup timer (5 s)
   cwlib_set_timer(5000, &timer_callback, NULL);

   printf("Hello from WASM timer!\n");
 }

 int main(int argc, char ** argv) {
   printf("Hello, WASI!\n");

   // setup timer (5 s)
   cwlib_set_timer(5000, &timer_callback, NULL);

   // create an event loop 
   for (;;) {
     cwlib_poll(1000);
   }

   return 0;
 }
