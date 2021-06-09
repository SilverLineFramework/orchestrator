 # ARTS Design Documentation

By leveraging a common runtime and carefully integrated resource monitoring, the ARENA Runtime Supervisor (ARTS) can handle very heterogenous compute resources, across compute classes, from small embedded devices to edge servers.

We currently have three runtime environments being worked on to interact with ARTS:
<!-- markdown-link-check-disable-next-line -->
 - [Embedded Runtime](https://github.com/conix-center/arena-runtime-zephyr)
<!-- markdown-link-check-disable-next-line -->
 - [Linux Runtime](https://github.com/conix-center/arena-runtime-linux)
 - [Browser Runtime](https://github.com/conix-center/arena-runtime-browser)

We also maintain a [simulated runtime](https://github.com/conix-center/arena-runtime-simulated) for prototyping.

You can use the issue tracker to start discussions, suggestions, etc.

## Design Notes Slides
- [Runtime Design Notes (a bit browser focused)](https://docs.google.com/presentation/d/1HJaQPFMV_sUyMLoiXciZn9KVTCNXCgQ5LeNxbp_Vf2U/edit?usp=sharing).
- [Embedded Runtime Design Notes](https://docs.google.com/presentation/d/1BP3cx1oRckuiQTNVvrfEUUt9D-pV1mHmJwtnUMnffGU/edit?usp=sharing).

## Runtime Quick Start Links/Notes

### Linux runtime
Start [here](https://github.com/conix-center/arena-runtime-linux) **james_dev branch** . Has intructions to setup; See docs.

Compile python to wasm requires:
 - changes the paho library to use channels
 - new signals to support asyncio
 - python library: no auth, persist over mqtt and "flattened" 

See:
https://github.com/conix-center/arena-runtime-linux/blob/james_dev/docs/rustpython.md

### Python interpreter we use 
https://github.com/conix-center/RustPython-for-the-Arena

### Embedded runtime
See slides. Needs a gateway to setup (e.g. python program on your laptop). 

https://github.com/conix-center/arena-runtime-zephyr

### Basic runtime, cli
Simple runtime, good to learn how to use/get started with WAMR

https://github.com/conix-center/arena-runtime-mini

### WAMR (this is the WASM runtime we use as a base for ours)
https://github.com/bytecodealliance/wasm-micro-runtime
