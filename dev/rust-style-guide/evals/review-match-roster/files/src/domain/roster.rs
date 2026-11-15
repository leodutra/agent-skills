//! A match roster: the players picked for one game, the first of them the captain.
use std::collections::BTreeMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct PlayerId(pub u32);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Player {
    pub id: PlayerId,
    pub name: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Roster {
    players: Vec<Player>,
    minutes: BTreeMap<PlayerId, u32>,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RosterError {
    #[error("a roster needs at least one player")]
    Empty,
    #[error("player {0:?} is picked twice")]
    Duplicate(PlayerId),
    #[error("the roster has no captain")]
    NoCaptain,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MinutesError {
    #[error("player {0:?} is not on this roster")]
    NotOnRoster(PlayerId),
    #[error("minutes for player {0:?} would overflow")]
    Overflow(PlayerId),
}

impl Roster {
    /// The coach's pick, captain first.
    pub fn try_new(players: Vec<Player>) -> Result<Self, RosterError> {
        if players.is_empty() {
            return Err(RosterError::Empty);
        }
        let mut minutes = BTreeMap::new();
        for player in &players {
            if minutes.insert(player.id, 0).is_some() {
                return Err(RosterError::Duplicate(player.id));
            }
        }
        Ok(Self { players, minutes })
    }

    /// The captain: the first player picked.
    pub fn captain(&self) -> Result<&Player, RosterError> {
        self.players.first().ok_or(RosterError::NoCaptain)
    }

    /// The player with this id, if they are on the roster.
    #[must_use]
    pub fn player(&self, id: PlayerId) -> Option<&Player> {
        self.players.iter().find(|player| player.id == id)
    }

    /// Adds minutes played by a player on this roster.
    pub fn add_minutes(&mut self, id: PlayerId, played: u32) -> Result<(), MinutesError> {
        let total = self.minutes.get_mut(&id).ok_or(MinutesError::NotOnRoster(id))?;
        *total = total.checked_add(played).ok_or(MinutesError::Overflow(id))?;
        Ok(())
    }

    /// Minutes the captain played, for the match report.
    pub fn captain_minutes(&self) -> Result<u32, RosterError> {
        let captain = self.captain()?;
        Ok(self.minutes.get(&captain.id).copied().unwrap_or_default())
    }
}
