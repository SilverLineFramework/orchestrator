 /** @file poll_example.c
  *  @brief Example showing poll on stdin, signalfd and a channel
  * 
  *  The runtime has setup acess to a channel under /ch/light
  *  Signals are indicated though a file also setup by the runtime
  *
  * Copyright (C) Wiselab CMU. 
  * @date April, 2020
  */
#include <stdio.h>
#include <poll.h>
#include <unistd.h>
#include "sys/signalfd.h"
#include <signal.h>

#define LINE_MAX 255

// file descriptor indexes
enum FDIs
{
    FDI_stdin = 0,
    FDI_signalfd,
    FDI_ch_light,
    FDI_NUM
};

int main(void)
{
    char buf[LINE_MAX];
    struct pollfd fds[FDI_NUM];
    int timeout_msecs = 5000;

    // add stdin
    fds[FDI_stdin].fd = fileno(stdin);
    fds[FDI_stdin].events = POLLIN;

    // add signalfd
    fds[FDI_signalfd].fd = signalfd(-1, NULL, 0); // mask and flags are ignored
    fds[FDI_signalfd].events = POLLRDNORM;
    if (fds[FDI_signalfd].fd < 0)
    {
        printf("error opening signalfd\n");
        return -1;
    }

    // add pubsub channel
    fds[FDI_ch_light].fd = open("/ch/light/data", O_RDWR, 0660);
    fds[FDI_ch_light].events = POLLRDNORM;
    if (fds[FDI_ch_light].fd < 0)
    {
        printf("error opening channel /ch/light/data\n");
        return -1;
    }

    // try sending a message to channel
    if (write(fds[FDI_ch_light].fd, "message", 8) != 8)
    {
        printf("error writing to /ch/light/data\n");
    }

    while (1)
    {
        int retval = poll(fds, FDI_NUM, timeout_msecs);

        if (retval > 0)
        {
            // event in one of the fds
            for (int i = 0; i < FDI_NUM; i++)
            {
                if (i == FDI_signalfd)
                {
                    struct signalfd_siginfo fdsi;           
                    // signal
                    ssize_t s = read(fds[i].fd, &fdsi, sizeof(struct signalfd_siginfo));
                    if (s > 0 && s != sizeof(struct signalfd_siginfo))
                    {
                        printf("error reading signalfd\n");
                    }
                    else if (s > 0)
                    {
                        if (fdsi.ssi_signo == SIGQUIT)
                        {
                            printf("Got SIGQUIT\n");
                            exit(EXIT_SUCCESS);
                        }
                        else if (fdsi.ssi_signo == SIGKILL)
                        {
                            printf("Got SIGKILL\n");
                            exit(EXIT_FAILURE);
                        }
                    }
                }
                else
                {
                    // read stdin/channel
                    if (read(fds[i].fd, buf, sizeof(buf)) > 0)
                    {
                        printf("rcvd: %s", buf);
                    }
                }
            }
        }
    }
    exit(EXIT_SUCCESS);
}
