
value : list 
  | tuple 
  | number
  | string
  | binary
  | atom
  | map
  | fun

list : "[" [value ("," value)*] "]"
tuple : "{" [value ("," value)*] "}"

map_pair: value "=>" value
map: "#{" [map_pair ("," map_pair)*] "}"

fun: "fun " atom ":" atom "/" number

string : ESCAPED_STRING
number : SIGNED_NUMBER

escaped_atom : ESCAPED_ATOM
bare_atom : LCASE_LETTER (UNDER|LCASE_LETTER|UCASE_LETTER|DIGIT)*
atom : escaped_atom | bare_atom

tuple_statement : tuple "."
atom_statement : bare_atom "."
statement : tuple_statement | atom_statement

binary_part : string | number
binary : "<<" [binary_part ("," binary_part)*] ">>"

module: statement*

COMMENT: /%[^\n]*/

_STRING_INNER: /.*?/
_STRING_ESC_INNER: _STRING_INNER /(?<!\\)(\\\\)*?/

UNDER: "_"
ESCAPED_ATOM : "'" _STRING_ESC_INNER "'"


%ignore COMMENT

%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER
%import common.WS
%import common.LCASE_LETTER
%import common.UCASE_LETTER
%import common.DIGIT
%ignore WS
