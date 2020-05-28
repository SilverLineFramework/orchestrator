#include <stdio.h>
#include <poll.h>
#include <unistd.h>
#include "sys/signalfd.h"
#include <signal.h>

#define LINE_MAX 255

int main(void)
{
    char buf[LINE_MAX];
    struct pollfd fds[3];
    int timeout_msecs = 2000;
    int retval;
    
    sigset_t mask = 0; /* our signalfd does not care about mask */
    struct signalfd_siginfo fdsi;
    ssize_t s;

    //sigemptyset(&mask);
    //sigaddset(&mask, SIGINT);
    //sigaddset(&mask, SIGQUIT);

           /* Block signals so that they aren't handled
              according to their default dispositions 

           if (sigprocmask(SIG_BLOCK, &mask, NULL) == -1)
               handle_error("sigprocmask");
            */



    //FILE * fp;
    //fopen("/ch/light/data", "rw");

    //if (fp == NULL) {
    //    printf("open file error\n");
    //}

    fds[0].fd = fileno(stdin);
    fds[0].events = POLLIN;
    fds[1].fd = signalfd(-1, &mask, 0);
    fds[1].events = POLLIN | POLLOUT;
    //fds[2].fd = open("/ch/light/data", O_RDWR, 0660);
    //fds[2].events = POLLIN | POLLOUT;

    if (fds[1].fd < 0) {
        printf("signalfd error\n");
        return -1;
    }

    printf("fd: %d\n", fds[1].fd);


    return 0;


    while (1)
    {
        retval = poll(fds, 1, timeout_msecs);

        if (retval > 0)
        {
            if (read(0, buf, sizeof(buf)) > 0)
            {
                printf("%s", buf);
            }
        }
    }
    exit(EXIT_SUCCESS);
}
