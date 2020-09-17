## Channels
Channels are a file-like abstraction that defines the access programs have to external resrources. For now, we use channels to define access to a pubsub structure, but imagine these can be used to define access to other device (e.g. sensors) and network resources.

The first implemenation of channels was a WASI-compatible broser implementation for the [browser runtime](https://github.com/conix-center/arena-runtime-browser)). We are now working on implementations that do not use WASI, due to memory limitations in embedded-devices. The host API of channels is defined bellow.

## Channel API

### Setup channel: 

```c
int ch_open(const char *chname, int flags, mode_t mode);
```

```c
int ch_close(int fd);
```

### Read/Write: 
```c
int ch_read_msg(int fd, char* buf, size_t size);
```

```c
int ch_write_msg(int fd, char* buf, size_t size);
```

### Poll a channel: 
```c
int ch_poll(int *chs, int nchs, int timeout);
```
