---
type: llm
focus: trace
weight: 1
---

TicketStore::get returns Result<Option<Ticket>, E> or an equivalent: a missing ticket is Ok(None) and a store failure is Err, and reassign keeps them apart (an unknown ticket and a store failure are different error variants)
