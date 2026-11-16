Money and quantity arithmetic that can overflow uses `checked_*` and returns an error; check a
possibly-zero divisor before `/` or `%`.

Question: can money or quantity arithmetic in this code overflow, or divide by a possibly-zero value,
without a check that returns an error?
