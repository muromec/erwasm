
# Readme

make run

# Wat

This compiles erlang and elixir into web assembly. Status: alpha, kinda works, still buggy.

Message passing: proof of concept, requires WasmFx (typed continuations) extension.

# How

Run erlang compiler to produce beam textual representation (.S file), read it and produce
web assembly textual representation. Compile web assembly and run with node or in a browser.

Wasm files are statically linked, there almost no runtime beyond atom, list, and tuple manipulation,
integer serialization, etc. Process and message passing is optionally linked as a minimal runtime.

# Why

If typed continuations become a thing, it would be possible to implement erlang-like actor
model with mailboxes. Why not compile beam directly into wasm at this point?


# Examples

See https://github.com/muromec/erwasm-vue and https://github.com/muromec/erwasm-tests for examples.

# What works

Things listed below mostly work:

- encoding/decoding json with jsone mostly works (see erwasm-tests);
- atom and integer serialization;
- pattern matching, including binary matching mostly works;
- utf8 and utf16 support in buffer matching and constructing;
- basic logic and ariphmetic;
- calling function from a different module, when statically linked;
- exception handling.

Process spawning and message passing works as a proof of concept with wasm-fx, which is under the flag in Chrome and node.

Hello world in elixir seems to work as well, but wasn't tested extensively.

# What doesnt work

 - passing functions as arguments (map, fitler, etc);
 - there is no gc, no memory is ever deallocated;
 - calling functions by runtime-specified atom (erlang:apply);
 - deserialization of atoms;
 - calendars;
 - floats;
 - integers with more than 28 bits;
 - proper scheduler for processes;
 - seem shim.wat for import that don't lead anywhere;
 - hot reload, clustering, hard realtime and constant time computation.

# Memory model

In-memory representation of structures follows that of AtomVM.
