#include <stdio.h>
#include <poll.h>
#include <unistd.h>
#include <signal.h>

#include <sys/signalfd.h>

int t=0;

#define CWLIB_CHK_START()  char *v = getenv("CWLIB_JTEL");\
                         if (v != NULL) goto cwlib_restart_event_loop

#define CWLIB_QUIT() exit(EXIT_SUCCESS);\
                    cwlib_restart_event_loop:\
                     printf("back!\n")

int main(int argc, char **argv)
{
    CWLIB_CHK_START(); // this must be right at the start of main

    int i;
    struct pollfd fds[1];

    // add signalfd
    fds[0].fd = signalfd(-1, NULL, 0); // mask and flags are ignored
    fds[0].events = POLLRDNORM;
    if (fds[0].fd < 0)
    {
        printf("error opening signalfd\n");
        return -1;
    }

    printf("i=%d, t=%d\n", i, t);
    i = 0;
    while (1)
    {
        int retval = poll(fds, 1, 100); // TODO: check poll timeout (buggy in browser)
        if (retval == 0) sleep(1900); // TMP!
        if (retval > 0)
        {
            struct signalfd_siginfo fdsi;
            // read signal struct
            ssize_t s = read(fds[0].fd, &fdsi, sizeof(struct signalfd_siginfo));
            if (s > 0 && s != sizeof(struct signalfd_siginfo))
            {
                printf("error reading signalfd\n");
            }
            else if (s > 0) // received a valid struct
            {
                if (fdsi.ssi_signo == SIGQUIT) // handle SIGQUIT
                {
                    t=10;
                    CWLIB_QUIT();
                }
            }
        }

        printf("#%d\n", i++);
    }
    return 0;
}
