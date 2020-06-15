 /** @file cwlib.h
 *  @brief Definitions for the CONIX WASM Library (CWLib)
 * 
 *  WASI wrapper to expose a simple pubsub enabled event-based interface for WASM modules.
 *
 *
 * Copyright (C) Wiselab CMU. 
 * @date April, 2020
 */

#ifndef _CSI_
#define _CSI_
#include <unistd.h>

#define BUF_MAX 1000

// file descriptor indexes
enum FDIs
{
  FDI_signalfd = 0,
  FDI_channels_start,
  FDI_MAX = 10
};


// Macro to declare function as an export
#define WASM_EXPORT __attribute__( ( visibility( "default" ) ) )

/**
 * Loop iteration callback function to be defined by the (cwlib) user; 
 * 
 * @param ctx user provided context to pass the handler
 */
typedef void (*cwlib_loop_calback_t)(void *ctx);

/**
 * Channel event handler function to be defined by the (cwlib) user; 
 * 
 * @param buf event-specific data read from the channel
 * @param count size of data read
 * @param ctx user provided context to pass the handler
 */
typedef void (*cwlib_channel_handler_t)(void *buf, size_t count, void *ctx);

/**
 * @struct channel
 * @brief Hold info about a channel
 */
typedef struct channel {
   char *path; /*!< channel path; cwlib allocated  */
   int flags; /*!< channel creation flags */
   mode_t mode; /*!< channel mode bits */
   int fdi; /*!<  index in fds array */
   cwlib_channel_handler_t handler; /*!< channel callback when new data is received */
   void *ctx; /*!< user provided context for channel callback */
} t_channel;

/**
 * Init cwlib
 * Setup signalfd; check if we have to jump to the event loop
 */
int cwlib_init();

/**
 * Setup a channel
 * 
 * @param chpath opens the channel specified by pathname
 * @param flags must include one of O_RDONLY, O_WRONLY, or O_RDWR. file creation flags and file status flags can be used, similar to open()
 * @param mode file mode bits applied when a new file is created, similar to open()
 * @param ch_handler handler to be called when new data is available on this channel
 * @param ctx user-specified data to be given to handler
 */
int cwlib_open_channel(const char *chpath, int flags, mode_t mode, cwlib_channel_handler_t ch_handler, void *ctx);

/**
 * Setup a callback every event loop iteration
 * 
 * @param loop_callback callback for event loop iteration
 * @param callback_ctx user provided callback context
 */
int cwlib_loop_callback(cwlib_loop_calback_t loop_callback, void *callback_ctx);

/**
 * Polls files and performs callbacks appropriately
 *
 * @param sleep_s amount of time, in milliseconds, to sleep if we have no events to wait
 * 
 */
int cwlib_loop(int sleep_ms);

#endif