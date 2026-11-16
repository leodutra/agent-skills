// expect: clippy::option_option
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Patch {
    pub nickname: Option<Option<String>>,
}
