#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NicknamePatch {
    Keep,
    Clear,
    Set(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Patch {
    pub nickname: NicknamePatch,
}
