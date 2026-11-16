- An operator means its mathematical or logical operation (`Add` adds); anything else is a named
  method.
- Macros last: a function, type or trait; then `macro_rules!`; then a proc macro.
- Every dependency is used: an unused one still compiles, ships and widens the supply chain.

Question: does this code break any of these rules?
