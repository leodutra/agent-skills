#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Invite {
    pub to: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NotAnEmail;

/// Builds the invite for an address the signup form already validated.
///
/// # Errors
/// [`NotAnEmail`] when `to` has no `@`.
pub fn invite(to: &str) -> Result<Invite, NotAnEmail> {
    if !to.contains('@') {
        return Err(NotAnEmail);
    }
    Ok(Invite { to: to.to_owned() })
}
