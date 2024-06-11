-module(listdemo).

-export([main/0, next/0]).

first([L|_X]) -> L.

second([_H|Tail]) -> first(Tail).

main() ->
%%  AB = [10, 12],
  A = first([1,2]),
  B = second([3,4]),
  console:log(A),
  console:log("Y", A + B).

next() ->
  AB = [$3, $4],
  A = first(AB),
  B = second(AB),
  console:log("AB", A, B),
  console:log("C", A + B).
