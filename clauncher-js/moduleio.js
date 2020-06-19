/**
 * @fileoverview Handle WASM module IO; communicates with the io worker thread (moduleio-worker) and also minimal signal support
 *
 * Copyright (C) Wiselab CMU.
 * @date April, 2020
 */
import { WasmFs } from "@wasmer/wasmfs";
import SharedArrayCircularBuffer from "/sa-cbuffer.js";
import * as WorkerMessages from "/worker-msgs.js";

/**
 * Gets stdin from shared buffer (filled by the mqtt worker) and sends stdout/stderr to mqtt worker
 */
export default class moduleIO {
  constructor(params) {
    // create wasmFs instance
    this.wasmFs = new WasmFs();

    // buffers to read data from; index 0 is stdin
    this.iob = [];
    this.iob[0] = {
      rflag: true,
      buf: new SharedArrayCircularBuffer(
        params.shared_array_buffer,
        params.mod_data.stdin_topic
      ),
    };

    // store channel info
    this.channels = [];

    // save module data
    this.modData = params.mod_data;

    // stdout/stderr write calls
    this.wasmFs.volume.fds[1].write = this.writePubsubStream.bind(
      this,
      this.modData.stdout_topic
    ); // bind write function with the class instance; pass the stdout topic as argument
    this.wasmFs.volume.fds[2].write = this.writePubsubStream.bind(
      this,
      this.modData.stdout_topic
    ); // bind write function with the class instance; pass the stdout topic as argument

    // assign all reads to fd 0 to our stdinRead function
    this.wasmFs.volume.fds[0].node.read = this.readBuffer.bind(this, 0); // bind read function with the class instance; pass the buffer index as argument

    // message channel port to the io worker that publishes output for the module
    this.IOWorkerPort = params.worker_port;

    // setup channels according to fd args
    this.setupChannelsFromModArgs(params.mod_data);

    // create /sys/signals
    this.wasmFs.volume.mkdirpBase("/sys/", 0o777);
    this.wasmFs.volume.openSync("/sys/signals", "w+"); // flag 'w+' to create the file
    console.log("fd: /sys/signals");
  }

  // setup channels
  setupChannelsFromModArgs(modData) {
    let modCh=undefined;
    if (typeof modData.channels === 'string' || modData.channels instanceof String) {
      try {
        modCh = JSON.parse(modData.channels);
      } catch(err) {
        console.log('could not parse channels');
      }
    } else modCh = modData.channels;
    
    if (modCh == undefined) return;
    if (modCh.length == 0) return;

    // create channels
    modCh.forEach((ch) => {
      if (ch.path.slice(-1) != "/") ch.path += "/";
      if (this.channels[ch.path] != undefined) {
        logError("Skipping channel:" + ch.path + " (repeat).");
      } else if (ch.path.startsWith("/ch/") == false) {
        logError(
          "Channel path must start with /ch/:" + ch.path + "(ignoring)."
        );
      } else {
        // directory for the channel
        this.wasmFs.volume.mkdirpBase(ch.path, 0o777);

        // save channel info
        this.channels[ch.path] = ch;

        // create files for the channel; each channel directory has a data, ctl, info files
        ["data", "ctl", "info"].forEach((fn) => {
          this.wasmFs.volume.openSync(ch.path + fn, "w+"); // flag 'w+' to create the file
          console.log("fd:", ch.path + fn);
        });
      }
    });
  }

  // return a list of directories used by channels; to be used by wasi preopen directories
  channelDirectories() {
    let chDirs = [];
    for (const [key, value] of Object.entries(this.channels)) {
      chDirs[key] = key;
    }
    return chDirs;
  }

  // wrap wasi path_open call to attach our IO calls to channels
  wrapPathOpen(wasi) {
    let _this = this;
    const prevPathOpen = wasi.wasiImport["path_open"];
    wasi.wasiImport["path_open"] = function (...args) {
      let result = prevPathOpen(...args);
      if (result == 0) {
        const p = Buffer.from(wasi.memory.buffer, args[2], args[3]).toString();
        const newfd = [...wasi.FD_MAP.keys()].reverse()[0];
        const f = wasi.FD_MAP.get(newfd);
        const dir = wasi.FD_MAP.get(args[0]);
        _this.attachIO(dir.path, p, f.real, newfd);
      }
      return result;
    };
  }

