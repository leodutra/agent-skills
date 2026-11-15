//! Tickets: their status, the store they live in, and reassignment.
use std::collections::BTreeMap;
use std::fmt;
use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct TicketId(pub u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct UserId(pub u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Status {
    Open,
    InProgress,
    Blocked,
    Closed,
}

impl Status {
    pub const ALL: [Self; 4] = [Self::Open, Self::InProgress, Self::Blocked, Self::Closed];

    /// The stored and displayed name.
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Open => "open",
            Self::InProgress => "in-progress",
            Self::Blocked => "blocked",
            Self::Closed => "closed",
        }
    }
}

impl fmt::Display for Status {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("unknown status: {0}")]
pub struct UnknownStatus(String);

impl FromStr for Status {
    type Err = UnknownStatus;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::ALL.into_iter().find(|status| status.as_str() == s).ok_or_else(|| UnknownStatus(s.to_owned()))
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Ticket {
    pub id: TicketId,
    pub title: String,
    pub assignee: UserId,
    pub status: Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("the ticket store is unavailable")]
pub struct StoreError;

pub trait TicketStore {
    /// The ticket with this id; `Ok(None)` when there is none.
    fn get(&self, id: TicketId) -> Result<Option<Ticket>, StoreError>;
    fn save(&mut self, ticket: Ticket) -> Result<(), StoreError>;
}

#[derive(Debug, Default)]
pub struct InMemoryStore {
    tickets: BTreeMap<TicketId, Ticket>,
}

impl TicketStore for InMemoryStore {
    fn get(&self, id: TicketId) -> Result<Option<Ticket>, StoreError> {
        Ok(self.tickets.get(&id).cloned())
    }

    fn save(&mut self, ticket: Ticket) -> Result<(), StoreError> {
        self.tickets.insert(ticket.id, ticket);
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ReassignError {
    #[error("ticket {0:?} does not exist")]
    UnknownTicket(TicketId),
    #[error("ticket {0:?} is closed")]
    Closed(TicketId),
    #[error(transparent)]
    Store(#[from] StoreError),
}

pub fn reassign<S: TicketStore>(store: &mut S, ticket: TicketId, to: UserId) -> Result<(), ReassignError> {
    let mut found = store.get(ticket)?.ok_or(ReassignError::UnknownTicket(ticket))?;
    if found.status == Status::Closed {
        return Err(ReassignError::Closed(ticket));
    }
    found.assignee = to;
    Ok(store.save(found)?)
}

#[cfg(test)]
mod tests {
    use proptest::prelude::*;

    use super::*;

    fn store_with(status: Status) -> InMemoryStore {
        let mut store = InMemoryStore::default();
        store.save(Ticket { id: TicketId(1), title: "login fails".to_owned(), assignee: UserId(7), status }).unwrap();
        store
    }

    #[derive(Debug)]
    struct DownStore;

    impl TicketStore for DownStore {
        fn get(&self, _id: TicketId) -> Result<Option<Ticket>, StoreError> {
            Err(StoreError)
        }

        fn save(&mut self, _ticket: Ticket) -> Result<(), StoreError> {
            Err(StoreError)
        }
    }

    #[test]
    fn reassigns_an_open_ticket() {
        let mut store = store_with(Status::Open);
        reassign(&mut store, TicketId(1), UserId(9)).unwrap();
        assert_eq!(store.get(TicketId(1)).unwrap().map(|t| t.assignee), Some(UserId(9)));
    }

    #[test]
    fn a_closed_ticket_is_not_reassigned() {
        let mut store = store_with(Status::Closed);
        assert_eq!(reassign(&mut store, TicketId(1), UserId(9)), Err(ReassignError::Closed(TicketId(1))));
    }

    #[test]
    fn an_unknown_ticket_is_its_own_error() {
        let mut store = InMemoryStore::default();
        assert_eq!(reassign(&mut store, TicketId(2), UserId(9)), Err(ReassignError::UnknownTicket(TicketId(2))));
    }

    #[test]
    fn a_store_failure_is_not_a_missing_ticket() {
        assert_eq!(reassign(&mut DownStore, TicketId(1), UserId(9)), Err(ReassignError::Store(StoreError)));
    }

    #[test]
    fn an_unknown_status_is_rejected() {
        assert_eq!("done".parse::<Status>(), Err(UnknownStatus("done".to_owned())));
    }

    proptest! {
        #[test]
        fn status_display_parses_back(status in prop::sample::select(Status::ALL.to_vec())) {
            prop_assert_eq!(status.to_string().parse::<Status>(), Ok(status));
        }
    }
}
