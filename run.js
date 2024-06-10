'use strict';
const { readFile } = require('node:fs/promises');
const { WASI } = require('wasi');
const { argv, env } = require('node:process');
const { join } = require('node:path');

const wasi = new WASI({
  version: 'preview1',
  args: argv,
  env,
});

(async () => {
  const fname = process.argv[2];
  const wasm = await WebAssembly.compile(
    await readFile(join(__dirname, fname)),
  );

  function readInt32(offset) {
    const bytes = new Uint8Array(instance.exports.memory.buffer);
    const len0 = bytes[offset];
    const len1 = bytes[offset + 1];
    const len2 = bytes[offset + 2];
    const len3 = bytes[offset + 3];

    return (len0 | len1 << 8 | len2 << 16 | len3 << 24);
  }

  function writeInt32(offset, value) {
    const bytes = new Uint8Array(instance.exports.memory.buffer);
    bytes[offset + 3] = (value >>> 24) & 0xFF;
    bytes[offset + 2] = (value >>> 16) & 0xFF;
    bytes[offset + 1] = (value >>> 8) & 0xFF;
    bytes[offset + 0] = (value) & 0xFF;
  }

  function get_string(offset) {
    const bytes = new Uint8Array(instance.exports.memory.buffer);
    const len = readInt32(offset);
    const textBytes = bytes.slice(offset + 4, offset + 4 + len);

    return new TextDecoder("utf8").decode(
      bytes.slice(offset + 4, offset + 4 + len)
    );
  }

  function write_string(value) {
    const bytes = new Uint8Array(instance.exports.memory.buffer);
    const offset = readInt32(0);
    const encoder = new TextEncoder();
    const value_bytes = encoder.encode(value);
    for(let idx = 0; idx < bytes.length; idx++) {
      bytes[idx + offset + 4] = value_bytes[idx];
    }
    writeInt32(offset, bytes.length);
    writeInt32(0, offset + 4 + bytes.length);
    return offset;
  }

  function unpack(...args) {
    const ret = [];
    for(let idx = 0; idx < args.length ; idx += 2) {
      const tag = args[idx];
      const val = args[idx + 1];
      if (tag === 0) {
        ret.push(val);
      }
      if (tag === 10) {
        ret.push(get_string(val));
      }
    }
    return ret;
  }
  function pack(...args) {
    const ret = [];
    for (let idx = 0; idx < args.length; idx += 1) {
      let arg = args[idx];
      if (typeof arg === 'number') {
        ret.push(0);
        ret.push(arg);
      } else if (typeof arg === 'string') {
        ret.push(10);
        ret.push(write_string(arg));
      }
    }
    return ret;
  }
  function call(name, ...args) {
    const arity = (args.length);
    const ret = instance.exports[`${name}/${arity}`](...pack(...args)) || [0, null];
    const _unpackedRet = unpack(...ret);
    return _unpackedRet.length === 1 ? _unpackedRet[0] : _unpackedRet;
  }
  const imports = {
    console: {
      log(...args) {
        const unpackedArgs = unpack(...args);
        console.log('log/' + (arguments.length/2), ...unpackedArgs);
        return [0, 0];
      }
    },
    erlang: {
      get_module_info() {
        throw new Error("We are not supposed to be here");
      }
    },
  };
  const instance = new WebAssembly.Instance(wasm, imports);
  console.log('main', call('main'));
  // console.log('conditional', call('conditional', 100));
  // console.log('loop', call('loop', 1));


})();
