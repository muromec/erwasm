
# Readme

make run

# Wat

This compiles erlang into web assembly. Status: proof of concept, mostly doesnt work.

# How

Run erlang compiler to produce beam textual representation (.S file), read it and produce
web assembly textual representation. Compile web assembly and run with node.

It does something, but is not practical at all.

# Why

If typed continuations become a thing, it would be possible to implement erlang-like actor
model with mailboxes. Why not compile beam directly into wasm at this point?
