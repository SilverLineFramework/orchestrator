/** @file cwlib.c
 *  @brief CONIX WASM Library (CWLib)
 *  @see cwlib.h for documentation
 *
 * Copyright (C) Wiselab CMU. 
 * @date April, 2020
 * 
 * @todo Implement timeout handlers setup by user
 */
#include <unistd.h>
#include <signal.h>
#include <stdio.h>
#include <poll.h>
#include <stdbool.h>
#include <string.h>

#include "sys/signalfd.h"
#include "cwlib.h"

/**
 * @internal Setup channels after migration
 * 
 * @return -1 on error; 0 otherwise 
 */
static int reopen_channels();

// array of all fds we are going wait for (with poll()), including channels
struct pollfd *g_fds = NULL;

// count of fds; start at FDI_channels_start as some (signalfd) fds should be created by default
int g_nfds = FDI_channels_start;

// information about channels
t_channel *g_channels = NULL;

// user callback for each event loop (temp fix until we have timer-based callbacks setup by the user)
cwlib_loop_calback_t g_loop_callback = NULL;

// user provided context for the event loop callback
void *g_loop_calback_ctx = NULL;

// event loop sleep time if we have no events to wait
const int dft_g_el_sleep_ms = 5000;
int g_el_sleep_ms = dft_g_el_sleep_ms;

// flag indicating if we received a quit signal
bool g_quit_pending = 0;

/** @copydoc reopen_channels */
int reopen_channels()
{
  // call signalfd again
  g_fds[FDI_signalfd].fd = signalfd(-1, NULL, 0); // mask and flags are ignored

  for (int i = FDI_channels_start; i < g_nfds; i++)
  {
    // call open again
    g_fds[i].fd = open(g_channels[i].path, g_channels[i].flags, g_channels[i].mode);
    if (g_fds[i].fd < 0)
    {
      return -1;
    }
  }

  return 0;
}

/** @copydoc cwlib_init */
int cwlib_init()
{
  char *v = getenv("CWLIB_JTEL"); // presence of env variable Jump To Event Loop (JTEL) indicates we should jump
  if (v != NULL)
  {
    g_el_sleep_ms = g_el_sleep_ms > 0 ? g_el_sleep_ms : dft_g_el_sleep_ms;
    // reopen channels
    reopen_channels();
    // call event loop
    cwlib_loop(g_el_sleep_ms);
  }
  else
  {
    g_fds = malloc(sizeof(struct pollfd) * FDI_MAX);
    if (g_fds == NULL)
      return -1;

    g_channels = malloc(sizeof(t_channel) * FDI_MAX);
    if (g_channels == NULL)
      return -1;

    // open signalfd
    int sfd = cwlib_channel_open("signalfd", O_RDONLY, 0, NULL, NULL);
    if (sfd < 0)
      return -1;
  }

  return 0;
}

/** @copydoc cwlib_channel_open */
int cwlib_channel_open(const char *path, int flags, mode_t mode, cwlib_channel_handler_t handler, void *ctx)
{
  if (g_fds == NULL)
    return -1;
  if (g_channels == NULL)
    return -1;
  if (g_nfds == FDI_MAX)
    return -1;

  // check if path to channel is already open
  for (int i = 0; i < g_nfds; i++)
  {
    if (strncmp(g_channels[i].path, path, strlen(path)) == 0)
    {
      return i;
    }
  }

  // open file descriptor
  int nfd = 0, chi = 0;
  if (strncmp(path, "signalfd", 8) == 0)
  {
    nfd = signalfd(-1, NULL, 0); // mask and flags are ignored
    if (nfd < 0)
      return -1;
    flags = O_RDONLY;
    chi = FDI_signalfd; // signalfd is always at a known index (0)
  }
  else
  {
    nfd = open(path, flags, mode);
    if (nfd < 0)
      return -1;
    chi = g_nfds;
    g_nfds++;
  }

  // add file descriptor to poll fd list
  g_fds[chi].fd = nfd;
  if (flags & O_RDONLY)
    g_fds[chi].events = POLLRDNORM;
  if (flags & O_WRONLY)
    g_fds[chi].events = POLLWRNORM;
  if (flags & O_RDWR)
    g_fds[chi].events = POLLWRNORM | POLLRDNORM;

  // save channel data
  int path_len = strnlen(path, FILE_PATH_MAX) + 1;
  g_channels[chi].path = malloc(path_len);
  if (g_channels[chi].path == NULL)
  {
    close(nfd);
    g_nfds--;
    return -1;
  }
  //strncpy_s(_channels[chi].path, path_len, path, path_len-1);
  memcpy(g_channels[chi].path, path, path_len - 1);
  g_channels[chi].path[path_len] = '\0';
  g_channels[chi].flags = flags;
  g_channels[chi].mode = mode;
  g_channels[chi].handler = handler;
  g_channels[chi].ctx = ctx;

  return nfd;
}

/** @copydoc cwlib_channel_callback */
int cwlib_channel_callback(int chfd, cwlib_channel_handler_t handler, void *ctx)
{
  int chi=0;
  // find channel
  for (; chi < g_nfds; chi++)
  {
    if (g_fds[chi].fd == chfd) break;
  }
  if (chi >= g_nfds) return -1;
  if (chi == FDI_signalfd)
    return -1; // no callbacks for signalfd, for now

  g_channels[chi].handler = handler;
  g_channels[chi].ctx = ctx;
  
  return 0;
}

/** @copydoc cwlib_loop_callback */
int cwlib_loop_callback(cwlib_loop_calback_t loop_callback, void *callback_ctx)
{
  g_loop_callback = loop_callback;
  g_loop_calback_ctx = callback_ctx;
  return 0;
}

/** @copydoc cwlib_loop */
int cwlib_loop(int sleep_ms)
{
  if (g_nfds < FDI_channels_start)
    return -1;

  char buf[BUF_MAX];

  while (1)
  {
    // loop callback
    g_loop_callback(g_loop_calback_ctx);

    // poll fds
    int retval = poll(g_fds, g_nfds, sleep_ms);
    bool no_fd_input = true;
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
          if (s > 0 && s == sizeof(struct signalfd_siginfo))
          {
            // SIGQUIT indicates a module migration; we save this state and only exit when all fds are empty
            if (fdsi.ssi_signo == SIGQUIT)
            {
              g_quit_pending = true;
            }
            else if (fdsi.ssi_signo == SIGKILL)
              exit(EXIT_SUCCESS);
          }
        }
        else
        {
          // read channel
          int n = read(g_fds[i].fd, buf, sizeof(buf));
          if (n > 0)
          {
            no_fd_input = false;
            // call channel handler
            if (g_channels[i].handler != NULL)
              g_channels[i].handler(buf, n, g_channels[i].ctx);
          }
        }
      }
    }
    // check if we can quit
    if (g_quit_pending == true && no_fd_input == true)
    {
      g_el_sleep_ms = sleep_ms; // save the last sleep value to call the event loop again
      g_quit_pending = false;
      exit(EXIT_SUCCESS);
    }
  }
}