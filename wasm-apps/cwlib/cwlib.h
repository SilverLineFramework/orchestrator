 /** @file cwlib.h
 *  @brief Definitions for the CONIX WASM Library (CWLib)
 * 
 *  Event-based library to perform file-based IO (for pubsub and signals) for WASM modules using WASI. 
 *  The event loop implemented by cwlib allows modules to migrate to other runtimes.
 * 
 *  Modules must have a main() with a predefined structure:
 *    1. first call performed by main (before any declaration or any other call) must be to cwlib_init()
 *    2. main sets up channels (or setup loop callback and timeout handlers, when available in cwlib)
 *    3. main calls cwlib_loop() to run the event loop
 *
 * Copyright (C) Wiselab CMU. 
 * @date April, 2020
 */

#ifndef _CSI_
#define _CSI_
#include <unistd.h>

#define BUF_MAX 1000
#define FILE_PATH_MAX 500

// file descriptor indexes; signalfd is always 0
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
 * 
 * @return -1 on error; 0 otherwise  
 */
WASM_EXPORT int cwlib_init();

/**
 * Setup a channel. 
 * 
 * Returns a channel file descriptor and setup a callback for when new data is available on the channel
 * Calls open() on the fiven channel path; different from open(), a channel has only one file descriptor. 
 * Multiple cwlib_channel_open() calls with the same path will return the same file descriptor.
 * 
 * The path "signalfd" is treated differently by calling signalfd() instead of open()
 * 
 * @param path opens the channel specified by pathname; if path is "signalfd", will call signalfd() to open it
 * @param flags must include one of O_RDONLY, O_WRONLY, or O_RDWR. file creation flags and file status flags can be used, similar to open()
 * @param mode file mode bits applied when a new file is created, similar to open()
 * @param handler handler to be called when new data is available on this channel
 * @param ctx user-specified data to be given to the handler
 * 
 * @return -1 on error; a channel file descriptor on success. a call to an existing path returns the previously created descriptor index
 */
int cwlib_channel_open(const char *chpath, int flags, mode_t mode, cwlib_channel_handler_t ch_handler, void *ctx);

/**
 * Setup/change a callback for an open channel
 * 
 * @todo support for signalfd callbacks (returns -1 if signalfd is given)
 * 
 * @param chfd channel fd returned by cwlib_channel_open
 * @param loop_callback callback for event loop iteration
 * @param callback_ctx user provided callback context
 * 
 * @return -1 on error; 0 otherwise
 */
int cwlib_channel_callback(int chfd, cwlib_channel_handler_t handler, void *ctx);

/**
 * Setup a callback every event loop iteration
 * 
 * @param loop_callback callback for event loop iteration
 * @param callback_ctx user provided callback context
 * 
 * @return -1 on error; 0 otherwise
 */
int cwlib_loop_callback(cwlib_loop_calback_t loop_callback, void *callback_ctx);

/**
 * Polls files and performs callbacks appropriately
 *
 * @param sleep_s amount of time, in milliseconds, to sleep if we have no events
 * 
 * @return -1 on error; does not return unless a signal is received
 */
int cwlib_loop(int sleep_ms);

#endif