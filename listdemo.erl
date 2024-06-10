-module(listdemo).

% -export([main/0, other/0]).
-export([main/0]).

first([L|_X]) -> L.

main() ->
  N = first(["X"]),
  console:log("Y", N).
