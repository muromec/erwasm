-module(listdemo).

-export([main/0]).

first([L|_X]) -> L.

second([_H|Tail]) -> first(Tail).

main() ->
  A = first([1,2]),
  B = second([3,4]),
  console:log("Y", A + B).
