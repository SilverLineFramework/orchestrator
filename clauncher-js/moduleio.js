/**
 * @fileoverview Handle WASM module IO; communicates with the io worker thread (moduleio-worker)
 *
 * Copyright (C) Wiselab CMU.
 * @date April, 2020
 */
import { WasmFs } from "@wasmer/wasmfs";
import SharedArrayCircularBuffer from "/sa-cbuffer.js";

/**
 * Gets stdin from shared buffer (filled by the mqtt worker) and sends stdout/stderr to mqtt worker
 */
export default class moduleStdIO {
  constructor(params) {

    // create wasmFs instance
    this.wasmFs = new WasmFs();

    // array of shared circular buffers; index 0 is stdin
    this.cb = [];
    this.cb[0] = new SharedArrayCircularBuffer(params.shared_array_buffer, params.mod_data.stdin_topic);

    // flag for reads to the fd
    this.readFlag = [];
    this.readFlag[0] = true;

    // store channel info
    this.channels = [];

    // save module uuid and stdout topic
    this.modData = { uuid: params.mod_data.uuid, stdout_topic: params.mod_data.stdout_topic};

    // stdout/stderr write calls 
    this.wasmFs.volume.fds[1].write = this.writePubsubStream.bind(this, this.modData.stdout_topic); // bind write function with the class instance; pass the stdout topic as argument
    this.wasmFs.volume.fds[2].write = this.writePubsubStream.bind(this, this.modData.stdout_topic); // bind write function with the class instance; pass the stdout topic as argument

    // assign all reads to fd 0 to our stdinRead function
    this.wasmFs.volume.fds[0].node.read = this.readPubsubStream.bind(this, 0); // bind read function with the class instance; pass the buffer index as argument

    // message channel port to the io worker that publishes output for the module
    this.IOWorkerPort = params.worker_port;

    // setup channels according to fd args
    this.setupChannelsFromModArgs(params.mod_data);

  }

  setupChannelsFromModArgs(modData) {
    let modCh = modData.channels;
    // create channels
    modCh.forEach((ch) => {
      if (ch.path.slice(-1) != "/") ch.path += "/";
      if (this.channels[ch.path] != undefined) {
        logError("Skipping channel:" + ch.path + " (repeat).");
      } else if (ch.path.startsWith("/ch/") == false) {
        logError("Channel path must start with /ch/:" + ch.path + "(ignoring).");
      } else {
        // directory for the channel
        this.wasmFs.volume.mkdirpBase( ch.path , 0o777);
        
        // save channel info
        this.channels[ch.path]=ch;

        // create files for the channel; each channel directory has a data, ctl, info files
        ["data", "ctl", "info"].forEach((fn) => {
          this.wasmFs.volume.openSync(ch.path+fn, "w+"); // flag 'w+' to create the file
          console.log("fd:", ch.path+fn);
        });  
      }
    });

  }

  channelDirectories() {
    let chDirs = [];
    for (const [key, value] of Object.entries(this.channels)) {
      chDirs[key] = key;
    }
    return chDirs;
  }

  // called by wasi path_open; attach the read/write functions for channels
  attachIO(path, fn, realfd, fd) {
    //console.log("attachIO",path, fn, realfd, fd);

    let ch = this.channels[path];
    if (ch == undefined) return;
    
    this.readFlag[fd] = true;
    let fullPath = path+fn;
    if (fn === "data") {
        // create a shared buffer to be used by both workers as a circular buffer
        let sb = SharedArrayCircularBuffer.createSharedBuffer();
        this.cb[fd] = new SharedArrayCircularBuffer(sb, fullPath); 
        // ask IOWorker to start a new channel stream
        this.IOWorkerPort.postMessage({type: WorkerMessages.msgType.new_stream, mod_uuid:this.modData.uuid, shared_array_buffer: sb, channel: ch});
        // attach read/write functions 
        if (ch.mode === "r" || ch.mode === "rw") {
          this.wasmFs.volume.fds[realfd].node.read = this.readPubsubStream.bind(this, newfd);
        }
        if (ch.mode === "w" || ch.mode === "rw") {
          this.wasmFs.volume.fds[realfd].write = this.writePubsubStream.bind(this, ch.params.topic);
        }
    } else {
      // mode for info and ctl
      let infoCtlMode = {info: "r", ctl: "w"};
      // attach read/write functions for info and ctl
      if (infoCtlMode[fn] === "r" || infoCtlMode[fn] === "rw") {
        this.wasmFs.volume.fds[readlfd].node.read = this.readInfoCtl.bind(this, newfd, ch);
      }
      if (infoCtlMode[fn] === "w" || infoCtlMode[fn] === "rw") {
        this.wasmFs.volume.fds[readlfd].write = this.writeInfoCtl.bind(this, newfd, ch);
      }
    }

  }

  logError(module, msg) {
    console.log("Error:", msg);
    writePubsubStream(this.modData.stdout_topic, buffer);
  }

  writePubsubStream(topic, buffer) {
    let strMsg;
    if (typeof buffer === 'string') {
      strMsg = buffer;
    } else {
      strMsg = buffer.toString();
    }
    if (strMsg === "\n") return buffer.length; // dont send just '\n'
    //console.log("WASM [", topic, "] :", strMsg);
    this.IOWorkerPort.postMessage({type: WorkerMessages.msgType.pub_msg, mod_uuid: this.modData.uuid, msg: strMsg, dst: topic});
    return buffer.length;
  }

  // Handle read of stream from pubsub (acts similar to C read)
  readPubsubStream(
    cbIndex, // index of the circular buffer to read data from (given through javascript bind())
    stdinBuffer, // Uint8Array of the buffer that is sent to the guest wasm module's standard input
    offset, // offset for the standard input
    length, // length of the standard input
    position // Position in the input
  ) {
    let cb = this.cb[cbIndex];

    // Per the C API, first read should be the string
    // Second read would be the end of the string
    if (this.readFlag[cbIndex] == false) {
      this.readFlag[cbIndex] = true;
      return 0;
    }

    if (cb.length() == 0) return 0;

    // place the string into the buffer for standard input
    const bytes = cb.pop(length);
    for (let x = 0; x < bytes.length; ++x) {
      stdinBuffer[x] = bytes[x];
    }

    cb.readFlag = false;
    
    // Return the current stdin, per the C API
    return bytes.length;
  }

  writeInfoCtl(cbIndex, ch) {
    this.logError("Write to " + ch.fn + ". Not implemented");
  }

  readInfoCtl(
    cbIndex, // index of the circular buffer to read data from (given through javascript bind())
    ch, // channel (given through javascript bind())
    stdinBuffer, // Uint8Array of the buffer that is sent to the guest wasm module's standard input
    offset, // offset for the standard input
    length, // length of the standard input
    position // Position in the input
  ) {
    this.logError("Read to " + ch.fn + ". Not implemented");
    return 0;    
  }
}