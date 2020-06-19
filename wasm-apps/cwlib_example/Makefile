# This compilation requires:
#   Wasienv: https://github.com/wasienv/wasienv
#   wabt: https://github.com/WebAssembly/wabt
#   grep and GNU sed (in macOS install with: brew install gnu-sed)

# NOTE: if defined, will copy wasm files to WASM_OUT_FOLDER (does *not* end with a '/')
WASM_OUT_FOLDER=../wasm-files

# NOTE: if defined and True, will insert a cwlib_init() call at the start of main
INSERT_CWLIB_INIT=True

# location of wabt binaries (https://github.com/WebAssembly/wabt)
WASM2WAT=../../../wabt/bin/wasm2wat
WAT2WASM=../../../wabt/bin/wat2wasm

# our sed syntax is for GNU sed; in MacOs we need to use gsed (install with: brew install gnu-sed)
UNAME_S=$(shell uname -s)
ifeq ($(UNAME_S),Linux)
SED=SEG
endif
ifeq ($(UNAME_S),Darwin)
SED=gsed
endif

# the compiler
CC=~/.wasienv/bin/wasicc

# main "executable" (get base folder name; NOTE: we assume that there is a $(MAIN).c)
MAIN=$(shell basename $(CURDIR))

# define library paths in addition to /usr/lib (e.g. LFLAGS = -L/home/newhall/lib  -L../lib)
LFLAGS= 

# libraries to link into executable (e.g.: LIBS = -lmylib -lm)
LIBS=

# includes
INCLUDES=-I../cwlib 

# libraries (e.g.: -lmylib -lm)
LIBS= 

# compiler flags 
# --allow-undefined allows external function declarations (e.g. functions defined outside wasm land); 
# --export-dynamic will export functions marked as visibility 'default' (so they are available to be called from outside wasm land)
CFLAGS=-Wl,--allow-undefined -Wl,--export-dynamic

# source files (NOTE: we assume that there is a $(MAIN).c)
SRCS=$(shell ls *.c| grep -v -e $(MAIN).c) ../cwlib/cwlib.c  ../cwlib/sys/signalfd.c 

OBJS=$(SRCS:.c=.o)

all: $(MAIN).wasm $(MAIN).wat
ifeq ($(INSERT_CWLIB_INIT),True)
	grep -c "call.*cwlib_init" $(MAIN).wat || ( $(SED) -e '/func.*main.*param.i32.i32/{N; /.*local/ a\    call $$cwlib_init\n    drop' -e '}' $(MAIN).wat > $(MAIN).wat.tmp && echo "Inserted cwlib_init() call." )
	test -f $(MAIN).wat.tmp && ( $(WAT2WASM) $(MAIN).wat.tmp -o $(MAIN).wasm ; mv $(MAIN).wat.tmp $(MAIN).wat ) || true
endif
ifdef WASM_OUT_FOLDER
	cp *wasm $(WASM_OUT_FOLDER)/
endif

$(MAIN).wasm: $(MAIN).c $(OBJS) 
	$(info $(MAIN).c)
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $(MAIN).c $(OBJS) $(LFLAGS) $(LIBS)

%.wat : %.wasm
	$(WASM2WAT) $<  > $@

%.wasm : %.c
	$(CC) $< -o $@ $(CFLAGS) $(LIBS)

%.o : %.c
	$(CC) -c $< -o $@ $(CFLAGS) $(LIBS)

clean:
	rm *wasm *wat $(WASM_OUT_FOLDER)/*wasm ../cwlib/*.o ../cwlib/sys/*.o

