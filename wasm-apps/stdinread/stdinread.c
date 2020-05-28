 /** @file stdinread.c
  *  @brief Example showing how to use poll and read from stdin when data is available
  * 
  */
#include <stdio.h>
#include <poll.h>
#include <unistd.h>

#define LINE_MAX 255

int main(void)
{
    char buf[LINE_MAX];
    struct pollfd fds[1];
    int timeout_msecs = 2000;
    int retval;

    fds[0].fd = fileno(stdin);
    fds[0].events = POLLIN;

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
