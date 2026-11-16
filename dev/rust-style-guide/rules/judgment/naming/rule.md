A name says what the thing does, never a catch-all (`Manager`, `Service`, `Utils`) or an
abbreviation a newcomer wouldn't know; a single-letter lifetime or generic parameter only where one
letter is unambiguous. Accessors follow std: `foo()`, `foo_mut()`, `set_foo()`, `take_foo()`,
`replace_foo()`, never `get_foo()`.

Question: does any name in this code break this rule?
