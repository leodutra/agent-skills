// expect: clippy::expl_impl_clone_on_copy
#[derive(Debug, Copy, PartialEq, Eq)]
pub struct Level(pub u8);

impl Clone for Level {
    fn clone(&self) -> Self {
        *self
    }
}
