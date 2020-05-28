 /** @file signalfd.c
  *  @brief Minimal signalfd support 
  * 
  *  WASI libc removes all signal-related code; This adds support for signalfd
  *  Signals are passed through a file at '/signalfd'; the runtime creates and updates this file
  * 
  *  With signalfd we poll/select the file to receive signals (no need for signal handlers)
  *
  * Copyright (C) Wiselab CMU. 
  * @date April, 2020
  */
#include "signalfd.h"

 /**
  * Create a file descriptor that can be used to accept signals 
  * http://man7.org/linux/man-pages/man2/signalfd.2.html
  * 
  * @param fd (should be -1) we only create new file descriptors
  * @param mask (ignored)
  * @param flags (ignored) 
  */
int signalfd(int fd, const sigset_t *mask, int flags) {
    if (fd != -1) return -1; /* only support creating a new fd */
    return open("/signalfd", O_RDONLY, 0660);
}

/*
            s = read(sfd, &fdsi, sizeof(struct signalfd_siginfo));
               if (s != sizeof(struct signalfd_siginfo))
                   handle_error("read");

               if (fdsi.ssi_signo == SIGINT) {
                   printf("Got SIGINT\n");
               } else if (fdsi.ssi_signo == SIGQUIT) {
                   printf("Got SIGQUIT\n");
                   exit(EXIT_SUCCESS);
               } else {
                   printf("Read unexpected signal\n");
               }
*/               