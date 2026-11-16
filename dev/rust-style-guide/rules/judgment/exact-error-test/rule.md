Per constructor: one accepted input, and every domain rejection reached by a test asserting its exact
error (`assert_eq!(Port::try_new(0), Err(ZeroPort))`).

Question: does a test in this code assert a rejection less exactly than the specific error value (a
wildcard `Err(_)`, `is_err()`, a message substring), or leave one of the constructor's rejections
untested?
