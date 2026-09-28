// A transition, not a constructor: each forbidden transition is a rejection too.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Order {
    Pending { total: u32 },
    Confirmed { total: u32 },
    Cancelled,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OrderError {
    OverLimit,
    NotPending,
}

impl Order {
    pub fn confirm(self, limit: u32) -> Result<Self, OrderError> {
        match self {
            Self::Pending { total } if total > limit => Err(OrderError::OverLimit),
            Self::Pending { total } => Ok(Self::Confirmed { total }),
            Self::Confirmed { .. } | Self::Cancelled => Err(OrderError::NotPending), // expect: untested-rejection
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn confirms_within_the_limit() {
        assert_eq!(Order::Pending { total: 5 }.confirm(10), Ok(Order::Confirmed { total: 5 }));
    }

    #[test]
    fn rejects_over_the_limit() {
        assert_eq!(Order::Pending { total: 50 }.confirm(10), Err(OrderError::OverLimit));
    }
}