  // attach the read/write functions for channels
  attachIO(path, fn, realfd) {
    console.log("attachIO", path, fn, realfd);

    // check if it is a '/sys' file
    if (path === "/sys/") {
      if (fn === "signals") {
        // create a shared circuler buffer to be used by both workers
        let sb = SharedArrayCircularBuffer.createSharedBuffer();
        this.iob[realfd] = { rflag: true };
        this.iob[realfd].buf = new SharedArrayCircularBuffer(
          sb,
          "/sys/signals"
        );
        // ask IOWorker to start a new stream
        this.IOWorkerPort.postMessage({
          type: WorkerMessages.msgType.new_stream,
          mod_uuid: this.modData.uuid,
          shared_array_buffer: sb,
          channel: { path: "/sys/signals", type: "signalfd", mode: "r" },
        });
        this.wasmFs.volume.fds[realfd].node.read = this.readBuffer.bind(this, realfd);
      }
      return;
    }

    let ch = this.channels[path];
    if (ch == undefined) return; // not a valid channel

    let fullPath = path + fn;
    this.iob[realfd] = { rflag: true };
    if (fn === "data") {
      // create a shared circuler buffer to be used by both workers
      let sb = SharedArrayCircularBuffer.createSharedBuffer();
      this.iob[realfd].buf = new SharedArrayCircularBuffer(sb, fullPath);
      // ask IOWorker to start a new stream
      this.IOWorkerPort.postMessage({
        type: WorkerMessages.msgType.new_stream,
        mod_uuid: this.modData.uuid,
        shared_array_buffer: sb,
        channel: ch,
      });
      // attach read/write functions
      if (ch.mode === "r" || ch.mode === "rw") {
        this.wasmFs.volume.fds[realfd].node.read = this.readBuffer.bind(this, realfd);
      }
      if (ch.mode === "w" || ch.mode === "rw") {
        this.wasmFs.volume.fds[realfd].write = this.writePubsubStream.bind(this, ch.params.topic);
      }
    } else {
      // mode for info and ctl
      let infoCtlMode = { info: "r", ctl: "w" };
      // attach read/write functions for info and ctl
      if (infoCtlMode[fn] === "r" || infoCtlMode[fn] === "rw") {
        this.wasmFs.volume.fds[readlfd].node.read = this.readInfoCtl.bind(this, realfd, ch);
      }
      if (infoCtlMode[fn] === "w" || infoCtlMode[fn] === "rw") {
        this.wasmFs.volume.fds[readlfd].write = this.writeInfoCtl.bind(this, realfd, ch);
      }
    }
  }

  // convenience method to send errors to pubsub stdout
  logError(module, msg) {
    console.log("Error:", msg);
    writePubsubStream(this.modData.stdout_topic, buffer);
  }

  // write to pubsub; send message to worker
  writePubsubStream(topic, buffer) {
    let strMsg;
    if (typeof buffer === "string") {
      strMsg = buffer;
    } else {
      strMsg = buffer.toString();
    }
    if (strMsg === "\n") return buffer.length; // dont send just '\n'
    //console.log("WASM [", topic, "] :", strMsg);
    this.IOWorkerPort.postMessage({
      type: WorkerMessages.msgType.pub_msg,
      mod_uuid: this.modData.uuid,
      msg: strMsg,
      dst: topic,
    });
    return buffer.length;
  }

  // handle read to a buffer (acts similar to C read)
  readBuffer(
    bKey, // key of the buffer to read data from (given through javascript bind())
    stdinBuffer, // Uint8Array of the buffer that is sent to the guest wasm module's standard input
    offset, // offset for the standard input
    length, // length of the standard input
    position // Position in the input
  ) {
    let iob = this.iob[bKey];

    // Per the C API, first read should be the string
    // Second read would be the end of the string
    if (iob.rflag == false) {
      iob.rflag = true;
      return 0;
    }

    if (iob.buf.length() == 0) return 0;
    
    let bytes = iob.buf.pop(length);
    // place the bytes into the buffer for standard input
    for (let x = 0; x < bytes.length; ++x) {
      stdinBuffer[x] = bytes[x];
    }

    iob.rflag = false;

    // Return the number of bytes, per the C API
    return bytes.length;
  }

  writeInfoCtl(cbIndex, ch) {
    this.logError("Write (info/ctl) not implemented.");
  }

  // handle read to a buffer (acts similar to C read)
  readInfoCtl(
    bKey, // key of the buffer to read data from (given through javascript bind())
    stdinBuffer, // Uint8Array of the buffer that is sent to the guest wasm module's standard input
    offset, // offset for the standard input
    length, // length of the standard input
    position // Position in the input
  ) {
    this.logError("Read (info/ctl) not implemented.");
  }
}
