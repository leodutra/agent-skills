Functions are total: code MUST NOT panic on valid input or `assert!` on user input. User input, CLI
arguments included, is an error the caller can handle, never a panic.

Question: does this code panic or `assert!` on input a caller or user supplies, instead of returning
an error?
