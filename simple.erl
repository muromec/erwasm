-module(simple).

-export([main/0, second/0, other/0, sum/2, sum/1]).

main() ->
  console:log(1, 3, "Hi"),
  1 + 1.


second() ->
  "X-Name".

other() ->
  main().


sum(A, B) -> 
  console:log("A", A),
  console:log("B", B),
  C = A + B,
  console:log("C", C),
  C.

sum(A) -> 
  sum(A, 1).
