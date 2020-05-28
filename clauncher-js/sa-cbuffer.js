/**
 * @fileoverview Thread-safe circular buffer (using SharedArrayBuffer for shared memory between workers) 
 *
 * Copyright (C) Wiselab CMU.
 * @date April, 2020
 */

 const DFT_BUFFER_SIZE = 2048; // 2 Kb buffer 

export default class SharedArrayCircularBuffer {
  /**
   * Create a SharedArrayBuffer instance of the needed size to store a circular buffer with byteSize bytes
   *
   * a circular buffer holds the following data:
   *   uint32[0]: head index of the circular buffer
   *   uint32[1]: tail index of the circular buffer
   *   uint32[2]: total bytes allocated (byteSize)
   *   uint32[3]: current number of bytes stored
   *   uint8: spinlock flag
   *   uint8[byteSize]: the circular buffer data
   *
   * @param byteSize size of the circular buffer
   */
  static createSharedBuffer(byteSize=DFT_BUFFER_SIZE) {
    let buffer = new SharedArrayBuffer(
      Uint32Array.BYTES_PER_ELEMENT * 4 + 1 + byteSize
    );

    // create views to the SharedArrayBuffer
    let uint32 = new Uint32Array(buffer, 0, 4); // view for head, tail, byteSize and current number of bytes stored
    let spinlock = new Uint8Array(buffer, Uint32Array.BYTES_PER_ELEMENT * 4, 1); // view to the spinlock flag

    // init head, tail, allocated size and current number of bytes stored
    uint32[0] = 0; // head (push to head)
    uint32[1] = 0; // tail (pop from tail)
    uint32[2] = byteSize; // total size allocated for the buffer data
    uint32[3] = 0; // current number of bytes stored

    spinlock[0] = 0;
    return buffer;
  }

  /**
   * Create an instance
   * @param buffer SharedArrayBuffer instance where the circular buffer data is stored (created with createSharedBuffer())
   * @param desc A string description of the buffer
   */
  constructor(buffer, desc) {
    if (buffer == undefined)
      throw new Error("Must provide a SharedArrayBuffer instance");

    // use the shared buffer for a structure that holds the circular buffer data:
    //    uint32[0]: head index of the circular buffer
    //    uint32[1]: tail index of the circular buffer
    //    uint32[2]: total bytes allocated (byteSize)
    //    uint32[3]: current number of bytes stored
    //    uint8: spinlock flag
    //    uint8[byteSize]: the circular buffer data
    this.buffer = buffer; // previously created shared array buffer

    let byteSize = buffer.byteLength - (Uint32Array.BYTES_PER_ELEMENT * 4 + 1);
    //console.log(buffer);

    // create views to the SharedArrayBuffer
    this.uint32 = new Uint32Array(this.buffer, 0, 4); // view for head, tail, byteSize and current number of bytes stored
    this.spinlock = new Uint8Array(this.buffer, Uint32Array.BYTES_PER_ELEMENT * 4, 1); // view to the spinlock flag
    this.bytes = new Uint8Array(this.buffer, Uint32Array.BYTES_PER_ELEMENT * 4 + 1, byteSize); // view to the bytes stored

    // flag to log when a push causes data to be overwritten (useful to check is buffer is too small)
    this.logOverwrite = true;

    this.desc = desc;
  }

  /**
   * Pop bytes from tail, wrapping arround; stop when empty (tail = head)
   * @param nbytes how many bytes to return
   * @return an array of min(nbytes, buffer length) bytes; returns an empty array if buffer is empty (tail = head)
   */
  pop(nbytes) {
    var data = [];

    // acquire lock
    while (Atomics.compareExchange(this.spinlock, 0, 0, 1) != 0);

    nbytes = Math.min(nbytes, this.uint32[3]);
    if (nbytes > 0) {
      for (var i = 0; i < nbytes; i++) {
        data[i] = this.bytes[(this.uint32[1] + i) % this.uint32[2]];
      }
      this.uint32[1] = (this.uint32[1] + i) % this.uint32[2];

      this.uint32[3] -= nbytes;
    }
    // release lock
    this.spinlock[0] = 0;

    return data; // returns an empty array if there are no bytes to return
  }

  /**
   * Push bytes to head, wrapping around and overwritting old vales
   * @param bytes byte array
   */
  push(bytes) {
    var i = 0;

    if (this.buffer === undefined)
      throw new Error("Must create a shared array instance");
    if (this.uint32[2] == 0)
      throw new Error("Must create a shared array instance with size >0");

    // acquire lock
    while (Atomics.compareExchange(this.spinlock, 0, 0, 1) != 0);

    // push items
    for (var i = 0; i < bytes.length; i++) {
      let ii = (this.uint32[0] + i) % this.uint32[2];
      this.bytes[ii] = bytes[i];
    }

    // update head
    this.uint32[0] = (this.uint32[0] + i) % this.uint32[2];

    // update tail, if needed
    if (bytes.length > this.uint32[2] - this.uint32[3]) {
      this.uint32[1] = this.uint32[0];
      if (this.logOverwrite == true) console.log("Circular buffer overwrite:", this.desc);
    }

    // update len
    this.uint32[3] += bytes.length;
    if (this.uint32[3] > this.uint32[2]) this.uint32[3] = this.uint32[2];

    // release lock
    this.spinlock[0] = 0;

    return this.uint32[3];
  }

  /**
   * Return number of bytes currently in the buffer
   */
  length() {
    return this.uint32[3];
  }

  /**
   * Return total bytes allocated for the buffer
   */
  size() {
    return this.uint32[2];
  }

  /**
   * Turn on/off the logging of when old values are overwritten
   * @param value true/false
   */
  setOverwriteLog(value) {
    this.logOverwrite = value;
  }

}
