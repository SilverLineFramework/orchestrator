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
#include <signal.h>
#include <stdio.h>
#include <poll.h>
#include <stdbool.h>
#include <string.h>

#include "sys/signalfd.h"
#include "cwlib.h"

// file descriptor indexes
enum FDIs
{
    FDI_signalfd=0,
    FDI_channels_start,
    FDI_MAX=10
};

// array of all fds we are going wait for (with poll()), including channels
struct pollfd g_fds[FDI_MAX];

// count of fds
int g_nfds=0;

// information about channels
t_channel g_channels[FDI_MAX-FDI_channels_start];

// user callback for each event loop (temp fix until we have timer-based callbacks setup by the user)
cwlib_loop_calback_t g_loop_callback = NULL;

// user provided context for the event loop callback
void *g_loop_calback_ctx = NULL;

// event loop sleep time if we have no events to wait
const int dft_g_el_sleep_ms = 5000;
int g_el_sleep_ms = dft_g_el_sleep_ms;

// flag indicating if we received a quit signal
bool g_quit_pending = 0;

/**
 * Init cwlib
 * Setup signalfd; check if we have to jump to the event loop
 * 
 * @param loop_callback callback for event loop iteration
 * @param callback_ctx user provided callback context
 */
int cwlib_init(cwlib_loop_calback_t loop_callback, void *callback_ctx) 
{
  // add signalfd
  g_fds[FDI_signalfd].fd = signalfd(-1, NULL, 0); // mask and flags are ignored
  g_fds[FDI_signalfd].events = POLLRDNORM;
  if (g_fds[FDI_signalfd].fd < 0)
  {
      printf("error opening signalfd\n");
      return -1;
  }
  g_nfds = 1;

  g_loop_callback = loop_callback;
  g_loop_calback_ctx = callback_ctx;

  char *v = getenv("CWLIB_JTEL"); // presence of env variable Jump To Event Loop (JTEL) indicates we should jump
  if (v != NULL) { 
    g_el_sleep_ms = g_el_sleep_ms > 0 ? g_el_sleep_ms : dft_g_el_sleep_ms;
    // reopen channels
    reopen_channels();
    // call event loop
    cwlib_loop(g_el_sleep_ms); 
  }

  return 0;
}

/**
 * Setup a channel
 * 
 * @param path opens the channel specified by pathname
 * @param flags must include one of O_RDONLY, O_WRONLY, or O_RDWR. file creation flags and file status flags can be used, similar to open()
 * @param mode file mode bits applied when a new file is created, similar to open()
 * @param handler handler to be called when new data is available on this channel
 * @param ctx user-specified data to be given to handler
 */
int cwlib_open_channel(const char *path, int flags, mode_t mode, cwlib_channel_handler_t handler, void *ctx) {
    if (g_nfds < FDI_channels_start) return -1;
    if (g_nfds == FDI_MAX) return -1;
    
    // add channel to fd list
    g_fds[g_nfds].fd = open(path, flags, mode);
    if (flags & O_RDONLY) g_fds[g_nfds].events = POLLRDNORM;
    if (flags & O_WRONLY) g_fds[g_nfds].events = POLLWRNORM;
    if (flags & O_RDWR) g_fds[g_nfds].events = POLLWRNORM | POLLRDNORM;
    if (g_fds[g_nfds].fd < 0)
    {
        printf("error opening channel %s\n", path);
        return -1;
    }
    
    // save channel data
    int nch = g_nfds-FDI_channels_start;
    g_channels[nch].path = malloc(strlen(path)+1);
    memcpy(g_channels[nch].path, path, strlen(path)+1);
    g_channels[nch].flags = flags;
    g_channels[nch].mode = mode;
    g_channels[nch].fdi = g_nfds;
    g_channels[nch].handler = handler;
    g_channels[nch].ctx = ctx;
    g_nfds++;

    return 0;
}

/**
 * @internal Setup channels after migration
 * 
 */
int reopen_channels() {
    for (int i = FDI_channels_start; i < g_nfds; i++) {
      // call open again
      g_fds[g_channels[i].fdi].fd = open(g_channels[i].path, g_channels[i].flags, g_channels[i].mode); 
      if (g_fds[g_channels[i].fdi].fd < 0)
      {
          printf("error opening channel %s\n", g_channels[i].path);
          return -1;
      }
    }
    
    return 0;
}

/**
 * Setup a callback every event loop iteration
 * 
 * @param loop_callback callback for event loop iteration
 * @param callback_ctx user provided callback context
 */
int cwlib_set_loop_callback(cwlib_loop_calback_t loop_callback, void *callback_ctx)  {
  g_loop_callback = loop_callback;
  g_loop_calback_ctx = callback_ctx;
}

/**
 * Polls files and performs callbacks appropriately
 *
 * @param sleep_s amount of time, in milliseconds, to sleep if we have no events to wait
 * 
 */
int cwlib_loop(int sleep_ms) {
    if (g_nfds < FDI_channels_start) return -1;

    char buf[BUF_MAX];

    while (1)
    {
        int retval = poll(g_fds, g_nfds, sleep_ms);
        if (retval > 0)
        {
            // event in one of the fds
            for (int i = 0; i < g_nfds; i++)
            {
                if (i == FDI_signalfd)
                {
                    struct signalfd_siginfo fdsi;           
                    // signal
                    ssize_t s = read(g_fds[i].fd, &fdsi, sizeof(struct signalfd_siginfo));
                    if (s > 0 && s != sizeof(struct signalfd_siginfo))
                    {
                        printf("error reading signalfd\n");
                    }
                    else if (s > 0)
                    {
                        // SIGQUIT indicates a module migration; we save this state; only exit when all fds are empty
                        if (fdsi.ssi_signo == SIGQUIT)
                        {
                            // save last sleep value
                            g_quit_pending = true;
                        }
                        else if (fdsi.ssi_signo == SIGKILL) exit(EXIT_SUCCESS);
                    }
                }
                else
                {
                    // read channel
                    int n = read(g_fds[i].fd, buf, sizeof(buf));
                    if (n > 0)
                    {
                        int ich = i-FDI_channels_start;
                        g_channels[ich].handler(buf, n, g_channels[ich].ctx);
                    }
                }
            }
        } else {
          // all fds are empty; check if we should quit
          if (g_quit_pending) {
            g_el_sleep_ms = sleep_ms; // save the last sleep value to call the event loop again
            g_quit_pending = false;
            exit(EXIT_SUCCESS);
          }
        }
        g_loop_callback(g_loop_calback_ctx);
    }

}