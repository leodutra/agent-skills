- A domain type holds one canonical, valid form of its value: minimal, with no leftover formatting or
  unused data, comparing and sorting correctly as stored. Parsing does whatever input needs to reach
  it (decodes the source's encoding, normalizes equivalent spellings) or rejects; every output
  (`Display`, serde, SQL, HTML, a log line) is derived from it for its sink and formatted or escaped
  there. No sink's form is ever stored.

Question: does this code break this rule?
