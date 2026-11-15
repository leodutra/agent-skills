//! Tickets: their status, the store they live in, and reassignment.
use std::collections::HashMap;

pub type TicketId = u64;
pub type UserId = u64;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum Status {
    Open,
    InProgress,
    Blocked,
    Closed,
}

impl Status {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Open => "open",
            Self::InProgress => "in-progress",
            Self::Blocked => "blocked",
            Self::Closed => "closed",
        }
    }

    #[must_use]
    pub fn parse(s: &str) -> Option<Self> {
        match s {
            "open" => Some(Self::Open),
            "in-progress" => Some(Self::InProgress),
            "blocked" => Some(Self::Blocked),
            "closed" => Some(Self::Closed),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Ticket {
    pub id: TicketId,
    pub title: String,
    pub assignee: UserId,
    pub status: Status,
}

pub trait TicketStore {
    fn get(&self, id: TicketId) -> Option<Ticket>;
    fn save(&mut self, ticket: Ticket);
}

#[derive(Debug, Default)]
pub struct InMemoryStore {
    tickets: HashMap<TicketId, Ticket>,
}

impl TicketStore for InMemoryStore {
    fn get(&self, id: TicketId) -> Option<Ticket> {
        self.tickets.get(&id).cloned()
    }

    fn save(&mut self, ticket: Ticket) {
        self.tickets.insert(ticket.id, ticket);
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ReassignError {
    #[error("ticket not found")]
    NotFound,
    #[error("ticket is closed")]
    Closed,
}

pub fn reassign<S: TicketStore>(store: &mut S, ticket: TicketId, to: UserId) -> Result<(), ReassignError> {
    let mut found = store.get(ticket).ok_or(ReassignError::NotFound)?;
    if found.status == Status::Closed {
        return Err(ReassignError::Closed);
    }
    found.assignee = to;
    store.save(found);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn store_with(status: Status) -> InMemoryStore {
        let mut store = InMemoryStore::default();
        store.save(Ticket { id: 1, title: "login fails".to_owned(), assignee: 7, status });
        store
    }

    #[test]
    fn reassigns_an_open_ticket() {
        let mut store = store_with(Status::Open);
        reassign(&mut store, 1, 9).unwrap();
        assert_eq!(store.get(1).map(|t| t.assignee), Some(9));
    }

    #[test]
    fn a_closed_ticket_is_not_reassigned() {
        let mut store = store_with(Status::Closed);
        assert_eq!(reassign(&mut store, 1, 9), Err(ReassignError::Closed));
    }

    #[test]
    fn status_names_round_trip() {
        for status in [Status::Open, Status::InProgress, Status::Blocked, Status::Closed] {
            assert_eq!(Status::parse(status.as_str()), Some(status));
        }
    }
}
