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

  function writeInt32(bytes, offset, value) {
    bytes[offset + 3] = (value >>> 24) & 0xFF;
    bytes[offset + 2] = (value >>> 16) & 0xFF;
    bytes[offset + 1] = (value >>> 8) & 0xFF;
    bytes[offset + 0] = (value) & 0xFF;
  }

  function decode_string(list) {
    const bytes = new Uint8Array(list);
    const ret = new TextDecoder("utf8").decode(bytes);
    return ret;
  }

  function maybe_string(value) {
    if (!Array.isArray(value)) {
      return value;
    }
    if (value.every((element) => (typeof element === 'number') && element >= 0x21 && element <= 126)) {
      return decode_string(value);
    }
    return value
  }

  function write_string(value) {
    const bytes = new Uint8Array(instance.exports.memory.buffer);
    let offset = readInt32(0);
    const ret = offset;
    const encoder = new TextEncoder();
    const value_bytes = encoder.encode(value);
    for(let idx = 0; idx < value_bytes.length; idx += 1) {
      writeInt32(bytes, offset, tag2((offset + 8), 0b01));
      writeInt32(bytes, offset + 4, tagF(value_bytes[idx]));
      offset += 8;
    }
    writeInt32(bytes, offset, 0x3b);
    writeInt32(bytes, offset + 4, 0);
    writeInt32(bytes, 0, offset + 8);

    // console.log('got ret', ret, offset);
    return ret;
  }

  function readList(offset, acc) {
    const tail = readInt32(offset);
    const value = readInt32(offset + 4);

    if (tail === 0x3b) {
      return acc;
    }
    return readList(tail >> 2, [...acc, read(value)]);
  }

  function read(v) {
    let val = v;
    let mem = v >>> 2;

    if (((val & 0b11) === 0b10)) { /// mem pointer
      val =  readInt32(mem);
    }
    if (((val & 0b11) === 0b01)) { /// list pointer
      return readList(mem, []);
    }

    if (((val & 0xF) === 0xF)) { // integer
      return (val >>> 4);
    }
    return null;

  }

  function unpack(...args) {
    // console.log('u', args);
    const ret = args.map(read);
    return ret;
  }
  function tag2(value, tag) {
    return value << 2 | tag;
  }
  function tagF(value) {
    return value << 4 | 0xF;
  }

  function pack(...args) {
    return args.map((arg) => {
      if (typeof arg === 'number') {
        return (arg << 4 | 0xF);
      } else if (typeof arg === 'string') {
        const mem = write_string(arg);
        return tag2(mem, 0b10);
      }
      return 0x01;
    });
  }
  function call(name, ...args) {
    const arity = (args.length);
    const packedArgs = pack(...args);
    // console.log('packed args', packedArgs);
    const ret = instance.exports[`${name}/${arity}`](...packedArgs);
    const _unpackedRet = unpack(ret).map(maybe_string);

    return _unpackedRet.length === 1 ? _unpackedRet[0] : _unpackedRet;
  }
  const imports = {
    console: {
      log(...args) {
        const unpackedArgs = unpack(...args)
          .map(maybe_string);
        console.log('log/' + (arguments.length), ...unpackedArgs);
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
  console.log('second', call('second'));
  console.log('n', call('n', 1));
  console.log('other', call('other'));
  console.log('conditional', call('conditional', 90));
  console.log('conditional', call('conditional', 900));
  console.log('loop', call('loop', 1));
  console.log('printStr', call('printStr', 'ME'));


})();
