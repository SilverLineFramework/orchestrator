 /** @file cwlib.h
 *  @brief Definitions for the CONIX WASM WASI Library
 * 
 *  WASI wrapper to expose a simple pubsub enabled event-based interface for WASM modules.
 *
 *
 * Copyright (C) Wiselab CMU. 
 * @date April, 2020
 */

#ifndef _CSI_
#define _CSI_

// Macro to declare function as an export
#define WASM_EXPORT __attribute__( ( visibility( "default" ) ) )

/**
 * Timer event handler function to be defined by the (cwlib) user; 
 * 
 * @param ctx user provided context to pass the handler
 */
typedef void (*cwlib_timer_handler_t)(void *ctx);

/**
 * Generic event handler function to be defined by the (cwlib) user; 
 * 
 * @param ev_type type of the event
 * @param ev_data event-specific data
 * @param ctx user provided context to pass the handler
 */
typedef void (*cwlib_event_handler_t)(int ev_type, void *ev_data, void *ctx);

/**
 * Setup a timer callback 
 * 
 * @param delay_ms interval in milliseconds
 * @param callback the time callback
 * @param ctx user provided context to pass to the timer
 */
int cwlib_set_timer(int delay_ms, cwlib_timer_handler_t timer_callback, void *ctx);

/**
 * Polls timers and files. Performs callbacks appropriately
 * Cwlib user should call cwlib_poll() in a loop
 *
 * @param sleep_s amount of time, in milliseconds, to sleep if we have no events to wait
 * 
 */
void cwlib_poll(int sleep_ms);

#endif