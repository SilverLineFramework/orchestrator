# This compilation requires Wasienv
# You can install it here:
# https://github.com/wasienv/wasienv

# NOTE: if defined, will copy wasm files to WASM_OUT_FOLDER (does *not* end with a '/')
WASM_OUT_FOLDER=../wasm

# the compiler
CC=~/.wasienv/bin/wasicc

# main "executable" (get base folder name; NOTE: we assume that there is a $(MAIN).c)
MAIN=$(shell basename $(CURDIR))

# define library paths in addition to /usr/lib (e.g. LFLAGS = -L/home/newhall/lib  -L../lib)
LFLAGS= 

# libraries to link into executable (e.g.: LIBS = -lmylib -lm)
LIBS=

# includes
INCLUDES=-Isys

# libraries (e.g.: -lmylib -lm)
LIBS= 

# compiler flags 
# --allow-undefined allows external function declarations (e.g. functions defined outside wasm land); 
# --export-dynamic will export functions marked as visibility 'default' (so they are available to be called from outside wasm land)
CFLAGS=-Wl,--allow-undefined -Wl,--export-dynamic 

# source files (NOTE: we assume that there is a $(MAIN).c)
SRCS=$(shell ls *.c| grep -v -e $(MAIN).c) 

OBJS=$(SRCS:.c=.o)

all: $(MAIN).wasm
	test -n "$(WASM_OUT_FOLDER)"  && cp *wasm $(WASM_OUT_FOLDER)/  || echo "done."

$(MAIN).wasm: $(MAIN).c $(OBJS) 
	$(info $(MAIN).c)
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $(MAIN).c $(OBJS) $(LFLAGS) $(LIBS)

%.wasm : %.c
	$(CC) $< -o $@ $(CFLAGS) $(LIBS)

%.o : %.c
	$(CC) -c $< -o $@ $(CFLAGS) $(LIBS)

clean:
	rm *wasm $(WASM_OUT_FOLDER)/*wasm sys/*.o 

