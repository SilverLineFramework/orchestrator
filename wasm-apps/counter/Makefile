# This compilation requires Wasienv
# You can install it here:
# https://github.com/wasienv/wasienv

# NOTE: if defined, will copy wasm files to WASM_OUT_FOLDER (does *not* end with a '/')
WASM_OUT_FOLDER=../wasm

# the compiler
CC=~/.wasienv/bin/wasicc

# libs
LIBS= 

# compiler flags 
# --allow-undefined allows external function declarations (e.g. functions defined outside wasm land); 
# --export-dynamic will export functions marked as visibility 'default' (so they are available to be called from outside wasm land)
CFLAGS=-Wl,--allow-undefined -Wl,--export-dynamic 

# source files
SRCS=$(wildcard *.c)

OBJS=$(SRCS:.c=.wasm)

all: $(OBJS)
	test -n "$(WASM_OUT_FOLDER)"  && cp *wasm $(WASM_OUT_FOLDER)/  || echo "done."

%.wasm : %.c
	$(CC) $< -o $@ $(CFLAGS) $(LIBS)

clean:
	rm *wasm $(WASM_OUT_FOLDER)/*wasm

